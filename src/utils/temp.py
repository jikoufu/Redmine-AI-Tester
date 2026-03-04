import dashscope
from http import HTTPStatus
import os
from dotenv import load_dotenv

load_dotenv()
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

resp = dashscope.TextEmbedding.call(
    model=dashscope.TextEmbedding.Models.text_embedding_v2,
    input='测试连接'
)

if resp.status_code == HTTPStatus.OK:
    print("✅ 阿里云连接成功！")
else:
    print(f"❌ 错误码：{resp.code}")
    print(f"❌ 错误消息：{resp.message}")