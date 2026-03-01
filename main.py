import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
import soundfile as sf
import sounddevice as sd
import time
import os
import matplotlib.pyplot as plt

# ------------------------
# PARAMETRELER
# ------------------------
fs = 8000
tone_duration = 0.05
silence_duration = 0.02
min_power_threshold = 50

low_freqs = [600, 697, 770, 852, 941, 1020]
high_freqs = [1100, 1209, 1336, 1477, 1633]

characters = [
    'A','B','C','Ç','D',
    'E','F','G','Ğ','H',
    'I','İ','J','K','L',
    'M','N','O','Ö','P',
    'R','S','Ş','T','U',
    'Ü','V','Y','Z',' '
]

freq_map = {}
index = 0
for f1 in low_freqs:
    for f2 in high_freqs:
        if index < len(characters):
            freq_map[characters[index]] = (f1, f2)
            index += 1
reverse_map = {v: k for k, v in freq_map.items()}

# ------------------------
# ENCODE
# ------------------------
def encode(text):
    signal = np.array([])
    t = np.linspace(0, tone_duration, int(fs*tone_duration), endpoint=False)
    silence = np.zeros(int(fs*silence_duration))
    for char in text:
        if char not in freq_map: continue
        f1,f2 = freq_map[char]
        tone = np.sin(2*np.pi*f1*t)+np.sin(2*np.pi*f2*t)
        signal = np.concatenate((signal,tone,silence))
    return signal

# ------------------------
# GOERTZEL
# ------------------------
def goertzel(samples,freq):
    N = len(samples)
    k = int(0.5 + (N*freq)/fs)
    w = (2*np.pi/N)*k
    cosine = np.cos(w)
    sine = np.sin(w)
    coeff = 2*cosine
    q0=q1=q2=0
    for sample in samples:
        q0=coeff*q1 - q2 + sample
        q2=q1
        q1=q0
    real = q1 - q2*cosine
    imag = q2*sine
    return real**2 + imag**2

# ------------------------
# DECODE
# ------------------------
def decode(filename):
    signal,_=sf.read(filename)
    step = int(fs*tone_duration)
    silence_step = int(fs*silence_duration)
    text=""
    i=0
    while i+step <= len(signal):
        window = signal[i:i+step]*np.hamming(step)
        low_powers = [(f, goertzel(window,f)) for f in low_freqs]
        best_low = max(low_powers,key=lambda x:x[1])
        high_powers = [(f, goertzel(window,f)) for f in high_freqs]
        best_high = max(high_powers,key=lambda x:x[1])
        if best_low[1]>min_power_threshold and best_high[1]>min_power_threshold:
            pair=(best_low[0],best_high[0])
            if pair in reverse_map: text+=reverse_map[pair]
        i+=step+silence_step
    return text

# ------------------------
# SES ÇALMA
# ------------------------
def play_audio(filename):
    data,fs_local=sf.read(filename)
    sd.play(data,fs_local)
    sd.wait()

def plot_signal(audio):
    plt.figure(figsize=(14,5))
    time_axis = np.linspace(0,len(audio)/fs,len(audio))
    plt.plot(time_axis,audio,color='#1f77b4',lw=1)
    plt.title("DTMF Sinyali (Zaman-Domain)",fontsize=16)
    plt.xlabel("Zaman (s)",fontsize=14)
    plt.ylabel("Genlik",fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.show()

# ------------------------
# GUI FONKSİYONLARI
# ------------------------
def on_submit():
    user_text = text_input.get("1.0","end-1c").upper()
    if not user_text:
        messagebox.showerror("Hata","Lütfen metin girin!")
        return
    audio = encode(user_text)
    filename = "dtmf_output.wav"
    if os.path.exists(filename):
        os.remove(filename)
        time.sleep(0.3)
    sf.write(filename,audio,fs)
    play_audio(filename)
    decoded_text = decode(filename)
    result_label.config(text=f"Çözülen Metin: {decoded_text}")
    plot_button.config(state='normal')
    global last_audio
    last_audio = audio

def on_plot():
    if last_audio is not None:
        plot_signal(last_audio)

# ------------------------
# MODERN ARAYÜZ
# ------------------------
root = tk.Tk()
root.title("DTMF Encoder/Decoder - Premium")
root.state('zoomed')
root.configure(bg="#12122b")

style = ttk.Style()
style.theme_use('clam')
style.configure('TButton',font=("Segoe UI",14,"bold"),
                foreground='white',background='#4e8cff',padding=10)
style.map('TButton',background=[('active','#357ab7')])

# Başlık
title_frame = tk.Frame(root,bg="#12122b")
title_frame.pack(pady=25)
tk.Label(title_frame,text="DTMF Metin Encoder/Decoder",font=("Segoe UI",28,"bold"),
         fg="#ffffff",bg="#12122b").pack()

# Giriş
input_frame = tk.Frame(root,bg="#1f1f3e",bd=2,relief='groove')
input_frame.pack(pady=20,padx=25,fill='x')
tk.Label(input_frame,text="Metninizi girin:",font=("Segoe UI",16),fg="white",bg="#1f1f3e").pack(anchor='w',padx=10,pady=5)
text_input = scrolledtext.ScrolledText(input_frame,height=6,font=("Segoe UI",14))
text_input.pack(padx=10,pady=5,fill='x')

# Butonlar
button_frame = tk.Frame(root,bg="#12122b")
button_frame.pack(pady=15)
submit_button = ttk.Button(button_frame,text="Gönder",command=on_submit)
submit_button.grid(row=0,column=0,padx=20)
plot_button = ttk.Button(button_frame,text="Grafiği Göster",command=on_plot,state='disabled')
plot_button.grid(row=0,column=1,padx=20)

# Sonuç
result_frame = tk.Frame(root,bg="#1f1f3e",bd=2,relief='groove')
result_frame.pack(padx=25,pady=15,fill='x')
result_label = tk.Label(result_frame,text="Çözülen Metin: ",font=("Segoe UI",16),
                        fg="white",bg="#1f1f3e",wraplength=1400,justify="left")
result_label.pack(padx=10,pady=10)

last_audio=None
root.mainloop()