import sounddevice as sd
import threading
import numpy as np
import time
from transformers import WhisperForConditionalGeneration, WhisperProcessor

sd.default.samplerate = 16000
sound_level_threshold = 0.0002
audio_data = np.array([])
audio_queue:np.array = np.array([])
inactive_count:float = 0.0
inactive_for_time:float = 2.0
is_chunk_active:bool = False

MODEL_NAME = "alvanlii/whisper-small-cantonese"
print('Model loaded')
processor = WhisperProcessor.from_pretrained(MODEL_NAME)
print('Processor Created')
model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)
print('Model initiated')

lock = threading.Lock()

#Recording thread
def callback(indata, frames, time, status):
    split_chunk(indata=indata, frames=frames)
def start_recording():
    with sd.InputStream(callback=callback, channels=1):
        while True:
            time.sleep(1/sd.default.samplerate)

def split_chunk(indata, frames):
    global inactive_count, audio_data, audio_queue, is_chunk_active
    print(np.mean(np.abs(indata)) > sound_level_threshold)
    if np.mean(np.abs(indata)) > sound_level_threshold:
        with lock:
            is_chunk_active = True
            inactive_count = 0
            audio_data = np.append(audio_data, indata[:, 0])
    elif is_chunk_active:
        with lock:
            inactive_count += frames/sd.default.samplerate
            audio_data = np.append(audio_data, indata[:, 0])
    else:
        with lock:
            inactive_count += frames/sd.default.samplerate

    if inactive_count > inactive_for_time and len(audio_data) > 1000:
        with lock:
            is_chunk_active = False
            process_stt(audio_data)
            audio_data = np.array([])

def process_stt(indata):
    print(f"Audio segment shape: {indata.shape}, ndim={indata.ndim}")
    processed_in = processor(indata, sampling_rate=sd.default.samplerate, return_tensors="pt")
    gout = model.generate(
        input_features=processed_in.input_features, 
        output_scores=True, return_dict_in_generate=True
    )
    transcription = processor.batch_decode(gout.sequences, skip_special_tokens=True)[0]
    print("\n",transcription)

recording_thread = threading.Thread(target=start_recording)

recording_thread.start()