# app.py
# Streamlit + Gemini(google-genai)로 "커플 싸움 판독기" 만들기
#
# 필요 패키지:
#   pip install streamlit google-genai
#
# .streamlit/secrets.toml 예시:
#   GEMINI_API_KEY="YOUR_API_KEY"

import json
import re
from typing import Optional, Tuple

import streamlit as st
from google import genai
from google.genai import types

# ----------------------------
# 설정
# ----------------------------
st.set_page_config(
    page_title="커플 싸움 판독기",
    page_icon="⚖️",
    layout="centered",
)

SYSTEM_PROMPT = "너는 커플 싸움 판독기야. 이 대화를 보고 남녀 과실 비율과 판결 이유를 재미있게 써줘."
MODEL_NAME = "gemini-1.5-flash"

BASE_OUTPUT_FORMAT_GUIDE = """
출력은 아래 형식을 꼭 지켜줘.

과실비율: 남자 XX% / 여자 YY%

판결문:
- 한 줄 요약: (딱 1줄)
- 핵심 근거 3가지:
  1) ...
  2) ...
  3) ...
- 최종 판결: (재미있게 1~2문장)

주의:
- 욕설/비하 표현은 순화해서.
- 개인을 특정할 수 있는 정보(전화번호, 계정, 실명 등)는 언급하지 마.
"""

# ----------------------------
# 유틸
# ----------------------------
@st.cache_resource
def get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def extract_fault_ratio(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    '과실비율: 남자 40% / 여자 60%' 같은 문자열에서 퍼센트 2개를 대충 추출.
    """
    # 남자/여자 라벨이 있으면 우선적으로 추출
    male = None
    female = None

    m = re.search(r"남자\s*[:\-]?\s*(\d{1,3})\s*%", text)
    f = re.search(r"여자\s*[:\-]?\s*(\d{1,3})\s*%", text)
    if m:
        male = int(m.group(1))
    if f:
        female = int(f.group(1))

    # 라벨이 없거나 한쪽만 잡히면, 처음 나오는 % 2개를 fallback으로 사용
    if male is None or female is None:
        percents = re.findall(r"(\d{1,3})\s*%", text)
        if len(percents) >= 2:
            a, b = int(percents[0]), int(percents[1])
            if male is None:
                male = a
            if female is None:
                female = b

    # 비정상 값 방어
    if male is not None and (male < 0 or male > 100):
        male = None
    if female is not None and (female < 0 or female > 100):
        female = None

    return male, female


def verdict_box(verdict_text: str, male: Optional[int], female: Optional[int]) -> None:
    st.markdown(
        """
        <style>
          .judge-wrap { border:1px solid rgba(255,255,255,0.12); border-radius:18px; padding:18px; background: rgba(255,255,255,0.04); }
          .judge-title { font-size: 20px; font-weight: 800; margin-bottom: 6px; }
          .judge-sub { opacity: 0.8; margin-bottom: 14px; }
          .judge-pre { white-space: pre-wrap; line-height: 1.6; font-size: 15px; }
          .pill { display:inline-block; padding:6px 10px; border-radius:999px; margin-right:8px; font-weight:700; font-size: 13px;
                  border:1px solid rgba(255,255,255,0.14); background: rgba(255,255,255,0.06); }
        </style>
        """,
        unsafe_allow_html=True,
    )

    pills = []
    if male is not None:
        pills.append(f"<span class='pill'>🙋‍♂️ 남자 {male}%</span>")
    if female is not None:
        pills.append(f"<span class='pill'>🙋‍♀️ 여자 {female}%</span>")

    st.markdown(
        f"""
        <div class="judge-wrap">
          <div class="judge-title">⚖️ 판결 결과</div>
          <div class="judge-sub">{''.join(pills) if pills else "과실 비율을 자동 추출하지 못했어요. 판결문 상단을 확인해 주세요."}</div>
          <div class="judge-pre">{verdict_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def call_gemini(client: genai.Client, contents, *, system_prompt: str) -> str:
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.8,
        ),
    )
    return (resp.text or "").strip()


# ----------------------------
# 메인 UI
# ----------------------------
st.title("⚖️ 커플 싸움 판독기")
st.caption("카톡 캡처 또는 글로 상황을 넣으면, 과실 비율과 판결문을 재미있게 써드립니다. (재미용)")

# API Key 로드
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    st.error("secrets에 GEMINI_API_KEY가 없어요. `.streamlit/secrets.toml`에 키를 추가해 주세요.")
    st.stop()

client = get_client(api_key)

tab1, tab2 = st.tabs(["📸 캡처로 판결", "📝 글로 판결"])

# ----------------------------
# 탭 1: 이미지
# ----------------------------
with tab1:
    st.subheader("📸 카톡 캡처 업로드")
    uploaded = st.file_uploader(
        "카톡 캡처 이미지를 올려주세요 (png/jpg/webp)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=False,
    )

    if uploaded:
        st.image(uploaded, caption="업로드된 이미지 미리보기", use_container_width=True)

    go_img = st.button("판결 받기", key="btn_img", use_container_width=True, disabled=(uploaded is None))

    if go_img and uploaded:
        try:
            image_bytes = uploaded.getvalue()
            mime_type = uploaded.type or "image/png"

            user_prompt = (
                "아래 이미지는 커플 간 카톡 대화 캡처야.\n"
                "대화를 읽고 '커플 싸움 판독' 판결을 내려줘.\n\n"
                + BASE_OUTPUT_FORMAT_GUIDE
            )

            with st.spinner("판사님 출근 중... 🧑‍⚖️"):
                result_text = call_gemini(
                    client,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        user_prompt,
                    ],
                    system_prompt=SYSTEM_PROMPT,
                )

            male, female = extract_fault_ratio(result_text)
            verdict_box(result_text, male, female)

        except Exception as e:
            st.error("분석 중 오류가 발생했어요.")
            st.exception(e)

# ----------------------------
# 탭 2: 텍스트
# ----------------------------
with tab2:
    st.subheader("📝 상황/대화 텍스트 붙여넣기")
    text_input = st.text_area(
        "대화 내용 또는 상황 설명을 길게 입력해 주세요",
        height=240,
        placeholder="예) 서로 말이 겹치면서 오해가 생겼고, 약속 시간 관련해서...\n(대화/상황을 그대로 붙여넣어도 OK)",
    )

    go_txt = st.button(
        "판결 받기",
        key="btn_txt",
        use_container_width=True,
        disabled=(not text_input.strip()),
    )

    if go_txt and text_input.strip():
        try:
            user_prompt = (
                "아래 텍스트는 커플의 대화/상황 설명이야.\n"
                "내용을 근거로 '커플 싸움 판독' 판결을 내려줘.\n\n"
                + BASE_OUTPUT_FORMAT_GUIDE
                + "\n\n[텍스트]\n"
                + text_input.strip()
            )

            with st.spinner("판사님 기록 검토 중... 📚"):
                result_text = call_gemini(
                    client,
                    contents=user_prompt,
                    system_prompt=SYSTEM_PROMPT,
                )

            male, female = extract_fault_ratio(result_text)
            verdict_box(result_text, male, female)

        except Exception as e:
            st.error("분석 중 오류가 발생했어요.")
            st.exception(e)

st.divider()
st.caption("⚠️ 본 앱은 재미/참고용입니다. 실제 관계 문제는 대화/중재/전문가 상담이 도움이 될 수 있어요.")
