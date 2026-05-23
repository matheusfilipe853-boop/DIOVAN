from core.orchestrator import Orchestrator
from interface.interface_factory import InterfaceFactory
from interface.adapters.tts import TTSAdapter

def run():
    orchestrator = Orchestrator()
    interface    = InterfaceFactory.get_interface()
    tts          = TTSAdapter()

    def on_input(user_input: str):
        interface.render_status("Processando...")

        print(f"\n\n🤖 DIOVAN: ", end="", flush=True)

        sentence_buffer = ""

        def on_token(token: str):
            nonlocal sentence_buffer
            print(token, end="", flush=True)
            sentence_buffer += token

            # Fala em chunks quando encontra pontuação final
            if any(sentence_buffer.strip().endswith(p) for p in [".", "!", "?"]):
                if len(sentence_buffer.strip()) > 10:
                    tts.speak(sentence_buffer.strip(), blocking=False)
                    sentence_buffer = ""

        response = orchestrator.chat(user_input, on_token=on_token)

        # Fala o que sobrou no buffer
        if sentence_buffer.strip():
            tts.speak(sentence_buffer.strip(), blocking=False)

        print("\n")
        print("─" * 60)

    def on_exit():
        pass

    interface.start(on_input, on_exit)

if __name__ == "__main__":
    run()
