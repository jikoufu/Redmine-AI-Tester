"""
markdown_export.py — 导出为本地 Markdown 文件
"""
import os

OUTPUT_DIR = "temp_md"


def export_report(issue_id: str, role: str, content: str) -> str:
    """保存报告，返回文件路径"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"issue_{issue_id}_{role}_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def export_chat(issue_id: str, role: str, history: list) -> str:
    """保存对话记录，自动加序号避免覆盖，返回文件路径"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    idx = 1
    while True:
        path = os.path.join(OUTPUT_DIR, f"issue_{issue_id}_{role}_chat_{idx}.md")
        if not os.path.exists(path):
            break
        idx += 1
    lines = [f"# Issue #{issue_id} 对话记录\n"]
    for msg in history:
        label = "**🧑 你**" if msg["role"] == "user" else "**🤖 AI**"
        lines.append(f"{label}\n\n{msg['content']}\n\n---\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path
