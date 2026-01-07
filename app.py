{\rtf1\ansi\ansicpg949\cocoartf2761
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 # app.py\
# Streamlit + Gemini(google-genai)\uc0\u47196  "\u52964 \u54540  \u49912 \u50880  \u54032 \u46021 \u44592 " \u47564 \u46308 \u44592 \
#\
# \uc0\u54596 \u50836  \u54056 \u53412 \u51648 :\
#   pip install streamlit google-genai\
#\
# .streamlit/secrets.toml \uc0\u50696 \u49884 :\
#   GEMINI_API_KEY="YOUR_API_KEY"\
\
import json\
import re\
from typing import Optional, Tuple\
\
import streamlit as st\
from google import genai\
from google.genai import types\
\
# ----------------------------\
# \uc0\u49444 \u51221 \
# ----------------------------\
st.set_page_config(\
    page_title="\uc0\u52964 \u54540  \u49912 \u50880  \u54032 \u46021 \u44592 ",\
    page_icon="\uc0\u9878 \u65039 ",\
    layout="centered",\
)\
\
SYSTEM_PROMPT = "\uc0\u45320 \u45716  \u52964 \u54540  \u49912 \u50880  \u54032 \u46021 \u44592 \u50556 . \u51060  \u45824 \u54868 \u47484  \u48372 \u44256  \u45224 \u45376  \u44284 \u49892  \u48708 \u50984 \u44284  \u54032 \u44208  \u51060 \u50976 \u47484  \u51116 \u48120 \u51080 \u44172  \u50024 \u51480 ."\
MODEL_NAME = "gemini-1.5-flash"\
\
BASE_OUTPUT_FORMAT_GUIDE = """\
\uc0\u52636 \u47141 \u51008  \u50500 \u47000  \u54805 \u49885 \u51012  \u44845  \u51648 \u53020 \u51480 .\
\
\uc0\u44284 \u49892 \u48708 \u50984 : \u45224 \u51088  XX% / \u50668 \u51088  YY%\
\
\uc0\u54032 \u44208 \u47928 :\
- \uc0\u54620  \u51460  \u50836 \u50557 : (\u46385  1\u51460 )\
- \uc0\u54645 \u49900  \u44540 \u44144  3\u44032 \u51648 :\
  1) ...\
  2) ...\
  3) ...\
- \uc0\u52572 \u51333  \u54032 \u44208 : (\u51116 \u48120 \u51080 \u44172  1~2\u47928 \u51109 )\
\
\uc0\u51452 \u51032 :\
- \uc0\u50837 \u49444 /\u48708 \u54616  \u54364 \u54788 \u51008  \u49692 \u54868 \u54644 \u49436 .\
- \uc0\u44060 \u51064 \u51012  \u53945 \u51221 \u54624  \u49688  \u51080 \u45716  \u51221 \u48372 (\u51204 \u54868 \u48264 \u54840 , \u44228 \u51221 , \u49892 \u47749  \u46321 )\u45716  \u50616 \u44553 \u54616 \u51648  \u47560 .\
"""\
\
# ----------------------------\
# \uc0\u50976 \u54008 \
# ----------------------------\
@st.cache_resource\
def get_client(api_key: str) -> genai.Client:\
    return genai.Client(api_key=api_key)\
\
\
def extract_fault_ratio(text: str) -> Tuple[Optional[int], Optional[int]]:\
    """\
    '\uc0\u44284 \u49892 \u48708 \u50984 : \u45224 \u51088  40% / \u50668 \u51088  60%' \u44057 \u51008  \u47928 \u51088 \u50676 \u50640 \u49436  \u54140 \u49468 \u53944  2\u44060 \u47484  \u45824 \u52649  \u52628 \u52636 .\
    """\
    # \uc0\u45224 \u51088 /\u50668 \u51088  \u46972 \u48296 \u51060  \u51080 \u51004 \u47732  \u50864 \u49440 \u51201 \u51004 \u47196  \u52628 \u52636 \
    male = None\
    female = None\
\
    m = re.search(r"\uc0\u45224 \u51088 \\s*[:\\-]?\\s*(\\d\{1,3\})\\s*%", text)\
    f = re.search(r"\uc0\u50668 \u51088 \\s*[:\\-]?\\s*(\\d\{1,3\})\\s*%", text)\
    if m:\
        male = int(m.group(1))\
    if f:\
        female = int(f.group(1))\
\
    # \uc0\u46972 \u48296 \u51060  \u50630 \u44144 \u45208  \u54620 \u51901 \u47564  \u51105 \u55176 \u47732 , \u52376 \u51020  \u45208 \u50724 \u45716  % 2\u44060 \u47484  fallback\u51004 \u47196  \u49324 \u50857 \
    if male is None or female is None:\
        percents = re.findall(r"(\\d\{1,3\})\\s*%", text)\
        if len(percents) >= 2:\
            a, b = int(percents[0]), int(percents[1])\
            if male is None:\
                male = a\
            if female is None:\
                female = b\
\
    # \uc0\u48708 \u51221 \u49345  \u44050  \u48169 \u50612 \
    if male is not None and (male < 0 or male > 100):\
        male = None\
    if female is not None and (female < 0 or female > 100):\
        female = None\
\
    return male, female\
\
\
def verdict_box(verdict_text: str, male: Optional[int], female: Optional[int]) -> None:\
    st.markdown(\
        """\
        <style>\
          .judge-wrap \{ border:1px solid rgba(255,255,255,0.12); border-radius:18px; padding:18px; background: rgba(255,255,255,0.04); \}\
          .judge-title \{ font-size: 20px; font-weight: 800; margin-bottom: 6px; \}\
          .judge-sub \{ opacity: 0.8; margin-bottom: 14px; \}\
          .judge-pre \{ white-space: pre-wrap; line-height: 1.6; font-size: 15px; \}\
          .pill \{ display:inline-block; padding:6px 10px; border-radius:999px; margin-right:8px; font-weight:700; font-size: 13px;\
                  border:1px solid rgba(255,255,255,0.14); background: rgba(255,255,255,0.06); \}\
        </style>\
        """,\
        unsafe_allow_html=True,\
    )\
\
    pills = []\
    if male is not None:\
        pills.append(f"<span class='pill'>\uc0\u55357 \u56907 \u8205 \u9794 \u65039  \u45224 \u51088  \{male\}%</span>")\
    if female is not None:\
        pills.append(f"<span class='pill'>\uc0\u55357 \u56907 \u8205 \u9792 \u65039  \u50668 \u51088  \{female\}%</span>")\
\
    st.markdown(\
        f"""\
        <div class="judge-wrap">\
          <div class="judge-title">\uc0\u9878 \u65039  \u54032 \u44208  \u44208 \u44284 </div>\
          <div class="judge-sub">\{''.join(pills) if pills else "\uc0\u44284 \u49892  \u48708 \u50984 \u51012  \u51088 \u46041  \u52628 \u52636 \u54616 \u51648  \u47803 \u54664 \u50612 \u50836 . \u54032 \u44208 \u47928  \u49345 \u45800 \u51012  \u54869 \u51064 \u54644  \u51452 \u49464 \u50836 ."\}</div>\
          <div class="judge-pre">\{verdict_text\}</div>\
        </div>\
        """,\
        unsafe_allow_html=True,\
    )\
\
\
def call_gemini(client: genai.Client, contents, *, system_prompt: str) -> str:\
    resp = client.models.generate_content(\
        model=MODEL_NAME,\
        contents=contents,\
        config=types.GenerateContentConfig(\
            system_instruction=system_prompt,\
            temperature=0.8,\
        ),\
    )\
    return (resp.text or "").strip()\
\
\
# ----------------------------\
# \uc0\u47700 \u51064  UI\
# ----------------------------\
st.title("\uc0\u9878 \u65039  \u52964 \u54540  \u49912 \u50880  \u54032 \u46021 \u44592 ")\
st.caption("\uc0\u52852 \u53665  \u52897 \u52376  \u46608 \u45716  \u44544 \u47196  \u49345 \u54889 \u51012  \u45347 \u51004 \u47732 , \u44284 \u49892  \u48708 \u50984 \u44284  \u54032 \u44208 \u47928 \u51012  \u51116 \u48120 \u51080 \u44172  \u50024 \u46300 \u47549 \u45768 \u45796 . (\u51116 \u48120 \u50857 )")\
\
# API Key \uc0\u47196 \u46300 \
api_key = st.secrets.get("GEMINI_API_KEY", "")\
if not api_key:\
    st.error("secrets\uc0\u50640  GEMINI_API_KEY\u44032  \u50630 \u50612 \u50836 . `.streamlit/secrets.toml`\u50640  \u53412 \u47484  \u52628 \u44032 \u54644  \u51452 \u49464 \u50836 .")\
    st.stop()\
\
client = get_client(api_key)\
\
tab1, tab2 = st.tabs(["\uc0\u55357 \u56568  \u52897 \u52376 \u47196  \u54032 \u44208 ", "\u55357 \u56541  \u44544 \u47196  \u54032 \u44208 "])\
\
# ----------------------------\
# \uc0\u53485  1: \u51060 \u48120 \u51648 \
# ----------------------------\
with tab1:\
    st.subheader("\uc0\u55357 \u56568  \u52852 \u53665  \u52897 \u52376  \u50629 \u47196 \u46300 ")\
    uploaded = st.file_uploader(\
        "\uc0\u52852 \u53665  \u52897 \u52376  \u51060 \u48120 \u51648 \u47484  \u50732 \u47140 \u51452 \u49464 \u50836  (png/jpg/webp)",\
        type=["png", "jpg", "jpeg", "webp"],\
        accept_multiple_files=False,\
    )\
\
    if uploaded:\
        st.image(uploaded, caption="\uc0\u50629 \u47196 \u46300 \u46108  \u51060 \u48120 \u51648  \u48120 \u47532 \u48372 \u44592 ", use_container_width=True)\
\
    go_img = st.button("\uc0\u54032 \u44208  \u48155 \u44592 ", key="btn_img", use_container_width=True, disabled=(uploaded is None))\
\
    if go_img and uploaded:\
        try:\
            image_bytes = uploaded.getvalue()\
            mime_type = uploaded.type or "image/png"\
\
            user_prompt = (\
                "\uc0\u50500 \u47000  \u51060 \u48120 \u51648 \u45716  \u52964 \u54540  \u44036  \u52852 \u53665  \u45824 \u54868  \u52897 \u52376 \u50556 .\\n"\
                "\uc0\u45824 \u54868 \u47484  \u51069 \u44256  '\u52964 \u54540  \u49912 \u50880  \u54032 \u46021 ' \u54032 \u44208 \u51012  \u45236 \u47140 \u51480 .\\n\\n"\
                + BASE_OUTPUT_FORMAT_GUIDE\
            )\
\
            with st.spinner("\uc0\u54032 \u49324 \u45784  \u52636 \u44540  \u51473 ... \u55358 \u56785 \u8205 \u9878 \u65039 "):\
                result_text = call_gemini(\
                    client,\
                    contents=[\
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),\
                        user_prompt,\
                    ],\
                    system_prompt=SYSTEM_PROMPT,\
                )\
