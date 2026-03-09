"""
exporter.py — 导出调度器

统一导出入口，协调 markdown_export 和 clipboard 两个子模块。
后续如需新增导出目标（如 Redmine 评论、钉钉消息），在此扩展。
"""
from src.export import markdown_export, clipboard


class Exporter:
    def export_report(self, issue_id: str, role: str, content: str):
        """保存报告文件并复制到剪贴板"""
        path = markdown_export.export_report(issue_id, role, content)
        clipboard.copy(content)
        print(f"\n{'─'*30}")
        print(f"✅ 报告已保存: {path}")
        print(f"📋 已复制到剪贴板")
        print(f"{'─'*30}")

    def export_chat(self, issue_id: str, role: str, history: list):
        """保存对话记录并复制最后一条 AI 回复到剪贴板"""
        if not history:
            print("⚠️  对话记录为空，无需保存。")
            return
        path = markdown_export.export_chat(issue_id, role, history)
        last_ai = next((m["content"] for m in reversed(history) if m["role"] == "assistant"), "")
        clipboard.copy(last_ai)
        print(f"\n✅ 对话记录已保存: {path}")
        print(f"📋 最后一条 AI 回复已复制到剪贴板")
