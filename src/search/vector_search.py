"""
vector_search.py — 本地向量库语义搜索

基于 FAISS 向量库进行语义相似度检索。
适合：描述模糊意图，如"支付失败相关问题"、"权限校验异常"。
"""
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VectorSearcher:
    def __init__(self, vector_db):
        """
        :param vector_db: 已加载的 FAISS VectorStore 实例，可以为 None
        """
        self.vector_db = vector_db

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        语义搜索。
        :param query: 自然语言查询
        :param top_k: 返回最相近的结果数量
        :return: 结果列表，每条含 id / content / score / source
        """
        if not self.vector_db:
            logger.warning("向量库未加载，无法进行语义搜索")
            return []
        try:
            docs_and_scores = self.vector_db.similarity_search_with_score(query, k=top_k)
            results = []
            for doc, score in docs_and_scores:
                similarity = round((1 - score) * 100, 1)  # 转换为相似度百分比
                results.append({
                    "id":         doc.metadata.get("id"),
                    "content":    doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "similarity": similarity,
                    "source":     "vector",
                })
            return results
        except Exception as e:
            logger.error("向量搜索异常: %s", e)
            return []
