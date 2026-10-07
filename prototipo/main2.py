import streamlit as st
import speech_recognition as sr
from openai import OpenAI
from gtts import gTTS
import os
from playsound import playsound
import time
from dotenv import load_dotenv

# Carrega as variáveis de ambiente

load_dotenv()

# Configuração da chave da OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Função para escutar e transcrever
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

# Função para consultar o modelo da OpenAI
def responder_openai(pergunta, historico):
    historico.append({"role": "user", "content": pergunta})
    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=historico
    )
    mensagem = resposta.choices[0].message.content
    historico.append({"role": "assistant", "content": mensagem})
    return mensagem, historico

# Falar com gTTS
def falar(texto):
    tts = gTTS(text=texto, lang='pt')
    caminho = "resposta.mp3"
    tts.save(caminho)
    playsound(caminho)
    os.remove(caminho)

# Interface do Streamlit
st.set_page_config(page_title="Assistente de Voz", page_icon="🎙️")

# Interface Streamlit
st.title("🗣️ Assistente de Voz SESAPI")
st.markdown("Fale e escute respostas naturais.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": "Você é um assistente útil que responde em português, de forma simpática e clara."}
    ]

if st.button("🎤 Falar"):
    pergunta = ouvir_microfone()
    if pergunta:
        with st.spinner("Pensando..."):
            resposta, st.session_state.chat_history = responder_openai(pergunta, st.session_state.chat_history)
            st.markdown(f"**🤖 Resposta:** {resposta}")
            falar(resposta)
