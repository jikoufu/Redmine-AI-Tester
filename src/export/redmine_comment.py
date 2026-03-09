"""
redmine_comment.py — 报告回写到 Redmine 评论区（未实现）

计划功能：
  - 将 AI 生成的报告作为 Issue 评论回写到 Redmine
  - 调用 PUT /issues/:id.json，在 notes 字段中写入内容
  - 支持回写前预览确认，防止误操作
"""

def post_comment(client, issue_id: str, content: str) -> bool:
    """
    :param client:   RedmineClient 实例
    :param issue_id: 目标 Issue ID
    :param content:  要写入的评论内容
    :return:         是否成功
    """
    # TODO: 实现回写逻辑
    raise NotImplementedError("Redmine 评论回写功能开发中")
