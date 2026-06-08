from .chunk_text import chunk_text, CHUNK_TEXT_SCHEMA
from .clean_text import clean_text, CLEAN_TEXT_SCHEMA
from .json_to_txt import json_to_txt, JSON_TO_TXT_SCHEMA
from .read_chunk import read_chunk, READ_CHUNK_SCHEMA
from .clean_text.llm_batch_clean import llm_batch_clean_text, LLM_BATCH_CLEAN_SCHEMA
from .write_file import write_file, WRITE_FILE_SCHEMA

TEXT_PROCESSING_TOOLS_SCHEMA = [
    CHUNK_TEXT_SCHEMA,
    CLEAN_TEXT_SCHEMA,
    JSON_TO_TXT_SCHEMA,
    READ_CHUNK_SCHEMA,
    LLM_BATCH_CLEAN_SCHEMA,
    WRITE_FILE_SCHEMA
]

TEXT_PROCESSING_AVAILABLE_TOOLS = {
    "chunk_text": chunk_text,
    "clean_text": clean_text,
    "json_to_txt": json_to_txt,
    "read_chunk": read_chunk,
    "llm_batch_clean_text": llm_batch_clean_text,
    "write_file": write_file
}

__all__ = ["TEXT_PROCESSING_TOOLS_SCHEMA", "TEXT_PROCESSING_AVAILABLE_TOOLS"]
