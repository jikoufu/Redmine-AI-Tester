"""
sync_flow.py — 数据同步交互流程

菜单：
  1. 全量同步（重建索引）
  2. 增量同步（点名同步指定 Issue）
"""

def run(client, v_manager, vector_db):
    """
    :return: 更新后的 vector_db 实例
    """
    print("\n同步模式：")
    print("  1. 全量同步（重建本地索引）")
    print("  2. 增量同步（更新指定 Issue）")
    sub = input("请选择 [默认 1]: ").strip() or "1"

    if sub == "1":
        vector_db = _full_sync(client, v_manager, vector_db)
    elif sub == "2":
        vector_db = _incremental_sync(client, v_manager, vector_db)

    return vector_db


def _full_sync(client, v_manager, vector_db):
    project_id  = input("Project ID（同步全部请直接回车）: ").strip()
    limit_input = input("Issue 数量上限（默认 100）: ").strip()
    try:
        total_limit = int(limit_input) if limit_input else 100
    except ValueError:
        total_limit = 100

    if vector_db:
        confirm = input(f"⚠️  全量同步 {total_limit} 条将重建索引，确认继续？(y/n): ").lower()
        if confirm != 'y':
            return vector_db

    print("🚀 正在从 Redmine 获取数据...")
    issues = client.get_issues_by_project(project_id or None, total_limit=total_limit)
    if issues:
        print(f"📦 抓取完成（{len(issues)} 条），正在构建向量库...")
        vector_db = v_manager.init_database(issues)
        if vector_db:
            print("✅ 全量同步完成。")
    else:
        print("❌ 未获取到数据，请检查网络或 Project ID。")
    return vector_db


def _incremental_sync(client, v_manager, vector_db):
    issue_id = input("🎯 请输入要同步的 Issue ID: ").strip()
    if not issue_id:
        return vector_db
    print(f"📡 正在获取 #{issue_id} 最新数据...")
    issue_raw = client._fetch_single_full_data(issue_id)
    if issue_raw:
        vector_db = v_manager.add_single_issue(issue_raw)
        print(f"✅ Issue #{issue_id} 已同步入库。")
    else:
        print("❌ 抓取失败，请确认 ID 是否存在。")
    return vector_db
