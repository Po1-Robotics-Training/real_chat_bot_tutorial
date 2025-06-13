import sounddevice as sd
import threading
import numpy as np
import time
import librosa
import os
import glob
from transformers import WhisperForConditionalGeneration, WhisperProcessor

sd.default.samplerate = 16000
sound_level_threshold = 0.05
audio_data = np.array([])
audio_queue:list = []
inactive_count:float = 0.0
inactive_for_time:float = 2.0

MODEL_NAME = "alvanlii/whisper-small-cantonese"
print('modelname')
processor = WhisperProcessor.from_pretrained(MODEL_NAME)
print('processor')
model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)
print('model')

lock = threading.Lock()

#Recording thread
def callback(indata, frames, time, status):
    split_chunk(indata=indata, frames=frames)
def start_recording():
    with sd.InputStream(callback=callback, channels=1):
        while True:
            time.sleep(1/sd.default.samplerate)

def split_chunk(indata, frames):
    global inactive_count, audio_data, audio_queue
    if np.mean(np.abs(indata)) > sound_level_threshold:
        with lock:
            inactive_count = 0
            audio_data = np.append(audio_data, indata[:, 0])
    else:
        with lock:
            inactive_count += frames/sd.default.samplerate

    if inactive_count > inactive_for_time:
        with lock:
            if len(audio_data) > 0:
                audio_queue.append(audio_data.tolist())
            audio_data = np.array([])

def process_stt(indata:np.array):
    processed_in = processor(indata, sampling_rate = sd.default.samplerate, return_tensors = "pt")
    print('generate')
    gout = model.generate(
        input_features = processed_in.input_features,
        output_scores = True,
        return_dict_in_generate = True
    )
    transcription = processor.batch_decode(gout.sequences, skip_special_tokens=True)[0]
    print(transcription)

#Main thread
def Main():
    global audio_data, audio_queue
    process_queue:np.array = np.array([])
    with lock:
        process_queue = audio_queue
    while True:
        while len(process_queue) > 0:
            process_stt(process_queue[0])
            with lock:
                process_queue = audio_queue
            process_queue = np.delete(process_queue, 0)

recording_thread = threading.Thread(target=start_recording)
main_thread = threading.Thread(target=Main)

recording_thread.start()
main_thread.start()