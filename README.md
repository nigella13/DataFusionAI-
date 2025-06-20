# My Python App

This application leverages Ollama to connect with local large language models (LLMs) for offline AI-powered responses.
 It integrates with a local database to answer database-related queries and uses FAISS for efficient document retrieval, enabling question-answering on loaded documents. 
 Additionally, it employs Retrieval-Augmented Generation (RAG) to fetch up-to-date information from the internet when needed.
 Finally, it combines these capabilities with the local LLM's built-in knowledge to provide comprehensive answers across diverse queries.

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/nigella13/DataFusionAI-.git


#### 2. Install Dependencies

pip install -r requirements.txt


### 3. Setup the Database

We use a sample MySQL database 

You can start with the sample database structure and load your own sample data  included in db/schema.sql).

SQL Dump File

db/
└── schema.sql

run below command to create the structure
psql -U myuser -d mydb -f db/schema.sql



### 🚀 4. Run the App

python app.py

