import os
from openai import OpenAI
import pyttsx3
import streamlit as st
import speech_recognition as sr
import tempfile
from gtts import gTTS
import pygame
import os
import threading
from dotenv import load_dotenv

# Carrega as variáveis de ambiente

load_dotenv()
# Inicializa a API da OpenAI (use sua chave da API)
#openai.api_key = os.getenv("OPENAI_API_KEY")  # Ou defina diretamente como string para testes

# Inicializa TTS
engine = pyttsx3.init()
engine.setProperty('rate', 170)

# OpenAI Client (substitua pela sua chave real)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



# 🎙️ Função para escutar via microfone
def ouvir_microfone():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Fale agora...")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
    try:
        texto = recognizer.recognize_google(audio, language="pt-BR")
        st.success(f"Você disse: {texto}")
        return texto
    except sr.UnknownValueError:
        st.warning("Não entendi o que você disse.")
    except sr.RequestError as e:
        st.error(f"Erro ao se conectar ao serviço de reconhecimento: {e}")
    return None

# 🤖 Função para gerar resposta com GPT-4o-mini
def responder_openai(pergunta, historico):
    historico.append({"role": "user", "content": pergunta})
    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=historico
    )
    mensagem = resposta.choices[0].message.content
    historico.append({"role": "assistant", "content": mensagem})
    return mensagem, historico

# 🔊 Falar resposta
def falar(texto):
    def run():
        engine.say(texto)
        engine.runAndWait()
    threading.Thread(target=run).start()


# 🌐 Interface Streamlit
st.title("🎤 Assistente de Voz")
st.markdown("Converse com a IA usando sua voz. Ela responde em voz alta.")

# Inicializa histórico de conversa
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": "Você é um assistente simpático que responde em português de forma clara e objetiva."}
    ]

# Botão para iniciar conversa
if st.button("🎙️ Falar"):
    pergunta = ouvir_microfone()
    if pergunta:
        with st.spinner("Pensando..."):
            resposta, st.session_state.chat_history = responder_openai(pergunta, st.session_state.chat_history)
            st.markdown(f"**🤖 Resposta:** {resposta}")
            falar(resposta)