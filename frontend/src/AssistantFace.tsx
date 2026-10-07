import React, { useEffect, useState } from 'react';

// Tipos de estados do robô
type AssistantState = 'idle' | 'listening' | 'thinking' | 'speaking';

interface AssistantFaceProps {
  state: AssistantState;
}

export function AssistantFace({ state }: AssistantFaceProps) {
  const [eyeColor, setEyeColor] = useState('bg-cyan-400');
  const [mouthShape, setMouthShape] = useState('h-3 w-16 rounded-full');

  useEffect(() => {
    switch (state) {
      case 'idle':
        setEyeColor('bg-cyan-400');
        setMouthShape('h-3 w-16 rounded-full');
        break;
      case 'listening':
        setEyeColor('bg-green-400');
        setMouthShape('h-6 w-12 rounded-full');
        break;
      case 'thinking':
        setEyeColor('bg-yellow-400');
        setMouthShape('h-4 w-8 rounded-full');
        break;
      case 'speaking':
        setEyeColor('bg-cyan-300');
        // A animação de fala será controlada pelo CSS
        setMouthShape('w-16 bg-white animate-talk');
        break;
    }
  }, [state]);

  return (
    <div className="flex flex-col items-center justify-center space-y-12 transition-all duration-500">
      
      {/* Olhos */}
      <div className="flex space-x-24">
        {/* Olho Esquerdo */}
        <div className={`w-24 h-32 rounded-[3rem] ${eyeColor} shadow-[0_0_30px_rgba(34,211,238,0.5)] flex items-center justify-center animate-blink transition-colors duration-500`}>
          {/* Reflexo (Brilho no olho) */}
          <div className="w-6 h-6 bg-white rounded-full opacity-60 absolute -mt-12 ml-6"></div>
        </div>
        
        {/* Olho Direito */}
        <div className={`w-24 h-32 rounded-[3rem] ${eyeColor} shadow-[0_0_30px_rgba(34,211,238,0.5)] flex items-center justify-center animate-blink transition-colors duration-500`}>
          {/* Reflexo (Brilho no olho) */}
          <div className="w-6 h-6 bg-white rounded-full opacity-60 absolute -mt-12 ml-6"></div>
        </div>
      </div>

      {/* Boca */}
      <div className={`bg-white transition-all duration-300 ${mouthShape} shadow-[0_0_15px_rgba(255,255,255,0.4)]`}></div>

    </div>
  );
}
