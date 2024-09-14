# import pyaudio
# import wave
# import numpy as np
# from scipy.io import wavfile
# from scipy import signal

# class AudioProcessor:
#     def __init__(self, rate=16000, chunk=1024, channels=1):
#         self.rate = rate
#         self.chunk = chunk
#         self.channels = channels
#         self.p = pyaudio.PyAudio()
#         self.stream = None

#     def start_stream(self):
#         self.stream = self.p.open(format=pyaudio.paInt16,
#                                   channels=self.channels,
#                                   rate=self.rate,
#                                   input=True,
#                                   frames_per_buffer=self.chunk)

#     def stop_stream(self):
#         if self.stream:
#             self.stream.stop_stream()
#             self.stream.close()

#     def capture_audio(self, duration):
#         """Capture audio for a specified duration."""
#         if not self.stream:
#             self.start_stream()

#         frames = []
#         for _ in range(0, int(self.rate / self.chunk * duration)):
#             data = self.stream.read(self.chunk)
#             frames.append(np.frombuffer(data, dtype=np.int16))

#         return np.concatenate(frames)

#     def preprocess_audio(self, audio):
#         """Apply noise reduction and normalization."""
#         # Convert to float
#         audio = audio.astype(np.float32)

#         # Noise reduction (simple high-pass filter)
#         b, a = signal.butter(5, 300/(self.rate/2), btype='highpass')
#         audio = signal.lfilter(b, a, audio)

#         # Normalization
#         audio = audio / np.max(np.abs(audio))

#         return audio

#     def save_audio(self, audio, filename):
#         """Save the audio to a WAV file."""
#         wavfile.write(filename, self.rate, (audio * 32767).astype(np.int16))

# def main():
#     # Test the AudioProcessor
#     processor = AudioProcessor()
#     print("Recording for 5 seconds...")
#     audio = processor.capture_audio(5)
#     print("Processing audio...")
#     processed_audio = processor.preprocess_audio(audio)
#     print("Saving audio...")
#     processor.save_audio(processed_audio, "test_audio.wav")
#     print("Audio saved to test_audio.wav")
#     processor.stop_stream()

# if __name__ == "__main__":
#     main()


import numpy as np
from scipy import signal
import os
from pydub import AudioSegment
import tempfile

class AudioProcessor:
    def __init__(self, rate=16000):
        self.rate = rate

    def load_audio(self, file_path):
        """Load an audio file (MP3 or WAV)."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        
        # Load audio file
        audio = AudioSegment.from_file(file_path)
        
        # Convert to mono if stereo
        if audio.channels > 1:
            audio = audio.set_channels(1)
        
        # Resample if necessary
        if audio.frame_rate != self.rate:
            audio = audio.set_frame_rate(self.rate)
        
        # Convert to numpy array
        samples = np.array(audio.get_array_of_samples()).astype(np.float32)
        
        # Normalize
        samples = samples / (2**15)  # Assuming 16-bit audio
        
        return samples

    def preprocess_audio(self, audio):
        """Apply noise reduction and normalization."""
        # Noise reduction (simple high-pass filter)
        b, a = signal.butter(5, 300/(self.rate/2), btype='highpass')
        audio = signal.lfilter(b, a, audio)

        # Normalization
        audio = audio / np.max(np.abs(audio))

        return audio

    def save_audio(self, audio, filename):
        """Save the audio to a WAV file."""
        audio = (audio * 32767).astype(np.int16)
        audio_segment = AudioSegment(
            audio.tobytes(), 
            frame_rate=self.rate,
            sample_width=audio.dtype.itemsize, 
            channels=1
        )
        audio_segment.export(filename, format="wav")

def process_audio_file(input_file, output_file):
    processor = AudioProcessor()
    
    print(f"Loading audio from {input_file}...")
    audio = processor.load_audio(input_file)
    
    print("Processing audio...")
    processed_audio = processor.preprocess_audio(audio)
    
    print(f"Saving processed audio to {output_file}...")
    processor.save_audio(processed_audio, output_file)
    
    print("Audio processing complete.")

def process_folder(input_folder, output_folder, limit=None):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    processor = AudioProcessor()
    
    mp3_files = [f for f in os.listdir(input_folder) if f.endswith(".mp3")]
    
    if limit is not None:
        mp3_files = mp3_files[:limit]
    
    total_files = len(mp3_files)
    
    for i, filename in enumerate(mp3_files, 1):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename[:-4] + ".wav")
        
        print(f"Processing file {i} of {total_files}: {filename}...")
        try:
            audio = processor.load_audio(input_path)
            processed_audio = processor.preprocess_audio(audio)
            processor.save_audio(processed_audio, output_path)
            print(f"Saved processed audio to {output_path}")
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
        
        print(f"Progress: {i}/{total_files} files processed")

def main():
    input_folder = "data/911_recordings"  # Replace with your folder path
    output_folder = "data/wav_output"  # Replace with your desired output folder path
    
    process_folder(input_folder, output_folder)

if __name__ == "__main__":
    main()