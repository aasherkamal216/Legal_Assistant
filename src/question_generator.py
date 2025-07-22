from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from config.settings import settings
from .prompts import SUGGESTED_QUESTIONS_PROMPT

class SuggestedQuestions(BaseModel):
    """A list of suggested questions based on a conversation."""
    questions: List[str] = Field(
        description="A list of 1 to 5 concise, standalone questions a user might ask based on the preceding conversation."
    )

class QuestionGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.PRIMARY_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.5
        ).with_structured_output(SuggestedQuestions)

    def generate_questions_from_conversation(self, conversation_history: List[dict]) -> List[str]:
        """
        Analyzes a conversation and generates relevant follow-up questions.
        """
        if not conversation_history or len(conversation_history) < 2:
            return []

        formatted_conversation = self._format_conversation(conversation_history)

        try:
            response = self.llm.invoke([
                SystemMessage(content=SUGGESTED_QUESTIONS_PROMPT),
                HumanMessage(content=f"<Conversation>\n{formatted_conversation}\n</Conversation>")
            ])
            return response.questions if response and response.questions else []
        except Exception as e:
            print(f"Error generating questions: {e}")
            return []

    def _format_conversation(self, conversation: List[dict]) -> str:
        """Formats conversation for LLM analysis."""
        formatted = []
        for msg in conversation:
            role = "User" if msg.get("role") == "user" else "Assistant"
            formatted.append(f"{role}: {msg.get('content', '')}")
        return "\n\n".join(formatted)