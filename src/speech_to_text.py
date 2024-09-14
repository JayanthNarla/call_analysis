import os
import speech_recognition as sr
from pydub import AudioSegment

def get_audio_duration(file_path):
    """Get the duration of an audio file in seconds."""
    audio = AudioSegment.from_wav(file_path)
    duration_seconds = len(audio) / 1000
    return duration_seconds

def filter_long_audio_files(input_folder, max_duration_minutes=7):
    """Remove audio files longer than the specified duration."""
    max_duration_seconds = max_duration_minutes * 60
    filtered_files = []
    removed_files = []

    for filename in os.listdir(input_folder):
        if filename.endswith(".wav"):
            file_path = os.path.join(input_folder, filename)
            duration = get_audio_duration(file_path)
            
            if duration <= max_duration_seconds:
                filtered_files.append(filename)
            else:
                removed_files.append(filename)
                os.remove(file_path)
                print(f"Removed {filename} (duration: {duration/60:.2f} minutes)")

    print(f"Removed {len(removed_files)} files longer than {max_duration_minutes} minutes.")
    return filtered_files

class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def transcribe_audio(self, audio_file):
        """Transcribe audio in chunks to handle longer audio files."""
        audio = AudioSegment.from_wav(audio_file)
        chunk_length_ms = 30000  # 30 seconds per chunk
        chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

        full_transcript = ""
        for i, chunk in enumerate(chunks):
            chunk.export("temp_chunk.wav", format="wav")
            with sr.AudioFile("temp_chunk.wav") as source:
                audio_chunk = self.recognizer.record(source)
            try:
                text = self.recognizer.recognize_google(audio_chunk)
                full_transcript += text + " "
                print(f"Transcribed chunk {i + 1}/{len(chunks)}")
            except sr.UnknownValueError:
                print(f"Chunk {i + 1} could not be understood")
            except sr.RequestError as e:
                print(f"Request error from Speech Recognition service; {e}")
        
        return full_transcript.strip()

def process_folder(input_folder, output_folder, limit=None):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Filter out long audio files
    filtered_files = filter_long_audio_files(input_folder)

    if limit:
        filtered_files = filtered_files[:limit]
    total_files = len(filtered_files)

    transcriber = SpeechToText()

    for i, filename in enumerate(filtered_files, 1):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename[:-4] + ".txt")

        print(f"Transcribing file {i} of {total_files}: {filename}...")
        try:
            transcript = transcriber.transcribe_audio(input_path)
            with open(output_path, "w", encoding="utf-8") as text_file:
                text_file.write(transcript)
            print(f"Saved transcript to {output_path}")
        except Exception as e:
            print(f"Error transcribing {filename}: {str(e)}")

        print(f"Progress: {i}/{total_files} files transcribed")

def main():
    input_folder = "data/wav_output"  # Replace with your folder path
    output_folder = "data/wav_stt_output"  # Replace with your desired output folder path

    # Process only the first 10 files (you can adjust this number or remove the limit)
    process_folder(input_folder, output_folder, limit=10)

if __name__ == "__main__":
    main()