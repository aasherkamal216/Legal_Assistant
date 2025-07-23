from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from config.settings import settings
from config.database import FAQDatabase

from .prompts import FAQ_PROMPT

class FAQ(BaseModel):
    question: str = Field(description="The FAQ question")
    answer: str = Field(description="The FAQ answer")
    category: str = Field(description="Legal category (e.g., Contract Law, Family Law, etc.)")

class FAQList(BaseModel):
    faqs: List[FAQ] = Field(description="List of generated FAQs")

class FAQGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.PRIMARY_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.3
        ).with_structured_output(FAQList)
        self.db = FAQDatabase(settings.DATABASE_PATH)

    def generate_and_store_faqs(self, conversation_history: List[Dict[str, str]]):
        """Generates FAQs from conversation and stores them directly in the database."""
        if not conversation_history or len(conversation_history) < 2:
            return

        formatted_conversation = self._format_conversation(conversation_history)
        
        try:
            result = self.llm.invoke([
                SystemMessage(content=FAQ_PROMPT),
                HumanMessage(content=f"<Conversation>\n{formatted_conversation}\n</Conversation>")
            ])
            
            if result and result.faqs:
                faq_dicts = [{"question": f.question, "answer": f.answer, "category": f.category} for f in result.faqs]
                self.db.insert_faqs(faq_dicts)
                print(f"Successfully generated and stored {len(faq_dicts)} FAQs.")
        except Exception as e:
            print(f"Error generating or storing FAQs: {e}")

    def _format_conversation(self, conversation: List[Dict[str, str]]) -> str:
        formatted = []
        for msg in conversation:
            role = "User" if msg.get("role") == "user" else "Assistant"
            formatted.append(f"{role}: {msg.get('content', '')}")
        return "\n\n".join(formatted)