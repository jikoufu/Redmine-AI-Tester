"""
base.py — 角色基类

所有角色继承 BaseRole，至少实现：
  - label            : 显示名称
  - description      : 菜单说明
  - system_prompt    : 报告生成 Prompt
  - free_chat_role   : 自由对话角色描述
"""
from abc import ABC, abstractmethod

class BaseRole(ABC):

    @property
    @abstractmethod
    def key(self) -> str:
        """角色唯一标识，例如 'qa'"""

    @property
    @abstractmethod
    def label(self) -> str:
        """菜单展示名称，例如 '🧪 测试开发工程师'"""

    @property
    @abstractmethod
    def description(self) -> str:
        """角色一句话说明"""

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """报告生成时使用的完整 System Prompt"""

    @property
    @abstractmethod
    def free_chat_role(self) -> str:
        """自由对话时的角色定位描述（一句话）"""
