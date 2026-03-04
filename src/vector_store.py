import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document


class VectorStoreManager:
    def __init__(self):
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY")
        )
        # 统一路径变量名为 db_path
        self.db_path = "index/redmine_faiss"

    def _format_issue_text(self, issue):
        """
        内部辅助方法：确保单条和全量同步的格式完全统一
        """
        i_id = issue.get('id', 'N/A')
        subject = issue.get('subject', '')
        description = issue.get('description', '') or ''

        # 提取评论
        journals = issue.get('journals', [])
        comments = " ".join([j.get('notes', '') for j in journals if j.get('notes')])

        # 保持与全量同步一致的【关键强化格式】
        full_text = f"【ISSUE_ID: {i_id}】\n主题: {subject}\n描述: {description}\n讨论: {comments}"

        # 长度截断处理
        if len(full_text) > 2000:
            full_text = full_text[:2000] + "... [内容过长已截断]"

        return full_text, i_id

    def init_database(self, issues_data):
        """将 Redmine 数据转换为向量索引"""
        docs = []
        for issue in issues_data:
            full_text, i_id = self._format_issue_text(issue)
            if full_text.strip():
                docs.append(Document(page_content=full_text, metadata={"id": i_id}))

        if not docs:
            print("⚠️ 未发现有效数据，无法建立索引。")
            return None

        try:
            vector_db = FAISS.from_documents(docs, self.embeddings)
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            vector_db.save_local(self.db_path)
            print(f"✅ 成功建立索引，共处理 {len(docs)} 条 Issue。")
            return vector_db
        except Exception as e:
            print(f"❌ 建立索引失败: {str(e)}")
            return None

    def load_db(self):
        """加载本地数据库"""
        if os.path.exists(os.path.join(self.db_path, "index.faiss")):
            try:
                return FAISS.load_local(
                    self.db_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"⚠️ 加载失败: {e}")
        return None

    def add_single_issue(self, issue):
        """将单个 Issue 转换为向量并入现有库（点名同步）"""
        # 1. 加载现有库
        vector_db = self.load_db()

        # 2. 使用统一的格式构造数据
        full_text, i_id = self._format_issue_text(issue)
        new_doc = Document(page_content=full_text, metadata={"id": i_id})

        if vector_db:
            print(f"🧬 正在将 #{i_id} 向量化并入库...")
            # 3. 增量添加
            vector_db.add_documents([new_doc])
            # 修正处：使用正确的 self.db_path
            vector_db.save_local(self.db_path)
            return vector_db
        else:
            print("💡 本地库不存在，将以该 Issue 初始化。")
            return self.init_database([issue])