import asyncio
import re
import hashlib
import json
import os
import time
import io
import base64
import urllib.request
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from gemini_webapi import GeminiClient, set_log_level, logger
from gemini_webapi.constants import Model
from gemini_webapi.exceptions import AuthError

# ---------------------------------------------------------------------------
# Setup and Configuration
# ---------------------------------------------------------------------------

def load_env_file(dotenv_path=".env"):
    """ โหลด Environment Variables จากไฟล์ .env """
    path = Path(dotenv_path)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("=", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                val = parts[1].strip().strip('"').strip("'")
                os.environ[key] = val

load_env_file()

# ดึงค่าคุกกี้
SECURE_1PSID = os.getenv("SECURE_1PSID")
SECURE_1PSIDTS = os.getenv("SECURE_1PSIDTS")

# ถ้าไม่มี .env ลองดึงจาก cookies.json
if not SECURE_1PSID:
    cookies_json_path = Path("cookies.json")
    if cookies_json_path.exists():
        try:
            data = json.loads(cookies_json_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for item in data:
                    if item.get("name") == "__Secure-1PSID":
                        SECURE_1PSID = item.get("value")
                    elif item.get("name") == "__Secure-1PSIDTS":
                        SECURE_1PSIDTS = item.get("value")
            elif isinstance(data, dict):
                SECURE_1PSID = data.get("__Secure-1PSID") or data.get("cookies", {}).get("__Secure-1PSID")
                SECURE_1PSIDTS = data.get("__Secure-1PSIDTS") or data.get("cookies", {}).get("__Secure-1PSIDTS")
        except Exception as e:
            print(f"⚠️ ไม่สามารถอ่านคุกกี้จาก cookies.json ได้: {e}")

# ---------------------------------------------------------------------------
# FastAPI initialization
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Gemini Web API Gateway",
    description="OpenAI Compatible API for reverse-engineered Gemini Web API wrapper.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global State & Client Management
# ---------------------------------------------------------------------------

client: Optional[GeminiClient] = None
# cache ของแชทเซสชัน: { prefix_hash: ChatSession }
session_cache: Dict[str, Any] = {}
# ล็อกสำหรับการเขียน cache เพื่อป้องกัน race conditions
cache_lock = asyncio.Lock()

# แผนผังการแปลงชื่อโมเดล
MODEL_MAPPING = {
    "gemini-3-pro": Model.BASIC_PRO,
    "gemini-3-flash": Model.BASIC_FLASH,
    "gemini-3-flash-thinking": Model.BASIC_THINKING,
    "gemini-3-pro-plus": Model.PLUS_PRO,
    "gemini-3-flash-plus": Model.PLUS_FLASH,
    "gemini-3-flash-thinking-plus": Model.PLUS_THINKING,
    "gemini-3-pro-advanced": Model.ADVANCED_PRO,
    "gemini-3-flash-advanced": Model.ADVANCED_FLASH,
    "gemini-3-flash-thinking-advanced": Model.ADVANCED_THINKING,
    "unspecified": Model.UNSPECIFIED
}

def get_model_enum(model_name: str) -> Model:
    """ แปลงข้อความชื่อโมเดลให้เป็น Model Enum ของ gemini_webapi """
    model_name_lower = model_name.lower()
    
    # จับคู่ตรงๆ
    if model_name_lower in MODEL_MAPPING:
        return MODEL_MAPPING[model_name_lower]
        
    # ค้นหาตามคีย์เวิร์ด
    if "thinking" in model_name_lower:
        return Model.BASIC_THINKING
    elif "pro" in model_name_lower:
        return Model.BASIC_PRO
    elif "flash" in model_name_lower:
        return Model.BASIC_FLASH
        
    return Model.UNSPECIFIED

def get_messages_hash(messages: List[dict]) -> str:
    """ สร้างแฮชของประวัติการคุยเพื่อให้ระบุตัวเซสชันได้ """
    serialized = json.dumps(messages, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def format_history_prompt(messages: List[dict]) -> str:
    """ แปลงประวัติแชททั้งหมดให้กลายเป็น Prompt เดียวสำหรับกรณีที่ไม่มีเซสชันในแคช """
    prompt_parts = []
    system_instruction = ""
    
    for msg in messages:
        role = msg.get("role", "user")
        content = extract_text_from_content(msg.get("content"))
        if role == "system":
            system_instruction = content
        elif role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
            
    full_prompt = ""
    if system_instruction:
        full_prompt += f"[System Instructions]\n{system_instruction}\n\n"
    
    if prompt_parts:
        full_prompt += "[Conversation History]\n" + "\n".join(prompt_parts) + "\n\n"
        
    # ทิ้งท้ายเพื่อให้โมเดลตอบกลับในฐานะ Assistant
    full_prompt += "Assistant: "
    return full_prompt

@app.on_event("startup")
async def startup_event():
    global client
    set_log_level("DEBUG")
    
    if not SECURE_1PSID:
        logger.error("❌ ไม่พบค่า __Secure-1PSID ใน .env หรือ cookies.json!")
        logger.error("กรุณาตั้งค่าคุกกี้ก่อนรัน API Server")
        return
        
    logger.info("🔌 กำลังเริ่มต้นระบบเชื่อมต่อกับ Google Gemini...")
    client = GeminiClient(secure_1psid=SECURE_1PSID, secure_1psidts=SECURE_1PSIDTS or "")
    try:
        await client.init(timeout=30, auto_refresh=True)
        port = int(os.getenv("PORT", 8000))
        logger.info(f"✅ เชื่อมต่อและยืนยันตัวตนสำเร็จ! API พร้อมให้บริการที่ http://localhost:{port}")
    except AuthError as e:
        logger.error(f"❌ การยืนยันตัวตนล้มเหลว: {e}")
        client = None

@app.on_event("shutdown")
async def shutdown_event():
    global client
    if client:
        logger.info("🔌 กำลังปิดการเชื่อมต่อ...")
        await client.close()
        logger.info("✅ ปิดการเชื่อมต่อเรียบร้อยแล้ว")

# ---------------------------------------------------------------------------
# Pydantic Schemas and Handlers for OpenAI compatibility
# ---------------------------------------------------------------------------

from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"❌ Validation Error: {exc.errors()}")
    try:
        body = await request.json()
        logger.error(f"Request body JSON: {json.dumps(body, indent=2)}")
    except Exception:
        try:
            body = await request.body()
            logger.error(f"Request body Raw: {body}")
        except Exception:
            pass
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
# sanitize_system_prompt was removed as Cline-specific prompt filtering is no longer required.

def extract_text_from_content(content: Any) -> str:
    """ ดึงข้อความดิบออกมาจากโครงสร้างของ OpenAI content (รองรับทั้ง String, List และ Dict) """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            elif isinstance(part, str):
                text_parts.append(part)
        return "\n".join(text_parts)
    if content is None:
        return ""
    return str(content)

async def download_image(url: str) -> bytes:
    """ ดาวน์โหลดรูปภาพจาก URL เพื่อแปลงเป็น bytes """
    def _fetch():
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read()
    return await asyncio.to_thread(_fetch)

def extract_text_and_files_from_content(content: Any) -> tuple[str, List[str]]:
    """ ดึงข้อความดิบ และรายการลิงก์รูปภาพ (Base64 หรือ URL) ออกมาจาก OpenAI content """
    if isinstance(content, str):
        return content, []
    if content is None:
        return "", []
        
    text_parts = []
    image_urls = []
    
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict):
                part_type = part.get("type")
                if part_type == "text":
                    text_parts.append(part.get("text", ""))
                elif part_type == "image_url":
                    image_url_obj = part.get("image_url")
                    if isinstance(image_url_obj, dict):
                        url = image_url_obj.get("url", "")
                        if url:
                            image_urls.append(url)
            elif isinstance(part, str):
                text_parts.append(part)
        return "\n".join(text_parts), image_urls
        
    return str(content), []

class ChatMessage(BaseModel):
    role: str
    content: Optional[Any] = None

    model_config = {
        "extra": "allow"
    }

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    user: Optional[str] = None

    model_config = {
        "extra": "allow"
    }

class ImageGenerationRequest(BaseModel):
    prompt: str
    n: Optional[int] = 1
    size: Optional[str] = "1024x1024"
    response_format: Optional[str] = "url"
    model: Optional[str] = "dall-e-3"
    image: Optional[str] = None

    model_config = {
        "extra": "allow"
    }

# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Gemini Web API Gateway is running.",
        "initialized": client is not None
    }

