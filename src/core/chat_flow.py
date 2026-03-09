"""
chat_flow.py — 自由多轮对话流程

流程：
  输入 Issue ID → 拉取数据 → 进入对话循环
  输入 save → 保存记录
  输入 q   → 返回主菜单
"""

def run(client, engine, exporter, session_mgr):
    issue_id = input("🔍 请输入要对话的 Issue ID: ").strip()
    if not issue_id:
        return

    is_deep = input("是否开启深度穿透模式？(y/n) [n]: ").strip().lower() == 'y'
    print(f"\n📡 正在获取 Issue #{issue_id} 数据...")
    issue_context = client.get_issue_detail(issue_id, deep_analysis=is_deep)
    if not issue_context:
        print(f"❌ 找不到 Issue #{issue_id}")
        return

    print(f"\n✅ 已加载，当前角色：{engine.role_label}")
    print("─" * 50)
    print("💡 输入任意指令开始对话，save 保存，q 退出")
    print("─" * 50)

    history = []
    while True:
        user_input = input("\n🧑 你: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ('q', 'exit', '退出'):
            print("↩️  返回主菜单。")
            break
        if user_input.lower() == 'save':
            exporter.export_chat(issue_id, engine.role, history)
            try:
                session_mgr.save(issue_id, engine.role, "chat", "", history)
            except NotImplementedError:
                pass
            continue

        print(f"\n🤖 [{engine.role_label}]: ", end="", flush=True)
        response = engine.free_chat(issue_context, user_input, history)
        if response:
            history.append({"role": "user",      "content": user_input})
            history.append({"role": "assistant",  "content": response})
