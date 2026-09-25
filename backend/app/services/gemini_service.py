import os
from datetime import datetime
from app.core.config import settings

class GeminiCommentaryService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                print("Gemini API client initialized successfully.")
            except Exception as e:
                print(f"Failed to initialize Gemini Client: {e}")

    async def generate_commentary(
        self,
        attacker_code: str,
        defender_code: str,
        probability: float,
        factors: list,
        circuit_name: str,
    ) -> dict:
        timestamp = datetime.utcnow().strftime("%H:%M:%S UTC")
        prob_percent = int(probability * 100)

        prompt = f"""
F1 경기 전문 해설위원으로서, 입문자도 쉽고 직관적으로 이해할 수 있는 1~2문장의 짧은 실시간 레이스 해설을 작성해줘.

- 서킷: {circuit_name}
- 상황: {attacker_code} 드라이버가 앞선 {defender_code} 드라이버를 상대로 추월 시도 중
- 머신러닝 추월 예측 성공률: {prob_percent}%
- 주요 요인: {', '.join(factors)}

해설은 한국어로 흥미진진하면서도 데이터(타이어, DRS, 속도 등)에 기반하여 작성해줘.
        """.strip()

        if self.client:
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                if response and response.text:
                    return {
                        "text": response.text.strip(),
                        "generatedAt": timestamp,
                        "model": "Gemini 2.5 Flash",
                    }
            except Exception as e:
                print(f"Gemini API call exception: {e}")

        # Fallback intelligent commentary generator if API key is not provided
        fallback_text = (
            f"{attacker_code} 드라이버가 {defender_code} 드라이버의 턱밑까지 바짝 추격하며 "
            f"추월 성공 가능성이 {prob_percent}%에 달합니다! "
            f"({factors[0] if factors else 'DRS 슬립스트림 활성화'})"
        )

        return {
            "text": fallback_text,
            "generatedAt": timestamp,
            "model": "F1.GG AI Analytics Engine",
        }

gemini_commentary_service = GeminiCommentaryService()
