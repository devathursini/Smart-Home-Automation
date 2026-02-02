import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import time
import platform
import random

# ---------------- SIMULATION OF DEVICES ----------------
class Device:
    def __init__(self): self.state=False
    @property
    def is_lit(self): return self.state
    def on(self): self.state=True
    def off(self): self.state=False

light = Device()
fan = Device()

class PIR:
    def motion(self): return random.choice([True,False,False])
pir = PIR()

# ---------------- SOUND ----------------
if platform.system()=="Windows":
    import winsound
    def click_sound(): winsound.Beep(800,120)
else:
    import os
    def click_sound(): os.system('printf "\a"')

# ---------------- DATABASE ----------------
conn = sqlite3.connect("smart_home.db")
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device TEXT,
    status TEXT,
    temperature REAL,
    humidity REAL,
    timestamp TEXT
)
""")
conn.commit()

def log_status(device,status,temp=None,hum=None):
    if temp is None: temp=random.randint(20,30)
    if hum is None: hum=random.randint(40,70)
    timestamp=time.strftime("%d-%m-%Y %H:%M:%S")
    cur.execute("INSERT INTO logs(device,status,temperature,humidity,timestamp) VALUES (?,?,?,?,?)",
                (device,status,temp,hum,timestamp))
    conn.commit()

# ---------------- GUI ----------------
root=tk.Tk()
root.title("🏠 Smart Home Automation")
root.geometry("750x650")
root.resizable(False,False)

# ---------------- ANIMATED BACKGROUND ----------------
canvas=tk.Canvas(root,width=750,height=650)
canvas.pack(fill="both",expand=True)
gradient_colors=["#1e272e","#6c5ce7","#00cec9","#fd79a8","#fab1a0","#fdcb6e"]
color_index=0
def animate_bg():
    global color_index
    canvas.configure(bg=gradient_colors[color_index])
    color_index=(color_index+1)%len(gradient_colors)
    root.after(500,animate_bg)
animate_bg()

frame=tk.Frame(canvas,bg="#000000")
frame.place(relx=0.5,rely=0.5,anchor="center")

# ---------------- TITLE ----------------
title=tk.Label(frame,text="Smart Home Automation",font=("Arial",24,"bold"),fg="white",bg="#000000")
title.pack(pady=15)
colors=["#00cec9","#6c5ce7","#fd79a8","#00b894","#fab1a0","#fdcb6e"]
c_idx=0
def animate_title():
    global c_idx
    title.config(fg=colors[c_idx])
    c_idx=(c_idx+1)%len(colors)
    root.after(300,animate_title)
animate_title()

# ---------------- DEVICE BUTTONS ----------------
def flash(btn):
    orig=btn.cget("bg")
    btn.config(bg="#fdcb6e")
    root.after(300,lambda:btn.config(bg=orig))

def toggle_light():
    if light.is_lit: light.off(); status="OFF"
    else: light.on(); status="ON"
    click_sound(); update_status(); log_status("Light",status); flash(light_btn)

def toggle_fan():
    if fan.is_lit: fan.off(); status="OFF"
    else: fan.on(); status="ON"
    click_sound(); update_status(); log_status("Fan",status); flash(fan_btn)

btn_frame=tk.Frame(frame,bg="#000000")
btn_frame.pack(pady=10)
light_btn=tk.Button(btn_frame,text="Toggle Light",width=20,height=2,bg="#2ecc71",fg="white",command=toggle_light)
light_btn.grid(row=0,column=0,padx=10)
fan_btn=tk.Button(btn_frame,text="Toggle Fan",width=20,height=2,bg="#0984e3",fg="white",command=toggle_fan)
fan_btn.grid(row=0,column=1,padx=10)

# ---------------- STATUS DISPLAY ----------------
status_label=tk.Label(frame,text="",font=("Arial",12),fg="white",bg="#000000",justify="left")
status_label.pack(pady=10)

motion_canvas=tk.Canvas(frame,width=100,height=100,bg="#000000",highlightthickness=0)
motion_canvas.pack()
motion_circle=motion_canvas.create_oval(20,20,80,80,fill="#dfe6e9")

temp_canvas=tk.Canvas(frame,width=300,height=20,bg="#222222",highlightthickness=0)
temp_canvas.pack(pady=5)
temp_bar=temp_canvas.create_rectangle(0,0,0,20,fill="#fdcb6e")
hum_canvas=tk.Canvas(frame,width=300,height=20,bg="#222222",highlightthickness=0)
hum_canvas.pack(pady=5)
hum_bar=hum_canvas.create_rectangle(0,0,0,20,fill="#00cec9")

# ---------------- UPDATE STATUS ----------------
def update_status():
    temp=random.randint(20,30)
    hum=random.randint(40,70)
    motion="Detected" if pir.motion() else "No motion"
    status_label.config(text=f"Light: {'ON' if light.is_lit else 'OFF'} | Fan: {'ON' if fan.is_lit else 'OFF'}\nMotion: {motion}\nTemp:{temp}°C Hum:{hum}%")
    motion_canvas.itemconfig(motion_circle,fill="#fdcb6e" if motion=="Detected" else "#dfe6e9")
    temp_width=int((temp-20)/10*300)
    hum_width=int((hum-40)/40*300)
    temp_canvas.coords(temp_bar,0,0,temp_width,20)
    hum_canvas.coords(hum_bar,0,0,hum_width,20)
    # Alerts
    if temp>28: messagebox.showwarning("Temp Alert",f"Temperature high: {temp}°C")
    if hum<45: messagebox.showwarning("Humidity Alert",f"Humidity low: {hum}%")
    if motion=="Detected": messagebox.showinfo("Motion Alert","Motion detected!")
    root.after(5000,update_status)

update_status()

# ---------------- AUTO LIGHT ----------------
def auto_light_check():
    if pir.motion() and not light.is_lit:
        light.on(); click_sound(); log_status("Light(Auto)","ON"); flash(light_btn)
    root.after(1000,auto_light_check)
auto_light_check()

# ---------------- SCHEDULE ----------------
schedules=[("Light","08:00","ON"),("Fan","22:00","OFF")]

def check_schedule():
    now=time.strftime("%H:%M")
    for device,time_str,action in schedules:
        if now==time_str:
            if device=="Light":
                light.on() if action=="ON" else light.off()
                log_status("Light(Scheduled)",action); flash(light_btn)
            if device=="Fan":
                fan.on() if action=="ON" else fan.off()
                log_status("Fan(Scheduled)",action); flash(fan_btn)
    root.after(60000,check_schedule)

check_schedule()

# ---------------- VIEW LOGS ----------------
def view_logs():
    log_win=tk.Toplevel(root)
    log_win.title("Logs")
    log_win.geometry("650x400")
    log_win.configure(bg="#2f3640")
    tk.Label(log_win,text="Device Logs",font=("Arial",14,"bold"),fg="#fbc531",bg="#2f3640").pack(pady=10)
    tree=ttk.Treeview(log_win,columns=("Device","Status","Temp","Hum","Time"),show="headings")
    tree.heading("Device",text="Device")
    tree.heading("Status",text="Status")
    tree.heading("Temp",text="Temp (°C)")
    tree.heading("Hum",text="Humidity (%)")
    tree.heading("Time",text="Timestamp")
    tree.pack(expand=True,fill="both",padx=10,pady=10)
    cur.execute("SELECT device,status,temperature,humidity,timestamp FROM logs ORDER BY id DESC LIMIT 50")
    for r in cur.fetchall(): tree.insert("",tk.END,values=r)

view_btn=tk.Button(frame,text="View Logs",bg="#fd79a8",fg="white",width=20,height=2,command=view_logs)
view_btn.pack(pady=10)

root.mainloop()
