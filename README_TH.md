# 🤖 คู่มือการเริ่มต้นใช้งานอย่างง่าย (Gemini-API Setup Guide)

คู่มือนี้แนะนำการติดตั้งและเรียกใช้งานโปรเจกต์ **Gemini-API** (Python Wrapper สำหรับ Google Gemini Web App) อย่างละเอียดเป็นภาษาไทย

---

## 📌 สิ่งที่ต้องเตรียม (Prerequisites)
- **Python 3.10 ขึ้นไป** (ตรวจสอบโดยพิมพ์ `python3 --version` ใน Terminal)
- บัญชี Google ที่ล็อกอินเข้าใช้งาน [Google Gemini](https://gemini.google.com) เรียบร้อยแล้ว

---

## 🚀 ขั้นตอนการติดตั้ง (Step-by-Step Installation)

### 1. โคลนโปรเจกต์ลงเครื่อง (Clone Repository)
หากคุณเพิ่งเริ่ม ให้โคลน Git หรือเปิดโฟลเดอร์นี้ใน Terminal ของคุณ:
```bash
git clone https://github.com/HanaokaYuzu/Gemini-API.git
cd Gemini-API
```

### 2. สร้างและใช้งาน Virtual Environment (venv)
เพื่อความเป็นระเบียบและไม่รบกวน Python Library ตัวอื่นๆ ในเครื่อง แนะนำให้สร้างสภาพแวดล้อมจำลอง (Virtual Environment):
```bash
# สร้าง venv
python3 -m venv .venv

# เปิดใช้งาน venv (บน macOS / Linux)
source .venv/bin/activate

# เปิดใช้งาน venv (บน Windows)
# .venv\Scripts\activate
```

### 3. ติดตั้ง Dependencies (Install Packages)
ติดตั้งไลบรารีของโปรเจกต์ในโหมดพัฒนา (Editable Mode) รวมถึงตัวเลือกดึงคุกกี้จากเบราว์เซอร์อัตโนมัติ (Optional: Browser Cookie Export):
```bash
pip install -e ".[browser]"
```

---

## 🔑 วิธีรับค่าคุกกี้เพื่อยืนยันตัวตน (Authentication Setup)

มี 2 วิธีหลักในการยืนยันตัวตนเพื่อให้สคริปต์ใช้งาน Gemini บัญชีของคุณได้:

### วิธีที่ 1: ดึงคุกกี้อัตโนมัติจากเบราว์เซอร์ (ง่ายที่สุด ⚡)
หากคุณล็อกอินบัญชี Google ใน Chrome, Edge, Safari หรือ Firefox ไว้ในเครื่องอยู่แล้ว ระบบจะพยายามเข้าถึงและดึงคุกกี้ที่จำเป็นมาใช้ในการยืนยันตัวตนให้อัตโนมัติโดยที่คุณไม่ต้องกรอกข้อมูลคีย์ใดๆ เอง

### วิธีที่ 2: ระบุคุกกี้ด้วยตัวเอง (Manual Setup)
ในกรณีที่ใช้งานบนเซิร์ฟเวอร์แบบไม่มีหน้าต่าง GUI (เช่น Docker หรือ Cloud VPS) หรือตัวเบราว์เซอร์ไม่รองรับการดึงอัตโนมัติ ให้ทำตามขั้นตอนนี้:

1. เปิดเบราว์เซอร์และเข้าไปที่ [Google Gemini](https://gemini.google.com) จากนั้นลงชื่อเข้าใช้งาน
2. กดปุ่ม `F12` บนคีย์บอร์ดเพื่อเปิด Web Inspector (หรือคลิกขวาที่หน้าเว็บแล้วเลือก "Inspect/ตรวจสอบ")
3. ไปที่แท็บ **Network** แล้วทำการรีเฟรชหน้าเว็บ (F5) หนึ่งครั้ง
4. คลิกเลือก Request ใดก็ได้ในแท็บ Network จากนั้นดูที่รายละเอียดของ Headers ในส่วน **Cookie** คัดลอกค่าคุกกี้ 2 ตัวดังนี้:
   - `__Secure-1PSID`
   - `__Secure-1PSIDTS`
5. สร้างไฟล์ชื่อ `.env` ไว้ในไดเรกทอรีหลักของโปรเจกต์ และระบุค่าดังนี้:
   ```env
   SECURE_1PSID="ค่าคุกกี้__Secure-1PSIDที่คัดลอกมา"
   SECURE_1PSIDTS="ค่าคุกกี้__Secure-1PSIDTSที่คัดลอกมา"
   ```
   *หรือ* คุณสามารถสร้างไฟล์ `cookies.json` และนำคุกกี้ไปเก็บไว้ในรูปแบบ JSON ได้เช่นกัน

---

## 🚀 เริ่มทดสอบระบบ

### 1. รันไฟล์ตัวอย่างการพัฒนา (`example.py`)
เราได้จัดเตรียมไฟล์ตัวอย่าง [example.py](file:///Users/crase/Documents/antigravity/fervent-lavoisier/example.py) ไว้ให้คุณทดสอบฟังก์ชันพื้นฐานและการแชทต่อเนื่อง:
```bash
# 1. เปิดใช้งาน Virtual Environment ก่อน (หากยังไม่ได้เปิด)
source .venv/bin/activate

# 2. รันไฟล์ตัวอย่างด้วยคำสั่ง python3
python3 example.py
```

### 2. รันผ่าน Command-Line Interface (CLI)
คุณสามารถสั่งงาน Gemini ผ่าน Terminal ได้ทันทีผ่านโปรแกรม [cli.py](file:///Users/crase/Documents/antigravity/fervent-lavoisier/cli.py):
```bash
# ตรวจสอบให้แน่ใจว่าเปิดใช้งาน venv อยู่ แล้วรันด้วย python3
python3 cli.py --cookies-json cookies.json ask "ความหมายของชีวิตคืออะไร?"
```

---

## 🌐 การเปิดใช้งาน API Server (OpenAI-Compatible Gateway)

เราได้สร้างโปรแกรม API Gateway ชื่อ [api_server.py](file:///Users/crase/Documents/antigravity/fervent-lavoisier/api_server.py) ซึ่งจะจำลองตัวเองเป็น OpenAI-compatible API เพื่อให้คุณสามารถเชื่อมต่อ Gemini บัญชีเว็บแอปเข้ากับเครื่องมือเอเจนต์เขียนโค้ด เช่น **Cline**, **LibreChat**, **Open WebUI** หรือสคริปต์ภายนอกอื่นๆ ได้

### 1. สตาร์ท API Server
ตรวจสอบให้แน่ใจว่าได้ระบุคุกกี้ในไฟล์ `.env` หรือ `cookies.json` เรียบร้อยแล้ว (หรือมีคุกกี้ในเบราว์เซอร์หลัก) จากนั้นรันคำสั่ง:
```bash
# 1. เปิดใช้งาน Virtual Environment (จำเป็น เพื่อให้สามารถเรียกใช้ไลบรารีที่ลงไว้ได้)
source .venv/bin/activate

# 2. รัน API Server ด้วย python3
python3 api_server.py
```
เซิร์ฟเวอร์จะเริ่มต้นทำงานที่พอร์ต `8000` (**`http://localhost:8000`** หรือ **`http://127.0.0.1:8000`**)
> 💡 **คำแนะนำสำหรับ macOS/Linux:** แนะนำให้เรียกใช้งานผ่านไอพีตรง `127.0.0.1` แทนคำว่า `localhost` เพื่อหลีกเลี่ยงปัญหาการแปลงไอพีเป็น IPv6 (`::1`) ซึ่งบางครั้งอาจทำให้เกิดการปฏิเสธการเชื่อมต่อ

### 2. การตั้งค่าใช้งานใน Cline (Cline Integration Guide)
หากคุณใช้ส่วนขยาย **Cline** ใน VS Code หรือ IDE อื่นๆ สามารถตั้งค่าได้ดังนี้:
- **API Provider**: เลือก `OpenAI Compatible`
- **Base URL**: ใส่ `http://127.0.0.1:8000/v1`
- **API Key**: ระบุค่าใดก็ได้ (เช่น `sk-gemini-webapi` หรือ `any-key`)
- **Model ID**: เลือกรุ่นที่ต้องการใช้งาน เช่น:
  - `gemini-3-flash-thinking` *(แนะนำอย่างยิ่ง! เพื่อใช้งานโหมดคิดวิเคราะห์ก่อนตอบ โดยการคิดจะแสดงผลในแถบความคิดพับได้ของ Cline)*
  - `gemini-3-pro`
  - `gemini-3-flash`
  - `unspecified`

---

## 💡 ฟีเจอร์พิเศษของ API Gateway (api_server.py)

1. **Stateful Heuristics (ระบบจำห้องแชทอัตโนมัติ)**
   - API จะแปลงการคุยแบบไร้สถานะ (Stateless) ของฝั่ง Client ให้เป็นแบบมีสถานะ (Stateful) โดยนำข้อความสนทนาเก่ามาทำแฮช (Hash) และดึงประวัติห้องแชทเดิมใน Google Gemini กลับมาคุยต่อโดยอัตโนมัติ ทำให้การคุยมีความลื่นไหลต่อเนื่องและประหยัดเวลาส่งข้อมูลประวัติกลับไปใหม่ทั้งหมด
2. **Reasoning Stream (การสตรีมขั้นตอนการคิด)**
   - สำหรับโมเดลที่มีการคิดวิเคราะห์อย่าง `gemini-3-flash-thinking` เซิร์ฟเวอร์จะสตรีมตัวอักษรของกระบวนการคิดวิเคราะห์กลับไปในคีย์ `reasoning_content` ของข้อมูลสตรีม (ทำให้แสดงผลเป็นแท็บคิดวิเคราะห์แบบสดๆ บนไคลเอนต์ที่รองรับ เช่น Cline ได้)
3. **Image Generation (ระบบสร้างรูปภาพ)**
   - รองรับ endpoint สำหรับสร้างรูปภาพตามมาตรฐานของ OpenAI ซึ่งทำงานร่วมกับโมเดล Imagen 3 ของกูเกิล

---

## 🔌 ตัวอย่างการใช้งาน API ด้วย cURL (API Usage Examples)

### A. บริการถามตอบทั่วไป (Chat Completions)
* **Endpoint:** `POST http://127.0.0.1:8000/v1/chat/completions`
* **การส่งอินพุตแบบมัลติโมดัล (Multimodal - ส่งรูปภาพพร้อม Prompt):**
  - รองรับการแนบรูปภาพเข้าไปพร้อมกับบทสนทนาตามรูปแบบมาตรฐานของ OpenAI โดยระบุชนิดเป็น `type: "image_url"`
  - รองรับรูปภาพทั้งในรูปแบบ **Base64 Data URL** (เช่น `data:image/png;base64,...`) และ **ลิงก์ URL รูปภาพทั่วไป** (ระบบจะดาวน์โหลดรูปภาพมาอัปโหลดเข้าเซสชันของ Gemini ให้อัตโนมัติ)
* **ตัวอย่างการยิงถามตอบทั่วไป:**
  ```bash
  curl http://127.0.0.1:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
      "model": "gemini-3-flash-thinking",
      "messages": [
        {"role": "user", "content": "อธิบายสั้นๆ ว่าแมวเข้าใจมนุษย์ไหม?"}
      ],
      "stream": false
    }'
  ```
* **ตัวอย่างการยิงถามตอบพร้อมส่งรูปภาพต้นแบบ:**
  ```bash
  curl http://127.0.0.1:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{
      "model": "gemini-3-flash",
      "messages": [
        {
          "role": "user",
          "content": [
            {"type": "text", "text": "อธิบายสิ่งที่เห็นในรูปภาพนี้"},
            {
              "type": "image_url",
              "image_url": {
                "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA..."
              }
            }
          ]
        }
      ],
      "stream": false
    }'
  ```
* **ตัวอย่างผลลัพธ์ที่ได้รับ (Response Example):**
  ```json
  {
    "id": "chatcmpl--8658571592482874660",
    "object": "chat.completion",
    "created": 1781745295,
    "model": "gemini-3-flash-thinking",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "**เข้าใจในระดับหนึ่ง แต่ไม่ใช่แบบที่มนุษย์เข้าใจกัน** \n\nแมวไม่ได้เข้าใจภาษาพูดหรือความหมายของคำศัพท์ (ยกเว้นชื่อตัวเองหรือคำสั้นๆ ที่เชื่อมโยงกับอาหาร/รางวัล) แต่พวกมันเชี่ยวชาญเรื่องการ**อ่านภาษากาย น้ำเสียง และอารมณ์**ของทาส..."
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 8,
      "completion_tokens": 163,
      "total_tokens": 172
    }
  }
  ```

### B. บริการสร้างรูปภาพ (Image Generation)
* **Endpoint:** `POST http://127.0.0.1:8000/v1/images/generations`
* **พารามิเตอร์ของ Payload:**
  - `prompt`: คำอธิบายรูปภาพที่ต้องการสร้าง (รองรับทั้งภาษาไทยและภาษาอังกฤษ)
  - `size`: ขนาด/อัตราส่วนภาพที่ต้องการสร้าง (เช่น `"1024x1024"`, `"16:9"`, `"9:16"`, `"4:3"`) **(หากไม่ส่งค่านี้มา ระบบจะตั้งค่าเริ่มต้นเป็น `"1024x1024"` โดยอัตโนมัติ)**
  - `image` *(ไม่บังคับ)*: ลิงก์ URL ของรูปภาพต้นแบบ หรือ Base64 Data URL ของรูปภาพที่ต้องการใช้อ้างอิง/ดัดแปลงในการสร้างภาพใหม่
  - *ระบบจะทำการแปลงค่า `size` ให้เป็นคำสั่งสัดส่วนภาพและแทรกลงใน Prompt ส่งไปยังโมเดล Imagen 3 ของ Google ให้อัตโนมัติ*
* **ตัวอย่างการส่ง Prompt สร้างภาพทั่วไป (Text-to-Image):**
  ```bash
  curl http://127.0.0.1:8000/v1/images/generations \
    -H "Content-Type: application/json" \
    -d '{
      "prompt": "a beautiful high quality image of a cybernetic cyberpunk cat on neon streets",
      "size": "1024x1024"
    }'
  ```
* **ตัวอย่างการส่ง Prompt สร้างภาพพร้อมแนบลิงก์รูปภาพอ้างอิง (Image URL Reference):**
  ```bash
  curl http://127.0.0.1:8000/v1/images/generations \
    -H "Content-Type: application/json" \
    -d '{
      "prompt": "change the background of this image to a vibrant neon cyberpunk city, night time",
      "size": "1024x1024",
      "image": "https://picsum.photos/id/237/1024/1024"
    }'
  ```
* **ตัวอย่างการส่ง Prompt สร้างภาพพร้อมแนบไฟล์รูปภาพอ้างอิงจากเครื่อง (Base64 Reference):**
  ```bash
  curl http://127.0.0.1:8000/v1/images/generations \
    -H "Content-Type: application/json" \
    -d '{
      "prompt": "add a futuristic cybernetic visor onto the face of the cat in this image",
      "size": "1024x1024",
      "image": "data:image/png;base64,iVBORw0KGgoAAA..."
    }'
  ```
* **ตัวอย่างผลลัพธ์ที่ได้รับ (Response Example):**
  ```json
  {
    "created": 1781745965,
    "data": [
      {
        "url": "https://lh3.googleusercontent.com/gg-dl/AFfU-fLOZByHPcweDqQh_5r0pUf2fPzslgEUH0wRh5NJqL8f_n14cVNdKN5Iv6ExlkrUSfn2r789POIK6oexb51KOYsT33pcS-CXiyQqwgKK27_-1xWscIMzLcw_Pn_nwleU4WJBJQt43jjTjxu8CuNxxh4PDWLr_3sXVXRc5Iny8q2bBeIPow"
      }
    ]
  }
  ```

---

## 🛠️ การแก้ไขปัญหาเบื้องต้น (Troubleshooting)

- **Error: Authentication failed / Unauthorized**
  - เกิดจากคุกกี้หมดอายุ หรือคุณคัดลอกมาไม่ครบถ้วน แนะนำให้เปิดเบราว์เซอร์ในโหมดไม่ระบุตัวตน (Incognito) เพื่อเข้าเว็บ Gemini ล็อกอินใหม่ แล้วคัดลอกคุกกี้อีกครั้ง
- **Error: Browser Permission Denied**
  - เมื่อใช้งานระบบดึงคุกกี้อัตโนมัติบน macOS หรือ Windows บางครั้งระบบปฏิบัติการอาจแสดงป๊อปอัปขอสิทธิ์การเข้าถึงข้อมูลคีย์บอร์ด/เบราว์เซอร์ หากไม่ประสงค์จะให้สิทธิ์ หรือระบบติดขัด ให้เปลี่ยนมาใช้วิธีนำคุกกี้มาใส่ในไฟล์ `.env` แทนเพื่อการประมวลผลที่สะดวกกว่า
- **Error: Failed to connect to localhost port 8000**
  - ตรวจสอบว่ามีบริการอื่นใช้พอร์ต `8000` อยู่หรือไม่ หากไม่มีและตัวระบบทำงานปกติแต่เชื่อมต่อไม่ได้ ให้ลองใช้ `127.0.0.1` แทน `localhost` ใน Base URL ของคุณ