\
            male, female = extract_fault_ratio(result_text)\
            verdict_box(result_text, male, female)\
\
        except Exception as e:\
            st.error("\uc0\u48516 \u49437  \u51473  \u50724 \u47448 \u44032  \u48156 \u49373 \u54664 \u50612 \u50836 .")\
            st.exception(e)\
\
# ----------------------------\
# \uc0\u53485  2: \u53581 \u49828 \u53944 \
# ----------------------------\
with tab2:\
    st.subheader("\uc0\u55357 \u56541  \u49345 \u54889 /\u45824 \u54868  \u53581 \u49828 \u53944  \u48537 \u50668 \u45347 \u44592 ")\
    text_input = st.text_area(\
        "\uc0\u45824 \u54868  \u45236 \u50857  \u46608 \u45716  \u49345 \u54889  \u49444 \u47749 \u51012  \u44600 \u44172  \u51077 \u47141 \u54644  \u51452 \u49464 \u50836 ",\
        height=240,\
        placeholder="\uc0\u50696 ) \u49436 \u47196  \u47568 \u51060  \u44217 \u52824 \u47732 \u49436  \u50724 \u54644 \u44032  \u49373 \u44220 \u44256 , \u50557 \u49549  \u49884 \u44036  \u44288 \u47144 \u54644 \u49436 ...\\n(\u45824 \u54868 /\u49345 \u54889 \u51012  \u44536 \u45824 \u47196  \u48537 \u50668 \u45347 \u50612 \u46020  OK)",\
    )\
