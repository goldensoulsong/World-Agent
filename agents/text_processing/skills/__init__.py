from .smart_chunking import SMART_CHUNKING_SKILL
from .data_cleaning import DATA_CLEANING_SKILL
from .full_llm_clean import FULL_LLM_CLEAN_SKILL

TEXT_PROCESSING_SKILLS = [
    SMART_CHUNKING_SKILL,
    DATA_CLEANING_SKILL,
    FULL_LLM_CLEAN_SKILL
]

__all__ = ["TEXT_PROCESSING_SKILLS"]
