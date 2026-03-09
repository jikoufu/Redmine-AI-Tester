"""clipboard.py — 复制到系统剪贴板"""
import pyperclip


def copy(text: str):
    """复制文本到剪贴板，失败时静默处理"""
    try:
        pyperclip.copy(text)
    except Exception:
        pass  # 某些服务器环境无剪贴板，不影响主流程
