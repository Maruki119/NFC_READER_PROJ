from tkinter import *
import time

root = Tk()
root.geometry("1100x600+0+0")
root.title("NFC READER GUI - ระบบชำระค่าทางด่วน")
root.configure(bg="seashell2")

#====================== Frame หลัก ======================
Tops = Frame(root, width=1100, height=50, bg="wheat", relief=SUNKEN)
Tops.pack(side=TOP)

f1 = Frame(root, width=1100, height=550, bg="seashell2", relief=SUNKEN)
f1.pack(side=TOP)

#==================== ตัวแปรที่จำเป็น ====================
# ใช้เก็บข้อมูลที่เกี่ยวข้องกับระบบทางด่วน
card_id_var   = StringVar()  # Card ID
entry_var     = StringVar()  # Entry point
exit_var      = StringVar()  # Exit point
balance_var   = StringVar()  # ยอดเงินคงเหลือ
cost_var      = StringVar()  # ค่าทางด่วน (จะคิดตามระยะทาง/ด่าน)
signal_status = StringVar()  # สถานะสัญญาณ (Pass/Denied)
signal_color  = StringVar()  # สีพื้นหลังสำหรับสถานะ

# กำหนดค่าทดสอบเริ่มต้น
card_id_var.set("1234567890")
entry_var.set("ด่าน A")
exit_var.set("ด่าน B")
balance_var.set("300")
cost_var.set("50")
signal_status.set("") 
signal_color.set("light grey")

#==================== ฟังก์ชันควบคุม =====================
def check_toll():
    """
    ตัวอย่างฟังก์ชันตรวจสอบว่ายอดเงินพอจ่ายค่าทางด่วนหรือไม่
    ถ้ายอดเงิน >= ค่าทางด่วน → ให้ผ่าน
    ถ้ายอดเงิน < ค่าทางด่วน → Denied
    """
    try:
        balance = float(balance_var.get())
        cost = float(cost_var.get())
        if balance >= cost:
            # อนุญาตให้ผ่าน
            update_signal(True)
        else:
            # ไม่ผ่าน
            update_signal(False)
    except:
        # ถ้าค่าไม่ใช่ตัวเลข ให้ถือว่าไม่ผ่าน
        update_signal(False)

def update_signal(can_pass):
    """อัปเดตสถานะสัญญาณ (Pass/Denied) และสีพื้นหลัง"""
    if can_pass:
        signal_status.set("Pass")
        signal_color.set("green")
    else:
        signal_status.set("Denied")
        signal_color.set("red")

def refresh_color():
    """เปลี่ยนสีพื้นหลัง Label ของสัญญาณตาม signal_color"""
    signal_label.config(bg=signal_color.get())
    root.after(100, refresh_color)

def btnExit():
    root.destroy()

#==================== เวลา (Time) ===========================
localtime = time.asctime(time.localtime(time.time()))

label_title = Label(
    Tops,
    font=('TH Saraban New', 40, 'bold'),
    text="ระบบชำระค่าทางด่วน",
    fg="Blue",
    bd=10,
    anchor='w',
    bg="seashell2"
)
label_title.grid(row=0, column=0)

label_time = Label(
    Tops,
    font=('TH Saraban New', 16, 'bold'),
    text=localtime,
    fg="Blue",
    bd=10,
    anchor='w',
    bg="seashell2"
)
label_time.grid(row=1, column=0)

#==================== ส่วนข้อมูลใน f1 ======================
Label(f1, font=('TH Sarabun New', 18, 'bold'), text="Card ID :",
      bg="seashell2", anchor='w').grid(row=0, column=0, padx=10, pady=10, sticky='e')

Label(f1, font=('TH Sarabun New', 18), textvariable=card_id_var,
      bd=2, width=16, bg="powder blue", justify='left').grid(row=0, column=1, padx=10, pady=10)

Label(f1, font=('TH Sarabun New', 18, 'bold'), text="Entry Point :",
      bg="seashell2", anchor='w').grid(row=1, column=0, padx=10, pady=10, sticky='e')

Label(f1, font=('TH Sarabun New', 18), textvariable=entry_var,
      bd=2, width=16, bg="powder blue", justify='left').grid(row=1, column=1, padx=10, pady=10)

Label(f1, font=('TH Sarabun New', 18, 'bold'), text="Exit Point :",
      bg="seashell2", anchor='w').grid(row=2, column=0, padx=10, pady=10, sticky='e')

Label(f1, font=('TH Sarabun New', 18), textvariable=exit_var,
      bd=2, width=16, bg="powder blue", justify='left').grid(row=2, column=1, padx=10, pady=10)

Label(f1, font=('TH Sarabun New', 18, 'bold'), text="Balance :",
      bg="seashell2", anchor='w').grid(row=0, column=2, padx=10, pady=10, sticky='e')

Label(f1, font=('TH Sarabun New', 18), textvariable=balance_var,
      bd=2, width=16, bg="powder blue", justify='right').grid(row=0, column=3, padx=10, pady=10)

Label(f1, font=('TH Sarabun New', 18, 'bold'), text="Cost :",
      bg="seashell2", anchor='w').grid(row=1, column=2, padx=10, pady=10, sticky='e')

Label(f1, font=('TH Sarabun New', 18), textvariable=cost_var,
      bd=2, width=16, bg="powder blue", justify='right').grid(row=1, column=3, padx=10, pady=10)

Label(f1, font=('TH Sarabun New', 18, 'bold'), text="Signal :",
      bg="seashell2", anchor='w').grid(row=2, column=2, padx=10, pady=10, sticky='e')

signal_label = Label(
    f1, font=('TH Sarabun New', 18, 'bold'),
    textvariable=signal_status,
    bd=2, width=16,
    fg="white",
    bg=signal_color.get()
)
signal_label.grid(row=2, column=3, padx=10, pady=10)

#======================== ปุ่มกด ==========================
Button(
    f1, text="Check Toll", font=('TH Sarabun New', 16, 'bold'),
    padx=10, pady=5, bg="light gray",
    command=check_toll
).grid(row=3, column=1, pady=20)

Button(
    f1, text="Exit", font=('TH Sarabun New', 16, 'bold'),
    padx=10, pady=5, bg="tomato",
    command=btnExit
).grid(row=3, column=2, pady=20)

#======================== เรียกใช้ฟังก์ชันอัปเดตสีสัญญาณ =====================
refresh_color()

#======================== เริ่มต้นโปรแกรม (Mainloop) =========================
root.mainloop()
