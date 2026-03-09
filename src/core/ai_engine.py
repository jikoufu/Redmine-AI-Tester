"""
ai_engine.py — AI 引擎核心

职责：
  - 管理当前角色（角色决定 Prompt 和报告结构）
  - 统一数据脱敏入口（所有上送数据必须经过此处）
  - 提供三种调用模式：报告生成 / 全局咨询 / 自由对话
"""
import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from src.roles.qa  import QARole
from src.roles.pm  import PMRole
from src.roles.dev import DevRole
from src.utils.privacy_guard import sanitize_with_report

load_dotenv()
logger = logging.getLogger(__name__)

# 角色注册表，新增角色只需在此注册
ROLES = {
    "qa":  QARole(),
    "pm":  PMRole(),
    "dev": DevRole(),
}
DEFAULT_ROLE = "qa"


def select_role() -> str:
    """交互式角色选择，返回角色 key。供 main.py 调用。"""
    print("\n" + "─" * 52)
    print("👤 请选择你的角色（影响 AI 分析视角与报告结构）：")
    print("─" * 52)
    keys = list(ROLES.keys())
    for i, key in enumerate(keys, 1):
        r = ROLES[key]
        print(f"  {i}. {r.label}  —  {r.description}")
    print("─" * 52)
    while True:
        raw = input("请输入序号 [默认 1]: ").strip()
        if not raw:
            chosen = keys[0]; break
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            chosen = keys[int(raw) - 1]; break
        print(f"⚠️  请输入 1 ~ {len(keys)} 之间的数字。")
    print(f"\n✅ 已切换为：{ROLES[chosen].label}\n")
    return chosen


class AIEngine:
    def __init__(self, role: str = DEFAULT_ROLE):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )
        self.model = "deepseek-chat"
        self.set_role(role)

    def set_role(self, role: str):
        if role not in ROLES:
            logger.warning("未知角色 '%s'，回退到 '%s'", role, DEFAULT_ROLE)
            role = DEFAULT_ROLE
        self.role = role
        self.role_config = ROLES[role]

    @property
    def role_label(self) -> str:
        return self.role_config.label

    # ── 隐私守卫 ──────────────────────────────────────────────
    def _sanitize(self, text: str) -> str:
        result = sanitize_with_report(text)
        if result.was_modified:
            print(f"\n🛡️  [隐私守卫] {result.summary()}")
        return result.sanitized_text

    # ── 底层流式调用 ──────────────────────────────────────────
    def _call_ai(self, system: str, user: str, temp: float = 0.7) -> str:
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system},
                          {"role": "user",   "content": user}],
                temperature=temp, stream=True,
            )
            full = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    c = chunk.choices[0].delta.content
                    print(c, end="", flush=True)
                    full += c
            print()
            return full
        except Exception as e:
            logger.error("AI 调用失败: %s", e)
            return f"❌ 调用失败: {e}"

    # ── 业务方法 ──────────────────────────────────────────────
    def generate_report(self, context: str) -> str:
        """生成角色视角的 Issue 分析报告"""
        safe = self._sanitize(context)
        return self._call_ai(
            self.role_config.system_prompt,
            f"请详细分析以下 Redmine 数据并输出报告：\n\n{safe}",
            temp=0.7
        )

    def simple_query(self, query: str, context: str) -> str:
        """全局咨询模式（RAG 检索后调用）"""
        safe_q = self._sanitize(query)
        safe_c = self._sanitize(context)
        system = f"你是一个专业技术项目助手，以 {self.role_label} 的视角回答问题。"
        return self._call_ai(system, f"参考资料：\n{safe_c}\n\n问题：{safe_q}", temp=0.1)

    def free_chat(self, issue_context: str, user_input: str, history: list) -> str:
        """多轮自由对话"""
        safe_input = self._sanitize(user_input)
        system = (
            f"{self.role_config.free_chat_role}\n"
            f"Issue 完整数据如下，作为所有回答的唯一参考：\n\n{issue_context}\n\n"
            "若数据中有 [*已脱敏] 占位符，请标注已做隐私处理，不要推测原始值。"
        )
        messages = [{"role": "system", "content": system}]
        messages.extend(history)
        messages.append({"role": "user", "content": safe_input})
        try:
            stream = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.5, stream=True
            )
            full = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    c = chunk.choices[0].delta.content
                    print(c, end="", flush=True)
                    full += c
            print()
            return full
        except Exception as e:
            logger.error("free_chat 调用失败: %s", e)
            return f"❌ 调用失败: {e}"
