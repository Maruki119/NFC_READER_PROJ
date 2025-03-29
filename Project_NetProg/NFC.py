import datetime
import json
import struct
import os
import time
from ftplib import FTP
from tkinter import *
import threading
from io import BytesIO
from smartcard.scard import *
from smartcard.util import toHexString
import smartcard.util
from smartcard.ATR import ATR
from smartcard.CardType import AnyCardType
from smartcard.CardRequest import CardRequest
from smartcard.CardConnectionObserver import CardConnectionObserver

# ===================== NFC READER =====================
VERBOSE = False

BLOCK_NUMBER = 0x04
AUTHENTICATE = [0xFF, 0x88, 0x00, BLOCK_NUMBER, 0x60, 0x00]
GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x04]
READ_16_BINARY_BLOCKS = [0xFF, 0xB0, 0x00, 0x04, 0x10]
UPDATE_FIXED_BLOCKS = [0xFF, 0xD6, 0x00, BLOCK_NUMBER, 0x10]

class NFC_Reader():
    def __init__(self, uid=""):
        self.uid = uid
        self.hresult, self.hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
        self.hresult, self.readers = SCardListReaders(self.hcontext, [])
        assert len(self.readers) > 0
        self.reader = self.readers[0]
        print("Found reader: " + str(self.reader))

        self.hresult, self.hcard, self.dwActiveProtocol = SCardConnect(
            self.hcontext,
            self.reader,
            SCARD_SHARE_SHARED,
            SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)

    def send_command(self, command):
        print("Sending command...")
        for iteration in range(1):
            try:
                self.hresult, self.response = SCardTransmit(self.hcard, self.dwActiveProtocol, command)
                value = toHexString(self.response, format=0)
                if VERBOSE:
                    print("Value: " + value + " , Response:  " + str(self.response) + " HResult: " + str(self.hresult))
            except Exception as e:
                print("No Card Found")
                print("Eror:", e)
                return None, None
            time.sleep(1)
        print("------------------------\n")
        return self.response, value

    def read_uid(self):
        print("Waiting for card...")
        while True:
            try:
                response, uid = self.send_command(GET_UID)
                if response:
                    print("Found!")
                    self.uid = uid
                    return uid.replace(" ", "_")
            except Exception as e:
                print("Error:", e)
                print("Card Not Found")
    
            # ลอง reconnect ใหม่ทุกครั้งที่ล้มเหลว
            try:
                self.hresult, self.hcard, self.dwActiveProtocol = SCardConnect(
                    self.hcontext,
                    self.reader,
                    SCARD_SHARE_SHARED,
                    SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)
            except Exception as e:
                print("Reconnect failed:", e)
    
            time.sleep(1)
            

    def write_data(self, string):
        int_array = list(map(ord, string))
        print("Writing data: " + str(int_array))
        if len(int_array) > 16:
            return
        command = UPDATE_FIXED_BLOCKS + int_array + [0x00] * (16 - len(int_array))
        response, _ = self.send_command(AUTHENTICATE)
        if response == [144, 0]:
            print("Authentication successful. Writing data...")
            self.send_command(command)
        else:
            print("Unable to authenticate.")

    def read_data(self):
        response, _ = self.send_command(AUTHENTICATE)
        if response == [144, 0]:
            _, value = self.send_command(READ_16_BINARY_BLOCKS)
            return value
        else:
            print("Unable to authenticate.")
            return None

# ===================== FTP CONFIG =====================
ftp_host = "172.20.10.7"
ftp_port = 21
ftp_user = "Maruki119"
ftp_pass = "Maruki119"

# ===================== อัปโหลดไฟล์ JSON ไป FTP =====================
def generate_and_upload_json(card_id, card_data):
    local_filename = f"{card_id}.json"
    remote_filename = f"{card_id}.json"

    with open(local_filename, 'w', encoding='utf-8') as f:
        json.dump(card_data, f, ensure_ascii=False, indent=4)

    ftp = FTP()
    try:
        ftp.connect(ftp_host, ftp_port)
        ftp.login(ftp_user, ftp_pass)
        ftp.set_pasv(True)
        try:
            ftp.mkd(card_id)
        except:
            pass
        ftp.cwd(card_id)
        with open(local_filename, 'rb') as f:
            ftp.storbinary(f'STOR {remote_filename}', f)
        ftp.quit()
    except Exception as e:
        print("FTP Error:", e)
        try:
            ftp.quit()
        except:
            pass

    try:
        os.remove(local_filename)
    except:
        pass

