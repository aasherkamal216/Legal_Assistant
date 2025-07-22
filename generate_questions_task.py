import argparse
import json
import os
import sys
import logging
from typing import List, Dict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add project root to sys.path to allow imports from src, config
try:
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    from src.question_generator import QuestionGenerator
    from src.vector_store import VectorStoreManager
except ImportError as e:
    logging.error(f"Failed to import project modules. Error: {e}")
    sys.exit(1)

def run_question_generation(conversation_file: str):
    """
    Loads a conversation, generates suggested questions, and stores them in Pinecone.
    """
    try:
        # 1. Load conversation from the temporary file
        logging.info(f"Loading conversation from {conversation_file}")
        with open(conversation_file, 'r') as f:
            conversation_history: List[Dict[str, str]] = json.load(f)
        
        if not conversation_history or len(conversation_history) < 2:
            logging.warning("Conversation is too short. Skipping question generation.")
            return

        # 2. Generate questions using the QuestionGenerator
        logging.info("Starting question generation process...")
        question_generator = QuestionGenerator()
        questions = question_generator.generate_questions_from_conversation(conversation_history)
        
        if not questions:
            logging.info("No new questions were generated from this conversation.")
            return

        # 3. Store the generated questions in Pinecone
        logging.info(f"Storing {len(questions)} generated questions in vector store...")
        vector_store_manager = VectorStoreManager()
        vector_store_manager.add_suggested_questions(questions)
        logging.info("Successfully stored questions.")

    except json.JSONDecodeError:
        logging.error(f"Error: Could not decode JSON from {conversation_file}.")
    except Exception as e:
        logging.error(f"An unexpected error occurred during question generation: {e}", exc_info=True)
    finally:
        # 4. Clean up the temporary file
        if os.path.exists(conversation_file):
            os.remove(conversation_file)
            logging.info(f"Cleaned up temporary file: {conversation_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate and store suggested questions from a conversation.")
    parser.add_argument("conversation_file", type=str, help="Path to the JSON file containing the conversation history.")
    
    args = parser.parse_args()
    run_question_generation(args.conversation_file)