# Desenvolvimento do Assistente de Voz para Tablet (Modo Totem)

Este plano descreve a arquitetura e os passos necessários para transformar os scripts locais atuais em uma solução robusta cliente-servidor. A solução final permitirá que um tablet exiba um rosto interativo que escuta e fala em tempo real, semelhante ao exemplo do vídeo.

## ⚠️ User Review Required
A arquitetura muda o paradigma atual. O processamento pesado e chaves de API sairão do dispositivo e ficarão centralizados num servidor backend Python (FastAPI). O tablet servirá apenas como um terminal visual e de áudio (PWA). Por favor, revise a arquitetura abaixo e as perguntas abertas antes de prosseguirmos.

## ❓ Open Questions
1. **Frontend Stack:** Prefere que o Frontend web seja construído usando **Next.js** (mais robusto, padrão da indústria hoje) ou **Vite + React** puro (mais leve e simples de compilar)?
2. **Motor de Voz (TTS):** Para a primeira versão, vamos focar em **Edge TTS** (Vozes da Microsoft, gratuitas e naturais) ou **OpenAI TTS** (Vozes de altíssima qualidade, mas consome saldo da sua chave de API atual)?
3. **Identidade Visual:** O frontend deve ter um Avatar (rosto robótico com olhos e boca como no vídeo) ou formas dinâmicas abstratas (ondas sonoras que reagem à voz)?

---

## Proposed Changes

A arquitetura será dividida em dois projetos independentes no seu ambiente: o **Backend** (API Python) e o **Frontend** (Interface Web).

### 1. Backend (Python + FastAPI)
O "Cérebro". Ele receberá conexões de áudio contínuas, processará e devolverá as respostas faladas.

#### [NEW] Backend Architecture
- **Servidor WebSockets:** Construído com `FastAPI` para manter conexões bidirecionais contínuas (full-duplex) com o tablet, essencial para baixa latência.
- **Pipeline de Conversação:**
  1. **STT (Speech-to-Text):** Integração com `OpenAI Whisper API` (ou Faster-Whisper caso o computador servidor seja forte o suficiente) para transcrição rápida do áudio recebido.
  2. **LLM:** `OpenAI GPT-4o-mini` gerenciando o estado da conversa e histórico do usuário.
  3. **TTS (Text-to-Speech):** Módulo para gerar o áudio e enviá-lo de volta via WebSocket assim que o texto estiver pronto.

### 2. Frontend (Web App)
O "Rosto". Rodará no navegador do tablet (Chrome/Safari) em tela cheia (PWA Kiosk Mode).

#### [NEW] Frontend Architecture
- **Captura de Áudio (WebRTC):** Script JavaScript para capturar o microfone e transmitir pacotes de áudio (chunks) constantemente via WebSocket.
- **Reprodução de Áudio (Web Audio API):** Script para receber os pacotes de voz do backend e tocar sem interrupções.
- **UI Responsiva e Animada:**
  - Gerenciamento de Estados: "Idle" (Ouvindo o ambiente), "Thinking" (Processando), "Speaking" (Falando).
  - Animações fluidas atreladas ao nível do som captado (VAD).
  - Design system responsivo para tablets (Landscape).

---

## Verification Plan

### Automated Tests
- Teste de conexão WebSocket (Backend ping/pong).
- Validação do fluxo completo sem áudio (Envio de texto -> Backend -> Retorno de texto/áudio mockado).

### Manual Verification
- Acessar o webapp pelo navegador do próprio computador de desenvolvimento para testar o microfone e captura.
- Testar a responsividade da "boca" ou "olhos" da UI ao receber o áudio de volta.
- (Etapa final) Abrir o link local no Tablet via rede Wi-Fi, colocar em tela cheia e interagir diretamente.
