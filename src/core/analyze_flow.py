"""
analyze_flow.py — 分析流程

流程：
  输入 Issue ID → 选择穿透模式 → 拉取数据 → AI 生成报告 → 导出
"""

def run(client, engine, exporter, session_mgr):
    """
    :param client:      RedmineClient
    :param engine:      AIEngine
    :param exporter:    Exporter
    :param session_mgr: SessionManager
    """
    issue_id = input("🔍 请输入要分析的 Issue ID: ").strip()
    if not issue_id:
        return

    print("\n  [n] 标准模式：仅分析该 Issue 本身")
    print("  [y] 深度穿透：分析该 Issue 及所有关联任务")
    is_deep = input("是否开启深度穿透模式？(y/n) [n]: ").strip().lower() == 'y'

    print(f"📡 正在获取数据...")
    issue_context = client.get_issue_detail(issue_id, deep_analysis=is_deep)
    if not issue_context:
        print(f"❌ 找不到 Issue #{issue_id}")
        return

    print(f"🤖 [{engine.role_label}] 正在生成报告...\n")
    report = engine.generate_report(str(issue_context))

    if report:
        exporter.export_report(issue_id, engine.role, report)
        try:
            session_mgr.save(issue_id, engine.role, "report", report)
        except NotImplementedError:
            pass
