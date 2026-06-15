import asyncio
import os
from pathlib import Path
from gemini_webapi import GeminiClient

def load_env_file(dotenv_path=".env"):
    """ ฟังก์ชันโหลดค่าตัวแปรจากไฟล์ .env แบบดั้งเดิมโดยไม่ต้องลงไลบรารีเพิ่ม """
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

# โหลดค่าคุกกี้จากไฟล์ .env
load_env_file()

# ดึงค่าคุกกี้จาก Environment Variables
SECURE_1PSID = os.getenv("SECURE_1PSID")
SECURE_1PSIDTS = os.getenv("SECURE_1PSIDTS")

async def main():
    # ตรวจสอบการตั้งค่าคุกกี้เบื้องต้น
    if not SECURE_1PSID:
        print("❌ ข้อผิดพลาด: ไม่พบค่า SECURE_1PSID ในไฟล์ .env")
        print("💡 กรุณาสร้างไฟล์ .env ในโฟลเดอร์นี้และใส่คีย์ดังนี้:")
        print("SECURE_1PSID=ค่าคุกกี้_1PSID_ที่นี่")
        print("SECURE_1PSIDTS=ค่าคุกกี้_1PSIDTS_ที่นี่ (ถ้ามี)")
        return

    print("🔌 กำลังเริ่มต้นระบบและเชื่อมต่อกับ Google Gemini...")
    
    # เริ่มต้นการทำงานของ Client
    client = GeminiClient(secure_1psid=SECURE_1PSID, secure_1psidts=SECURE_1PSIDTS or "")
    
    try:
        # เปิดการเชื่อมต่อ
        await client.init(timeout=30, auto_refresh=True)
        print("✅ เชื่อมต่อและยืนยันตัวตนสำเร็จ!\n")

        # --- ตัวอย่างที่ 1: การถามตอบทั่วไป (Single-turn Question) ---
        print("🤖 [ตัวอย่างที่ 1: ถามตอบทั่วไป]")
        prompt = "แนะนำภาษาโปรแกรมที่น่าเรียนสำหรับปีนี้ 3 ภาษาและเหตุผลสั้นๆ"
        print(f"คำถาม: {prompt}")
        
        response = await client.generate_content(prompt)
        print(f"\nคำตอบจาก Gemini:\n{response.text}")
        print("=" * 60 + "\n")

        # --- ตัวอย่างที่ 2: การแชทแบบคุยต่อเนื่อง (Multi-turn Chat Session) ---
        print("💬 [ตัวอย่างที่ 2: การสนทนาต่อเนื่อง (Chat)]")
        chat = client.start_chat()
        
        # ส่งข้อความแรก
        msg1 = "วันนี้ฉันอยากกินอาหารไทยรสชาติจัดจ้าน"
        print(f"คุณ: {msg1}")
        res1 = await chat.send_message(msg1)
        print(f"Gemini: {res1.text}\n")
        
        # ส่งข้อความที่สอง (Gemini จะจำบริบทจากข้อความแรกได้)
        msg2 = "จากเมนูที่แนะนำเมื่อกี้ มีตัวเลือกไหนที่ไม่มีเนื้อสัตว์บ้าง?"
        print(f"คุณ: {msg2}")
        res2 = await chat.send_message(msg2)
        print(f"Gemini: {res2.text}")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการทำงาน: {e}")
    finally:
        # ปิดการทำงาน Client เพื่อเคลียร์ทรัพยากร
        await client.close()
        print("🔌 ปิดการเชื่อมต่อเรียบร้อยแล้ว")

if __name__ == "__main__":
    asyncio.run(main())