\
    go_txt = st.button(\
        "\uc0\u54032 \u44208  \u48155 \u44592 ",\
        key="btn_txt",\
        use_container_width=True,\
        disabled=(not text_input.strip()),\
    )\
\
    if go_txt and text_input.strip():\
        try:\
            user_prompt = (\
                "\uc0\u50500 \u47000  \u53581 \u49828 \u53944 \u45716  \u52964 \u54540 \u51032  \u45824 \u54868 /\u49345 \u54889  \u49444 \u47749 \u51060 \u50556 .\\n"\
                "\uc0\u45236 \u50857 \u51012  \u44540 \u44144 \u47196  '\u52964 \u54540  \u49912 \u50880  \u54032 \u46021 ' \u54032 \u44208 \u51012  \u45236 \u47140 \u51480 .\\n\\n"\
                + BASE_OUTPUT_FORMAT_GUIDE\
                + "\\n\\n[\uc0\u53581 \u49828 \u53944 ]\\n"\
                + text_input.strip()\
            )\
\
            with st.spinner("\uc0\u54032 \u49324 \u45784  \u44592 \u47197  \u44160 \u53664  \u51473 ... \u55357 \u56538 "):\
                result_text = call_gemini(\
                    client,\
                    contents=user_prompt,\
                    system_prompt=SYSTEM_PROMPT,\
                )\
\
            male, female = extract_fault_ratio(result_text)\
            verdict_box(result_text, male, female)\
\
        except Exception as e:\
            st.error("\uc0\u48516 \u49437  \u51473  \u50724 \u47448 \u44032  \u48156 \u49373 \u54664 \u50612 \u50836 .")\
            st.exception(e)\
\
st.divider()\
st.caption("\uc0\u9888 \u65039  \u48376  \u50545 \u51008  \u51116 \u48120 /\u52280 \u44256 \u50857 \u51077 \u45768 \u45796 . \u49892 \u51228  \u44288 \u44228  \u47928 \u51228 \u45716  \u45824 \u54868 /\u51473 \u51116 /\u51204 \u47928 \u44032  \u49345 \u45812 \u51060  \u46020 \u50880 \u51060  \u46112  \u49688  \u51080 \u50612 \u50836 .")\
}