import sounddevice as sd
import time
import numpy as np

sd.default.samplerate = 16000

audio_data:np.array = np.array([])

def callback(indata, frames, time, status):
    global audio_data
    audio_data = np.append(audio_data, np.mean(np.abs(indata[:, 0])))
def start_recording():
    with sd.InputStream(callback=callback, channels=1):
        while len(audio_data) < 100:
            time.sleep(1/sd.default.samplerate)

print("please start speaking")
start_recording()
print(audio_data)
print(np.mean(np.abs(audio_data)))