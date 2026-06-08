# --- 2. 系统权限工具 (System Tools) ---
from .system.read_file import read_file, READ_FILE_SCHEMA
from .system.list_dir import list_dir, LIST_DIR_SCHEMA
from .system.load_skill.load_skill import load_skill_sop, LOAD_SKILL_SCHEMA, register_skills, clear_skills

# --- 3. 网络工具 (Network Tools) ---
from .network.web_search import search_web, SEARCH_WEB_SCHEMA

SYSTEM_TOOLS_SCHEMA = [
    READ_FILE_SCHEMA,
    LIST_DIR_SCHEMA,
    LOAD_SKILL_SCHEMA
]

NETWORK_TOOLS_SCHEMA = [
    SEARCH_WEB_SCHEMA
]

TOOLS_SCHEMA = SYSTEM_TOOLS_SCHEMA + NETWORK_TOOLS_SCHEMA

AVAILABLE_TOOLS = {
    # System
    "read_file": read_file,
    "list_dir": list_dir,
    "load_skill_sop": load_skill_sop,
    
    # Network
    "search_web": search_web
}

__all__ = ["TOOLS_SCHEMA", "AVAILABLE_TOOLS", "SYSTEM_TOOLS_SCHEMA", "NETWORK_TOOLS_SCHEMA", "register_skills", "clear_skills"]
