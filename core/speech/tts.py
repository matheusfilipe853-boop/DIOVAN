"""
Text-to-Speech: converte texto em voz.
Troca fácil entre Piper (local) e outras engines.
"""

class TextToSpeech:
    def __init__(self, engine="piper"):
        self.engine = engine

    def speak(self, text: str):
        """Reproduz o texto como áudio"""
        # TODO: implementar com Piper ou similar
        print(f"[TTS] {text}")  # Placeholder por enquanto
