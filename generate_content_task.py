import argparse
import json
import os
import sys
import logging
from typing import List, Dict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add project root to sys.path
try:
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    from src.faq_generator import FAQGenerator
    from src.question_generator import QuestionGenerator
    from src.vector_store import VectorStoreManager
except ImportError as e:
    logging.error(f"Failed to import project modules. Error: {e}")
    sys.exit(1)

def run_content_generation(conversation_file: str):
    """
    Orchestrates the generation of both FAQs (to SQLite) and suggested questions (to Pinecone).
    """
    try:
        logging.info(f"Loading conversation from {conversation_file}")
        with open(conversation_file, 'r') as f:
            conversation_history: List[Dict[str, str]] = json.load(f)
        
        if len(conversation_history) < 2:
            logging.warning("Conversation too short. Skipping content generation.")
            return

        # --- 1. Generate and Store FAQs ---
        logging.info("Starting FAQ generation...")
        faq_generator = FAQGenerator()
        faq_generator.generate_and_store_faqs(conversation_history)
        
        # --- 2. Generate and Store Suggested Questions ---
        logging.info("Starting Suggested Questions generation...")
        question_generator = QuestionGenerator()
        questions = question_generator.generate_questions_from_conversation(conversation_history)
        
        if questions:
            logging.info(f"Storing {len(questions)} suggested questions in vector store...")
            vector_store_manager = VectorStoreManager()
            vector_store_manager.add_suggested_questions(questions)
            logging.info("Successfully stored suggested questions.")
        else:
            logging.info("No suggested questions were generated.")

    except Exception as e:
        logging.error(f"An unexpected error occurred during content generation: {e}", exc_info=True)
    finally:
        if os.path.exists(conversation_file):
            os.remove(conversation_file)
            logging.info(f"Cleaned up temporary file: {conversation_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and store FAQs and suggested questions from a conversation.")
    parser.add_argument("conversation_file", type=str, help="Path to the JSON file containing the conversation history.")
    
    args = parser.parse_args()
    run_content_generation(args.conversation_file)