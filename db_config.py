import os

def get_db_path():
    return os.getenv("DB_PATH", "Genai.db")  # fallback to local file