# ===================== ดาวน์โหลดข้อมูลจาก FTP =====================
def download_card_data(card_id):
    try:
        ftp = FTP()
        ftp.connect(ftp_host, ftp_port)
        ftp.login(ftp_user, ftp_pass)
        ftp.set_pasv(True)
        ftp.cwd(card_id)
        filename = f"{card_id}.json"
        bio = BytesIO()
        ftp.retrbinary(f'RETR {filename}', bio.write)
        ftp.quit()
        bio.seek(0)
        data = bio.read().decode("utf-8")
        return json.loads(data)
    except Exception as e:
        print("Download Error:", e)
        return None

# ===================== บันทึก transaction log =====================
def update_transaction_log(card_data, entry_point=None, exit_point=None, cost=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if exit_point is None:
        card_data["transaction_log"].append({
            "type": "entry",
            "time": timestamp,
            "detail": f"Entered at {entry_point}"
        })
    else:
        card_data["transaction_log"].append({
            "type": "exit",
            "time": timestamp,
            "detail": f"Exited from {exit_point} (entered at {entry_point}), cost {cost}"
        })
    return card_data

# ===================== GUI =====================
root = Tk()
root.geometry("1100x600+0+0")
root.title("NFC READER GUI - ระบบชำระค่าทางด่วน")
root.configure(bg="seashell2")

Tops = Frame(root, width=1100, height=50, bg="wheat", relief=SUNKEN)
Tops.pack(side=TOP)

f1 = Frame(root, width=1100, height=550, bg="seashell2", relief=SUNKEN)
f1.pack(side=TOP)

card_id_var   = StringVar()
entry_var     = StringVar(value="ด่าน A")
exit_var      = StringVar(value="ด่าน B")
balance_var   = StringVar()
cost_var      = StringVar(value="0")
signal_status = StringVar()
signal_color  = StringVar(value="light grey")
mode_var      = StringVar(value="entry")

entry_options = ["ด่าน A", "ด่าน B", "ด่าน C"]

# ===================== คำนวณค่าทางด่วน =====================
def calculate_cost(entry, exit):
    table = {
        ("ด่าน A", "ด่าน B"): 150,
        ("ด่าน A", "ด่าน C"): 200,
        ("ด่าน B", "ด่าน C"): 50
    }
    if entry == exit:
        return 0
    return table.get((entry, exit)) or table.get((exit, entry), 50)

# ===================== ฟังก์ชันแสดงผล =====================
def update_signal(can_pass):
    if can_pass:
        signal_status.set("PASS")
        signal_color.set("green")
    else:
        signal_status.set("DENIED")
        signal_color.set("red")

# ===================== ฟังก์ชันหลัก =====================
def thread_ab():
    print("Start Thread A B!")
    card_id = card_id_var.get()
    entry_point = entry_var.get()
    exit_point = exit_var.get()

    card_data = download_card_data(card_id)
    if card_data is None:
        print("ไม่พบข้อมูลการ์ดใน FTP")
        update_signal(False)
        return
    
    balance = float(card_data.get("balance", 0))
    balance_var.set(str(balance))

    if mode_var.get() == "entry":
        if balance < 200:
            update_signal(False)
        else:
            update_signal(True)
    else:
        cost = calculate_cost(entry_point, exit_point)
        cost_var.set(str(cost))
        if balance >= cost:
            update_signal(True)
        else:
            update_signal(False)

    # รัน thread CD แยก
    threading.Thread(target=thread_cd, args=(card_data,), daemon=True).start()

def thread_cd(card_data):
    print("Start Thread C!")
    card_id = card_data["card_id"]
    entry_point = entry_var.get()
    exit_point = exit_var.get()
    balance = float(card_data.get("balance", 0))

    if mode_var.get() == "entry":
        update_transaction_log(card_data, entry_point=entry_point)
    else:
        cost = float(cost_var.get())
        if balance >= cost:
            card_data["balance"] -= cost
            update_transaction_log(card_data, entry_point=entry_point, exit_point=exit_point, cost=cost)

    generate_and_upload_json(card_id, card_data)

def reset_fields():
    reader = NFC_Reader()
    card_id = reader.read_uid().replace(" ", "_")
    
    card_id_var.set(card_id)
    card_data = download_card_data(card_id)
    if card_data is None:
        print("ไม่พบข้อมูลการ์ดใน FTP")
        update_signal(False)
        
    try:
        balance = float(card_data.get("balance", 0))
        balance_var.set(str(balance))
        print("Card id:", card_id)
    except:
        balance_var.set("0")
        print("Please register!!")

# ===================== ส่วนบน =====================
Label(Tops, font=('TH Saraban New', 40, 'bold'), text="ระบบชำระค่าทางด่วน", fg="Blue", bd=10, anchor='w', bg="seashell2").grid(row=0, column=0)
Label(Tops, font=('TH Saraban New', 16, 'bold'), text=datetime.datetime.now().strftime("%c"), fg="Blue", bd=10, anchor='w', bg="seashell2").grid(row=1, column=0)

# ===================== UI หลัก =====================
Label(f1, text="Card ID:", font=('TH Sarabun New', 18, 'bold'), bg="seashell2").grid(row=0, column=0, padx=10, pady=10, sticky='e')
Label(f1, textvariable=card_id_var, font=('TH Sarabun New', 18)).grid(row=0, column=1, padx=10, pady=10)

Label(f1, text="Entry Point:", font=('TH Sarabun New', 18, 'bold'), bg="seashell2").grid(row=1, column=0, padx=10, pady=10, sticky='e')
OptionMenu(f1, entry_var, *entry_options).grid(row=1, column=1, padx=10, pady=10)

Label(f1, text="Exit Point:", font=('TH Sarabun New', 18, 'bold'), bg="seashell2").grid(row=2, column=0, padx=10, pady=10, sticky='e')
OptionMenu(f1, exit_var, *entry_options).grid(row=2, column=1, padx=10, pady=10)

Label(f1, text="Balance:", font=('TH Sarabun New', 18, 'bold'), bg="seashell2").grid(row=0, column=2, padx=10, pady=10, sticky='e')
Label(f1, textvariable=balance_var, font=('TH Sarabun New', 18), bg="powder blue", width=16, justify='right').grid(row=0, column=3, padx=10, pady=10)

Label(f1, text="Cost:", font=('TH Sarabun New', 18, 'bold'), bg="seashell2").grid(row=1, column=2, padx=10, pady=10, sticky='e')
Label(f1, textvariable=cost_var, font=('TH Sarabun New', 18), bg="powder blue", width=16, justify='right').grid(row=1, column=3, padx=10, pady=10)

Label(f1, text="Signal:", font=('TH Sarabun New', 18, 'bold'), bg="seashell2").grid(row=2, column=2, padx=10, pady=10, sticky='e')
Label(f1, textvariable=signal_status, font=('TH Sarabun New', 18, 'bold'), width=16, fg="white", bg=signal_color.get()).grid(row=2, column=3, padx=10, pady=10)

Button(f1, text="Reset", font=('TH Sarabun New', 14, 'bold'),
       command=reset_fields, bg="orange").grid(row=3, column=2, padx=5, pady=20, sticky='e')

Label(f1, text="Mode:", font=('TH Sarabun New', 18, 'bold'), bg="seashell2").grid(row=3, column=0, padx=10, pady=10, sticky='e')
Radiobutton(f1, text="Entry", variable=mode_var, value="entry", font=('TH Sarabun New', 16), bg="seashell2").grid(row=3, column=1, sticky='w')
Radiobutton(f1, text="Exit", variable=mode_var, value="exit", font=('TH Sarabun New', 16), bg="seashell2").grid(row=3, column=1, sticky='e')

Button(f1, text="Tap Card", font=('TH Sarabun New', 16, 'bold'), bg="light green", command=lambda: threading.Thread(target=thread_ab, daemon=True).start()).grid(row=4, column=1, pady=20)
Button(f1, text="Exit", font=('TH Sarabun New', 16, 'bold'), bg="tomato", command=root.destroy).grid(row=4, column=2, pady=20)

reader = NFC_Reader()

card_id = reader.read_uid()

card_id_var.set(card_id)

card_data = download_card_data(card_id)
if card_data is None:
    print("ไม่พบข้อมูลการ์ดใน FTP")
    update_signal(False)
    
try:
    balance = float(card_data.get("balance", 0))
    balance_var.set(str(balance))

    print("Card id:", card_id)
except:
    print("Please register!!")
    balance_var.set("0")

root.mainloop()

