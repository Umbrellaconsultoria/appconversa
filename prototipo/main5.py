import streamlit as st
import whisper
import tempfile
import os
from pydub import AudioSegment
import threading
import time
import speech_recognition as sr
from io import BytesIO
from docx import Document
from fpdf import FPDF
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Inicializa o modelo Whisper localmente
model = whisper.load_model("base")  # Pode ser tiny, base, small, medium, large

# Função para transcrever arquivo de áudio/vídeo
def transcrever_audio(file_path):
    result = model.transcribe(file_path, verbose=True)
    return result["text"]

# Função para escutar microfone em tempo real e transcrever
class TranscricaoTempoReal:
    def __init__(self):
        self.ativo = False
        self.texto = ""

    def escutar(self):
        self.ativo = True
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            st.info("Escutando...")
            while self.ativo:
                try:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                    frase = recognizer.recognize_google(audio, language="pt-BR")
                    self.texto += frase + "\n"
                    st.success(f"Você disse: {frase}")
                except Exception as e:
                    st.warning(f"Erro: {e}")

    def parar(self):
        self.ativo = False

# Função para salvar arquivos

def salvar_txt(texto):
    return BytesIO(texto.encode("utf-8"))

def salvar_docx(texto):
    buffer = BytesIO()
    doc = Document()
    doc.add_paragraph(texto)
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def salvar_pdf(texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for linha in texto.splitlines():
        # Converte para latin-1 ignorando caracteres incompatíveis
        linha = linha.encode("latin-1", "ignore").decode("latin-1")
        pdf.multi_cell(0, 10, linha)

    # Exporta como string (dest='S') e converte para BytesIO
    pdf_string = pdf.output(dest='S').encode('latin1')
    buffer = BytesIO(pdf_string)
    return buffer

def salvar_md(texto):
    return BytesIO(texto.encode("utf-8"))

# Interface do Streamlit
st.set_page_config(page_title="Transcrição de Aúdios", layout="centered")
st.title("🎧 Transcrição de aúdios...")
st.markdown("Upload de áudio/vídeo ou fala ao vivo para transcrição")

modo = st.radio("Escolha o modo de entrada:", ["Arquivo áudio/vídeo", "Escuta em tempo real"])
texto_transcrito = ""

if modo == "Arquivo áudio/vídeo":
    uploaded_file = st.file_uploader("Envie o arquivo de áudio ou vídeo", type=["mp3", "wav", "mp4", "m4a"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name[-4:]) as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        with st.spinner("Transcrevendo..."):
            texto_transcrito = transcrever_audio(temp_file_path)
            st.text_area("Transcrição", texto_transcrito, height=300)
        os.remove(temp_file_path)

elif modo == "Escuta em tempo real":
    if "transcricao" not in st.session_state:
        st.session_state.transcricao = TranscricaoTempoReal()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶ Iniciar Escuta"):
            thread = threading.Thread(target=st.session_state.transcricao.escutar)
            thread.start()

    with col2:
        if st.button("⏹ Parar Escuta"):
            st.session_state.transcricao.parar()
            texto_transcrito = st.session_state.transcricao.texto
            st.text_area("Transcrição Final", texto_transcrito, height=300)

# Opção de download
if texto_transcrito:
    st.markdown("### Baixar Transcrição")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.download_button("Salvar TXT", salvar_txt(texto_transcrito), file_name="transcricao.txt")
    with col2:
        st.download_button("Salvar DOCX", salvar_docx(texto_transcrito), file_name="transcricao.docx")
    with col3:
        st.download_button("Salvar PDF", salvar_pdf(texto_transcrito), file_name="transcricao.pdf")
    with col4:
        st.download_button("Salvar MD", salvar_md(texto_transcrito), file_name="transcricao.md")
