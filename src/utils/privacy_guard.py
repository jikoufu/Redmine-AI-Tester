"""
privacy_guard.py — 数据隐私脱敏模块

职责：在任何数据上送至外部 AI API 之前，进行强制性的本地脱敏处理。
所有规则均在本地执行，零数据外泄风险。

脱敏覆盖范围：
  - IPv4 / IPv6 地址
  - 数据库连接字符串（含账号密码）
  - 密码 / 密钥 / Token 字段
  - API Key（含常见厂商格式）
  - JWT Token
  - 邮箱地址
  - 中国大陆手机号
  - 中国居民身份证号
  - URL 中内嵌的认证凭据
  - 私有网段 IP（内网地址）
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ── 脱敏占位符统一定义（方便后续审计/替换） ──────────────────────────────
MASK = {
    "ip":         "[IP已脱敏]",
    "db":         "[数据库连接已脱敏]",
    "secret":     "[密钥已脱敏]",
    "apikey":     "[APIKey已脱敏]",
    "jwt":        "[JWT已脱敏]",
    "email":      "[邮箱已脱敏]",
    "phone":      "[手机号已脱敏]",
    "id_card":    "[证件号已脱敏]",
    "url_cred":   "[URL凭据已脱敏]",
}


@dataclass
class SanitizeResult:
    """脱敏结果，携带原文长度与命中规则统计，便于审计日志。"""
    sanitized_text: str
    original_length: int
    hit_rules: list = field(default_factory=list)

    @property
    def was_modified(self) -> bool:
        return bool(self.hit_rules)

    def summary(self) -> str:
        if not self.hit_rules:
            return "✅ 未检测到敏感信息"
        return f"🛡️ 已脱敏 {len(self.hit_rules)} 处: {', '.join(sorted(set(self.hit_rules)))}"


# ── 脱敏规则表（有序执行，优先级从高到低） ────────────────────────────────
# 格式：(规则名称, 正则表达式, 替换占位符)
_RULES: list[tuple[str, re.Pattern, str]] = []

def _rule(name: str, pattern: str, mask_key: str, flags=re.IGNORECASE):
    """注册一条脱敏规则"""
    _RULES.append((name, re.compile(pattern, flags), MASK[mask_key]))


# 1. 数据库连接字符串（最高优先级，防止账密泄露）
#    匹配：mysql://user:pass@host:port/db  /  jdbc:mysql://...  等
_rule("db_conn_string",
      r"(jdbc:|mysql|postgresql|mongodb|redis|oracle|sqlserver|mssql)"
      r"(://|:)[^\s\"'<>]{3,}",
      "db")

# 2. URL 内嵌凭据：https://user:password@host
_rule("url_credentials",
      r"https?://[^@\s]+:[^@\s]+@[^\s\"'<>]+",
      "url_cred")

# 3. JWT Token（三段式 base64，特征明显）
_rule("jwt_token",
      r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
      "jwt",
      flags=0)

# 4. 常见 API Key 格式
#    - 纯十六进制 32/40/64 位
#    - sk-xxxxxxxx (OpenAI/DeepSeek 风格)
#    - AKID / AKLT 开头 (腾讯云)
#    - LTAI 开头 (阿里云)
_rule("api_key_hex",
      r"\b[0-9a-fA-F]{32,64}\b",
      "apikey",
      flags=0)

_rule("api_key_sk",
      r"\bsk-[A-Za-z0-9]{20,}\b",
      "apikey",
      flags=0)

_rule("api_key_tencent",
      r"\b(AKID|AKLT)[A-Za-z0-9]{16,}\b",
      "apikey",
      flags=0)

_rule("api_key_aliyun",
      r"\bLTAI[A-Za-z0-9]{16,}\b",
      "apikey",
      flags=0)

# 5. 密码 / 密钥字段（key=value 格式，支持中英文字段名）
#    匹配：password=xxx / passwd: xxx / secret_key = xxx / api_key=xxx 等
_rule("secret_field",
      r"(password|passwd|secret|private_?key|api_?key|access_?key|auth_?token"
      r"|authorization|credentials?|密码|密钥|口令)"
      r"\s*[:=]\s*\S+",
      "secret")

# 6. IPv4 地址（含私有网段）
_rule("ipv4",
      r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b",
      "ip",
      flags=0)

# 7. IPv6 地址（简化匹配，覆盖标准格式与压缩格式）
_rule("ipv6",
      r"\b(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}\b",
      "ip",
      flags=0)

# 8. 邮箱地址
_rule("email",
      r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
      "email",
      flags=0)

# 9. 中国大陆手机号（1 开头 11 位，支持 +86 前缀）
_rule("cn_phone",
      r"(?:\+?86[-\s]?)?1[3-9]\d{9}\b",
      "phone",
      flags=0)

# 10. 中国居民身份证号（18 位，末位可为 X）
_rule("cn_id_card",
      r"\b[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b",
      "id_card",
      flags=0)


class PrivacyGuard:
    """
    隐私守卫：对任意文本执行全规则脱敏，返回 SanitizeResult。

    用法：
        guard = PrivacyGuard()
        result = guard.sanitize(raw_text)
        print(result.summary())
        clean_text = result.sanitized_text
    """

    def __init__(self, extra_keywords: Optional[list[str]] = None):
        """
        :param extra_keywords: 业务自定义的额外敏感词列表，精确全词匹配后替换为 [已脱敏]
        """
        self._extra_patterns: list[re.Pattern] = []
        if extra_keywords:
            for kw in extra_keywords:
                self._extra_patterns.append(
                    re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
                )

    def sanitize(self, text: str) -> SanitizeResult:
        """
        对输入文本执行完整脱敏流程。
        :param text: 待脱敏的原始文本
        :return: SanitizeResult（含脱敏后文本 + 命中规则统计）
        """
        if not text or not isinstance(text, str):
            return SanitizeResult(sanitized_text=text or "", original_length=0)

        original_length = len(text)
        hit_rules: list[str] = []
        result = text

        # 执行标准规则
        for rule_name, pattern, placeholder in _RULES:
            new_result, count = pattern.subn(placeholder, result)
            if count > 0:
                hit_rules.extend([rule_name] * count)
                result = new_result

        # 执行自定义业务敏感词
        for pattern in self._extra_patterns:
            new_result, count = pattern.subn("[已脱敏]", result)
            if count > 0:
                hit_rules.extend(["custom_keyword"] * count)
                result = new_result

        sanitize_result = SanitizeResult(
            sanitized_text=result,
            original_length=original_length,
            hit_rules=hit_rules,
        )

        # 记录审计日志（不含原文，只记录命中规则）
        if sanitize_result.was_modified:
            logger.warning(
                "🛡️ PrivacyGuard 拦截敏感信息 | 原文长度=%d | %s",
                original_length,
                sanitize_result.summary()
            )

        return sanitize_result

    def sanitize_text(self, text: str) -> str:
        """
        快捷方法：直接返回脱敏后的字符串（忽略统计信息）。
        """
        return self.sanitize(text).sanitized_text


# ── 模块级单例，供其他模块直接 import 使用 ─────────────────────────────────
_default_guard = PrivacyGuard()


def sanitize(text: str) -> str:
    """
    模块级快捷函数，使用默认守卫实例直接脱敏并返回字符串。

    示例：
        from src.privacy_guard import sanitize
        clean = sanitize(raw_content)
    """
    return _default_guard.sanitize_text(text)


def sanitize_with_report(text: str) -> SanitizeResult:
    """
    模块级快捷函数，返回完整脱敏报告（含命中规则统计）。
    """
    return _default_guard.sanitize(text)
