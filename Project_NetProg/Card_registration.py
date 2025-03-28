from tkinter import *
from tkinter import messagebox  # นำเข้า messagebox สำหรับแสดง popup
import random
import ssl
import smtplib
import json
import os
from ftplib import FTP
from email.message import EmailMessage
from io import BytesIO  # สำหรับดาวน์โหลดข้อมูลจาก FTP เป็น bytes
import datetime  # สำหรับบันทึกเวลา

# ===================== Global Data =====================
card_data = {}       # สำหรับข้อมูล OTP และสถานะการลงทะเบียน: { card_id: {"email": ..., "otp": ..., "registered": ...} }
accounts_data = {}   # สำหรับข้อมูลบัญชีผู้ใช้: { card_id: {"card_id":..., "balance":..., "email":..., "top_up_history":..., "transaction_log": ...} }

# ===================== ฟังก์ชันส่ง OTP =====================
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
        print("OTP sent successfully!")
    except Exception as e:
        print("Error sending email:", e)

# ===================== ฟังก์ชันสำหรับดาวน์โหลดข้อมูล JSON จาก FTP =====================
def download_json_from_ftp(card_id):
    """
    ตรวจสอบว่ามีไฟล์ JSON สำหรับ card_id ใน FTP Server หรือไม่
    ถ้ามี: ดาวน์โหลดและคืนค่าเป็น dict
    ถ้าไม่มีหรือเกิดข้อผิดพลาด: คืนค่า None
    """
    ftp_host = "localhost"
    ftp_port = 21
    ftp_user = "admin"
    ftp_pass = "admin"
    target_file = f"{card_id}.json"
    
    ftp = FTP()
    try:
        print(f"Connecting to FTP server {ftp_host}:{ftp_port} ...")
        ftp.connect(ftp_host, ftp_port)
        ftp.login(ftp_user, ftp_pass)
        ftp.set_pasv(True)
        ftp.cwd(card_id)
        files = ftp.nlst()
        if target_file not in files:
            print(f"File '{target_file}' not found in folder '{card_id}'")
            ftp.quit()
            return None
        
        bio = BytesIO()
        ftp.retrbinary('RETR ' + target_file, bio.write)
        ftp.quit()
        bio.seek(0)
        data = bio.read().decode('utf-8')
        return json.loads(data)
    except Exception as e:
        print("FTP Error while downloading:", e)
        try:
            ftp.quit()
        except:
            pass
        return None

# ===================== ฟังก์ชันสำหรับสร้างและอัปโหลดไฟล์ JSON ไปยัง FTP =====================
def generate_and_upload_json(card_id, card_data):
    """
    1) สร้างไฟล์ JSON ในเครื่องจาก card_data
    2) อัปโหลดไฟล์ JSON ไปยัง FTP Server ในโฟลเดอร์ card_id
    3) ลบไฟล์ JSON ที่สร้างไว้ในเครื่อง
    """
    ftp_host = "localhost"
    ftp_port = 21
    ftp_user = "admin"
    ftp_pass = "admin"

    local_filename = f"{card_id}.json"
    remote_filename = f"{card_id}.json"

    with open(local_filename, 'w', encoding='utf-8') as f:
        json.dump(card_data, f, ensure_ascii=False, indent=4)
    print(f"JSON file '{local_filename}' created.")

    ftp = FTP()
    try:
        print(f"Connecting to FTP server {ftp_host}:{ftp_port} ...")
        ftp.connect(ftp_host, ftp_port)
        ftp.login(ftp_user, ftp_pass)
        ftp.set_pasv(True)
        try:
            ftp.mkd(card_id)
            print(f"Directory '{card_id}' created on FTP server.")
        except Exception as e:
            print(f"Could not create directory '{card_id}' (maybe it already exists): {e}")
        ftp.cwd(card_id)
        with open(local_filename, 'rb') as f:
            ftp.storbinary(f'STOR {remote_filename}', f)
        print(f"Uploaded '{local_filename}' as '{remote_filename}' into folder '{card_id}'")
        ftp.quit()
    except Exception as e:
        print("FTP Error:", e)
        if ftp:
            ftp.close()

    try:
        os.remove(local_filename)
        print(f"Local file '{local_filename}' has been deleted.")
    except Exception as e:
        print(f"Error deleting local file '{local_filename}': {e}")

