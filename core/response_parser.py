import re


class ResponseParser:
    @staticmethod
    def extract_text(content: str) -> str:
        if not isinstance(content, str):
            return ""

        cleaned = content

        # Remove inline tool tokens
        cleaned = re.sub(r"to=\w+", "", cleaned)
        cleaned = re.sub(r"\b(commentary|analysis|bio)\b", "", cleaned, flags=re.IGNORECASE)

        # Remove JSON fragments
        cleaned = re.sub(r"\{[^{}]*\}", "", cleaned)

        # Remove CJK / Thai ranges
        cleaned = re.sub(r"[\u4e00-\u9fff\u0e00-\u0e7f]+", "", cleaned)

        # Normalize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned


# Simple internal test
if __name__ == "__main__":
    test_input = (
        "User's name is abhix. to=bio commentary json {\"name\":\"abhix\"} 代理联系"
    )
    print(ResponseParser.extract_text(test_input))
