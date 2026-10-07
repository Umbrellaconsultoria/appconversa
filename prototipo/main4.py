import streamlit as st
import speech_recognition as sr
from openai import OpenAI
from gtts import gTTS
import os
import time
import threading
from playsound import playsound
from dotenv import load_dotenv

# Carrega as variáveis de ambiente

load_dotenv()

# Configuração da chave da OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Inicializa sessão
if "escutando" not in st.session_state:
    st.session_state.escutando = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": "Você é um assistente útil que responde em português, de forma resumida, simpática, clara e objetiva."}
    ]
if "ultima_pergunta" not in st.session_state:
    st.session_state.ultima_pergunta = ""

# Inicializa cliente OpenAI
#client = OpenAI(api_key="SUA_CHAVE_OPENAI")

# Fala
def falar(texto):
    tts = gTTS(text=texto, lang='pt',)
    filename = "resposta.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

# Consulta IA
def responder_openai(pergunta, historico):
    historico.append({"role": "user", "content": pergunta})
    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=historico
    )
    mensagem = resposta.choices[0].message.content
    historico.append({"role": "assistant", "content": mensagem})
    return mensagem

# Função de escuta contínua sem acessar session_state diretamente
def ouvir_loop(ultima_pergunta_local, historico_local):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        while True:
            try:
                print("🎙️ Ouvindo...")
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=6)
                texto = recognizer.recognize_google(audio, language="pt-BR")

                if texto and texto != ultima_pergunta_local:
                    ultima_pergunta_local = texto
                    historico_local.append({"role": "user", "content": texto})
                    resposta = responder_openai(texto, historico_local)
                    historico_local.append({"role": "assistant", "content": resposta})
                    print(f"🤖 {resposta}")
                    falar(resposta)

                    # Atualiza o histórico na sessão para exibir
                    st.session_state.chat_history = historico_local
                    st.session_state.ultima_pergunta = ultima_pergunta_local

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                print("Não entendi. Pode repetir?")
            except Exception as e:
                print(f"Erro: {e}")
            time.sleep(1)

# Interface do Streamlit
st.set_page_config(page_title="Assistente de Voz", page_icon="🎙️")
#
# Título
st.title("🎙️ Assistente Sempre Ativo")
st.markdown("Fale naturalmente. O assistente responde em voz.")

# Botões
col1, col2 = st.columns(2)
if col1.button("🔊 Iniciar Escuta"):
    if not st.session_state.escutando:
        st.session_state.escutando = True
        threading.Thread(
            target=ouvir_loop,
            args=(st.session_state.ultima_pergunta, st.session_state.chat_history.copy()),
            daemon=True
        ).start()

if col2.button("🛑 Parar Escuta"):
    st.session_state.escutando = False
    st.warning("Escuta interrompida manualmente.")

# Mostra histórico
st.markdown("### 💬 Histórico da Conversa")
for msg in st.session_state.chat_history[1:]:
    if msg["role"] == "user":
        st.markdown(f"**🙋 Você:** {msg['content']}")
    elif msg["role"] == "assistant":
        st.markdown(f"**🤖 Assistente:** {msg['content']}")
