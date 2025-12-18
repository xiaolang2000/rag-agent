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


rag_object = RAGFlow(api_key=API_KEY, base_url=BASE_URL)
session = assistant.create_session()    

print(f"\n==================== {ASSISTANT_NAME} =====================\n")
print("Hello. What can I do for you?")

# 流式回答
while True:
    question = input("\n==================== User =====================\n> ")
    print(f"\n==================== {ASSISTANT_NAME} =====================\n")
    
    cont = ""
    for ans in session.ask(question, stream=True):
        print(ans.content[len(cont):], end='', flush=True)
        cont = ans.content
