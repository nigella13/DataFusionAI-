from pathlib import Path
from datetime import datetime

#CHROMA_SETTINGS = {
#    "persist_directory": str(Path("C:/Users/ze288365/Documents/GenAI Course/Langchain/shared_chromadb").absolute()),
#    "collection_name": "knowledge_base",
##    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
#    "min_similarity_score": 0.3 
#}



CHROMA_SETTINGS = {
    "persist_directory": r"C:/Users/ze288365/Documents/GenAI Course/Langchain/shared_chromadb",
    "collection_name": "knowledge_base",
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "min_similarity_score": 0.3,
    "chroma_client_settings": {  
        "anonymized_telemetry": False,
        "persist_directory": r"C:/Users/ze288365/Documents/GenAI Course/Langchain/shared_chromadb"
    }
}