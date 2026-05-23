"""
Speech-to-Text: converte voz em texto usando Whisper.
Roda 100% local, sem internet.
"""

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

class SpeechToText:
    def __init__(self, model_size="base"):
        if not WHISPER_AVAILABLE:
            print("⚠️  Whisper não instalado. STT indisponível.")
            self.model = None
            return
        # Modelos disponíveis: tiny, base, small, medium, large
        # tiny/base = mais leve, small/medium = mais preciso
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_path: str = None) -> str:
        """
        Se audio_path for None, grava do microfone.
        Se for um arquivo, transcreve o arquivo.
        """
        # TODO: implementar gravação do microfone
        if self.model is None:
            return ""
        if audio_path:
            result = self.model.transcribe(audio_path)
            return result["text"]
        return ""
