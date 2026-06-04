from .web_search import search_web, SEARCH_WEB_SCHEMA
from .read_file import read_file, READ_FILE_SCHEMA
from .write_file import write_file, WRITE_FILE_SCHEMA
from .chunk_text import chunk_text, CHUNK_TEXT_SCHEMA
from .clean_text import clean_text, CLEAN_TEXT_SCHEMA
from .read_chunk import read_chunk, READ_CHUNK_SCHEMA
from .json_to_txt import json_to_txt, JSON_TO_TXT_SCHEMA
from .clean_text.llm_batch_clean import llm_batch_clean_text, LLM_BATCH_CLEAN_SCHEMA
from .list_dir import list_dir, LIST_DIR_SCHEMA

TOOLS_SCHEMA = [
    SEARCH_WEB_SCHEMA,
    READ_FILE_SCHEMA,
    WRITE_FILE_SCHEMA,
    CHUNK_TEXT_SCHEMA,
    CLEAN_TEXT_SCHEMA,
    READ_CHUNK_SCHEMA,
    JSON_TO_TXT_SCHEMA,
    LLM_BATCH_CLEAN_SCHEMA,
    LIST_DIR_SCHEMA
]

AVAILABLE_TOOLS = {
    "search_web": search_web,
    "read_file": read_file,
    "write_file": write_file,
    "chunk_text": chunk_text,
    "clean_text": clean_text,
    "read_chunk": read_chunk,
    "json_to_txt": json_to_txt,
    "llm_batch_clean_text": llm_batch_clean_text,
    "list_dir": list_dir
}

__all__ = ["TOOLS_SCHEMA", "AVAILABLE_TOOLS"]
