"""
DIOVAN — TTS Adapter (Qwen3-TTS)
Síntese de voz com clonagem baseada no arquivo de referência.
Roda 100% local, sem internet.
"""

import os
import sys
import torch
import soundfile as sf
import subprocess
from interface.base_interface import BaseInterface

# Adiciona o repositório Qwen3-TTS ao path
QWEN_TTS_PATH = "/tmp/Qwen3-TTS"
if QWEN_TTS_PATH not in sys.path:
    sys.path.insert(0, QWEN_TTS_PATH)

# Configurações
VOICE_REF_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../../assets/voice/VOZDIOVAN.mp3"
)

# Prompt de estilo da voz do DIOVAN
# Ajuste conforme o resultado dos testes
VOICE_STYLE_PROMPT = """
Fale de forma assertiva, clara e com autoridade.
Ritmo moderado, voz grave e confiante.
Tom neutro e profissional, sem emoção excessiva.
"""

OUTPUT_AUDIO_PATH = "/tmp/diovan_response.wav"


class TTSAdapter:
    """
    Adapter de síntese de voz usando Qwen3-TTS com clonagem.
    Pode ser usado standalone ou integrado ao TerminalAdapter.
    """

    def __init__(self):
        self.model      = None
        self.processor  = None
        self.ready      = False
        self._load_model()

    def _load_model(self):
        """Carrega o modelo Qwen3-TTS localmente"""
        try:
            from transformers import AutoProcessor, AutoModel

            print("⟳ Carregando modelo Qwen3-TTS...")

            model_id = "Qwen/Qwen3-TTS-0.6B-Base"  # Modelo mais leve

            self.processor = AutoProcessor.from_pretrained(
                model_id,
                trust_remote_code=True
            )
            self.model = AutoModel.from_pretrained(
                model_id,
                torch_dtype=torch.float32,  # CPU — usa float32
                trust_remote_code=True
            )
            self.model.eval()
            self.ready = True
            print("✅ Qwen3-TTS carregado com sucesso")

        except Exception as e:
            print(f"⚠️  Qwen3-TTS não disponível: {e}")
            print("   DIOVAN vai responder só por texto por enquanto.")
            self.ready = False

    def speak(self, text: str) -> bool:
        """
        Sintetiza o texto com a voz clonada do DIOVAN e reproduz.
        Retorna True se funcionou, False se falhou.
        """
        if not self.ready:
            return False

        try:
            # Lê o áudio de referência
            ref_audio, ref_sr = self._load_reference()

            # Gera o áudio com clonagem de voz
            inputs = self.processor(
                text=text,
                ref_audio=ref_audio,
                ref_audio_sr=ref_sr,
                voice_description=VOICE_STYLE_PROMPT,
                return_tensors="pt"
            )

            with torch.no_grad():
                outputs = self.model.generate(**inputs)

            # Salva o áudio gerado
            audio_data = outputs[0].cpu().numpy()
            sf.write(OUTPUT_AUDIO_PATH, audio_data, samplerate=24000)

            # Reproduz o áudio
            self._play_audio(OUTPUT_AUDIO_PATH)
            return True

        except Exception as e:
            print(f"⚠️  Erro na síntese de voz: {e}")
            return False

    def _load_reference(self):
        """Carrega o arquivo de referência de voz"""
        import torchaudio

        if not os.path.exists(VOICE_REF_PATH):
            raise FileNotFoundError(f"Arquivo de voz não encontrado: {VOICE_REF_PATH}")

        waveform, sample_rate = torchaudio.load(VOICE_REF_PATH)

        # Converte para mono se necessário
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        return waveform, sample_rate

    def _play_audio(self, path: str):
        """Reproduz áudio no Linux"""
        players = ["aplay", "paplay", "ffplay -nodisp -autoexit"]

        for player in players:
            try:
                cmd = player.split() + [path]
                subprocess.run(cmd, check=True,
                             capture_output=True, timeout=60)
                return
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue

        print(f"⚠️  Nenhum player de áudio encontrado. Áudio salvo em: {path}")
