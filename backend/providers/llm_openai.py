import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIProvider:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-5.4-mini"
        self.system_prompt = (
            f"Você é um assistente de voz amigável, objetivo e conciso. "
            f"Seu nome é {os.getenv('ASSISTANT_NAME', 'MarIA')}. "
            f"Responda em português, de forma coloquial e natural."
        )

    async def generate_response(self, user_message: str, chat_history: list = None) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if chat_history:
            messages.extend(chat_history)
            
        messages.append({"role": "user", "content": user_message})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Erro no OpenAIProvider LLM: {e}")
            return "Desculpe, tive um problema ao processar sua solicitação."
