from openai import OpenAI
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv() # Load environment variables from .env file

# 配置连接到本地 LM Studio 或云端 LLM
client = OpenAI(
    base_url=os.getenv("OPENAI_API_BASE", "http://127.0.0.1:1234/v1"),  # 指向 LM Studio 或云端 LLM
    api_key=os.getenv("OPENAI_API_KEY", "lm-studio")  # LM Studio 通常不需要 Key，但这行必须填占位符
)

def consult_gpt_oss(prompt):
    """
    发送请求给本地的 GPT-OSS-20B
    """
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL_NAME", "Qwen3-14B"), # Default to Qwen3-14B
            messages=[
                {"role": "system", "content": "你是一个流式细胞术专家，请以 JSON 格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, # 低温度保证逻辑稳定性
            response_format={"type": "json_object"} # Explicitly request JSON object
        )
        llm_output = response.choices[0].message.content
        print(f"Raw LLM Response: {llm_output}") # Debug print
        return llm_output
    except Exception as e:
        return f"连接错误: {e}"

