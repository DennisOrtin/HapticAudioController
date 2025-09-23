"""
Bass-to-Arduino Bridge
----------------------

This Python program:
1. Detects if an Arduino (Uno/other compatible devices) is connected via USB.
2. Opens the system audio input (e.g., speaker loopback, mic, etc.) using PyAudio.
3. Captures real-time audio chunks, converts them into NumPy arrays.
4. Extracts the "bass" frequency band (50–200 Hz) using FFT.
5. Computes the average energy of that band, normalizes to 0–255.
6. Sends the value over Serial to the Arduino, where it can be used for PWM/motor control.

Dependencies:
    pip install pyaudio numpy pyserial

Note:
    - On Windows, set input_device_index to the WASAPI loopback device
      to capture system audio ("what you hear").
    - On macOS/Linux, use a virtual loopback device (BlackHole, Soundflower, PulseAudio).
"""

import numpy as np
import pyaudio
import serial
import serial.tools.list_ports
import time


# -----------------------------
# 1. Find Arduino automatically
# -----------------------------
def find_arduino():
    """
    Scan available serial ports and try to identify an Arduino Uno (Elegoo, clone, etc.)
    Returns: port string (e.g., "COM3" or "/dev/ttyACM0") or None if not found.
    """
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        # Many Uno R3 clones have "Arduino" or "wchusbserial" in description
        if "Arduino" in port.description or "wchusbserial" in port.device.lower() or "ttyACM" in port.device or "Arduino" in str(
                port.manufacturer):
            return port.device
    return None


arduino_port = find_arduino()
if arduino_port is None:
    print("❌ No Arduino detected. Please plug it in and try again.")
    exit(1)

print(f"✅ Arduino detected on {arduino_port}")

# Open Serial connection (match Arduino sketch baud rate!)
BAUD = 115200
ser = serial.Serial(arduino_port, BAUD, timeout=0, bytesize=8)
time.sleep(5)  # give Arduino time to reset

# -----------------------------
# 2. Audio capture setup
# -----------------------------
CHUNK = 1024  # samples per frame
RATE = 44100  # sampling rate (Hz)
BASS_LOW = 30  # Hz cutoff low
BASS_HIGH = 200  # Hz cutoff high
gainTimer = 0
timerGainMaxHigh = 60
timerGainMaxMid = 120
timerGainMaxLow = 90
gain = 0.006

p = pyaudio.PyAudio()

info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

for i in range(0, numdevices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

input_device_id = int(input("Enter ID: "))
adaptiveGain = str(input("Would you like adaptive gain? Y/N")).capitalize() == "Y"
if not adaptiveGain:
    gain = float(input(str("What gain would you like? Default: " + str(gain) + " ")))
# You may need to set input_device_index to your loopback device
stream = p.open(format=pyaudio.paInt16,
                channels=1,  # mono
                rate=RATE,
                input=True,
                input_device_index=input_device_id,
                frames_per_buffer=CHUNK)

print("🎵 Capturing audio... press Ctrl+C to stop.")

# -----------------------------
# 3. Processing loop
# -----------------------------
try:
    prevVal = 0
    while True:
        # --- Read raw audio ---
        data = stream.read(CHUNK, exception_on_overflow=False)
        samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)

        # --- Apply FFT ---
        fft = np.fft.rfft(samples * np.hanning(len(samples)))  # windowed FFT
        freqs = np.fft.rfftfreq(len(samples), 1.0 / RATE)
        magnitude = np.abs(fft)

        # --- Extract bass band (50–500 Hz) ---
        mask = (freqs >= BASS_LOW) & (freqs <= BASS_HIGH)
        bass_energy = magnitude[mask].mean()
        # --- Normalize to 0–255 ---
        # Scale factor depends on your system volume; tune "gain" until motor feels right
        if adaptiveGain:
            val = int(np.clip(bass_energy * gain, 0, 255))
            prevVal = val
            if prevVal < 205 < val:
                gainTimer = 0
            elif val < 195 < prevVal:
                gainTimer = 0
            if val > 230:
                gainTimer += 1
                if gainTimer > timerGainMaxHigh:
                    gain -= 0.0008*(float(gainTimer*2)/timerGainMaxHigh)
            elif 205 < val < 231:
                gainTimer += 1
                if gainTimer > timerGainMaxHigh:
                    gain -= 0.0004*(float(gainTimer*2)/timerGainMaxHigh)
            elif 80 < val < 195:
                gainTimer +=1
                if gainTimer > timerGainMaxMid:
                    gain+=0.0005
            elif bass_energy > 50 and val < 81:
                gainTimer += 1
                if gainTimer > timerGainMaxLow:
                    gain += 0.009
            else:
                gainTimer = 0
        else:
            val = int(np.clip(bass_energy * gain, 0, 255))
        # --- Send byte to Arduino ---
        print("Final " + str(val) + " Timer: " + str(gainTimer) + " Gain: " + str(gain))
        ser.write((val.to_bytes(1, byteorder='big')))


except KeyboardInterrupt:
    print("\n🛑 Stopping...")

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()
    ser.close()
    print("✅ Clean exit.")
