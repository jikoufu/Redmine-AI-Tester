"""
redmine_search.py — Redmine 实时关键字搜索

调用 Redmine /search.json API，返回精确关键字匹配的 Issue 列表。
适合：知道确切词汇，如接口名、错误码、功能模块名。
"""
import requests
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RedmineSearcher:
    def __init__(self, client):
        """
        :param client: RedmineClient 实例（复用其 url / headers 配置）
        """
        self.client = client

    def search(self, keyword: str, project_id: str = None, limit: int = 10) -> list[dict]:
        """
        关键字搜索 Redmine Issue。
        :param keyword:    搜索关键词
        :param project_id: 限定项目（None 表示全局搜索）
        :param limit:      返回结果数量上限
        :return:           Issue 列表，每条含 id / title / status / url
        """
        endpoint = f"{self.client.url}/search.json?q={keyword}&issues=1&limit={limit}"
        if project_id:
            endpoint += f"&scope=project&project_id={project_id}"
        try:
            resp = requests.get(endpoint, headers=self.client.headers, verify=False, timeout=10)
            if resp.status_code != 200:
                logger.warning("Redmine 搜索失败 HTTP %s", resp.status_code)
                return []
            results = resp.json().get("results", [])
            return [
                {
                    "id":     r.get("id"),
                    "title":  r.get("title", ""),
                    "status": r.get("status", ""),
                    "url":    r.get("url", ""),
                    "source": "redmine",
                }
                for r in results if r.get("type") == "issue"
            ]
        except Exception as e:
            logger.error("Redmine 搜索异常: %s", e)
            return []
