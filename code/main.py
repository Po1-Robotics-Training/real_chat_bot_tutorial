import sounddevice as sd
import threading
import numpy as np
import time
from transformers import WhisperForConditionalGeneration, WhisperProcessor

# Set default sampling rate for audio recording
sd.default.samplerate = 16000

# Threshold to detect if audio chunk contains sound
sound_level_threshold = 0.0002

# Buffers and states for audio data and silence detection
audio_data = np.array([])       # Stores accumulated active audio samples
audio_queue: np.array = np.array([])   # (Unused in current code)
inactive_count: float = 0.0     # Duration of detected silence in seconds
inactive_for_time: float = 2.0  # Time threshold to consider audio chunk ended (2 seconds)
is_chunk_active: bool = False   # Flag indicates if currently recording active audio segment

# Model and processor initialization for Whisper speech-to-text
MODEL_NAME = "alvanlii/whisper-small-cantonese"
print('Model loaded')
processor = WhisperProcessor.from_pretrained(MODEL_NAME)
print('Processor Created')
model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)
print('Model initiated')

# Thread synchronization lock to avoid race conditions on shared variables
lock = threading.Lock()

# Callback function invoked by sounddevice for each audio block recorded
def callback(indata, frames, time, status):
    # Process each recorded audio chunk
    split_chunk(indata=indata, frames=frames)
# Function to start the recording stream and keep it alive
def start_recording():
    with sd.InputStream(callback=callback, channels=1):
        while True:
            # Sleep briefly to prevent busy waiting
            time.sleep(1/sd.default.samplerate)

# Function to handle audio chunk splitting based on sound activity
def split_chunk(indata, frames):
    global inactive_count, audio_data, audio_queue, is_chunk_active

    # Calculate mean absolute amplitude of the current audio chunk
    if np.mean(np.abs(indata)) > sound_level_threshold: 
        # Detected sound above threshold, append to active audio buffer
        with lock:
            is_chunk_active = True
            inactive_count = 0  # reset silence timer
            audio_data = np.append(audio_data, indata[:, 0])
    elif is_chunk_active: 
        # Currently recording audio but current chunk is quiet; keep recording for now
        with lock:
            inactive_count += frames / sd.default.samplerate
            audio_data = np.append(audio_data, indata[:, 0])
    else:
        # Not currently recording, increment silence timer
        with lock:
            inactive_count += frames / sd.default.samplerate

    # If silence duration exceeded threshold and some audio was accumulated, process it
    if inactive_count > inactive_for_time and len(audio_data) > 1000:
        with lock:
            is_chunk_active = False
            process_stt(audio_data)  # send audio segment for transcription
            audio_data = np.array([])  # reset audio buffer

# Function to run speech-to-text on an audio segment using Whisper
def process_stt(indata):
    print(f"Audio segment shape: {indata.shape}, ndim={indata.ndim}")
    # Preprocess audio for Whisper model input
    processed_in = processor(indata, sampling_rate=sd.default.samplerate, return_tensors="pt")
    # Generate transcription output tokens
    gout = model.generate(
        input_features=processed_in.input_features, 
        output_scores=True, return_dict_in_generate=True
    )
    # Decode tokens into text transcription
    transcription = processor.batch_decode(gout.sequences, skip_special_tokens=True)[0]
    print("\n", transcription)

# Create and start a separate thread to handle continuous audio recording
recording_thread = threading.Thread(target=start_recording)
recording_thread.start()