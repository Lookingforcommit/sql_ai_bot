from langchain_gigachat import GigaChat
from langchain.schema import SystemMessage, HumanMessage, AIMessage
import os
from typing import Optional, List, Dict
from dotenv import load_dotenv


class AIManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        self.chat: Optional[GigaChat] = None
        self._initialize_chat()

    def _initialize_chat(self):
        load_dotenv()
        api_key = os.getenv("GIGACHAT_API_KEY")

        if not api_key:
            print("Warning: GIGACHAT_API_KEY not found in environment variables")
            self.chat = None
            return

        try:
            self.chat = GigaChat(
                credentials=api_key,
                verify_ssl_certs=False
            )
        except Exception as e:
            print(f"Error initializing GigaChat: {e}")
            self.chat = None

    def _convert_messages_to_langchain(self, messages: List[Dict[str, str]]) -> List:
        converted_messages = []
        for message in messages:
            if message["role"] == "system":
                converted_messages.append(SystemMessage(content=message["content"]))
            elif message["role"] == "user":
                converted_messages.append(HumanMessage(content=message["content"]))
            elif message["role"] == "assistant":
                converted_messages.append(AIMessage(content=message["content"]))
        return converted_messages

    async def get_sql_error_help(self, query: str, error_message: str) -> str:
        if not self.chat:
            return "Извините, сервис анализа ошибок временно недоступен."

        messages = [
            {
                "role": "system",
                "content": """Вы - эксперт SQL, который помогает исправлять ошибки в запросах. 
                Объясните причину ошибки простым языком и предложите исправление."""
            },
            {
                "role": "user",
                "content": f"""Помогите исправить SQL запрос.
                Запрос: {query}
                Ошибка: {error_message}
                """
            }
        ]

        try:
            langchain_messages = self._convert_messages_to_langchain(messages)
            response = self.chat.invoke(langchain_messages)
            return response.content
        except Exception as e:
            return f"Произошла ошибка при анализе запроса: {e}"

    async def continue_dialogue(self, message_history: List[Dict[str, str]]) -> str:
        if not self.chat:
            return "Извините, сервис временно недоступен."

        try:
            langchain_messages = self._convert_messages_to_langchain(message_history)
            response = self.chat.invoke(langchain_messages)
            return response.content
        except Exception as e:
            return f"Произошла ошибка при обработке вашего вопроса: {e}"