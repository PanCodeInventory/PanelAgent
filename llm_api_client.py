from openai import OpenAI
import pandas as pd

# 配置连接到本地 LM Studio
client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",  # 指向 LM Studio
    api_key="lm-studio"  # LM Studio 通常不需要 Key，但这行必须填占位符
)

def consult_gpt_oss(prompt):
    """
    发送请求给本地的 GPT-OSS-20B
    """
    try:
        response = client.chat.completions.create(
            model="Qwen3-14B",  # Updated to match the user's loaded model
            messages=[
                {"role": "system", "content": "你是一个流式细胞术专家，请以 JSON 格式输出。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, # 低温度保证逻辑稳定性
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"连接错误: {e}"

