# --- 1. 沙盒工具 (Sandbox Tools) ---
from .sandbox.chunk_text import chunk_text, CHUNK_TEXT_SCHEMA
from .sandbox.clean_text import clean_text, CLEAN_TEXT_SCHEMA
from .sandbox.json_to_txt import json_to_txt, JSON_TO_TXT_SCHEMA
from .sandbox.read_chunk import read_chunk, READ_CHUNK_SCHEMA
from .sandbox.clean_text.llm_batch_clean import llm_batch_clean_text, LLM_BATCH_CLEAN_SCHEMA
from .sandbox.write_file import write_file, WRITE_FILE_SCHEMA

# --- 2. 系统权限工具 (System Tools) ---
from .system.read_file import read_file, READ_FILE_SCHEMA
from .system.list_dir import list_dir, LIST_DIR_SCHEMA
from .system.load_skill import load_skill_sop, LOAD_SKILL_SCHEMA

# --- 3. 网络工具 (Network Tools) ---
from .network.web_search import search_web, SEARCH_WEB_SCHEMA

SANDBOX_TOOLS_SCHEMA = [
    CHUNK_TEXT_SCHEMA,
    CLEAN_TEXT_SCHEMA,
    JSON_TO_TXT_SCHEMA,
    READ_CHUNK_SCHEMA,
    LLM_BATCH_CLEAN_SCHEMA,
    WRITE_FILE_SCHEMA
]

SYSTEM_TOOLS_SCHEMA = [
    READ_FILE_SCHEMA,
    LIST_DIR_SCHEMA,
    LOAD_SKILL_SCHEMA
]

NETWORK_TOOLS_SCHEMA = [
    SEARCH_WEB_SCHEMA
]

TOOLS_SCHEMA = SANDBOX_TOOLS_SCHEMA + SYSTEM_TOOLS_SCHEMA + NETWORK_TOOLS_SCHEMA

AVAILABLE_TOOLS = {
    # Sandbox
    "chunk_text": chunk_text,
    "clean_text": clean_text,
    "json_to_txt": json_to_txt,
    "read_chunk": read_chunk,
    "llm_batch_clean_text": llm_batch_clean_text,
    "write_file": write_file,
    
    # System
    "read_file": read_file,
    "list_dir": list_dir,
    "load_skill_sop": load_skill_sop,
    
    # Network
    "search_web": search_web
}

__all__ = ["TOOLS_SCHEMA", "AVAILABLE_TOOLS", "SANDBOX_TOOLS_SCHEMA", "SYSTEM_TOOLS_SCHEMA", "NETWORK_TOOLS_SCHEMA"]
