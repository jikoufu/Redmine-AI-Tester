"""
session.py — 会话与历史记录管理

职责：
  - 保存每次分析/对话的记录（Issue ID、角色、时间、报告内容）
  - 提供历史列表查询
  - 支持加载历史记录继续对话

存储格式：JSON 文件，每条记录一个文件，存于 temp_md/sessions/
"""
import os, json
from datetime import datetime

SESSION_DIR = os.path.join("temp_md", "sessions")


class SessionManager:
    def __init__(self):
        os.makedirs(SESSION_DIR, exist_ok=True)

    def save(self, issue_id: str, role: str, session_type: str,
             content: str, history: list = None) -> str:
        """
        保存一条分析/对话记录。
        :param issue_id:    Issue ID
        :param role:        角色 key（qa / pm / dev）
        :param session_type: 'report' | 'chat'
        :param content:     报告内容或最终 AI 回复
        :param history:     多轮对话历史（仅 chat 类型需要）
        :return:            保存的文件路径
        """
        # TODO: 实现保存逻辑
        raise NotImplementedError

    def list_sessions(self, issue_id: str = None, role: str = None) -> list[dict]:
        """
        列出历史记录，支持按 issue_id / role 过滤。
        :return: 记录元信息列表，每条含 id / issue_id / role / type / created_at / file_path
        """
        # TODO: 实现列表查询逻辑
        raise NotImplementedError

    def load(self, session_id: str) -> dict:
        """
        加载指定历史记录。
        :return: 含 issue_id / role / content / history 的字典
        """
        # TODO: 实现加载逻辑
        raise NotImplementedError

    def delete(self, session_id: str) -> bool:
        """删除指定历史记录。"""
        # TODO: 实现删除逻辑
        raise NotImplementedError
