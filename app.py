import streamlit as st
import google.generativeai as genai

st.title("🔍 모델 확인기")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    st.write("내 API 키로 사용 가능한 모델 목록:")
    
    # 사용 가능한 모델 리스트 출력
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            st.code(m.name)
            
except Exception as e:
    st.error(f"에러: {e}")