@app.get("/v1/models")
async def list_models():
    """ คืนค่าโมเดลทั้งหมดที่รองรับให้ Cline / ไคลเอนต์อื่นๆ ตรวจสอบได้ """
    models = [
        {"id": "gemini-3-pro", "object": "model", "created": int(time.time()), "owned_by": "google"},
        {"id": "gemini-3-flash", "object": "model", "created": int(time.time()), "owned_by": "google"},
        {"id": "gemini-3-flash-thinking", "object": "model", "created": int(time.time()), "owned_by": "google"},
        {"id": "unspecified", "object": "model", "created": int(time.time()), "owned_by": "google"}
    ]
    return {"object": "list", "data": models}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    global client
    if not client:
        raise HTTPException(status_code=503, detail="Gemini client is not initialized or authenticated.")
        
    messages_dict = []
    for m in request.messages:
        messages_dict.append({
            "role": m.role,
            "content": m.content
        })
    if not messages_dict:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty.")
        
    model_enum = get_model_enum(request.model)
    
    # 1. จัดสรร Chat Session (Heuristics)
    chat_session = None
    last_user_message = ""
    is_new_session = True
    prefix_hash = None
    
    # ดึงข้อมูล Prompt ข้อความและไฟล์แนบจากข้อความล่าสุดของผู้ใช้
    last_content = messages_dict[-1]["content"]
    last_user_message_text, image_urls = extract_text_and_files_from_content(last_content)
    
    files_to_upload = []
    for url in image_urls:
        if url.startswith("data:image/"):
            try:
                header, base64_data = url.split(",", 1)
                ext = ".png"
                if "jpeg" in header or "jpg" in header:
                    ext = ".jpg"
                elif "gif" in header:
                    ext = ".gif"
                elif "webp" in header:
                    ext = ".webp"
                
                file_bytes = base64.b64decode(base64_data)
                bio = io.BytesIO(file_bytes)
                bio.name = f"image_{int(time.time())}{ext}"
                files_to_upload.append(bio)
                logger.info(f"📸 พบบทสนทนาแนบรูปภาพแบบ Base64 (นามสกุล: {ext})")
            except Exception as e:
                logger.error(f"❌ ไม่สามารถดีโค้ด Base64 image ได้: {e}")
        elif url.startswith("http://") or url.startswith("https://"):
            try:
                logger.info(f"📸 กำลังดาวน์โหลดรูปภาพจาก URL: {url}")
                file_bytes = await download_image(url)
                ext = ".jpg"
                parsed_url = urlparse(url)
                path_ext = os.path.splitext(parsed_url.path)[1]
                if path_ext.lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                    ext = path_ext.lower()
                
                bio = io.BytesIO(file_bytes)
                bio.name = f"image_{int(time.time())}{ext}"
                files_to_upload.append(bio)
            except Exception as e:
                logger.error(f"❌ ไม่สามารถดาวน์โหลดรูปภาพจาก URL ได้: {url}, Error: {e}")

    last_user_message = last_user_message_text
    
    if len(messages_dict) > 1:
        # มีการตอบโต้มาก่อนหน้านี้
        prefix = messages_dict[:-1]
        prefix_hash = get_messages_hash(prefix)
        
        async with cache_lock:
            if prefix_hash in session_cache:
                chat_session = session_cache[prefix_hash]
                is_new_session = False
                logger.info(f"🎯 Cache Hit! รันต่อจากเซสชันเดิม (Prefix Hash: {prefix_hash[:8]})")
                
    # 2. กรณีที่ไม่พบเซสชันในแคช (Cache Miss)
    if is_new_session:
        logger.info("⚡ Cache Miss! กำลังสร้างห้องแชทใหม่สำหรับประวัติแชทชุดนี้")
        chat_session = client.start_chat(model=model_enum)
        
        if len(messages_dict) > 1:
            # แปลงบทสนทนาเก่าเป็น Prompt เดียวป้อนเข้าเครื่องแชทใหม่
            last_user_message = format_history_prompt(messages_dict)
            
    # 3. ส่วนของการส่งข้อมูลและส่งกลับ (Streaming / Non-Streaming)
    logger.info(f"📤 Outgoing Model: {model_enum.name if hasattr(model_enum, 'name') else model_enum} | Prompt Length: {len(last_user_message)}")
    logger.debug(f"📝 Full Outgoing Prompt:\n{last_user_message}")
    created_time = int(time.time())
    completion_id = f"chatcmpl-{hash(last_user_message)}"
    
    if request.stream:
        # --- แบบ STREAMING RESPONSE ---
        async def stream_generator():
            full_response_text = ""
            full_thinking_text = ""
            
            try:
                async for chunk in chat_session.send_message_stream(last_user_message, files=files_to_upload or None):
                    # ส่งความคิดวิเคราะห์ก่อน (ถ้ามี)
                    if chunk.thoughts_delta:
                        full_thinking_text += chunk.thoughts_delta
                        chunk_data = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": request.model,
                            "choices": [{
                                "index": 0,
                                "delta": {"role": "assistant", "reasoning_content": chunk.thoughts_delta},
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                        
                    # ส่งข้อความผลลัพธ์ปกติ
                    if chunk.text_delta:
                        full_response_text += chunk.text_delta
                        chunk_data = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": request.model,
                            "choices": [{
                                "index": 0,
                                "delta": {"role": "assistant", "content": chunk.text_delta},
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                        
                # อัปเดตเซสชันใหม่ลงแคชเมื่อตอบเสร็จ
                full_conversation = messages_dict + [{"role": "assistant", "content": full_response_text}]
                new_hash = get_messages_hash(full_conversation)
                async with cache_lock:
                    session_cache[new_hash] = chat_session
                    # ลบของเก่าออกเพื่อไม่ให้เปลืองเมมโมรี่ (ถ้ามี)
                    if prefix_hash and prefix_hash in session_cache:
                        session_cache.pop(prefix_hash, None)
                
                # ส่งจบสตรีม
                final_chunk = {
                    "id": completion_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }]
                }
                yield f"data: {json.dumps(final_chunk, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                
            except BaseException as e:
                # ลบออกจากแคชทันทีเมื่อมีปัญหาหรือผู้ใช้ยกเลิก
                if prefix_hash and prefix_hash in session_cache:
                    async with cache_lock:
                        session_cache.pop(prefix_hash, None)
                        logger.warning(f"🧹 ลบเซสชันที่เกิดปัญหาออกจากแคชแล้ว (Prefix Hash: {prefix_hash[:8]})")
                
                # ถ้ากดยกเลิกสตรีม หรือผู้ใช้หยุดแชท
                if isinstance(e, (GeneratorExit, asyncio.CancelledError)):
                    logger.warning(f"⚠️ ผู้ใช้ยกเลิกหรือปิดการเชื่อมต่อสตรีม ({type(e).__name__})")
                    raise e
                
                # กรณีเกิด Error อื่นๆ
                logger.error(f"❌ เกิดข้อผิดพลาดขณะสตรีมคำตอบ: {e}")
                try:
                    error_chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created_time,
                        "model": request.model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": f"\n\n[API Gateway Error]: {e}"},
                            "finish_reason": "stop"
                        }]
                    }
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception:
                    pass
                
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
        
    else:
        # --- แบบ NON-STREAMING RESPONSE ---
        try:
            response = await chat_session.send_message(last_user_message, files=files_to_upload or None)
            full_response_text = response.text
            
            # อัปเดตลงแคช
            full_conversation = messages_dict + [{"role": "assistant", "content": full_response_text}]
            new_hash = get_messages_hash(full_conversation)
            async with cache_lock:
                session_cache[new_hash] = chat_session
                if prefix_hash and prefix_hash in session_cache:
                    session_cache.pop(prefix_hash, None)
                    
            message_payload = {
                "role": "assistant",
                "content": full_response_text
            }
            if response.thoughts:
                message_payload["reasoning_content"] = response.thoughts
                
            response_data = {
                "id": completion_id,
                "object": "chat.completion",
                "created": created_time,
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": message_payload,
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(last_user_message) // 4,  # ประมาณการคร่าวๆ
                    "completion_tokens": len(full_response_text) // 4,
                    "total_tokens": (len(last_user_message) + len(full_response_text)) // 4
                }
            }
            return JSONResponse(content=response_data)
            
        except BaseException as e:
            logger.error(f"❌ เกิดข้อผิดพลาดใน API: {e}")
            if prefix_hash and prefix_hash in session_cache:
                async with cache_lock:
                    session_cache.pop(prefix_hash, None)
                    logger.warning(f"🧹 ลบเซสชันที่เกิดปัญหาออกจากแคชแล้ว (Prefix Hash: {prefix_hash[:8]})")
            if isinstance(e, Exception):
                raise HTTPException(status_code=500, detail=str(e))
            raise e

