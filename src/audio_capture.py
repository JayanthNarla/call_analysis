import azure.cognitiveservices.speech as speechsdk
import pyaudio
import wave
import numpy as np
from pydub import AudioSegment
import threading
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Replace with your Azure Speech Service subscription key and region
SPEECH_KEY = os.getenv('SPEECH_KEY')
SPEECH_REGION = os.getenv("SPEECH_REGION")

# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000


# Folder to save recordings
RECORDINGS_FOLDER = "data/wav_recordings"

def get_next_filename(base_name, extension):
    if not os.path.exists(RECORDINGS_FOLDER):
        os.makedirs(RECORDINGS_FOLDER)
    
    index = 1
    while True:
        file_name = os.path.join(RECORDINGS_FOLDER, f"{base_name}_{index}.{extension}")
        if not os.path.exists(file_name):
            return file_name
        index += 1

def azure_live_transcribe(stop_event, transcript_file):
    try:
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        speech_config.speech_recognition_language="en-US"
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

        print("Speak into your microphone.")

        def recognizing_cb(evt):
            print(f'RECOGNIZING: {evt.result.text}', end='\r')

        def recognized_cb(evt):
            recognized_text = f'{evt.result.text}'
            print(recognized_text)
            with open(transcript_file, 'a') as f:
                f.write(recognized_text + '\n')

        speech_recognizer.recognizing.connect(recognizing_cb)
        speech_recognizer.recognized.connect(recognized_cb)

        speech_recognizer.start_continuous_recognition()

        while not stop_event.is_set():
            time.sleep(0.1)

        speech_recognizer.stop_continuous_recognition()

    except Exception as e:
        print(f"An error occurred in speech recognition: {str(e)}")

def record_audio(filename, stop_event):
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording...")

    frames = []

    try:
        while not stop_event.is_set():
            data = stream.read(CHUNK)
            frames.append(data)
    except Exception as e:
        print(f"An error occurred while recording: {str(e)}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    print("\nFinished recording.")

    temp_wav = "temp.wav"
    wf = wave.open(temp_wav, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    AudioSegment.from_wav(temp_wav).export(filename, format='mp3')
    os.remove(temp_wav)
    print(f"Audio saved as {filename}")
def wait_for_enter(stop_event):
    input("Press Enter to stop recording...\n")
    stop_event.set()

def main():
    stop_event = threading.Event()

    audio_file = get_next_filename("recording", "mp3")
    transcript_file = get_next_filename("transcript", "txt")

    transcribe_thread = threading.Thread(target=azure_live_transcribe, args=(stop_event, transcript_file))
    record_thread = threading.Thread(target=record_audio, args=(audio_file, stop_event))
    enter_thread = threading.Thread(target=wait_for_enter, args=(stop_event,))

    transcribe_thread.start()
    record_thread.start()
    enter_thread.start()

    transcribe_thread.join()
    record_thread.join()
    enter_thread.join()

    print(f"Transcript saved as {transcript_file}")

if __name__ == "__main__":
    main()