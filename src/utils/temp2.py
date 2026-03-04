import os
from redminelib import Redmine
from dotenv import load_dotenv

load_dotenv()


def test_connection():
    url = os.getenv("REDMINE_URL")
    key = os.getenv("REDMINE_KEY")

    print(f"📡 正在尝试连接: {url}")
    try:
        redmine = Redmine(url, key=key)
        # 尝试获取当前用户信息（这是最直接的鉴权测试）
        user = redmine.user.get('current')
        print(f"✅ 认证成功！当前用户: {user.firstname} {user.lastname}")

        # 尝试访问你输入的项目
        project_id = "dev-team-1"
        project = redmine.project.get(project_id)
        print(f"✅ 项目访问成功！项目名称: {project.name}")

    except Exception as e:
        print(f"❌ 认证失败！错误详情: {str(e)}")


if __name__ == "__main__":
    test_connection()