@app.post("/v1/images/generations")
async def generate_images(request: ImageGenerationRequest):
    global client
    if not client:
        raise HTTPException(status_code=503, detail="Gemini client is not initialized or authenticated.")
        
    prompt = request.prompt
    # ดึงค่า size หรือใช้ default 1024x1024
    size = request.size or "1024x1024"
    
    # แปลงค่า size ให้เป็นคำสั่ง Aspect Ratio สำหรับโมเดลสร้างภาพของ Gemini (Imagen 3)
    aspect_map = {
        "1024x1024": "1:1 square",
        "1600x900": "16:9 widescreen",
        "1920x1080": "16:9 widescreen",
        "900x1600": "9:16 vertical",
        "1080x1920": "9:16 vertical",
        "4:3": "4:3 landscape",
        "3:2": "3:2",
        "16:9": "16:9 widescreen",
        "9:16": "9:16 vertical",
        "1:1": "1:1 square"
    }
    
    aspect_desc = aspect_map.get(size.lower())
    if aspect_desc:
        prompt = f"{prompt} in {aspect_desc} aspect ratio"
    else:
        prompt = f"{prompt} in {size} aspect ratio"
        
    # บังคับเพิ่มคำสั่งสร้างภาพหากยังไม่มี
    if not any(keyword in prompt.lower() for keyword in ["generate", "create", "draw", "paint", "make a picture", "ภาพ", "สร้างภาพ", "วาด"]):
        prompt = f"Generate an image of: {prompt}"
        
    # จัดเตรียมรูปภาพแนบอ้างอิง (ถ้ามี)
    files_to_upload = []
    if request.image:
        url = request.image
        if url.startswith("data:image/"):
            try:
                header, base64_data = url.split(",", 1)
                ext = ".png"
                if "jpeg" in header or "jpg" in header:
                    ext = ".jpg"
                elif "gif" in header:
                    ext = ".gif"
                elif "webp" in header:
                    ext = ".webp"
                
                file_bytes = base64.b64decode(base64_data)
                bio = io.BytesIO(file_bytes)
                bio.name = f"image_{int(time.time())}{ext}"
                files_to_upload.append(bio)
                logger.info(f"🎨 แนบรูปภาพต้นแบบสร้างรูปภาพแบบ Base64 (นามสกุล: {ext})")
            except Exception as e:
                logger.error(f"❌ ไม่สามารถดีโค้ด Base64 image สำหรับ Image Generation ได้: {e}")
        elif url.startswith("http://") or url.startswith("https://"):
            try:
                logger.info(f"🎨 กำลังดาวน์โหลดรูปภาพอ้างอิงจาก URL: {url}")
                file_bytes = await download_image(url)
                ext = ".jpg"
                parsed_url = urlparse(url)
                path_ext = os.path.splitext(parsed_url.path)[1]
                if path_ext.lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                    ext = path_ext.lower()
                
                bio = io.BytesIO(file_bytes)
                bio.name = f"image_{int(time.time())}{ext}"
                files_to_upload.append(bio)
            except Exception as e:
                logger.error(f"❌ ไม่สามารถดาวน์โหลดรูปภาพอ้างอิงได้: {url}, Error: {e}")

    logger.info(f"🎨 Generating image via Web API with prompt: {prompt} | requested size: {size} | reference image: {bool(files_to_upload)}")
    
    try:
        response = await client.generate_content(prompt, files=files_to_upload or None)
        
        if not response.images:
            raise HTTPException(
                status_code=400, 
                detail=f"No image was generated by the model. Response text: {response.text}"
            )
            
        data_list = []
        for img in response.images:
            data_list.append({"url": img.url})
            
        # คืนค่าตามโครงสร้างมาตรฐานของ OpenAI Images API
        return {
            "created": int(time.time()),
            "data": data_list[:request.n] if request.n else data_list
        }
    except Exception as e:
        logger.error(f"❌ Failed to generate image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # รันบน localhost หรือ 0.0.0.0 ก็ได้
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=False)
