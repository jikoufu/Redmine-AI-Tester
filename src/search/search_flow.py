"""
search_flow.py — 搜索交互流程

流程：
  输入关键字 → 选择搜索模式 → 展示结果 → 选择 Issue 直接跳转分析或对话
"""
from src.core import analyze_flow, chat_flow


def run(searcher, engine, client):
    keyword = input("🔍 请输入搜索关键字: ").strip()
    if not keyword:
        return

    print("\n搜索模式：")
    print("  1. 联合搜索（Redmine + 向量库，推荐）")
    print("  2. 仅 Redmine 实时搜索（精确关键字）")
    print("  3. 仅向量库语义搜索（模糊意图）")
    mode_map = {"1": "combined", "2": "redmine", "3": "vector"}
    mode_input = input("请选择 [默认 1]: ").strip() or "1"
    mode = mode_map.get(mode_input, "combined")

    project_id = input("限定项目 ID（留空表示全局）: ").strip() or None

    print(f"\n🔎 正在搜索 [{mode}] 模式...")
    results = searcher.search(keyword, mode=mode, project_id=project_id)

    _display_results(results)

    # 搜索后直接选 ID 跳转，无需回主菜单
    while True:
        action = input("\n输入 Issue ID 进行操作，或回车返回主菜单: ").strip()
        if not action:
            break
        print("\n  a. 生成分析报告")
        print("  b. 进入自由对话")
        sub = input("请选择 (a/b): ").strip().lower()
        if sub == 'a':
            # 复用 analyze_flow，但直接传入 issue_id 跳过输入步骤
            _direct_analyze(action, client, engine)
        elif sub == 'b':
            _direct_chat(action, client, engine)


def _display_results(results: dict):
    redmine = results.get("redmine", [])
    vector  = results.get("vector",  [])

    if redmine:
        print(f"\n{'━'*10} Redmine 实时结果（{len(redmine)} 条）{'━'*10}")
        for r in redmine:
            print(f"  #{r['id']:>6}  [{r.get('status','')}]  {r['title']}")
    else:
        print("\n  Redmine：无匹配结果")

    if vector:
        print(f"\n{'━'*10} 向量库语义结果（{len(vector)} 条）{'━'*10}")
        for r in vector:
            tag = "（Redmine 中也存在）" if r.get("also_in_redmine") else ""
            print(f"  #{r['id']:>6}  相似度 {r.get('similarity', '?')}%  {tag}")
            print(f"           {r['content'][:80]}...")
    else:
        print("\n  向量库：无匹配结果")


def _direct_analyze(issue_id: str, client, engine):
    """跳过输入步骤，直接分析指定 Issue"""
    is_deep = input("是否开启深度穿透？(y/n) [n]: ").strip().lower() == 'y'
    issue_context = client.get_issue_detail(issue_id, deep_analysis=is_deep)
    if not issue_context:
        print(f"❌ 找不到 Issue #{issue_id}")
        return
    print(f"\n🤖 [{engine.role_label}] 正在生成报告...\n")
    from src.export.exporter import Exporter
    report = engine.generate_report(str(issue_context))
    if report:
        Exporter().export_report(issue_id, engine.role, report)


def _direct_chat(issue_id: str, client, engine):
    """跳过输入步骤，直接进入指定 Issue 对话"""
    is_deep = input("是否开启深度穿透？(y/n) [n]: ").strip().lower() == 'y'
    issue_context = client.get_issue_detail(issue_id, deep_analysis=is_deep)
    if not issue_context:
        print(f"❌ 找不到 Issue #{issue_id}")
        return
    print(f"\n✅ 已加载 Issue #{issue_id}，进入对话...")
    history = []
    from src.export.exporter import Exporter
    exporter = Exporter()
    while True:
        user_input = input("\n🧑 你: ").strip()
        if not user_input or user_input.lower() in ('q', 'exit'):
            break
        if user_input.lower() == 'save':
            exporter.export_chat(issue_id, engine.role, history)
            continue
        print(f"\n🤖 [{engine.role_label}]: ", end="", flush=True)
        response = engine.free_chat(issue_context, user_input, history)
        if response:
            history.append({"role": "user",     "content": user_input})
            history.append({"role": "assistant", "content": response})
