import speech_recognition as sr
import pyttsx3
import sounddevice as sd
import numpy as np
import threading
import queue
import time
from typing import Optional, Callable

class VoiceInterface:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.engine = pyttsx3.init()
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.callback: Optional[Callable[[str], None]] = None

    def speak(self, text: str):
        """Convert text to speech."""
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self, callback: Callable[[str], None]):
        """Start listening for voice input."""
        self.callback = callback
        self.is_listening = True
        threading.Thread(target=self._listen_thread, daemon=True).start()

    def stop_listening(self):
        """Stop listening for voice input."""
        self.is_listening = False

    def _listen_thread(self):
        """Background thread for continuous listening."""
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            while self.is_listening:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio)
                    if self.callback:
                        self.callback(text)
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    print(f"Error in voice recognition: {e}")
                    continue

    def process_audio(self, audio_data: np.ndarray, sample_rate: int):
        """Process audio data from stream."""
        try:
            audio = sr.AudioData(audio_data.tobytes(), sample_rate, 2)
            text = self.recognizer.recognize_google(audio)
            if self.callback:
                self.callback(text)
        except Exception as e:
            print(f"Error processing audio: {e}")

def create_voice_interface() -> VoiceInterface:
    """Create and initialize a voice interface."""
    return VoiceInterface() 