# ===================== ฟังก์ชันสำหรับ GUI การลงทะเบียน =====================
def send_otp():
    """
    1. ดึง Card ID กับ Email จากช่องกรอก
    2. ตรวจสอบว่ามี Card ID นี้ใน FTP Server อยู่หรือไม่
       - ถ้ามี: แสดงข้อความแจ้งว่า Card ID มีอยู่แล้วและไม่ส่ง OTP
       - ถ้าไม่: สร้าง OTP ส่งอีเมลและแสดง popup แจ้งว่า OTP ถูกส่งเรียบร้อยแล้ว
    """
    card_id = card_id_var.get().strip()
    email = email_var.get().strip()

    if not card_id:
        status_var.set("กรุณาใส่ Card ID")
        return
    if not email:
        status_var.set("กรุณาใส่ Email")
        return

    # ตรวจสอบว่ามี Card ID นี้ใน FTP Server อยู่หรือไม่
    ftp_data = download_json_from_ftp(card_id)
    if ftp_data is not None:
        status_var.set("Card ID มีอยู่แล้วในระบบ FTP")
        messagebox.showerror("Error", f"Card ID {card_id} มีอยู่แล้วในระบบ FTP ไม่สามารถส่ง OTP ได้")
        return

    new_otp = generate_otp()
    if card_id not in card_data:
        card_data[card_id] = {"email": email, "otp": new_otp, "registered": False}
    else:
        card_data[card_id]["email"] = email
        card_data[card_id]["otp"] = new_otp
        card_data[card_id]["registered"] = False

    send_otp_by_email(email, new_otp)
    status_var.set(f"OTP sent to {email} (ตัวอย่าง OTP: {new_otp})")
    messagebox.showinfo("OTP Sent", f"OTP ถูกส่งไปยัง {email} เรียบร้อยแล้ว!")

def confirm_otp():
    """
    1. ตรวจสอบ OTP ที่กรอกกับข้อมูลใน card_data
    2. ถ้า OTP ถูกต้อง: ตรวจสอบว่าลงทะเบียนไปแล้วหรือยังโดยดูจาก FTP Server
       - ถ้าลงทะเบียนไปแล้ว: แจ้งเตือนไม่ให้ลงทะเบียนซ้ำ
       - ถ้ายังไม่ลงทะเบียน: สร้างข้อมูลบัญชีและอัปโหลดไปยัง FTP
    3. แสดงข้อความแจ้งทำงานสำเร็จ
    """
    card_id = card_id_var.get().strip()
    input_otp = otp_var.get().strip()
  
    if card_id not in card_data:
        status_var.set("ไม่พบข้อมูล Card ID กรุณาส่ง OTP ก่อน")
        return

    correct_otp = card_data[card_id]["otp"]
    if input_otp == correct_otp:
        # ตรวจสอบใน FTP Server ว่ามีข้อมูล card_id อยู่หรือไม่
        ftp_data = download_json_from_ftp(card_id)
        if ftp_data is not None:
            status_var.set("Card นี้ลงทะเบียนไปแล้ว ไม่สามารถลงทะเบียนซ้ำได้")
            messagebox.showerror("Error", "Card นี้ลงทะเบียนไปแล้ว กรุณาใช้ Card อื่น หรือเข้าสู่ระบบเติมเงิน")
            return

        card_data[card_id]["registered"] = True
        sample_data = {
            "card_id": card_id,
            "balance": 0,
            "email": card_data[card_id]["email"],
            "top_up_history": [],
            "transaction_log": []
        }
        try:
            generate_and_upload_json(card_id, sample_data)
            accounts_data[card_id] = sample_data
        except Exception as E:
            print("Error:", E)
        status_var.set(f"Card {card_id} ลงทะเบียนสำเร็จ!")
        messagebox.showinfo("Success", f"Card {card_id} ลงทะเบียนและอัปโหลดข้อมูลสำเร็จ! ทำงานสำเร็จ")
    else:
        status_var.set("OTP ไม่ถูกต้อง")

