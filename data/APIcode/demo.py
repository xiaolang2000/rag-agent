import json
import threading
import requests
from fastapi import FastAPI, Form, BackgroundTasks
from ragflow_sdk import RAGFlow
import json

app = FastAPI()

def load_config(path="config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

cfg = load_config()

API_KEY = cfg["ragflow"]["api_key"]
BASE_URL = cfg["ragflow"]["base_url"]
ASSISTANT_NAME = cfg["ragflow"]["assistant_name"]

MAIN_SERVER = cfg["server"]["main_server"]

# ===== 全局：RAGFlow assistant & session 缓存 =====
rag_object = RAGFlow(api_key=API_KEY, base_url=BASE_URL)
assistants = rag_object.list_chats(name=ASSISTANT_NAME)
if not assistants:
    raise RuntimeError(f"找不到名为 {ASSISTANT_NAME} 的 chat assistant")
assistant = assistants[0]

# from_user(openid) -> Session
_sessions = {}
_sessions_lock = threading.Lock()


def get_or_create_session(from_user: str):
    """为每个用户维护一个 RAGFlow session，保证多轮上下文"""
    with _sessions_lock:
        sess = _sessions.get(from_user)
        if sess is None:
            sess = assistant.create_session(name=f"wx_{from_user}")
            _sessions[from_user] = sess
        return sess


# def send_custom_message(openid: str, content: str):
#     """通过服务器接口发送客服消息"""
#     url = f"{MAIN_SERVER}/send_custom_message"
#     data = {"openid": openid, "message_type": "text", "content": content}
#     try:
#         resp = requests.post(
#             url,
#             data=json.dumps(data, ensure_ascii=False).encode("utf-8"),
#             headers={"Content-Type": "application/json"},
#             timeout=15,
#         )
#         return resp.json()
#     except Exception as e:
#         print(f"发送客服消息失败: {e}")
#         return {"errcode": -1, "errmsg": str(e)}

def send_custom_message(openid: str, content: str):
    print(f"\n==== MOCK SEND ====\nTO: {openid}\n{content}\n===================\n")
    return {"errcode": 0, "errmsg": "mocked"}


def ragflow_answer_text(from_user: str, question: str) -> str:
    """把文本问题交给 RAGFlow，拿到完整回复（非流式拼接）"""
    sess = get_or_create_session(from_user)

    # stream=True 时，ans.content 会逐步变长；我们取最终完整 content
    final = ""
    for ans in sess.ask(question, stream=True):
        final = ans.content
    return final.strip() or "（未生成有效回复）"


def process_and_send(from_user: str, content: str, msg_type: str):
    """后台任务：调用 RAGFlow 生成回复，并通过客服接口发送"""
    try:
        if msg_type == "text":
            reply = ragflow_answer_text(from_user, content)

        elif msg_type == "image":
            # 你现在只有图片 URL；是否能“上传图片到 RAGFlow”取决于 RagFlow 是否提供文件上传接口
            # 这里先做降级：告诉用户已收到图片 + 引导发文字描述
            reply = (
                "已收到图片链接，但当前接口未把图片上传到知识库/对话中供模型解析。\n"
                f"图片URL：{content}\n"
                "你可以补充一句文字描述你想问什么，我再帮你分析。"
            )

        else:
            reply = f"收到 {msg_type} 类型消息，但当前仅对接了 text/image。"

        result = send_custom_message(from_user, reply)
        print(f"客服消息发送结果: {result}")

    except Exception as e:
        print(f"process_and_send 异常: {e}")
        send_custom_message(from_user, f"系统处理失败：{e}")


@app.post("/message")
async def receive_message(
    background_tasks: BackgroundTasks,
    from_user: str = Form(...),
    content: str = Form(...),
    type: str = Form(...),
):
    print(f"收到消息: from_user={from_user}, content={content}, type={type}")

    # 立即返回一个“已收到”的同步响应（避免 webhook 超时）
    background_tasks.add_task(process_and_send, from_user, content, type)
    return "已收到，正在处理…"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
