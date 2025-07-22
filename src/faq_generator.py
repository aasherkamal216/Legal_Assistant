from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from config.settings import settings
from config.database import FAQDatabase
from .prompts import FAQ_PROMPT


class FAQ(BaseModel):
    question: str = Field(description="The FAQ question")
    answer: str = Field(description="The FAQ answer")
    category: str = Field(
        description="Legal category (e.g., Contract Law, Family Law, etc.)"
    )


class FAQList(BaseModel):
    faqs: List[FAQ] = Field(description="List of generated FAQs")


class FAQGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.PRIMARY_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.3,
        )
        self.db = FAQDatabase(settings.DATABASE_PATH)

    def generate_faqs_from_conversation(
        self, conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Generate FAQs from conversation history"""

        # Format conversation for analysis
        formatted_conversation = self._format_conversation(conversation_history)

        faq_generator = self.llm.with_structured_output(FAQList)
        result = faq_generator.invoke(
            [
                SystemMessage(content=FAQ_PROMPT),
                HumanMessage(content=formatted_conversation),
            ]
        )

        if not result.faqs:
            return []

        # Convert to dict format
        faq_dicts = [
            {"question": faq.question, "answer": faq.answer, "category": faq.category}
            for faq in result.faqs
        ]

        # Store in database
        if faq_dicts:
            self.db.insert_faqs(faq_dicts)

        return faq_dicts

    def _format_conversation(self, conversation: List[Dict[str, str]]) -> str:
        """Format conversation for LLM analysis"""
        formatted = []
        for msg in conversation:
            role = "Human" if msg.get("role") == "user" else "Assistant"
            formatted.append(f"{role}: {msg.get('content', '')}")
        return "\n\n".join(formatted)

    def get_top_faqs(self, limit: int = 8, category: str = None) -> List[Dict]:
        """Get top FAQs from database"""
        return self.db.get_top_faqs(limit, category)

    def get_categories(self) -> List[str]:
        """Get all FAQ categories"""
        return self.db.get_categories()
