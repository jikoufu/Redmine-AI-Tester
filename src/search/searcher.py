"""
searcher.py — 搜索调度器

统一入口，支持三种模式：
  - redmine : 仅 Redmine 实时关键字搜索
  - vector  : 仅本地向量库语义搜索
  - combined: 两者同时搜索，结果合并去重（推荐）
"""
from src.search.redmine_search import RedmineSearcher
from src.search.vector_search  import VectorSearcher
from src.utils.logger import get_logger

logger = get_logger(__name__)


class Searcher:
    def __init__(self, client, vector_db):
        self.redmine = RedmineSearcher(client)
        self.vector  = VectorSearcher(vector_db)

    def search(self, keyword: str, mode: str = "combined",
               project_id: str = None, top_k: int = 5) -> dict:
        """
        执行搜索并返回结构化结果。
        :param keyword:    搜索词
        :param mode:       'redmine' | 'vector' | 'combined'
        :param project_id: Redmine 项目过滤（仅 redmine/combined 模式有效）
        :param top_k:      每个来源最多返回条数
        :return: { "redmine": [...], "vector": [...] }
        """
        redmine_results, vector_results = [], []

        if mode in ("redmine", "combined"):
            redmine_results = self.redmine.search(keyword, project_id, limit=top_k)

        if mode in ("vector", "combined"):
            vector_results = self.vector.search(keyword, top_k=top_k)

        # 去重：vector 结果中 id 与 redmine 重复的打上标记，不删除，展示时注明
        redmine_ids = {r["id"] for r in redmine_results}
        for r in vector_results:
            if r["id"] in redmine_ids:
                r["also_in_redmine"] = True

        return {"redmine": redmine_results, "vector": vector_results}
