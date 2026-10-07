import os
import tempfile
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAI_STTProvider:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "whisper-1"

    async def transcribe_audio(self, audio_bytes: bytes) -> str:
        if not audio_bytes or len(audio_bytes) < 1000: # Ignora ruídos muito curtos
            return ""
            
        # Cria um arquivo temporário físico no disco para garantir compatibilidade de decodificação
        temp_filename = ""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
                temp_audio.write(audio_bytes)
                temp_filename = temp_audio.name

            # O SDK prefere ler de um objeto 'open' de arquivo físico
            with open(temp_filename, "rb") as file_to_upload:
                response = await self.client.audio.transcriptions.create(
                    model=self.model,
                    file=file_to_upload,
                    language="pt", 
                    response_format="text"
                )
            
            return response.strip()
            
        except Exception as e:
            print(f"Erro no OpenAI_STTProvider: {e}")
            return ""
        finally:
            # Sempre tenta limpar o arquivo temporário
            if temp_filename and os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except Exception as cleanup_error:
                    print(f"Erro ao deletar temp file: {cleanup_error}")
