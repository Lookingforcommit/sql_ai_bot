from langchain.schema import HumanMessage, SystemMessage
from langchain_gigachat import GigaChat
import os
from typing import Optional
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
                model="GigaChat:latest",
                verify_ssl_certs=False
            )
        except Exception as e:
            print(f"Error initializing GigaChat: {e}")
            self.chat = None

    async def get_sql_error_help(self, query: str, error_message: str) -> str:
        if not self.chat:
            return "Извините, сервис анализа ошибок временно недоступен."

        messages = [
            SystemMessage(content="""Вы - эксперт SQL, который помогает исправлять ошибки в запросах. 
            Объясните причину ошибки простым языком и предложите исправление."""),
            HumanMessage(content=f"""Помогите исправить SQL запрос.
            Запрос: {query}
            Ошибка: {error_message}
            """)
        ]

        try:
            response = self.chat.invoke(messages)
            return response.content
        except Exception as e:
            return f"Произошла ошибка при анализе запроса: {e}"