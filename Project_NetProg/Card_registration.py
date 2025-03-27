# seven_registration.py

from tkinter import *
import random
import ssl
import smtplib
import json
import os
from ftplib import FTP
from email.message import EmailMessage

# ===================== ตัวแปรเก็บข้อมูลการลงทะเบียน (ในที่นี้เป็น Dict ชั่วคราว) =====================
card_data = {}  # โครงสร้างตัวอย่าง: { card_id: {"email": ..., "otp": ..., "registered": ...} }

# ===================== ฟังก์ชันส่ง OTP (ตัวอย่าง) =====================
def generate_otp(length=6):
    """สร้างรหัส OTP จำนวน length หลัก (ค่าเริ่มต้น 6)"""
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def send_otp_by_email(receiver_email, otp):
    """
    ตัวอย่างการส่งอีเมล OTP (โค้ดจำลองการส่ง)
    หากต้องการส่งจริงให้แก้ smtp_server, port, sender_email, password
    """
    
    smtp_server = "smtp.gmail.com"  
    port = 587  
    sender_email = "nakrobpanejohn@gmail.com"   
    password = "xkgd alam gjvj gwzc"  

    message = EmailMessage()
    message.set_content(f"Your OTP is: {otp}")
    message["Subject"] = "Your OTP Code"
    message["From"] = sender_email
    message["To"] = receiver_email

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            server.send_message(message)
        print("OTP sent successfully!")  # แสดงที่ console
    except Exception as e:
        print("Error sending email:", e)

# ===================== ฟังก์ชันหลักสำหรับ GUI =====================
def send_otp():
    """
    1. ดึง Card ID กับ Email จากช่องกรอก
    2. สร้าง OTP
    3. เก็บ OTP ลงใน card_data
    4. (จำลอง) ส่งอีเมล
    5. แสดงผลว่าส่ง OTP แล้ว
    """
    card_id = card_id_var.get().strip()
    email = email_var.get().strip()

    if not card_id:
        status_var.set("กรุณาใส่ Card ID")
        return
    if not email:
        status_var.set("กรุณาใส่ Email")
        return

    new_otp = generate_otp()  # สร้าง OTP
    # เก็บข้อมูลใน dict ถ้า card_id ยังไม่มี
    if card_id not in card_data:
        card_data[card_id] = {
            "email": email,
            "otp": new_otp,
            "registered": False
        }
    else:
        card_data[card_id]["email"] = email
        card_data[card_id]["otp"] = new_otp
        card_data[card_id]["registered"] = False

   
    send_otp_by_email(email, new_otp)

    status_var.set(f"OTP sent to {email} (ตัวอย่าง OTP: {new_otp})")

def confirm_otp():
    """
    1. อ่าน Card ID
    2. อ่าน OTP ที่กรอก
    3. เทียบกับ otp ใน card_data
    4. ถ้าตรง -> registered = True
    """
    card_id = card_id_var.get().strip()
    input_otp = otp_var.get().strip()
  
    if card_id not in card_data:
        status_var.set("ไม่พบข้อมูล Card ID กรุณาส่ง OTP ก่อน")
        return

    

    correct_otp = card_data[card_id]["otp"]
    if input_otp == correct_otp:
        card_data[card_id]["registered"] = True
        sample_data = {
            "card_id":card_id,
            "balance": 0,
            "email": card_data[card_id]["email"],
            "top_up_history": [],
            "transaction_log": []
        }
        try:
            # print("CardID:",card_id,sample_data)
            generate_and_upload_json(card_id,sample_data)
        except E:
            print("Error:",E)
        status_var.set(f"Card {card_id} ลงทะเบียนสำเร็จ!")
    else:
        status_var.set("OTP ไม่ถูกต้อง")

