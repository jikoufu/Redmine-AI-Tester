import os
import requests
from dotenv import load_dotenv
import urllib3

# 禁用不安全请求警告（针对公司内部未配置 SSL 证书的 Redmine 域名）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 加载 .env 配置文件中的环境变量
load_dotenv()


class RedmineClient:
    def __init__(self):
        """
        初始化客户端，从环境变量读取配置信息
        """
        # 基础 URL 处理，去除末尾可能存在的斜杠
        self.url = os.getenv("REDMINE_URL", "").rstrip('/')
        # 从环境变量获取 API Key (确保 .env 中 key 名为 REDMINE_API_KEY)
        self.key = os.getenv("REDMINE_API_KEY")

        if not self.key:
            print("❌ 警告：未在 .env 中找到 REDMINE_API_KEY，请检查变量名！")

        # 设置通用的请求头
        self.headers = {
            "X-Redmine-API-Key": self.key,
            "Content-Type": "application/json"
        }

    def get_issues_by_project(self, project_id=None, total_limit=1000):
        """
        全量/分页抓取指定项目下的 Issue
        :param project_id: Redmine 项目 ID，若为 None 则抓取全部可见项目
        :param total_limit: 总计抓取上限，默认 1000 条
        :return: 包含 issue 对象的列表
        """
        all_issues = []
        offset = 0
        page_size = 100  # Redmine 单页最大限制通常是 100

        print(f"🚀 开始全量同步 (目标: {total_limit} 条)...")

        try:
            while len(all_issues) < total_limit:
                # 构造分页请求 URL，开启 status_id=* 以抓取包括已关闭的所有状态
                endpoint = f"{self.url}/issues.json?status_id=*&limit={page_size}&offset={offset}&include=journals"
                if project_id:
                    endpoint += f"&project_id={project_id}"

                response = requests.get(endpoint, headers=self.headers, verify=False, timeout=15)

                if response.status_code != 200:
                    print(f"❌ 分页抓取中断 (HTTP {response.status_code})")
                    break

                data = response.json()
                current_issues = data.get('issues', [])

                if not current_issues:
                    print("✅ 已抓取所有可见数据。")
                    break

                all_issues.extend(current_issues)
                print(f"📥 已下载 {len(all_issues)} 条...")

                # 更新偏移量，准备抓下一页
                offset += page_size

                # 如果已返回的 Issue 总数少于总计数，说明抓完了
                if len(all_issues) >= data.get('total_count', 0):
                    break

            return all_issues[:total_limit]

        except Exception as e:
            print(f"❌ 翻页抓取异常: {str(e)}")
            return all_issues

    def get_issue_detail(self, issue_id, deep_analysis=False):
        """
        获取 Issue 详情，支持可选的穿透深度分析模式
        :param issue_id: Redmine Issue ID
        :param deep_analysis: 是否开启穿透模式（抓取关联任务详情）
        """
        # 1. 抓取主 Issue (包含关系列表 relations 和评论记录 journals)
        main_issue = self._fetch_single_full_data(issue_id)
        if not main_issue:
            return None

        # 初始化内容上下文，首先存入主任务信息
        header = f"【深度分析模式】" if deep_analysis else "【标准模式】"
        all_context = [f"=== 主任务 #{issue_id} {header} ===\n{self._format_issue_for_ai(main_issue)}"]

        # 2. 如果开启深度分析，且主任务有关联 Issue
        if deep_analysis:
            relations = main_issue.get('relations', [])
            if relations:
                print(f"🔗 发现 {len(relations)} 个关联项，正在进行深度穿透抓取...")
                for rel in relations:
                    # 获取关联的另一端 ID（避开当前 issue 自己的 ID）
                    rel_id = rel.get('issue_to_id') if rel.get('issue_id') == int(issue_id) else rel.get('issue_id')

                    # 递归/穿透抓取关联 Issue 的内容
                    rel_data = self._fetch_single_full_data(rel_id)
                    if rel_data:
                        all_context.append(f"=== 关联详情 #{rel_id} ===\n{self._format_issue_for_ai(rel_data)}")

        # 3. 合并文本返回。若为穿透模式，则包含主任务+所有关联详情。
        return "\n\n".join(all_context)

    def _fetch_single_full_data(self, issue_id):
        """
        内部私有方法：负责单条数据的网络请求
        """
        # include 参数确保返回评论记录 (journals) 和 关联关系 (relations)
        endpoint = f"{self.url}/issues/{issue_id}.json?include=journals,relations"
        try:
            resp = requests.get(endpoint, headers=self.headers, verify=False, timeout=5)
            return resp.json().get('issue') if resp.status_code == 200 else None
        except:
            return None

    def _format_issue_for_ai(self, issue):
        """
        内部私有方法：将复杂的 JSON 响应清洗为 AI 易读的 Markdown 文本结构
        """
        subject = issue.get('subject', '无标题')
        desc = issue.get('description', '（无描述内容）')
        status = issue.get('status', {}).get('name', '未知状态')

        # 提取并清洗评论记录
        journals = issue.get('journals', [])
        notes_list = []
        for j in journals:
            user_name = j.get('user', {}).get('name', '匿名用户')

            # --- 核心修复位置 ---
            # 使用 .get('notes') 获取值，如果为 None，则默认为空字符串 ''
            raw_note = j.get('notes')
            if raw_note is None:
                raw_note = ""

            note_content = raw_note.strip()
            # ------------------

            if note_content:
                notes_list.append(f"- {user_name}: {note_content}")

        notes_str = "\n".join(notes_list) if notes_list else "无相关讨论"

        return f"主题: {subject}\n状态: {status}\n描述: {desc}\n讨论记录:\n{notes_str}"