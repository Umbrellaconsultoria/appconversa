import os
import json
import re
import unicodedata
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv

# Importando os providers
from providers.llm_openai import OpenAIProvider
from providers.tts_edge import EdgeTTSProvider
from providers.stt_openai import OpenAI_STTProvider

load_dotenv()

app = FastAPI(title="Assistente de Voz API")

# Função utilitária para remover acentos (ex: Valéria -> Valeria)
def remove_accents(input_str):
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

# Configurações do Assistente
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "MarIA").strip()
WAKEWORD_NORMALIZED = remove_accents(ASSISTANT_NAME)

# Regex estrito: O nome (ou comando) DEVE estar no início da frase.
# Ele ignora espaços em branco e permite prefixos de atenção opcionais como "Ok", "Oi", "Olá", "Ei".
# Isso evita acionamento com frases aleatórias no meio de conversas (ex: "Isso valeria a pena?").
WAKEWORD_REGEX = re.compile(rf'^\s*(?:ok\s+|oi\s+|ola\s+|ei\s+)?{WAKEWORD_NORMALIZED}\b', re.IGNORECASE)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge-tts")
STT_PROVIDER = os.getenv("STT_PROVIDER", "openai")

# Instanciando (No futuro, pode-se usar um padrão Factory baseado no .env)
llm = OpenAIProvider()
tts = EdgeTTSProvider()
stt = OpenAI_STTProvider()

@app.get("/")
async def root():
    return {
        "status": "online",
        "assistant_name": ASSISTANT_NAME,
        "providers": {
            "llm": LLM_PROVIDER,
            "tts": TTS_PROVIDER,
            "stt": STT_PROVIDER
        }
    }

@app.websocket("/ws/audio")
async def websocket_audio(websocket: WebSocket):
    await websocket.accept()
    print(f"Cliente conectado. Wakeword ativa: '{ASSISTANT_NAME}'")
    
    # Histórico temporário da sessão do websocket
    chat_history = []
    
    try:
        while True:
            # 1. Recebe chunks de áudio do frontend (bytes)
            # O frontend deve enviar um chunk fechado de voz (ex: áudio gravado quando o VAD detecta que o usuário terminou de falar)
            data = await websocket.receive_bytes()
            print(f"Recebido áudio de {len(data)} bytes. Transcrevendo...")
            
            # Envia o estado "thinking" para a UI animar o rosto
            await websocket.send_text(json.dumps({"type": "state", "value": "thinking"}))
            
            # 2. STT: Transcreve o áudio para texto
            transcription = await stt.transcribe_audio(data)
            
            if not transcription:
                await websocket.send_text(json.dumps({"type": "state", "value": "idle"}))
                continue
                
            print(f"Transcrição: {transcription}")
            await websocket.send_text(json.dumps({"type": "transcript", "value": transcription}))
            
            # 3. Verifica a Wakeword
            transcription_normalized = remove_accents(transcription)
            if not WAKEWORD_REGEX.search(transcription_normalized):
                print("Wakeword não detectada. Ignorando.")
                await websocket.send_text(json.dumps({"type": "state", "value": "idle"}))
                continue
            
            print("Wakeword detectada! Processando resposta...")
            
            # 4. LLM: Gera a resposta
            # Opcional: Remover a wakeword da transcrição antes de mandar pro GPT para ficar mais limpo
            cleaned_prompt = WAKEWORD_REGEX.sub('', transcription).strip()
            if not cleaned_prompt:
                cleaned_prompt = "Oi!" # Se o usuário disser apenas o nome do robô
                
            resposta_texto = await llm.generate_response(cleaned_prompt, chat_history)
            print(f"[{ASSISTANT_NAME}]: {resposta_texto}")
            
            # Atualiza histórico
            chat_history.append({"role": "user", "content": cleaned_prompt})
            chat_history.append({"role": "assistant", "content": resposta_texto})
            
            # Avisa a UI sobre o texto que será falado (com a formatação original)
            await websocket.send_text(json.dumps({"type": "answer_text", "value": resposta_texto}))
            await websocket.send_text(json.dumps({"type": "state", "value": "speaking"}))
            
            # Limpa caracteres de formatação Markdown antes de gerar o áudio para evitar que o robô fale "asterisco"
            clean_tts_text = re.sub(r'[*_#`~]', '', resposta_texto)
            
            # 5. TTS: Gera o áudio com o texto limpo
            audio_bytes = await tts.generate_audio(clean_tts_text)
            
            # 6. Envia o áudio binário de volta para o frontend reproduzir
            if audio_bytes:
                await websocket.send_bytes(audio_bytes)
            
            # Volta para o estado inicial
            await websocket.send_text(json.dumps({"type": "state", "value": "idle"}))
            
    except WebSocketDisconnect:
        print("Cliente desconectado.")
    except Exception as e:
        print(f"Erro no websocket: {e}")
