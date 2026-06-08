from .rag_tools import add_to_knowledge_base, search_knowledge_base, ADD_TO_KB_SCHEMA, SEARCH_KB_SCHEMA

RAG_TOOLS_SCHEMA = [
    ADD_TO_KB_SCHEMA,
    SEARCH_KB_SCHEMA
]

RAG_AVAILABLE_TOOLS = {
    "add_to_knowledge_base": add_to_knowledge_base,
    "search_knowledge_base": search_knowledge_base
}

__all__ = ["RAG_TOOLS_SCHEMA", "RAG_AVAILABLE_TOOLS"]
