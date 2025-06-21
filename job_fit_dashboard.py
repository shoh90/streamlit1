# 전체 통합 Python 코드

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path
import glob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import platform
from groq import Groq
import re

# --- 기본 설정 ---
st.set_page_config(page_title="Job-Fit Insight AI Dashboard", page_icon="🧠", layout="wide")

# --- DB 로딩 ---
@st.cache_resource
def init_connection():
    db_file = Path("data/job_fit_insight.db")
    if not db_file.exists():
        st.error("DB 파일이 없습니다.")
        st.stop()
    return sqlite3.connect(db_file, check_same_thread=False)

@st.cache_data
def load_data(conn):
    skills_df = pd.read_sql("SELECT * FROM top10_skills_per_job", conn)
    levels_df = pd.read_sql("SELECT * FROM joblevel_counts", conn)
    try:
        csv_files = glob.glob("data/rallit_*.csv")
        rallit_df = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True).drop_duplicates()
    except: rallit_df = None
    return skills_df, levels_df, rallit_df

# --- AI 추천 함수 ---
def prepare_context(skills_df, levels_df, rallit_df, interest_job, career_level):
    txt = f"### [{interest_job} 직무 시장 기술]
"
    df1 = skills_df[skills_df['직무'] == interest_job]
    if not df1.empty:
        txt += df1[['기술스택', '빈도']].to_markdown(index=False) + "\n\n"
    df2 = levels_df[levels_df['직무'] == interest_job]
    if not df2.empty:
        txt += f"### [{interest_job} 직무 경력 분포]\n"
        txt += df2[['jobLevels', '공고수']].to_markdown(index=False) + "\n\n"
    if rallit_df is not None:
        keyword = interest_job
        job_mask = rallit_df['title'].str.contains(keyword, case=False, na=False)
        if career_level == "상관 없음":
            career_mask = True
        else:
            career_mask = rallit_df['jobLevels'].str.contains(career_level.replace("-", "~"), case=False, na=False)
        job_df = rallit_df[job_mask & career_mask].head(3)
        if not job_df.empty:
            txt += "### [공고 예시]\n" + job_df[['title','companyName','jobLevels']].to_markdown(index=False) + "\n\n"
    return txt

def get_ai_recommendation(client, model, temp, max_tokens, context_text, interest_job):
    if client is None: return None
    prompt = f"""
당신은 커리어 코치입니다. 아래는 특정 직무({interest_job})에 대한 시장 데이터입니다.
이 정보를 기반으로 사용자가 관심 가질만한 추천 직무 1개를 제시해주세요.
사유도 간단히 설명해주세요.

{context_text}

📌 답변 형식:
추천 직무: <직무명>
추천 사유: <사유>
"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temp,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content

# --- UI 입력 ---
with st.sidebar:
    st.title("🧠 Job-Fit 프로필")
    job_category_map = {"데이터 분석":[], "마케팅":[], "기획":[], "프론트엔드":[], "백엔드":[], "AI/ML":[], "디자인":[], "영업":[], "고객지원":[], "인사":[]}
    job_list = sorted(list(job_category_map.keys()))
    interest_job = st.selectbox("관심 직무", job_list)
    career_level = st.selectbox("희망 경력", ["상관 없음", "신입", "1-3년", "4-6년", "7-10년 이상"])
    model = st.selectbox("Groq 모델", ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"])
    temp = st.slider("Temperature", 0.0, 1.0, 0.2)
    max_tokens = st.slider("Max tokens", 128, 4096, 1024)

# --- 실행 ---
conn = init_connection()
skills_df, levels_df, rallit_df = load_data(conn)
client = Groq(api_key=st.secrets["GROQ_API_KEY"]) if "GROQ_API_KEY" in st.secrets else None
context = prepare_context(skills_df, levels_df, rallit_df, interest_job, career_level)
ai_text = get_ai_recommendation(client, model, temp, max_tokens, context, interest_job)
match = re.search(r"추천 직무:\s*(.+)", ai_text or "")
ai_top_job = match.group(1).strip() if match else interest_job

# --- 출력 ---
st.title("🧠 Job-Fit Insight with AI")
st.header(f"🏆 AI 추천 직무: {ai_top_job}")
st.markdown("---")
if ai_text:
    st.markdown("**📝 추천 사유 및 분석**")
    st.code(ai_text, language='markdown')
else:
    st.warning("AI 분석 결과를 불러올 수 없습니다.")