# ===================== ฟังก์ชันสำหรับหน้าการเติมเงิน =====================
def open_top_up_window():
    top_window = Toplevel(root)
    top_window.geometry("400x300")
    top_window.title("Top Up")
    top_window.configure(bg="seashell2")
    
    top_card_id_var = StringVar()
    top_amount_var = StringVar()
    top_status_var = StringVar()
    
    Label(top_window, text="Top Up", font=('TH Saraban New', 20, 'bold'),
          bg="seashell2", fg="blue").pack(pady=10)
    
    frame_top = Frame(top_window, bg="seashell2")
    frame_top.pack(pady=10)
    
    Label(frame_top, text="Card ID:", font=('TH Sarabun New', 16, 'bold'),
          bg="seashell2").grid(row=0, column=0, padx=5, pady=5, sticky='e')
    Entry(frame_top, textvariable=top_card_id_var, font=('TH Sarabun New', 16),
          width=20, bg="white").grid(row=0, column=1, padx=5, pady=5)
    
    Label(frame_top, text="Amount:", font=('TH Sarabun New', 16, 'bold'),
          bg="seashell2").grid(row=1, column=0, padx=5, pady=5, sticky='e')
    Entry(frame_top, textvariable=top_amount_var, font=('TH Sarabun New', 16),
          width=20, bg="white").grid(row=1, column=1, padx=5, pady=5)
    
    def perform_top_up():
        card_id = top_card_id_var.get().strip()
        amount_str = top_amount_var.get().strip()
        if card_id == "":
            top_status_var.set("กรุณาใส่ Card ID")
            return
        if amount_str == "":
            top_status_var.set("กรุณาใส่จำนวนเงิน")
            return
        try:
            amount = float(amount_str)
        except ValueError:
            top_status_var.set("จำนวนเงินไม่ถูกต้อง")
            return
        
        # ตรวจสอบข้อมูลใน FTP Server ว่ามี card_id หรือไม่
        ftp_data = download_json_from_ftp(card_id)
        if ftp_data is None:
            top_status_var.set("Card ID ไม่พบในระบบ FTP กรุณาลงทะเบียนก่อน")
            return
        
        # ใช้ข้อมูลจาก FTP มาอัปเดตบัญชี
        accounts_data[card_id] = ftp_data
        account = accounts_data[card_id]
        account["balance"] += amount
        
        # บันทึกเวลาเติมเงิน
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        account["top_up_history"].append({"amount": amount, "time": timestamp})
        
        # อัปเดตไฟล์ JSON บน FTP ด้วยข้อมูลที่อัปเดตแล้ว
        generate_and_upload_json(card_id, account)
        
        top_status_var.set(f"เติมเงินสำเร็จ! ยอดเงินใหม่: {account['balance']}")
        messagebox.showinfo("Success", f"เติมเงินสำเร็จ!\nยอดเงินใหม่: {account['balance']}\nเวลา: {timestamp}\nทำงานสำเร็จ")
    
    Button(frame_top, text="Top Up", font=('TH Sarabun New', 14, 'bold'),
           command=perform_top_up, bg="light green").grid(row=2, column=0, columnspan=2, pady=10)
    
    Label(top_window, textvariable=top_status_var, font=('TH Sarabun New', 16, 'bold'),
          fg="red", bg="seashell2").pack(pady=10)
    
    Button(top_window, text="Close", font=('TH Sarabun New', 14, 'bold'),
           command=top_window.destroy, bg="tomato").pack(pady=10)

# ===================== ฟังก์ชันสำหรับ Reset และ Exit =====================
def reset_fields():
    card_id_var.set("")
    email_var.set("")
    otp_var.set("")
    status_var.set("")

def exit_app():
    root.destroy()

# ===================== ส่วน GUI หลัก =====================
root = Tk()
root.geometry("600x400")
root.title("NFC_registration")
root.configure(bg="seashell2")

card_id_var = StringVar()
email_var = StringVar()
otp_var = StringVar()
status_var = StringVar()  # สำหรับแสดงสถานะ/ข้อความ

# Title
Label(root, text="NFC Card Registration", font=('TH Saraban New', 24, 'bold'),
      bg="seashell2", fg="blue").pack(pady=10)

# Frame สำหรับการลงทะเบียน
frame_main = Frame(root, bg="seashell2")
frame_main.pack(pady=10)

Label(frame_main, text="Card ID:", font=('TH Sarabun New', 16, 'bold'),
      bg="seashell2").grid(row=0, column=0, padx=5, pady=5, sticky='e')
Entry(frame_main, textvariable=card_id_var, font=('TH Sarabun New', 16),
      width=20, bg="white").grid(row=0, column=1, padx=5, pady=5)

Label(frame_main, text="Email:", font=('TH Sarabun New', 16, 'bold'),
      bg="seashell2").grid(row=1, column=0, padx=5, pady=5, sticky='e')
Entry(frame_main, textvariable=email_var, font=('TH Sarabun New', 16),
      width=20, bg="white").grid(row=1, column=1, padx=5, pady=5)

Button(frame_main, text="Send OTP", font=('TH Sarabun New', 14, 'bold'),
       command=send_otp, bg="light green").grid(row=1, column=2, padx=5, pady=5)

Label(frame_main, text="OTP:", font=('TH Sarabun New', 16, 'bold'),
      bg="seashell2").grid(row=2, column=0, padx=5, pady=5, sticky='e')
Entry(frame_main, textvariable=otp_var, font=('TH Sarabun New', 16),
      width=20, bg="white").grid(row=2, column=1, padx=5, pady=5)

Button(frame_main, text="Confirm", font=('TH Sarabun New', 14, 'bold'),
       command=confirm_otp, bg="light blue").grid(row=2, column=2, padx=5, pady=5)

# ปุ่มสำหรับ Reset, Top Up และ Exit
Button(frame_main, text="Reset", font=('TH Sarabun New', 14, 'bold'),
       command=reset_fields, bg="orange").grid(row=3, column=1, padx=5, pady=20, sticky='e')
Button(frame_main, text="Exit", font=('TH Sarabun New', 14, 'bold'),
       command=exit_app, bg="tomato").grid(row=3, column=2, padx=5, pady=20, sticky='w')

# ปุ่มเปิดหน้าการเติมเงิน
Button(root, text="Top Up", font=('TH Sarabun New', 14, 'bold'),
       command=open_top_up_window, bg="light blue").pack(pady=5)

Label(root, textvariable=status_var, font=('TH Sarabun New', 16, 'bold'),
      fg="red", bg="seashell2").pack(pady=10)

root.mainloop()
