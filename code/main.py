import sounddevice as sd
import threading
import numpy as np
import time
import os
from matplotlib import pyplot

sd.default.samplerate = 8000
sound_level_threshold = 0.1
audio_data = np.array([])

lock = threading.Lock()

#Recording
def callback(indata, frames, time, status):
    global audio_data
    with lock:
        audio_data = np.append(audio_data, indata[:,0])
def start_recording():
    with sd.InputStream(callback=callback, channels=1):
        while True:
            time.sleep(1/sd.default.samplerate)

#split audio_data into chunks for data processing
def split_chunk(is_active_from_previous_segment:bool):
    global audio_data
    with lock:
        chunk_audio:np.array = audio_data
    while len(chunk_audio) <= 0:
        time.sleep(1/sd.default.samplerate)

    if is_active_from_previous_segment:
        active_frame_start = 0

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
        print('audio_data')
        if frame >= len(chunk_audio) - 1:
            if is_active and active_frame_start != None:
                chunk_data = chunk_audio[active_frame_start:len(chunk_audio) - 1]
            if active_frame_start != None and active_frame_end != None:
                chunk_data = chunk_audio[active_frame_start:active_frame_end]

            with lock:
                audio_data = np.delete(arr=audio_data, obj=range(0,len(chunk_audio)))

            return is_active, chunk_data
        
        if abs(chunk_audio[frame]) >= sound_level_threshold:
            is_active = True
            active_counter += 1
            if active_frame_start == None:
                active_frame_start = frame
        else:
            if is_active == False:
                inactive_counter += 1
            is_active = False
            if active_frame_end == None and active_frame_start != None and inactive_counter > inactive_for_time:
                active_frame_end = frame
        
        frame += 1

#Main thread
def Main():
    chunk:np.array = np.array([])
    is_active_from_previous_chunk:bool = False
    current_chunk:np.array = np.array([])
    while True:
        current_chunk = np.array([])
        print(audio_data)
        is_active_from_previous_chunk, current_chunk = split_chunk(is_active_from_previous_segment=is_active_from_previous_chunk)
        print(audio_data)
        chunk = np.append(chunk, current_chunk)

        if is_active_from_previous_chunk == False:
            print('Chunk fisished\n')
            print(current_chunk)

if __name__ == '__main__':
    recording_thread = threading.Thread(target=start_recording)
    main_thread = threading.Thread(target=Main)

    recording_thread.start()
    main_thread.start()