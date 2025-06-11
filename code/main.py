import sounddevice as sd
import threading
import numpy as np
import time
import os
from matplotlib import pyplot

sd.default.samplerate = 16384
sound_level_threshold = 0.002
audio_data = np.array([])

lock = threading.Lock()

#Recording
def callback(indata, frames, time, status):
    global audio_data
    with lock:
        audio_data = np.append(audio_data, indata[:,0])
def start_recording():
    with sd.InputStream(callback=callback, channels=1):
        pass

#split audio_data into chunks for data processing
def split_chunk(is_active_from_previous_segment:bool):
    with lock:
        pass
    while len(audio_data) <= 0:
        time.sleep(sd.default.samplerate)

    chunk_data:np.array = np.array([])

    active_for_time:int = sd.default.samplerate * 1
    inactive_for_time:int = sd.default.samplerate * 2

    frame:int = 0

    active_counter:int = 0
    inactive_counter:int = 0

    active_frame_start:int = None
    active_frame_end:int = None
    
    is_active:bool = None

    while True:
        if frame >= len(audio_data[0]) - 1:
            return is_active, chunk_data
        
        if abs(audio_data[0][frame]) >= sound_level_threshold:
            is_active = True
            active_counter += 1
            if active_frame_start != None:
                active_frame_start = frame
        else:
            if is_active == False:
                inactive_counter += 1
            is_active = False
            if active_frame_end != None:
                active_frame_end = frame
            if inactive_counter < inactive_for_time:
                active_frame_end = None
    
        if active_counter > active_for_time:
            is_active = False

#Main thread
def Main():
    while True:
        chunk = split_chunk()
        #if len(chunk) > 0:
        #    print(chunk)

if __name__ == '__main__':
    recording_thread = threading.Thread(target=start_recording)
    main_thread = threading.Thread(target=Main)

    recording_thread.start()
    main_thread.start()