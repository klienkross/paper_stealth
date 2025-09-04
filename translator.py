import requests
import random
import hashlib

def baidu_translate(text, appid, secret_key, from_lang='en', to_lang='zh', glossary_id=None):
    """
    使用百度翻译API翻译文本
    :param glossary_id: 可选参数；术语库ID，如果提供则启用术语库
    """
    if not text.strip():
        return text

    salt = str(random.randint(32768, 65536))
    sign_str = appid + text + salt + secret_key
    sign = hashlib.md5(sign_str.encode()).hexdigest()

    url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
    # 将参数放在请求体中 (data)，而不是URL里 (params)
    data = {
        'q': text,        # 要翻译的文本
        'from': from_lang, # 源语言
        'to': to_lang,    # 目标语言
        'appid': appid,   # APP ID
        'salt': salt,     # 随机盐
        'sign': sign      # 签名
    }
    
    # 如果提供了术语库ID，则添加到请求参数中
    if glossary_id is not None:
        data['action'] = 1  # 百度API启用术语库的action值，请根据最新文档确认
        data['glossaryId'] = glossary_id

    try:
        response = requests.post(url, data=data)
        result = response.json()
        
        if 'trans_result' in result:
            translated_text = '\n'.join([item['dst'] for item in result['trans_result']])
            return translated_text
        else:
            print("翻译出错：", result)
            return f"[翻译失败] {text}"

    except Exception as e:
        print(f"请求异常：{e}")
        print(f"响应状态码: {response.status_code}")
        print(f"响应文本: {response.text}") # 这会打印出服务器返回的真实内容，帮助诊断
        return f"[翻译异常] {text}"