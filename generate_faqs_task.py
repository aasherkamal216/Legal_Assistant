import argparse
import json
import os
import sys
import logging
from typing import List, Dict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add project root to sys.path to allow imports from src, config
# This makes the script runnable from the project root directory
try:
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    from src.faq_generator import FAQGenerator
except ImportError as e:
    logging.error(f"Failed to import project modules. Make sure you are running this script from the 'legal_assistant' project root. Error: {e}")
    sys.exit(1)


def run_faq_generation(conversation_file: str):
    """
    Loads a conversation from a file, generates FAQs using the FAQGenerator,
    and handles cleanup.
    """
    try:
        # 1. Load conversation from the temporary file
        logging.info(f"Loading conversation from {conversation_file}")
        with open(conversation_file, 'r') as f:
            conversation_history: List[Dict[str, str]] = json.load(f)
        
        # Avoid processing very short or empty conversations
        if not conversation_history or len(conversation_history) < 2:
            logging.warning("Conversation is too short. Skipping FAQ generation.")
            return

        # 2. Instantiate generator and run the process
        logging.info("Starting FAQ generation process...")
        faq_generator = FAQGenerator()
        generated_faqs = faq_generator.generate_faqs_from_conversation(conversation_history)
        
        if generated_faqs:
            logging.info(f"Successfully generated and stored {len(generated_faqs)} FAQs.")
        else:
            logging.info("No new FAQs were generated from this conversation.")

    except json.JSONDecodeError:
        logging.error(f"Error: Could not decode JSON from {conversation_file}.")
    except Exception as e:
        # Log any other errors for debugging
        logging.error(f"An unexpected error occurred during FAQ generation: {e}", exc_info=True)
    finally:
        # 3. Clean up the temporary conversation file to ensure privacy and tidiness
        if os.path.exists(conversation_file):
            os.remove(conversation_file)
            logging.info(f"Cleaned up temporary file: {conversation_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate FAQs in the background from a conversation history file.")
    parser.add_argument("conversation_file", type=str, help="Path to the JSON file containing the conversation history.")
    
    args = parser.parse_args()
    
    run_faq_generation(args.conversation_file)