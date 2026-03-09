import os
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import urllib3
from src.utils.privacy_guard import sanitize

# 禁用不安全请求警告（针对公司内部未配置 SSL 证书的 Redmine 域名）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

logger = logging.getLogger(__name__)


class RedmineClient:
    def __init__(self):
        """
        初始化客户端，从环境变量读取配置信息
        """
        self.url = os.getenv("REDMINE_URL", "").rstrip('/')
        self.key = os.getenv("REDMINE_API_KEY")

        if not self.key:
            logger.error("未在 .env 中找到 REDMINE_API_KEY，请检查变量名！")
            print("❌ 警告：未在 .env 中找到 REDMINE_API_KEY，请检查变量名！")

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
        page_size = 100

        print(f"🚀 开始全量同步 (目标: {total_limit} 条)...")

        try:
            while len(all_issues) < total_limit:
                endpoint = (
                    f"{self.url}/issues.json"
                    f"?status_id=*&limit={page_size}&offset={offset}&include=journals"
                )
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

                offset += page_size

                if len(all_issues) >= data.get('total_count', 0):
                    break

            return all_issues[:total_limit]

        except Exception as e:
            logger.error("翻页抓取异常: %s", str(e))
            print(f"❌ 翻页抓取异常: {str(e)}")
            return all_issues

    def get_issue_detail(self, issue_id, deep_analysis=False):
        """
        获取 Issue 详情，支持可选的穿透深度分析模式。
        返回的文本已经过隐私脱敏处理。

        :param issue_id: Redmine Issue ID
        :param deep_analysis: 是否开启穿透模式（抓取关联任务详情，并发执行）
        """
        main_issue = self._fetch_single_full_data(issue_id)
        if not main_issue:
            return None

        header = "【深度分析模式】" if deep_analysis else "【标准模式】"

        # ✅ 对主任务格式化结果做隐私脱敏
        main_formatted = self._format_issue_for_ai(main_issue)
        all_context = [f"=== 主任务 #{issue_id} {header} ===\n{main_formatted}"]

        # 深度穿透：并发拉取所有关联任务
        if deep_analysis:
            relations = main_issue.get('relations', [])
            if relations:
                print(f"🔗 发现 {len(relations)} 个关联项，正在并发穿透抓取...")

                # 计算各关联 Issue 的 ID（排除自身）
                rel_ids = [
                    rel.get('issue_to_id') if rel.get('issue_id') == int(issue_id)
                    else rel.get('issue_id')
                    for rel in relations
                    if rel.get('issue_to_id') or rel.get('issue_id')
                ]

                # 并发拉取（最多 5 个线程，避免对 Redmine 服务端造成压力）
                with ThreadPoolExecutor(max_workers=5) as executor:
                    future_map = {
                        executor.submit(self._fetch_single_full_data, rid): rid
                        for rid in rel_ids if rid != int(issue_id)
                    }
                    for future in as_completed(future_map):
                        rid = future_map[future]
                        try:
                            rel_data = future.result()
                            if rel_data:
                                # ✅ 关联任务同样脱敏处理
                                rel_formatted = self._format_issue_for_ai(rel_data)
                                all_context.append(f"=== 关联详情 #{rid} ===\n{rel_formatted}")
                        except Exception as e:
                            logger.warning("关联 Issue #%s 抓取失败: %s", rid, str(e))
                            print(f"⚠️ 关联 Issue #{rid} 抓取失败: {e}")

        return "\n\n".join(all_context)

    def _fetch_single_full_data(self, issue_id):
        """
        内部私有方法：负责单条数据的网络请求。
        返回原始 JSON dict，不做脱敏（脱敏在格式化层统一处理）。
        """
        endpoint = f"{self.url}/issues/{issue_id}.json?include=journals,relations"
        try:
            resp = requests.get(endpoint, headers=self.headers, verify=False, timeout=5)
            if resp.status_code == 200:
                return resp.json().get('issue')
            else:
                logger.warning("获取 Issue #%s 失败，HTTP %s", issue_id, resp.status_code)
                return None
        except Exception as e:
            logger.warning("获取 Issue #%s 网络异常: %s", issue_id, str(e))
            return None

    def _format_issue_for_ai(self, issue) -> str:
        """
        内部私有方法：将原始 JSON 清洗为 AI 易读的文本结构。

        【隐私保护】此处为格式化层的脱敏屏障：
          - 对 subject / description / notes 分别脱敏后再拼接
          - 确保拼合后的完整文本再做一次全局兜底脱敏
          - 双重保护，防止字段拼接后产生新的敏感信息组合
        """
        # 字段级脱敏（第一道屏障）
        subject = sanitize(issue.get('subject', '无标题'))
        desc    = sanitize(issue.get('description', '（无描述内容）') or '（无描述内容）')
        status  = issue.get('status', {}).get('name', '未知状态')  # 状态名无需脱敏

        # 提取并清洗评论记录
        journals = issue.get('journals', [])
        notes_list = []
        for j in journals:
            user_name = j.get('user', {}).get('name', '匿名用户')
            raw_note = (j.get('notes') or '').strip()
            if raw_note:
                # 每条评论内容单独脱敏（第一道屏障）
                safe_note = sanitize(raw_note)
                notes_list.append(f"- {user_name}: {safe_note}")

        notes_str = "\n".join(notes_list) if notes_list else "无相关讨论"

        # 拼接完整文本
        full_text = (
            f"主题: {subject}\n"
            f"状态: {status}\n"
            f"描述: {desc}\n"
            f"讨论记录:\n{notes_str}"
        )

        # 全局兜底脱敏（第二道屏障：防止字段拼合后的组合泄露）
        return sanitize(full_text)
