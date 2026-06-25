import re


class ResponseParser:
    _BLOCKLIST_KEYWORDS = [
        # Gambling / scam / promo patterns (observed corruption tokens)
        "娱乐城",
        "赌博",
        "赌",
        "博彩",
        "老虎机",
        "棋牌",
        "彩票",
        "投注",
        "赚钱",
        "affiliate",
        "casino",
        "bet",
        "porn",
        "sex",
        "av",
        "xxx",
        "adult",
        "test123",
        "qq",
        "wechat",
        "telegram",
        "whatsapp",
        "join now",
        "click here",
        "promotion",
        "offer",
        "bonus",
        "free money",
        "http://",
        "https://",
        "www.",
        # Observed injected garbage fragments
        "to=bio",
        "analysis",
        "commentary",
        "final",
        "json",
        "format=",
        "_色",
        "代理",
        "联系",
        "注册送",
        "日日",
        "无码",
        "下注",
        "开户",
        "娱乐",
        "平台",
        "彩票",
        "双色球",
        "百家乐",
    ]

    @staticmethod
    def _strip_non_latin(text: str) -> str:
        # Allow only safe ASCII characters
        return re.sub(r"[^A-Za-z0-9 .,!?\-\'\"():]", "", text)

    @classmethod
    def extract_text(cls, content: str) -> str:
        if not isinstance(content, str):
            return ""

        original = content
        cleaned = content

        # 1. Remove JSON-like fragments
        cleaned = re.sub(r"\{.*?\}", "", cleaned)

        # 2. Remove protocol-style tokens (to=..., format=...)
        cleaned = re.sub(r"\b\w+=\w+", "", cleaned)

        # 3. Remove explicit blocklisted keywords (case-insensitive)
        lowered = cleaned.lower()
        for keyword in cls._BLOCKLIST_KEYWORDS:
            if keyword.lower() in lowered:
                cleaned = re.sub(re.escape(keyword), "", cleaned, flags=re.IGNORECASE)
                lowered = cleaned.lower()

        # 4. Remove all non-Latin / non-ASCII characters aggressively
        cleaned = cls._strip_non_latin(cleaned)

        # 5. Collapse whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # 6. Sanity check: if too much content stripped, fallback
        if not cleaned:
            return "I didn't understand that - could you rephrase?"

        if len(cleaned) < max(5, int(0.1 * len(original))):
            return "I didn't understand that - could you rephrase?"

        return cleaned


# Local test
if __name__ == "__main__":
    test_input = (
        "User's name is Abhishek. to=bio 代理联系 commentary {\"name\":\"Abhishek\"}"
    )
    print(ResponseParser.extract_text(test_input))
