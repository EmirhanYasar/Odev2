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
fs = 8000  # Örnekleme frekansı
tone_duration = 0.04  # Her karakterin sesi 40 ms sürecek
silence_duration = 0.01  # Sessizlik süresi (10 ms)
min_power_threshold = 10  # Eşik değeri (daha düşük olanlar yok sayılacak)

# ------------------------
# FREKANSLAR
# ------------------------
low_freqs = [697, 770, 852, 941]   # Düşük frekanslar
high_freqs = [1209, 1336, 1477, 1633]  # Yüksek frekanslar

# Türk alfabesi ve boşluk karakteri
characters = [
    'A', 'B', 'C', 'Ç', 'D', 'E', 'F', 'G', 'Ğ', 'H', 'I', 'İ', 'J', 'K', 'L', 'M', 'N', 'O', 'Ö', 'P', 'R', 'S', 'Ş', 'T', 'U', 'Ü', 'V', 'Y', 'Z', ' '
]

# Frekans eşlemeleri
freq_map = {}
index = 0

# Frekans çifti oluşturuluyor
for f1 in low_freqs:
    for f2 in high_freqs:
        if index < len(characters):  # Eğer index 30'u geçmiyorsa
            freq_map[characters[index]] = (f1, f2)
            index += 1

# Frekans çiftlerine karşılık gelen karakterlerin ters eşlemesi
reverse_map = {v: k for k, v in freq_map.items()}

# ------------------------
# ENCODE (Sinyal Sentezleme)
# ------------------------
def encode(text):
    signal = np.array([])  # Başlangıçta boş bir dizi oluşturuluyor
    t = np.linspace(0, tone_duration, int(fs * tone_duration), endpoint=False)  # Zaman dizisi (30-50 ms arası)
    silence = np.zeros(int(fs * silence_duration))  # Sessizlik dizisi

    # Metindeki her karakteri dönüştür
    for char in text:
        if char not in freq_map:
            continue
        f1, f2 = freq_map[char]  # Karaktere karşılık gelen frekansları al
        tone = np.sin(2 * np.pi * f1 * t) + np.sin(2 * np.pi * f2 * t)  # Sinyali oluştur
        signal = np.concatenate((signal, tone, silence))  # Sinyali ve sessizliği birleştir

    return signal

# ------------------------
# GOERTZEL (Frekans Algoritması)
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
# DECODE (Çözümleme)
# ------------------------
def decode(filename):
    signal, _ = sf.read(filename)
    step = int(fs * tone_duration)
    silence_step = int(fs * silence_duration)
    text = ""

    i = 0
    while i + step <= len(signal):
        window = signal[i:i+step]

        max_power = 0
        best_pair = None

        # Frekans çiftlerinin tespiti
        for f1 in low_freqs:
            for f2 in high_freqs:
                power = goertzel(window, f1) + goertzel(window, f2)
                if power > max_power and power > min_power_threshold:
                    max_power = power
                    best_pair = (f1, f2)

        if best_pair in reverse_map:
            text += reverse_map[best_pair]

        i += step + silence_step

    return text

# ------------------------
# SESİ ÇALMA FONKSİYONU
# ------------------------
def play_audio(filename):
    data, fs = sf.read(filename)  # Ses dosyasını oku
    sd.play(data, fs)  # Ses dosyasını çal
    sd.wait()  # Sesin tamamlanmasını bekle

# ------------------------
# Gelişmiş Tkinter Arayüzü
# ------------------------

def on_submit():
    user_text = text_input.get("1.0", "end-1c").upper()  # Kullanıcının girdiği metni al
    if not user_text:
        messagebox.showerror("Hata", "Lütfen bir metin girin!")
        return

    # Encoding (Metni ses dosyasına dönüştür)
    audio = encode(user_text)
    filename = "dtmf_output.wav"
    
    # Dosyanın var olup olmadığını kontrol et
    if os.path.exists(filename):
        os.remove(filename)  # Eğer dosya varsa, sil
        time.sleep(0.5)  # Dosyanın silinmesi için bekle

    sf.write(filename, audio, fs)  # Ses dosyasını kaydet
    messagebox.showinfo("Başarılı", f"Ses dosyası oluşturuldu: {filename}")

    # Ses dosyasını çal
    play_audio(filename)

    # Decoding (Çözümleme)
    decoded_text = decode(filename)
    result_label.config(text=f"Çözülen Metin: {decoded_text}")

    # Sinyal Grafiği Çizme (Zaman Domaini)
    plt.figure(figsize=(10, 6))
    time_axis = np.linspace(0, len(audio) / fs, len(audio))  # Zaman eksenini oluştur
    plt.plot(time_axis, audio)
    plt.title("DTMF Sinyali Zaman-Domain Grafiği")
    plt.xlabel("Zaman (s)")
    plt.ylabel("Genlik")
    plt.grid(True)
    plt.show()

# Tkinter arayüzü oluşturma
root = tk.Tk()
root.title("DTMF Encoder/Decoder")
root.geometry("600x500")

# Başlık
label = tk.Label(root, text="DTMF Metin Encoder/Decoder", font=("Helvetica", 16))
label.pack(pady=10)

# Kullanıcı metni girmesi için etiket
label2 = tk.Label(root, text="Metninizi buraya girin", font=("Helvetica", 12))
label2.pack(pady=10)

# Çok satırlı metin kutusu (scrollable)
text_input = tk.Text(root, height=6, width=50)
text_input.pack(pady=10)

# Gönder Butonu
submit_button = tk.Button(root, text="Gönder", command=on_submit, font=("Helvetica", 12))
submit_button.pack(pady=20)

# Çözülen metin etiketi
result_label = tk.Label(root, text="Çözülen Metin: ", font=("Helvetica", 12))
result_label.pack(pady=10)

# GUI arayüzünü çalıştır
root.mainloop()