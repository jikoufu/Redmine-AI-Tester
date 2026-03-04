import os
import pyperclip
import requests
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()


def safe_get(data, key, default=""):
    """安全获取字段，确保返回的是字符串"""
    val = data.get(key)
    return str(val).strip() if val is not None else default


def get_issue_text_v2():
    url = os.getenv("REDMINE_URL", "").rstrip('/')
    key = os.getenv("REDMINE_API_KEY")

    issue_id = input("\n🔢 请输入要获取的 Issue ID: ").strip()
    if not issue_id: return

    endpoint = f"{url}/issues/{issue_id}.json?include=journals"
    headers = {"X-Redmine-API-Key": key}

    try:
        print(f"📡 正在抓取 #{issue_id}...")
        response = requests.get(endpoint, headers=headers, verify=False, timeout=10)

        if response.status_code == 200:
            issue_data = response.json().get('issue', {})

            # --- 提取核心信息 ---
            subject = safe_get(issue_data, 'subject', '无主题')
            description = safe_get(issue_data, 'description', '（该 Issue 无描述内容）')
            status = issue_data.get('status', {}).get('name', '未知状态')

            output = [
                f"=== ISSUE #{issue_id} ===",
                f"【主题】: {subject}",
                f"【状态】: {status}",
                f"【描述】: \n{description}\n",
                "=== 历史讨论与变更记录 ==="
            ]

            # --- 提取评论 (防御性循环) ---
            journals = issue_data.get('journals', [])
            valid_notes_count = 0

            for j in journals:
                # 只有当包含 notes 字段且内容不为空时才记录
                note_content = safe_get(j, 'notes')
                if note_content:
                    user_name = j.get('user', {}).get('name', '未知用户')
                    created_at = safe_get(j, 'created_on')[:10]
                    valid_notes_count += 1
                    output.append(f"[{valid_notes_count}] {user_name} ({created_at}):\n{note_content}\n")

            final_text = "\n".join(output)

            # 复制到剪贴板
            pyperclip.copy(final_text)

            print("=" * 40)
            # 预览前 300 字
            print(final_text[:300] + "..." if len(final_text) > 300 else final_text)
            print("=" * 40)
            print(f"✅ 提取成功！已过滤冗余信息，共提取 {valid_notes_count} 条有效评论。")
            print(f"📋 内容已复制，请前往 Web AI 粘贴。")

        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"内容: {response.text}")

    except Exception as e:
        # 打印详细错误位置
        import traceback
        print(f"❌ 运行异常!")
        traceback.print_exc()


if __name__ == "__main__":
    get_issue_text_v2()