def generate_and_upload_json(card_id, card_data):
    """
    1) สร้างไฟล์ JSON ในเครื่อง (local) จาก card_data
    2) อัปโหลดไฟล์ JSON ไปยัง FTP Server โดยใช้โฟลเดอร์ card_id
    3) ลบไฟล์ JSON ที่สร้างไว้ในเครื่อง
    """
    # ตั้งค่าการเชื่อมต่อ FTP (FileZilla Server)
    ftp_host = "localhost"    
    ftp_port = 21          
    ftp_user = "admin"        
    ftp_pass = "admin"        

    # ชื่อไฟล์ JSON ที่จะสร้างและอัปโหลด
    local_filename = f"{card_id}.json"   # เช่น 123456.json
    remote_filename = f"{card_id}.json"  # ตั้งให้เหมือนกันได้ หรือปรับชื่อไฟล์ปลายทางตามต้องการ

    
    # 1) สร้างไฟล์ JSON ในเครื่อง
    with open(local_filename, 'w', encoding='utf-8') as f:
        # Dump data เป็น JSON (ensure_ascii=False เพื่อให้รองรับภาษาไทยได้)
        json.dump(card_data, f, ensure_ascii=False, indent=4)
    print(f"JSON file '{local_filename}' created.")

    # 2) เชื่อมต่อและอัปโหลดไฟล์ไปยัง FTP
    ftp = FTP()
    try:
        print(f"Connecting to FTP server {ftp_host}:{ftp_port} ...")
        ftp.connect(ftp_host, ftp_port)
        ftp.login(ftp_user, ftp_pass)
        print("FTP login successful.")

        # ตั้งโหมด PASV (passive mode) ถ้าจำเป็น
        ftp.set_pasv(True)

        # (ตัวอย่าง) สร้างโฟลเดอร์ชื่อ card_id หากยังไม่มี
        try:
            ftp.mkd(card_id)
            print(f"Directory '{card_id}' created on FTP server.")
        except Exception as e:
            print(f"Could not create directory '{card_id}' (maybe it already exists): {e}")

        # เข้าไปในโฟลเดอร์ card_id
        ftp.cwd(card_id)

        # อัปโหลดไฟล์ JSON
        with open(local_filename, 'rb') as f:
            ftp.storbinary(f'STOR {remote_filename}', f)
        print(f"Uploaded '{local_filename}' as '{remote_filename}' into folder '{card_id}'")

        # ปิดการเชื่อมต่อ FTP
        ftp.quit()
        print("FTP connection closed.")

    except Exception as e:
        print("FTP Error:", e)
        if ftp:
            ftp.close()

    # 3) ลบไฟล์ JSON ออกจากเครื่อง
    try:
        os.remove(local_filename)
        print(f"Local file '{local_filename}' has been deleted.")
    except Exception as e:
        print(f"Error deleting local file '{local_filename}': {e}")

def reset_fields():
    """ล้างค่าที่กรอกบนหน้าจอ"""
    card_id_var.set("")
    email_var.set("")
    otp_var.set("")
    status_var.set("")

def exit_app():
    root.destroy()

# ===================== ส่วน GUI ด้วย Tkinter =====================
root = Tk()
root.geometry("600x400")
root.title("NFC_registration")
root.configure(bg="seashell2")

card_id_var = StringVar()
email_var = StringVar()
otp_var = StringVar()
status_var = StringVar()  # ไว้แสดงสถานะ/ข้อความ

# ====== Title ======
Label(root, text="NFC Card Registration", font=('TH Saraban New', 24, 'bold'),
      bg="seashell2", fg="blue").pack(pady=10)

# ====== Frame หลัก ======
frame_main = Frame(root, bg="seashell2")
frame_main.pack(pady=10)

# ====== Card ID ======
Label(frame_main, text="Card ID:", font=('TH Sarabun New', 16, 'bold'),
      bg="seashell2").grid(row=0, column=0, padx=5, pady=5, sticky='e')
Entry(frame_main, textvariable=card_id_var, font=('TH Sarabun New', 16),
      width=20, bg="white").grid(row=0, column=1, padx=5, pady=5)

# ====== Email ======
Label(frame_main, text="Email:", font=('TH Sarabun New', 16, 'bold'),
      bg="seashell2").grid(row=1, column=0, padx=5, pady=5, sticky='e')
Entry(frame_main, textvariable=email_var, font=('TH Sarabun New', 16),
      width=20, bg="white").grid(row=1, column=1, padx=5, pady=5)

# ====== ปุ่ม Send OTP ======
Button(frame_main, text="Send OTP", font=('TH Sarabun New', 14, 'bold'),
       command=send_otp, bg="light green").grid(row=1, column=2, padx=5, pady=5)

# ====== OTP ======
Label(frame_main, text="OTP:", font=('TH Sarabun New', 16, 'bold'),
      bg="seashell2").grid(row=2, column=0, padx=5, pady=5, sticky='e')
Entry(frame_main, textvariable=otp_var, font=('TH Sarabun New', 16),
      width=20, bg="white").grid(row=2, column=1, padx=5, pady=5)

# ====== ปุ่มยืนยัน OTP ======
Button(frame_main, text="Confirm", font=('TH Sarabun New', 14, 'bold'),
       command=confirm_otp, bg="light blue").grid(row=2, column=2, padx=5, pady=5)

# ====== ปุ่ม Reset และ Exit ======
Button(frame_main, text="Reset", font=('TH Sarabun New', 14, 'bold'),
       command=reset_fields, bg="orange").grid(row=3, column=1, padx=5, pady=20, sticky='e')

Button(frame_main, text="Exit", font=('TH Sarabun New', 14, 'bold'),
       command=exit_app, bg="tomato").grid(row=3, column=2, padx=5, pady=20, sticky='w')

# ====== Label แสดงสถานะ ======
Label(root, textvariable=status_var, font=('TH Sarabun New', 16, 'bold'),
      fg="red", bg="seashell2").pack(pady=10)

root.mainloop()
