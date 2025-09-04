from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
import json
import time
import fitz
from translator import baidu_translate
import os
from dotenv import load_dotenv

load_dotenv()
BAIDU_APPID = os.getenv('BAIDU_APPID')
BAIDU_SECRET_KEY = os.getenv('BAIDU_SECRET_KEY')
if not BAIDU_APPID or not BAIDU_SECRET_KEY:
    raise ValueError("请在 .env 文件中设置 BAIDU_APPID 和 BAIDU_SECRET_KEY")

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

    # 响应内容
    raw_text = extract_text_from_pdf("test_data/nphoton.2017.116.pdf")
    cleaned_text = clean_extracted_text(raw_text)
    translated_text = baidu_translate(cleaned_text, BAIDU_APPID, BAIDU_SECRET_KEY)


    your_content = f"# 翻译结果：\n{translated_text}"

    # 如果客户端要求流式传输，我们就返回流式响应
    if request.stream:
        def generate_stream():
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
                            "content": your_content
                        },
                        "finish_reason": "stop"
                    }
                ]
            }
            yield f"data: {json.dumps(data_chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate_stream(), media_type="text/event-stream")
    
    # 如果不是流式请求，返回原来的正常响应
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
                "id": "my-translator", 
                "object": "model",
                "created": 1686935000,
                "owned_by": "my-org"
            }
        ]
    }
    return JSONResponse(content=fake_models_list)

def extract_text_from_pdf(pdf_path):
    """从指定的PDF路径中提取文本，并确保中文正确编码"""
    text = ""
    # text = page.get_text("text")

    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # 获取页面所有文本块的信息，包含详细属性
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            # 只处理包含文本的块
            if block["type"] == 0: 
                # 计算这个文本块占据的面积
                rect = block["bbox"]
                block_area = (rect[2] - rect[0]) * (rect[3] - rect[1]) # (x1, y1, x2, y2) -> 宽*高
                
                # 启发式规则：如果文本块面积非常小，很可能是图注或页码，跳过它
                # 你也可以根据块的位置（如非常靠近页面边缘）来过滤页眉页脚
                if block_area < 500: # 这个阈值500可以调整，是一个经验值
                    continue
                
                # 如果是正常大小的文本块，则添加它的文本
                for line in block["lines"]:
                    for span in line["spans"]:
                        text += span["text"]
                    text += "\n" # 在行尾添加换行
                text += "\n" # 在块尾添加空行，分隔段落
    doc.close()
    return text


def clean_extracted_text(raw_text):
    """
    智能清理文本：合并被断开的单词，保留段落结构。
    """
    lines = raw_text.splitlines()
    cleaned_lines = []
    current_paragraph = []  # 用一个列表临时存储当前段落的行

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            # 遇到空行，说明是段落分隔符
            if current_paragraph:  # 如果当前段落有内容，就把它合并成一段并保存
                cleaned_lines.append(" ".join(current_paragraph))
                current_paragraph = []  # 重置当前段落
            cleaned_lines.append("")  # 保留空行作为段落间隔
        else:
            # 检查当前行是否以结束标点结尾（表示一个句子结束）
            if stripped_line.endswith(('.', '!', '?', ';', ':', '"', "'")):
                current_paragraph.append(stripped_line)
                # 如果句子结束了，可以考虑直接提交当前段落，也可以继续累积
                # 这里选择累积到遇到空行再提交，更适合学术论文的长段落
            else:
                # 如果行尾没有结束标点，很可能是一个单词被断开了，去掉行尾的连字符并合并
                line_without_hyphen = stripped_line.rstrip('-')
                current_paragraph.append(line_without_hyphen)

    # 处理文件末尾最后一段没有空行的情况
    if current_paragraph:
        cleaned_lines.append(" ".join(current_paragraph))

    # 用换行符连接所有处理好的段落和空行
    return "\n".join(cleaned_lines)

# 你可以在代码里测试一下这个函数
if __name__ == "__main__":
    print(extract_text_from_pdf("test.pdf"))