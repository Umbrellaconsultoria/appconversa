import os
import edge_tts
from io import BytesIO

class EdgeTTSProvider:
    def __init__(self):
        # pt-BR-AntonioNeural (Male) or pt-BR-FranciscaNeural (Female)
        self.voice = "pt-BR-FranciscaNeural"

    async def generate_audio(self, text: str) -> bytes:
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            return audio_data
        except Exception as e:
            print(f"Erro no EdgeTTSProvider: {e}")
            return b""
