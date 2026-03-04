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


def fetch_full_issue_content(url, headers, issue_id, is_sub=False):
    """提取 Issue 的全量描述和评论"""
    prefix = "  [关联] " if is_sub else ""
    endpoint = f"{url}/issues/{issue_id}.json?include=journals"

    try:
        response = requests.get(endpoint, headers=headers, verify=False, timeout=10)
        if response.status_code != 200:
            return f"{prefix}❌ 无法获取 Issue #{issue_id}", []

        issue_data = response.json().get('issue', {})
        subject = safe_get(issue_data, 'subject', '无主题')
        description = safe_get(issue_data, 'description', '（无描述）')

        text_block = [
            f"{prefix}## {'🔗 关联' if is_sub else '🚀 主任务'} #{issue_id}: {subject}",
            f"{prefix}**状态**: {issue_data.get('status', {}).get('name')}\n",
            f"{prefix}### 📝 描述\n{description}\n"
        ]

        journals = issue_data.get('journals', [])
        notes_list = []
        for j in journals:
            note = safe_get(j, 'notes')
            if note:
                user = j.get('user', {}).get('name', '未知用户')
                date = safe_get(j, 'created_on')[:10]
                notes_list.append(f"{prefix}- **{user}** ({date}): {note}")

        if notes_list:
            text_block.append(f"{prefix}### 💬 历史讨论")
            text_block.extend(notes_list)

        relations = issue_data.get('relations', []) if not is_sub else []
        return "\n".join(text_block), relations
    except Exception as e:
        return f"{prefix}❌ 解析 #{issue_id} 出错: {str(e)}", []


def run_deep_report():
    url = os.getenv("REDMINE_URL", "").rstrip('/')
    key = os.getenv("REDMINE_API_KEY")
    headers = {"X-Redmine-API-Key": key}

    main_id = input("\n🔢 请输入主 Issue ID: ").strip()
    if not main_id: return

    # 1. 准备目录
    output_dir = "temp_md"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📂 已创建目录: {output_dir}")

    print(f"📡 开始深度抓取 #{main_id}...")

    # 2. 抓取内容
    main_text, relations = fetch_full_issue_content(url, headers, main_id)
    final_output = [f"# Redmine Issue 深度报告: #{main_id}\n", main_text]

    if relations:
        print(f"🔗 发现 {len(relations)} 个关联项，正在穿透...")
        final_output.append("\n" + "=" * 30 + "\n# 🔗 关联详情汇总\n" + "=" * 30)
        for rel in relations:
            rel_id = rel.get('issue_to_id') if rel.get('issue_id') == int(main_id) else rel.get('issue_id')
            print(f"  ↪️ 正在抓取 #{rel_id}...")
            rel_content, _ = fetch_full_issue_content(url, headers, rel_id, is_sub=True)
            final_output.append(rel_content)

    full_text = "\n\n".join(final_output)

    # 3. 写入文件
    file_name = f"issue_{main_id}.md"
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    # 4. 复制到剪贴板
    pyperclip.copy(full_text)

    print("\n" + "★" * 40)
    print(f"✅ 处理完成！")
    print(f"📝 文件已保存至: {file_path}")
    print(f"📋 内容已同步至剪贴板，可直接粘贴。")
    print("★" * 40)


if __name__ == "__main__":
    run_deep_report()