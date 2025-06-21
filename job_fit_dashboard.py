import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path
import glob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import platform
from llama_stack.llama import Llama # --- [병합] Llama 라이브러리 임포트 ---

# --- 1. 페이지 기본 설정 ---
st.set_page_config(page_title="Job-Fit Insight Dashboard", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")

# --- 2. CSS 스타일링 ---
st.markdown("""
<style>
    .main-header { background: linear-gradient(90deg, #1f4e79 0%, #2980b9 100%); padding: 1.5rem; border-radius: 10px; color: white; margin-bottom: 2rem; }
    .highlight-card { background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #ff6b35; }
    .job-posting-card { background: #ffffff; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 1rem; border: 1px solid #e9ecef; }
    .job-posting-card a { text-decoration: none; color: #1f4e79; font-weight: bold; font-size: 1.1em; }
    .job-posting-card p { margin: 0.3rem 0; color: #495057; font-size: 0.9em; }
    div[data-testid="metric-container"] { background-color: #f8f9fa; border-left: 5px solid #2980b9; padding: 1rem; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 데이터 로딩 및 처리 함수 ---
@st.cache_resource
def init_connection(db_path="data/job_fit_insight.db"):
    # ... (이전과 동일)
    db_file = Path(db_path)
    if not db_file.exists(): st.error(f"DB 파일('{db_path}') 없음. `setup_database.py` 실행 필요."); st.stop()
    return sqlite3.connect(db_file, check_same_thread=False)

def generate_sample_youth_data():
    # ... (이전과 동일)
    data = {'성별': ['남성', '여성', '남성', '여성'], '연령계층별': ['15-29세', '15-29세', '30-39세', '30-39세'], '2025.03_실업률': [6.8, 6.1, 3.1, 3.5], '2025.03_경제활동인구': [2450000, 2150000, 3400000, 3100000], '2025.03_취업자': [2283000, 2018000, 3295000, 2990000], '2025.04_실업률': [7.0, 6.3, 3.2, 3.6], '2025.04_경제활동인구': [2460000, 2160000, 3420000, 3120000], '2025.04_취업자': [2287000, 2023000, 3310000, 3010000], '2025.05_실업률': [6.9, 6.2, 3.0, 3.4], '2025.05_경제활동인구': [2470000, 2170000, 3430000, 3130000], '2025.05_취업자': [2299000, 2035000, 3325000, 3020000]}
    return pd.DataFrame(data)

@st.cache_data
def load_data(_conn):
    # ... (이전과 동일)
    skills_df = pd.read_sql("SELECT * FROM top10_skills_per_job", _conn)
    levels_df = pd.read_sql("SELECT * FROM joblevel_counts", _conn)
    rallit_df = None
    try:
        csv_files = glob.glob(str(Path("data") / "rallit_*.csv"))
        if csv_files: rallit_df = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True).drop_duplicates(subset=['url']).reset_index(drop=True)
    except Exception as e: print(f"Error loading Rallit CSVs: {e}")
    try: youth_df = pd.read_sql("SELECT * FROM youth_summary", _conn)
    except pd.io.sql.DatabaseError: youth_df = generate_sample_youth_data()
    overall_data = youth_df.groupby('연령계층별', as_index=False).sum(numeric_only=True)
    overall_data["성별"] = "전체"
    rate_cols = [col for col in youth_df.columns if "_실업률" in col]
    mean_rates = youth_df.groupby('연령계층별')[rate_cols].mean().reset_index()
    for col in rate_cols: overall_data[col] = overall_data['연령계층별'].map(mean_rates.set_index('연령계층별')[col])
    youth_df = pd.concat([youth_df, overall_data], ignore_index=True)
    id_vars = ["성별", "연령계층별"]
    unemp_long = youth_df.melt(id_vars=id_vars, value_vars=rate_cols, var_name="월", value_name="실업률")
    pop_long = youth_df.melt(id_vars=id_vars, value_vars=[c for c in youth_df.columns if "_경제활동인구" in c], var_name="월", value_name="경제활동인구")
    emp_long = youth_df.melt(id_vars=id_vars, value_vars=[c for c in youth_df.columns if "_취업자" in c], var_name="월", value_name="취업자")
    unemp_long["월"], pop_long["월"], emp_long["월"] = [df["월"].str.replace(s, "") for df, s in [(unemp_long, "_실업률"), (pop_long, "_경제활동인구"), (emp_long, "_취업자")]]
    trend_df = unemp_long.merge(pop_long, on=id_vars+["월"]).merge(emp_long, on=id_vars+["월"])
    trend_df["월"] = pd.to_datetime(trend_df["월"], format="%Y.%m").dt.strftime("%Y.%m")
    trend_df = trend_df.sort_values("월")
    return trend_df, skills_df, levels_df, rallit_df

# --- [병합] Llama 모델 로딩 함수 ---
@st.cache_resource
def load_llama_model(model_id):
    try:
        llm = Llama(model_id=model_id)
        return llm
    except Exception as e:
        st.error(f"'{model_id}' 모델 로딩 실패. 모델을 다운로드했는지 확인하세요.", icon="🚨")
        st.code(f"llama model download --source meta --model-id {model_id}", language="bash")
        return None

# (이하 다른 함수들은 이전과 동일)

# --- 4. 분석 로직 및 5. 사이드바 UI ---
# (calculate_job_fit 등 이전 로직 함수들은 그대로 유지)
def calculate_job_fit(work_style, work_env, interest_job):
    job_fit_scores = {}
    # ...
    return job_fit_scores

with st.sidebar:
    st.title("My Job-Fit Profile")
    with st.container(border=True):
        st.header("👤 나의 프로필 설정")
        # ... (이전 프로필 설정 UI 유지)
        job_category_map = { "데이터 분석": ["데이터", "분석", "Data", "BI"], "마케팅": ["마케팅", "마케터", "Marketing", "광고", "콘텐츠"], "기획": ["기획", "PM", "PO", "서비스", "Product"], "프론트엔드": ["프론트엔드", "Frontend", "React", "Vue", "웹 개발"], "백엔드": ["백엔드", "Backend", "Java", "Python", "서버", "Node.js"], "AI/ML": ["AI", "ML", "머신러닝", "딥러닝", "인공지능"], "디자인": ["디자인", "디자이너", "Designer", "UI", "UX", "BX", "그래픽"], "영업": ["영업", "Sales", "세일즈", "비즈니스", "Business Development"], "고객지원": ["CS", "CX", "고객", "지원", "서비스 운영"], "인사": ["인사", "HR", "채용", "조직문화", "Recruiting"] }
        job_options = sorted(list(job_category_map.keys()))
        interest_job = st.selectbox("관심 직무", job_options, key="interest_job")
        career_options = ["상관 없음", "신입", "1-3년", "4-6년", "7-10년 이상"]
        career_level = st.selectbox("희망 경력 수준", career_options, key="career_level")
        
    with st.container(border=True):
        st.header("🧠 나의 성향 진단")
        # ... (이전 성향 진단 UI 유지)
        work_style = st.radio("선호하는 업무 스타일은?", ["분석적이고 논리적", "창의적이고 혁신적", "체계적이고 계획적", "사교적이고 협력적"], key="work_style")
        work_env = st.radio("선호하는 업무 환경은?", ["독립적으로 일하기", "팀워크 중심", "빠른 변화와 도전", "안정적이고 예측 가능한"], key="work_env")

    # --- [병합] Llama 모델 설정 UI 추가 ---
    st.write("")
    with st.container(border=True):
        st.header("🦙 AI 도우미 설정")
        default_model = "llama-4-scout-17b-16e-instruct"
        selected_model_id = st.text_input("사용할 Llama 모델 ID", default_model)
        temperature = st.slider("Temperature (창의성)", 0.0, 1.0, 0.1, 0.05)
        max_tokens = st.slider("Max Tokens (최대 답변 길이)", 128, 4096, 1024, 128)

# --- 6. 메인 로직 실행 ---
conn = init_connection()
trend_df, skills_df, levels_df, rallit_df = load_data(conn)
job_fit_scores = calculate_job_fit(work_style, work_env, interest_job)
score_df = pd.DataFrame(job_fit_scores.items(), columns=["직무", "적합도"]).sort_values("적합도", ascending=False).reset_index(drop=True)
top_job = score_df.iloc[0]["직무"] if not score_df.empty else "분석 결과 없음"

# --- [병합] Llama 모델 로드 ---
llm = load_llama_model(selected_model_id)
if llm is None:
    st.sidebar.error(f"'{selected_model_id}' 모델을 로드할 수 없습니다.")
else:
    st.sidebar.success(f"✅ AI 도우미 준비 완료!")


# --- 7. 대시보드 본문 ---
st.markdown('<div class="main-header"><h1>🧠 Job-Fit Insight Dashboard</h1><p>나의 성향과 시장 데이터를 결합한 최적의 커리어 인사이트를 찾아보세요.</p></div>', unsafe_allow_html=True)

# --- [병합] 탭에 'Llama 4 AI 도우미' 추가 ---
main_tabs = st.tabs(["🚀 나의 맞춤 분석", "📊 시장 동향 분석", "🦙 Llama 4 AI 도우미"])

# 나의 맞춤 분석 탭 (이전과 동일)
with main_tabs[0]:
    # ... (이전 코드와 동일, 수정 없음)
    pass

# 시장 동향 분석 탭 (이전과 동일)
with main_tabs[1]:
    # ... (이전 코드와 동일, 수정 없음)
    pass

# --- [병합] Llama 4 AI 도우미 탭 신규 구현 ---
with main_tabs[2]:
    st.subheader("Llama 4 Scout 기반 AI 분석")

    if llm is None:
        st.error("AI 도우미를 사용하려면 사이드바에서 모델을 성공적으로 로드해야 합니다.")
    else:
        ai_feature_tabs = st.tabs(["**📄 AI 직무 분석**", "**💬 AI 커리어 상담**"])

        # AI 직무 분석 기능
        with ai_feature_tabs[0]:
            st.markdown("##### 채용 공고를 입력하면 Llama 4가 분석해 드립니다.")
            job_desc_input = st.text_area("여기에 채용 공고를 붙여넣으세요:", height=250, placeholder="예시: '메타에서 Llama 4를 다룰 AI 엔지니어를 찾습니다...'")
            if st.button("분석 시작하기", key="analyze_job"):
                if not job_desc_input:
                    st.warning("분석할 채용 공고를 입력해주세요.")
                else:
                    with st.spinner("Llama 4 Scout가 채용 공고를 분석 중입니다..."):
                        system_prompt = "You are a professional HR analyst. Analyze a job description and provide a structured summary in Korean."
                        user_prompt = f"""Analyze the following job description and provide the output in the specified format below.
                        **Job Description:**\n---\n{job_desc_input}\n---\n
                        **Output Format:**
                        ### 📝 핵심 요약 (3가지)
                        - [핵심 역할 및 책임 1]
                        - [핵심 역할 및 책임 2]
                        - [핵심 역할 및 책임 3]
                        ### 🛠️ 요구 기술 스택
                        - [기술 1], [기술 2], ...
                        ### 📈 예상 경력 수준
                        - [예: 신입, 1~3년차, 5년 이상 등]
                        ### 🗣️ 면접 예상 질문 (3가지)
                        1. [기술 또는 경험 관련 질문 1]
                        2. [문제 해결 능력 관련 질문 2]
                        3. [조직 문화 적합성 관련 질문 3]"""
                        
                        response = llm.create_chat_completion(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=temperature, max_tokens=max_tokens)
                        analysis_result = response['choices'][0]['message']['content']
                    st.markdown("---"); st.subheader("🤖 Llama 4 Scout 분석 결과"); st.markdown(analysis_result)

        # AI 커리어 상담 기능
        with ai_feature_tabs[1]:
            st.markdown("##### 현재 나의 프로필을 바탕으로 커리어에 대해 질문해보세요.")
            
            # 사용자 프로필 요약
            user_profile = f"저는 **{interest_job}** 직무에 관심이 있고, 희망 경력은 **{career_level}** 입니다. 저의 성향은 **{work_style}**하고, **{work_env}** 환경을 선호합니다."
            st.info(f"**현재 프로필:** {user_profile}")

            # 질문 예시
            question_examples = [
                "이 프로필에 어울리는 다른 직무를 추천해주세요.",
                f"{interest_job} 직무로 성장하기 위한 학습 로드맵을 짜주세요.",
                "제 성향에 맞는 회사를 찾으려면 어떤 점을 고려해야 할까요?"
            ]
            selected_question = st.selectbox("질문 예시를 선택하거나 직접 입력하세요:", [""] + question_examples)
            user_question = st.text_input("질문 입력:", value=selected_question)

            if st.button("Llama에게 질문하기", key="ask_career"):
                if not user_question:
                    st.warning("질문을 입력해주세요.")
                else:
                    with st.spinner("Llama 4 Scout가 답변을 생성 중입니다..."):
                        system_prompt = "You are a friendly and insightful career counselor. Based on the user's profile, answer their career-related questions in Korean."
                        full_prompt = f"**User Profile:**\n{user_profile}\n\n**User Question:**\n{user_question}"
                        
                        response = llm.create_chat_completion(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": full_prompt}], temperature=temperature, max_tokens=max_tokens)
                        career_advice = response['choices'][0]['message']['content']
                    st.markdown("---"); st.subheader("🤖 Llama 4 Scout 커리어 조언"); st.markdown(career_advice)


# 8. 푸터
st.markdown("---")
st.markdown('<div style="text-align: center; color: #666;"><p>🧠 Job-Fit Insight Dashboard | Powered by Streamlit & Llama 4</p></div>', unsafe_allow_html=True)
