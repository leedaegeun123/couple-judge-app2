import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. 페이지 설정
st.set_page_config(page_title="커플 싸움 AI 판사", page_icon="⚖️")

# 2. API Key 연결
try:
    # Streamlit Secrets에서 키를 가져옴
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error("⚠️ API Key 오류! Streamlit Secrets에 GOOGLE_API_KEY를 설정해주세요.")
    st.stop()

# 3. 모델 설정 (Gemini 1.5 Flash)
model = genai.GenerativeModel("gemini-1.5-flash")

# 4. 화면 디자인 (제목)
st.title("⚖️ 커플 싸움 AI 판사")
st.write("누가 잘못했는지 AI가 3초 만에 판결해 드립니다.")

# 5. 탭 구성
tab1, tab2 = st.tabs(["📸 캡처로 판결", "📝 글로 판결"])

# --- 탭 1: 이미지 업로드 ---
with tab1:
    uploaded_file = st.file_uploader("카톡 캡처 이미지를 올려주세요", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="증거 제출 완료", use_column_width=True)
        
        if st.button("📸 캡처본으로 판결 받기"):
            with st.spinner("판사님이 분석 중입니다..."):
                try:
                    # AI에게 이미지 분석 요청
                    prompt = """
                    너는 20년 경력의 이혼 전문 변호사이자 AI 판사야.
                    이 대화 내용을 보고 다음 순서로 분석해줘.
                    1. 팩트체크 (객관적 사실)
                    2. 과실비율 (남자 vs 여자 %)
                    3. 판결문 (명쾌하고 위트있게)
                    4. 솔루션 (행동 지침)
                    """
                    response = model.generate_content([prompt, image])
                    st.success("판결 완료!")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"에러가 발생했습니다: {e}")

# --- 탭 2: 텍스트 입력 ---
with tab2:
    user_text = st.text_area("억울한 사연을 적어주세요", height=150)
    if st.button("📝 글로 판결 받기"):
        if user_text:
            with st.spinner("판사님이 분석 중입니다..."):
                try:
                    # AI에게 텍스트 분석 요청
                    prompt = f"""
                    너는 20년 경력의 이혼 전문 변호사이자 AI 판사야.
                    다음 사연을 보고 다음 순서로 분석해줘.
                    1. 팩트체크 (객관적 사실)
                    2. 과실비율 (남자 vs 여자 %)
                    3. 판결문 (명쾌하고 위트있게)
                    4. 솔루션 (행동 지침)
                    
                    사연: {user_text}
                    """
                    response = model.generate_content(prompt)
                    st.success("판결 완료!")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"에러가 발생했습니다: {e}")
