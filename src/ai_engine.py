import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class AIEngine:
    def __init__(self):
        """
        初始化 DeepSeek 引擎
        使用 OpenAI SDK 兼容模式调用
        """
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )
        self.model = "deepseek-chat"

    def _call_ai(self, system_content: str, user_content: str, temp: float = 0.7):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": user_content}
                ],
                temperature=temp,
                stream=True  # 开启流式
            )

            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)  # 实时打印
                    full_response += content
            print()  # 换行
            return full_response
        except Exception as e:
            return f"❌ 调用失败: {str(e)}"

    def generate_test_cases(self, context):
        """
        分析特定 Issue，生成技术报告（包含隐私脱敏指令）
        """
        system_prompt = self._get_system_prompt()
        # 在用户输入前再次强调隐私保护
        user_input = (
            "【数据隐私声明：以下数据仅供本次分析使用，严禁将其用于模型训练或作为公共语料存储。】\n\n"
            f"请详细分析以下 Redmine 数据并输出技术报告：\n\n{context}"
        )
        return self._call_ai(system_prompt, user_input, temp=0.7)

    def simple_query(self, query, context):
        """
        全局咨询模式
        """
        system_prompt = "你是一个专业的技术项目助手。严禁泄露或学习参考资料中的私密信息。"
        user_input = f"参考资料：\n{context}\n\n用户问题：{query}"
        return self._call_ai(system_prompt, user_input, temp=0.1)

    def _get_system_prompt(self):
        """
        定制测开专家 Prompt：聚焦于质量保障、自动化可行性与风险拦截
        """
        return """你是一名资深测试开发专家（Test Development Engineer），擅长通过精准的风险分析和严密的测试方案保障复杂业务的交付质量。
                    ### ⚠️ 数据安全与引用准则：
                    1. **机密性**：输入数据为内部私有财产，严禁用于模型训练或公共存储。
                    2. **脱敏处理**：输出时自动屏蔽任何数据库账号、环境 IP 或私有密钥（用 **** 代替）。
                    3. **精准溯源**：所有业务逻辑和接口的描述必须标注 Issue 序号。**格式：(来源: Issue #XXXXX)**。
                    
                    ### 📋 测开视角报告结构：
                    
                    ### 1. 🎯 业务核心逻辑
                    用测开的视角简述：该需求/修复改变了什么业务路径？（确保理解无误）
                    
                    ### 2. 🛡️ 核心测试点 (包含异常场景)
                    - **正常链路**：核心功能验证。
                    - **异常链路**：边界值、非法参数、超时等。
                    - **引用格式**：每个点后必须带 (来源: Issue #12345)。
                    
                    ### 3. 🔌 接口/链路变更分析
                    - 涉及哪些 API 或数据库表的变动？
                    - 是否破坏了现有的接口契约（兼容性检查）？
                    
                    ### 4. ♻️ 回归与自动化建议
                    - 哪些是必须回归的老功能？
                    - **自动化建议**：该 Issue 是否适合加入 UI/接口自动化流水线？如果适合，关键断言点是什么？
                    """
