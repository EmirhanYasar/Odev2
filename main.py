import tkinter as tk
from tkinter import messagebox
import numpy as np
import soundfile as sf
import time
import os
import sounddevice as sd
import matplotlib.pyplot as plt

# ------------------------
# PARAMETRELER
# ------------------------
fs = 8000
tone_duration = 0.05
silence_duration = 0.02
min_power_threshold = 50

# ------------------------
# 30 HARF İÇİN FREKANSLAR (6x5)
# ------------------------
low_freqs = [600, 697, 770, 852, 941, 1020]
high_freqs = [1100, 1209, 1336, 1477, 1633]

characters = [
    'A', 'B', 'C', 'Ç', 'D',
    'E', 'F', 'G', 'Ğ', 'H',
    'I', 'İ', 'J', 'K', 'L',
    'M', 'N', 'O', 'Ö', 'P',
    'R', 'S', 'Ş', 'T', 'U',
    'Ü', 'V', 'Y', 'Z', ' '
]

# Frekans eşleme
freq_map = {}
index = 0
for f1 in low_freqs:
    for f2 in high_freqs:
        if index < len(characters):
            freq_map[characters[index]] = (f1, f2)
            index += 1

reverse_map = {v: k for k, v in freq_map.items()}

# ------------------------
# ENCODE (METNİ SİNYALE ÇEVİRME)
# ------------------------
def encode(text):
    signal = np.array([])
    t = np.linspace(0, tone_duration, int(fs * tone_duration), endpoint=False)
    silence = np.zeros(int(fs * silence_duration))

    for char in text:
        if char not in freq_map:
            continue
        f1, f2 = freq_map[char]
        tone = np.sin(2 * np.pi * f1 * t) + np.sin(2 * np.pi * f2 * t)
        signal = np.concatenate((signal, tone, silence))

    return signal

# ------------------------
# GOERTZEL ALGORİTMASI
# ------------------------
def goertzel(samples, freq):
    N = len(samples)
    k = int(0.5 + (N * freq) / fs)
    w = (2.0 * np.pi / N) * k
    cosine = np.cos(w)
    sine = np.sin(w)
    coeff = 2 * cosine
    q0 = q1 = q2 = 0

    for sample in samples:
        q0 = coeff * q1 - q2 + sample
        q2 = q1
        q1 = q0

    real = q1 - q2 * cosine
    imag = q2 * sine
    return real**2 + imag**2

# ------------------------
# DECODE (SİNYALİ HARFE ÇEVİRME)
# ------------------------
def decode(filename):
    signal, _ = sf.read(filename)
    step = int(fs * tone_duration)
    silence_step = int(fs * silence_duration)
    text = ""

    i = 0
    while i + step <= len(signal):
        window = signal[i:i+step]

        # -------- Hamming Pencereleme --------
        window = window * np.hamming(len(window))

        # -------- Goertzel ile frekans tespiti --------
        low_powers = [(f, goertzel(window, f)) for f in low_freqs]
        best_low = max(low_powers, key=lambda x: x[1])

        high_powers = [(f, goertzel(window, f)) for f in high_freqs]
        best_high = max(high_powers, key=lambda x: x[1])

        if best_low[1] > min_power_threshold and best_high[1] > min_power_threshold:
            pair = (best_low[0], best_high[0])
            if pair in reverse_map:
                text += reverse_map[pair]

        i += step + silence_step

    return text

# ------------------------
# SESİ ÇALMA
# ------------------------
def play_audio(filename):
    data, fs_local = sf.read(filename)
    sd.play(data, fs_local)
    sd.wait()

# ------------------------
# TKINTER GUI
# ------------------------
def on_submit():
    user_text = text_input.get("1.0", "end-1c").upper()

    if not user_text:
        messagebox.showerror("Hata", "Lütfen metin girin!")
        return

    audio = encode(user_text)
    filename = "dtmf_output.wav"

    if os.path.exists(filename):
        os.remove(filename)
        time.sleep(0.3)

    sf.write(filename, audio, fs)

    play_audio(filename)

    decoded_text = decode(filename)
    result_label.config(text=f"Çözülen Metin: {decoded_text}")

    # -------- Zaman-Domain Grafiği --------
    plt.figure(figsize=(10, 4))
    time_axis = np.linspace(0, len(audio)/fs, len(audio))
    plt.plot(time_axis, audio)
    plt.title("DTMF Sinyali (Zaman Domain)")
    plt.xlabel("Zaman (s)")
    plt.ylabel("Genlik")
    plt.grid()
    plt.show()

# ------------------------
# GUI ELEMENTLERİ
# ------------------------
root = tk.Tk()
root.title("DTMF 30 Harf Encoder/Decoder")
root.geometry("600x500")

tk.Label(root, text="DTMF Metin Encoder/Decoder", font=("Helvetica", 16)).pack(pady=10)
tk.Label(root, text="Metninizi girin", font=("Helvetica", 12)).pack(pady=5)

text_input = tk.Text(root, height=6, width=50)
text_input.pack(pady=10)

tk.Button(root, text="Gönder", command=on_submit, font=("Helvetica", 12)).pack(pady=15)

result_label = tk.Label(root, text="Çözülen Metin: ", font=("Helvetica", 12))
result_label.pack(pady=10)

root.mainloop()