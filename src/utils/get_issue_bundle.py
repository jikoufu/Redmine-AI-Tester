import os
import pyperclip
import requests
from dotenv import load_dotenv
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()


class RedmineUltimateCrawler:
    def __init__(self):
        self.url = os.getenv("REDMINE_URL", "").rstrip('/')
        self.key = os.getenv("REDMINE_API_KEY")
        self.headers = {"X-Redmine-API-Key": self.key}

    def get_full_issue_detail(self, issue_id, prefix="  "):
        """抓取一个 Issue 的所有文字信息：描述 + 评论"""
        # 增加 include=journals 抓取评论
        endpoint = f"{self.url}/issues/{issue_id}.json?include=journals"
        try:
            resp = requests.get(endpoint, headers=self.headers, verify=False, timeout=5)
            if resp.status_code == 200:
                data = resp.json().get('issue', {})
                subject = data.get('subject', '无主题')
                desc = data.get('description', '（无描述）')

                content = [
                    f"{prefix}📌 [Issue #{issue_id}] {subject}",
                    f"{prefix}内容正文:\n{desc}\n"
                ]

                # 抓取并提取该 Issue 的评论
                journals = data.get('journals', [])
                valid_notes = [j.get('notes').strip() for j in journals if j.get('notes')]
                if valid_notes:
                    content.append(f"{prefix}💬 重要补充/评论:")
                    for idx, note in enumerate(valid_notes):
                        content.append(f"{prefix}  {idx + 1}. {note}")

                return "\n".join(content) + f"\n{prefix}" + "-" * 40
        except:
            return f"{prefix}❌ [Issue #{issue_id}] 抓取详情失败"
        return None

    def run(self):
        issue_id = input("\n🔢 请输入主任务 ID (如 90911): ").strip()
        if not issue_id: return

        # 1. 抓取主 Issue，同时包含关系、子任务和评论
        print(f"📡 正在深度解析主任务 #{issue_id}...")
        # 注意这里增加了 children
        endpoint = f"{self.url}/issues/{issue_id}.json?include=relations,journals,children"

        try:
            response = requests.get(endpoint, headers=self.headers, verify=False)
            main_data = response.json().get('issue', {})

            output = [
                f"=== 🧩 主任务核心背景 #{issue_id} ===",
                f"主题: {main_data.get('subject')}",
                f"描述: {main_data.get('description') or '见下方关联内容'}\n"
            ]

            # 2. 处理子任务 (Children)
            children = main_data.get('children', [])
            if children:
                output.append("=== 👶 发现子任务 (Sub-tasks) ===")
                for child in children:
                    c_id = child.get('id')
                    print(f"  ↪️ 正在同步子任务 #{c_id}...")
                    output.append(self.get_full_issue_detail(c_id, prefix="    "))

            # 3. 处理关联任务 (Relations)
            relations = main_data.get('relations', [])
            if relations:
                output.append("=== 🔗 发现关联详情 (Related Issues) ===")
                for rel in relations:
                    rel_id = rel.get('issue_to_id') if rel.get('issue_id') == int(issue_id) else rel.get('issue_id')
                    print(f"  ↪️ 正在同步关联项 #{rel_id}...")
                    output.append(self.get_full_issue_detail(rel_id, prefix="    "))

            # 4. 主任务自己的评论
            output.append("\n=== 📢 主任务讨论记录 ===")
            for j in main_data.get('journals', []):
                if j.get('notes'):
                    output.append(f"[{j.get('user', {}).get('name')}]: {j.get('notes')}")

            final_text = "\n".join(output)
            pyperclip.copy(final_text)

            print(f"\n✅ 深度同步完成！")
            print(f"📊 数据包含：主描述 + {len(children)}个子任务详情 + {len(relations)}个关联任务详情。")
            print(f"📋 已经全量复制，请去 Web AI 粘贴。")

        except Exception as e:
            print(f"❌ 运行失败: {str(e)}")


if __name__ == "__main__":
    RedmineUltimateCrawler().run()