import os
import re
import wave
import subprocess
import threading
import queue
import time
from dotenv import load_dotenv
load_dotenv()

OUTPUT_DIR = "/tmp/diovan_tts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SYSTEM_PHRASES = {
    "processing": "Processando...",
    "searching" : "Buscando informações...",
    "executing" : "Executando...",
    "done"      : "Concluído.",
    "error"     : "Ocorreu um erro.",
}

class TTSAdapter:
    def __init__(self):
        self.voice_path = os.getenv("DIOVAN_VOICE", "./piper/voices/pt_BR-cadu-medium.onnx")
        self.voice      = None
        self.ready      = False
        self._queue     = queue.Queue()
        self._counter   = 0
        self._worker    = threading.Thread(target=self._process_queue, daemon=True)
        self._worker.start()
        # Lazy load in background
        threading.Thread(target=self._load, daemon=True).start()

    def _clean_text(self, text: str) -> str:
        """Remove emojis e caracteres especiais antes de sintetizar"""
        # Remove emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F9FF"
            "\U00002600-\U000027BF"
            "\U0000FE00-\U0000FE0F"
            "]+", flags=re.UNICODE
        )
        text = emoji_pattern.sub("", text)
        # Remove marcadores como *, #, -
        text = re.sub(r"[*#─▸◈⟳✅❌⚠️📂🔍]", "", text)
        # Limpa espaços duplos
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _load(self):
        try:
            from piper.voice import PiperVoice
            self.voice = PiperVoice.load(self.voice_path)
            self.ready = True
        except Exception as e:
            print(f"\n⚠️  TTS não disponível: {e}")

    def speak(self, text: str, blocking: bool = False):
        if not text.strip():
            return
        self._queue.put(("speak", text))

    def speak_system(self, key: str):
        phrase = SYSTEM_PHRASES.get(key)
        if phrase:
            self.speak(phrase)

    def clear_queue(self):
        """Limpa fila quando novo input chega"""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def _process_queue(self):
        while True:
            try:
                _, text = self._queue.get(timeout=1)
                if self.ready:
                    self._generate_and_play(text)
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"\n⚠️  TTS queue error: {e}")

    def _generate_and_play(self, text: str):
        text = self._clean_text(text)
        if not text:
            return

        try:
            self._counter += 1
            output = f"{OUTPUT_DIR}/chunk_{self._counter}.wav"

            import wave
            with wave.open(output, "wb") as wav_file:
                self.voice.synthesize_wav(text, wav_file)

            playback_timeout = int(os.getenv("TTS_PLAYBACK_TIMEOUT", "120"))
            subprocess.run(
                ["aplay", "-q", output],
                check=False,
                timeout=playback_timeout
            )
        except Exception as e:
            print(f"\n⚠️  TTS error: {e}")
