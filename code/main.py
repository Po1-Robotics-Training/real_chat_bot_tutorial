import sounddevice as sd
import threading
import numpy as np
import time
import os
from matplotlib import pyplot

sd.default.samplerate = 8000
sound_level_threshold = 0.05
audio_data = np.array([])
inactive_count:float = 0.0
inactive_for_time:float = 2.0

lock = threading.Lock()

#Recording
def callback(indata, frames, time, status):
    split_chunk(indata=indata, frames=frames)
def start_recording():
    with sd.InputStream(callback=callback, channels=1):
        while True:
            time.sleep(1/sd.default.samplerate)

def split_chunk(indata, frames):
    global inactive_count, audio_data
    if np.mean(np.abs(indata)) > sound_level_threshold:
        with lock:
            inactive_count = 0
            audio_data = np.append(audio_data, indata[:, 0])
    else:
        with lock:
            inactive_count += frames/sd.default.samplerate

    if inactive_count > inactive_for_time:
        with lock:
            audio_data = np.array([])

#Main thread
def Main():
    global audio_data
    while True:
        time.sleep(1/sd.default.samplerate)
        print(audio_data)

recording_thread = threading.Thread(target=start_recording)
main_thread = threading.Thread(target=Main)

recording_thread.start()
main_thread.start()