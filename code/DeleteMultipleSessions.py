from ragflow_sdk import RAGFlow
import json

def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

cfg = load_config()

API_KEY = cfg["ragflow"]["api_key"]
BASE_URL = cfg["ragflow"]["base_url"]
ASSISTANT_NAME = cfg["ragflow"]["assistant_name"]

rag_object = RAGFlow(api_key=API_KEY, base_url=BASE_URL)
assistant = rag_object.list_chats(name=ASSISTANT_NAME)
assistant = assistant[0]

assistant.delete_sessions(ids=["7bf32c50dbdc11f09c9366467d7c1b19",])