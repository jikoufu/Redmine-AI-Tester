"""
main.py — 程序入口（函数式风格）

设计原则：
  - 每个菜单项对应一个纯函数，输入明确，输出明确
  - 状态（vector_db、engine、client）通过参数显式传递，不使用全局变量
  - 副作用（IO、网络、文件写入）集中在各 flow 模块，main 只做调度
  - 用 dispatch_table 替代 if/elif 链，新增菜单项只需加一行
"""

import os
from dotenv import load_dotenv

from src.core.ai_engine       import AIEngine, select_role
from src.sync.redmine_client  import RedmineClient
from src.sync.vector_store    import VectorStoreManager
from src.search.searcher      import Searcher
from src.export.exporter      import Exporter
from src.core.session         import SessionManager

load_dotenv()


# ── 初始化 ────────────────────────────────────────────────────────────────────

def init_components(role: str) -> dict:
    """
    初始化所有核心组件，返回 app_state 字典。
    所有状态集中在此处，后续通过参数传递，不使用全局变量。
    """
    client    = RedmineClient()
    v_manager = VectorStoreManager()
    vector_db = v_manager.load_db()

    print("✅ 本地索引加载成功。" if vector_db else "⚠️  未发现本地索引，请先执行选项 1 同步数据。")

    return {
        "client":      client,
        "engine":      AIEngine(role=role),
        "v_manager":   v_manager,
        "vector_db":   vector_db,
        "exporter":    Exporter(),
        "session_mgr": SessionManager(),
    }


# ── 菜单渲染 ──────────────────────────────────────────────────────────────────

def render_menu(engine: AIEngine) -> None:
    print(f"\n{'='*16} Redmine AI 助手  [{engine.role_label}] {'='*16}")
    print("1. [同步]     数据同步（全量 / 增量）")
    print("2. [搜索]     关键字 / 语义 / 联合搜索")
    print("3. [分析]     生成 Issue 角色报告")
    print("4. [对话]     基于 Issue 的自由多轮对话")
    print("5. [历史]     查看 / 继续历史分析记录")
    print("6. [批量]     多 Issue 汇总分析报告")
    print("7. [切换角色] 切换当前分析视角")
    print("q. 退出")


# ── 各菜单项处理函数 ──────────────────────────────────────────────────────────

def handle_sync(state: dict) -> dict:
    """选项 1：数据同步，返回更新后的 state"""
    from src.sync import sync_flow
    new_vector_db = sync_flow.run(state["client"], state["v_manager"], state["vector_db"])
    return {
        **state,
        "vector_db": new_vector_db,
        "searcher":  build_searcher(state["client"], new_vector_db),
    }


def handle_search(state: dict) -> dict:
    """选项 2：搜索 Issue"""
    from src.search import search_flow
    search_flow.run(state["searcher"], state["engine"], state["client"])
    return state


def handle_analyze(state: dict) -> dict:
    """选项 3：生成分析报告"""
    from src.core import analyze_flow
    analyze_flow.run(state["client"], state["engine"], state["exporter"], state["session_mgr"])
    return state


def handle_chat(state: dict) -> dict:
    """选项 4：自由多轮对话"""
    from src.core import chat_flow
    chat_flow.run(state["client"], state["engine"], state["exporter"], state["session_mgr"])
    return state


def handle_history(state: dict) -> dict:
    """选项 5：历史记录"""
    from src.core import history_flow
    history_flow.run(state["session_mgr"], state["engine"], state["client"])
    return state


def handle_batch(state: dict) -> dict:
    """选项 6：批量分析"""
    from src.core import batch_flow
    batch_flow.run(state["client"], state["engine"], state["exporter"], state["session_mgr"])
    return state


def handle_switch_role(state: dict) -> dict:
    """选项 7：切换角色，返回更新了 engine 的新 state"""
    new_role = select_role()
    state["engine"].set_role(new_role)
    return state


# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def build_searcher(client: RedmineClient, vector_db) -> Searcher:
    """构造 Searcher，vector_db 可以为 None（降级为仅 Redmine 搜索）"""
    return Searcher(client=client, vector_db=vector_db)


def build_dispatch_table() -> dict:
    """
    构建菜单调度表：{ 选项字符 -> 处理函数 }
    新增菜单项只需在此加一行，无需修改主循环。
    """
    return {
        "1": handle_sync,
        "2": handle_search,
        "3": handle_analyze,
        "4": handle_chat,
        "5": handle_history,
        "6": handle_batch,
        "7": handle_switch_role,
    }


def ensure_dirs(dirs: list[str]) -> None:
    """确保必要目录存在"""
    for d in dirs:
        os.makedirs(d, exist_ok=True)


# ── 主循环 ────────────────────────────────────────────────────────────────────

def run(state: dict, dispatch: dict) -> None:
    """
    主事件循环（尾递归改迭代）。
    state 不可变原则：每次操作返回新 state，原 state 不修改。
    """
    while True:
        render_menu(state["engine"])
        choice = input("请选择操作: ").strip().lower()

        if choice == 'q':
            print("👋 再见！")
            break

        handler = dispatch.get(choice)
        if handler:
            state = handler(state)
        else:
            print("⚠️  无效选项，请重新输入。")


# ── 入口 ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ensure_dirs(["index", "temp_md", "logs"])

    role     = select_role()
    state    = init_components(role)
    state    = {**state, "searcher": build_searcher(state["client"], state["vector_db"])}
    dispatch = build_dispatch_table()

    run(state, dispatch)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 程序已被用户强制中断。")