from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
import json
import time

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# 定义一个数据模型，用来接收请求
class ChatRequest(BaseModel):
    model: str
    messages: list
    stream: bool = False

@app.post("/v1/chat/completions")
def fake_ai_response(request: ChatRequest):

    # 2. 你原来准备好的响应内容
    your_content = "# 这是我的第一篇论文\n> 这是一段引用。\n- 这是列表项1\n- 这是列表项2\n\n**完美！**"

    # 3. 如果客户端要求流式传输，我们就返回流式响应
    if request.stream:
        def generate_stream():
            # 模拟一个快速的、只有一个数据块的"流"
            data_chunk = {
                "id": "chatcmpl-fake-id-12345",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": your_content  # 一次性返回所有内容
                        },
                        "finish_reason": "stop"
                    }
                ]
            }
            yield f"data: {json.dumps(data_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate_stream(), media_type="text/event-stream")
    
    # 4. 如果不是流式请求，返回原来的正常响应
    else:
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": your_content
                    }
                }
            ]
        }

# --- 新增以下代码来让日志安静 ---
@app.post("/api/backends/chat-completions/status")
def fake_status():
    """伪造一个状态接口，让SillyTavern前端安心"""
    fake_response = {
        "status": "ready",
        "message": "Fake backend is running smoothly!",
        "model": "my-translator"
    }
    return JSONResponse(content=fake_response)

# 如果你的SillyTavern版本请求的路径不同，你可能需要也加上这个
@app.post("/api/backends/openaiapiv3/status")
def fake_status_v3():
    return fake_status()

@app.get("/v1/models")
def get_models():
    """伪造一个模型列表接口，告诉前端我们只有一个叫'my-translator'的模型"""
    fake_models_list = {
        "object": "list",
        "data": [
            {
                "id": "my-translator", # 这个名字和你之前随便起的模型名对应上就行
                "object": "model",
                "created": 1686935000,
                "owned_by": "my-org"
            }
        ]
    }
    return JSONResponse(content=fake_models_list)
