import os
import pyperclip
from dotenv import load_dotenv
from src.redmine_client import RedmineClient
from src.ai_engine import AIEngine
from src.vector_store import VectorStoreManager

# 加载 .env 环境变量（API Key, URL 等）
load_dotenv()


def run_helper():
    """
    主程序入口：控制台交互逻辑
    """
    # 1. 初始化核心组件
    client = RedmineClient()  # 负责与 Redmine API 通讯
    engine = AIEngine()  # 负责调用大模型 (DeepSeek)
    v_manager = VectorStoreManager()  # 负责本地向量库 (FAISS) 操作

    # 2. 启动时尝试加载本地已有的向量库索引
    vector_db = v_manager.load_db()

    while True:
        print("\n" + "=" * 20 + " Redmine AI 助手 (测开增强版) " + "=" * 20)
        print("1. [同步] 抓取全量数据并建立索引 (支持分页)")
        print("2. [分析] 针对特定 Issue 生成测开报告 (可选穿透模式)")
        print("3. [咨询] 全局项目/API 咨询 (带上下文检索)")
        print("4. [点名同步] 将特定 ID 的 Issue 强制更新到向量库")
        print("q. 退出")

        choice = input("请选择操作: ").strip().lower()

        if choice == 'q':
            print("👋 再见！程序已安全退出。")
            break

        # --- 选项 1: 全量数据同步 ---
        if choice == '1':
            project_id = input("请输入 Project ID (同步全部请直接回车): ").strip()
            limit_input = input("请输入需要同步的 Issue 数量 (默认 100): ").strip()
            try:
                total_limit = int(limit_input) if limit_input else 100
            except ValueError:
                total_limit = 100

            # 风险提示：如果本地已有库，全量同步通常会消耗较多 Token
            if vector_db:
                confirm = input(f"⚠️ 全量同步 {total_limit} 条数据将消耗 Token，确认继续？(y/n): ").lower()
                if confirm != 'y': continue

            print(f"🚀 正在从 Redmine 获取数据...")
            issues = client.get_issues_by_project(project_id, total_limit=total_limit)

            if issues:
                print(f"📦 抓取完成，正在构建向量库 (共 {len(issues)} 条)...")
                vector_db = v_manager.init_database(issues)
                if vector_db:
                    print(f"✅ 同步完成！本地索引已保存至 index/ 目录。")
            else:
                print("❌ 未获取到数据，请检查网络或 Project ID。")

        # --- 选项 2: 深度测开分析报告 (核心功能) ---
        elif choice == '2':
            issue_id = input("🔍 请输入要分析的 Issue ID: ").strip()
            if not issue_id: continue

            # --- 新增：用户自主选择是否开启穿透分析 ---
            print("\n模式选择：")
            print("  [n] 标准模式：仅分析该 Issue 本身 (更省 Token, 速度快)")
            print("  [y] 深度穿透：分析该 Issue 及其所有【关联任务】详情 (更全面, 消耗较多)")
            mode = input("是否开启深度穿透模式？(y/n) [n]: ").strip().lower()
            is_deep = True if mode == 'y' else False

            print(f"📡 正在获取数据 (深度模式: {'开启' if is_deep else '关闭'})...")
            # 这里的 get_issue_detail 已经支持 deep_analysis 参数
            issue_context = client.get_issue_detail(issue_id, deep_analysis=is_deep)

            if issue_context:
                print("🤖 AI 正在生成测开专家报告（流式输出中）...\n")

                # 调用 AI 引擎生成报告内容
                report_content = engine.generate_test_cases(str(issue_context))

                if report_content:
                    # 自动保存为 Markdown 文件，方便团队分享
                    output_dir = "temp_md"
                    os.makedirs(output_dir, exist_ok=True)
                    file_name = f"issue_{issue_id}_report.md"
                    file_path = os.path.join(output_dir, file_name)

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(report_content)

                    # 同步到剪贴板，方便直接粘贴到钉钉/企业微信或 Redmine 评论
                    pyperclip.copy(report_content)

                    print(f"\n" + "-" * 30)
                    print(f"✅ 报告生成成功！")
                    print(f"📝 存档路径: {file_path}")
                    print(f"📋 内容已自动复制到剪贴板。")
                    print("-" * 30)
            else:
                print(f"❌ 找不到 Issue #{issue_id}，请确认 ID 是否存在。")

        # --- 选项 3: 基于本地库的全局咨询 (RAG) ---
        elif choice == '3':
            if not vector_db:
                print("❌ 错误：本地库为空，请先执行选项 1 同步数据！")
                continue

            query = input("🔍 咨询关于项目或 API 的问题: ")
            # 在向量库中检索最相关的 3 条上下文
            docs = vector_db.similarity_search(query, k=3)

            context_list = [f"--- 参考数据 ---\n{d.page_content}" for d in docs]
            full_context = "\n\n".join(context_list)

            print("🤖 AI 正在结合本地 Issue 库进行检索回答...\n")
            engine.simple_query(query, full_context)

        # --- 选项 4: 点名同步 (增量更新) ---
        elif choice == '4':
            issue_id = input("🎯 请输入要强制同步入库的 Issue ID: ").strip()
            if not issue_id: continue

            print(f"📡 正在获取 #{issue_id} 的最新状态...")
            # 注意：同步入库通常建议用标准模式，保持向量库格式整齐
            issue_raw = client._fetch_single_full_data(issue_id)

            if issue_raw:
                # add_single_issue 方法会自动保存索引到本地
                vector_db = v_manager.add_single_issue(issue_raw)
                print(f"✅ Issue #{issue_id} 已成功并入本地向量库！")
            else:
                print(f"❌ 抓取失败，无法同步该 ID。")


if __name__ == "__main__":
    # 程序启动前，确保必要的目录存在
    os.makedirs("index", exist_ok=True)
    os.makedirs("temp_md", exist_ok=True)

    try:
        run_helper()
    except KeyboardInterrupt:
        print("\n👋 程序已被用户强制中断。")