import { useState, useEffect, useRef } from 'react'
import { AssistantFace } from './AssistantFace'
import './index.css'

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [assistantState, setAssistantState] = useState<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  const [transcript, setTranscript] = useState('');
  const [assistantMessage, setAssistantMessage] = useState('');
  
  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const silenceTimerRef = useRef<number | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  
  // Usamos ref para acessar o estado atualizado dentro dos loops assíncronos
  const assistantStateRef = useRef<'idle' | 'listening' | 'thinking' | 'speaking'>('idle');
  
  const updateAssistantState = (newState: 'idle' | 'listening' | 'thinking' | 'speaking') => {
      assistantStateRef.current = newState;
      setAssistantState(newState);
  };

  // Parâmetros do detector de silêncio
  const SILENCE_THRESHOLD = 5; 
  const SILENCE_DURATION_MS = 1500; 
  const isSpeakingRef = useRef(false);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) wsRef.current.close();
      stopRecording();
    };
  }, []);

  // Conecta ao servidor WebSocket através do proxy do Vite para evitar erro de Conteúdo Misto (Mixed Content)
  const connectWebSocket = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host; // Inclui IP e porta atual (ex: 192.168.0.117:5173)
    const wsUrl = `${protocol}//${host}/ws/audio`; 
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('Conectado ao servidor!');
      setIsConnected(true);
      startVoiceDetection(ws);
    };

    ws.onmessage = async (event) => {
      if (typeof event.data === 'string') {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'state') updateAssistantState(msg.value);
          if (msg.type === 'transcript') setTranscript(msg.value);
          if (msg.type === 'answer_text') setAssistantMessage(msg.value);
        } catch (e) {
          console.error("Erro ao fazer parse da mensagem:", e);
        }
      } 
      else if (event.data instanceof Blob) {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
            mediaRecorderRef.current.pause();
        }
        await playAudioBuffer(event.data);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      updateAssistantState('idle');
      stopRecording();
      setTimeout(connectWebSocket, 3000);
    };

    wsRef.current = ws;
  };

  const startVoiceDetection = async (ws: WebSocket) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyser = audioCtx.createAnalyser();
      const microphone = audioCtx.createMediaStreamSource(stream);
      
      analyser.minDecibels = -90;
      analyser.maxDecibels = -10;
      analyser.smoothingTimeConstant = 0.85;
      microphone.connect(analyser);

      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const fullAudioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        chunksRef.current = []; 
        
        if (fullAudioBlob.size > 2000 && ws.readyState === WebSocket.OPEN) {
          console.log("Enviando áudio de tamanho:", fullAudioBlob.size);
          ws.send(fullAudioBlob);
        }

        // Só reinicia a gravação se não estiver pensando nem falando
        if (ws.readyState === WebSocket.OPEN && 
            assistantStateRef.current !== 'speaking' && 
            assistantStateRef.current !== 'thinking') {
            mediaRecorder.start();
        }
      };

      mediaRecorder.start();

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const checkVolume = () => {
        analyser.getByteFrequencyData(dataArray);
        
        // Se a IA está processando ou falando, ignoramos o microfone para evitar self-trigger
        if (assistantStateRef.current === 'speaking' || assistantStateRef.current === 'thinking') {
             requestAnimationFrame(checkVolume);
             return;
        }

        let sum = 0;
        for(let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
        }
        const averageVolume = sum / bufferLength;

        if (averageVolume > SILENCE_THRESHOLD) {
            if (!isSpeakingRef.current) {
                console.log("Detectou fala...");
                isSpeakingRef.current = true;
                updateAssistantState('listening');
            }
            if (silenceTimerRef.current) {
                clearTimeout(silenceTimerRef.current);
                silenceTimerRef.current = null;
            }
        } else {
            if (isSpeakingRef.current && !silenceTimerRef.current) {
                console.log("Usuário parou de falar.");
                silenceTimerRef.current = window.setTimeout(() => {
                    console.log("Fechando pacote de áudio (silêncio atingido).");
                    isSpeakingRef.current = false;
                    
                    if (mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                    }
                    
                }, SILENCE_DURATION_MS);
            }
        }
        requestAnimationFrame(checkVolume);
      };

      checkVolume();

    } catch (err) {
      console.error("Erro ao acessar microfone:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
  };

  const playAudioBuffer = async (blob: Blob) => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    const audioCtx = audioContextRef.current;
    
    try {
      const arrayBuffer = await blob.arrayBuffer();
      const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
      const source = audioCtx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioCtx.destination);
      
      updateAssistantState('speaking');
      source.start();
      
      source.onended = () => {
        updateAssistantState('idle');
        
        // Limpa qualquer chunk acumulado durante a fala da IA antes de retomar
        chunksRef.current = [];
        
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'paused') {
            mediaRecorderRef.current.resume();
        } else if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'inactive') {
            mediaRecorderRef.current.start();
        }
      };
    } catch (error) {
      console.error("Erro ao tocar o áudio:", error);
    }
  };

  const handleStartInteraction = () => {
    if (audioContextRef.current?.state === 'suspended') {
      audioContextRef.current.resume();
    }
    if (!isConnected) connectWebSocket();
  };

  return (
    <div className="w-full h-screen bg-slate-900 flex flex-col items-center justify-center relative overflow-hidden">
      
      <div className={`absolute inset-0 opacity-20 transition-colors duration-700 
        ${assistantState === 'idle' ? 'bg-cyan-900' : 
          assistantState === 'listening' ? 'bg-green-900' : 
          assistantState === 'thinking' ? 'bg-yellow-900' : 'bg-cyan-600'}`}>
      </div>

      <div className="z-10 flex flex-col items-center w-full max-w-4xl px-8">
        
        <div className="absolute top-6 right-8 flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 shadow-[0_0_10px_#22c55e]' : 'bg-red-500 animate-pulse'}`}></div>
          <span className="text-slate-400 text-sm font-medium">
            {isConnected ? 'Online' : 'Conectando...'}
          </span>
        </div>

        <div className="my-16">
          <AssistantFace state={assistantState} />
        </div>

        <div className="mt-8 h-32 flex flex-col items-center justify-center w-full text-center">
          {transcript && assistantState !== 'speaking' && (
            <p className="text-slate-400 text-lg italic opacity-80 transition-opacity">
              "{transcript}"
            </p>
          )}
          
          {assistantMessage && assistantState === 'speaking' && (
            <p className="text-white text-2xl font-medium tracking-wide mt-2">
              {assistantMessage}
            </p>
          )}

          {!isConnected && (
            <button 
              onClick={handleStartInteraction}
              className="mt-6 px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-full font-semibold transition-all shadow-[0_0_15px_rgba(8,145,178,0.5)]"
            >
              Iniciar Conexão Manual
            </button>
          )}
        </div>

      </div>
    </div>
  )
}

export default App
