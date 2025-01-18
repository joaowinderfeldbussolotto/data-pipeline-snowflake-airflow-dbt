
import time
import logging
from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def llm_call(func):
    """Decorator to handle LLM calls with rate limiting and logging."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Starting LLM call: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            time.sleep(1.5) 
            logger.info(f"Completed LLM call: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in LLM call {func.__name__}: {str(e)}")
            raise
    return wrapper


def get_model_name(llm) -> str:
    """
    Get the name of the language model.
    
    Args:
        llm: The language model instance
        
    Returns:
        str: The model name or 'Unknown' if not found
    """
    if llm is None:
        logger.warning("LLM instance is None")
        return "Unknown"

    try:
        if hasattr(llm, 'model_name'):
            return llm.model_name
        if hasattr(llm, 'model'):
            return llm.model
        
        logger.warning(f"Could not determine model name for LLM type: {type(llm)}")
        return "Unknown"
        
    except Exception as e:
        logger.error(f"Error getting model name: {str(e)}")
        return "Unknown"