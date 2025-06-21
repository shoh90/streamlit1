import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path

# --- 페이지 설정 ---
st.set_page_config(
    page_title="Job-Fit Insight Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 스타일링 ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2980b9 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2980b9;
        margin-bottom: 1rem;
    }
    .highlight-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #ff6b35;
    }
</style>
""", unsafe_allow_html=True)


# --- 데이터베이스 연결 및 데이터 로딩 (수정된 부분) ---

# 1. DB 연결을 캐싱하는 함수 (리소스 캐싱)
@st.cache_resource
def init_connection(db_path="data/job_fit_insight.db"):
    """SQLite DB에 대한 연결을 초기화하고 캐싱합니다."""
    db_file = Path(db_path)
    if not db_file.exists():
        st.error(f"데이터베이스 파일('{db_path}')을 찾을 수 없습니다. `setup_database.py`를 먼저 실행해주세요.")
        st.stop()
    return sqlite3.connect(db_file, check_same_thread=False)

# 2. 데이터를 쿼리하는 함수 (데이터 캐싱)
@st.cache_data
def load_data(_conn):
    """DB 연결을 사용하여 모든 테이블을 로드합니다."""
    youth_df = pd.read_sql("SELECT * FROM youth_summary", _conn)
    skills_df = pd.read_sql("SELECT * FROM top10_skills_per_job", _conn)
    levels_df = pd.read_sql("SELECT * FROM joblevel_counts", _conn)
    return youth_df, skills_df, levels_df

# DB 연결 및 데이터 로드 실행
conn = init_connection()
youth_df, skills_df, levels_df = load_data(conn)


# --- 개인 맞춤 분석 로직 ---
job_characteristics = {
    "데이터 분석": {"work_style": "분석적이고 논리적", "work_env": "독립적으로 일하기"},
    "마케팅": {"work_style": "창의적이고 혁신적", "work_env": "팀워크 중심"},
    "기획": {"work_style": "체계적이고 계획적", "work_env": "팀워크 중심"},
    "프론트엔드": {"work_style": "창의적이고 혁신적", "work_env": "독립적으로 일하기"},
    "백엔드": {"work_style": "분석적이고 논리적", "work_env": "독립적으로 일하기"},
    "AI/ML": {"work_style": "분석적이고 논리적", "work_env": "독립적으로 일하기"}
}

def calculate_job_fit(work_style, work_env, interest_job):
    job_fit_scores = {}
    for job, char in job_characteristics.items():
        score = 0
        if work_style == char["work_style"]: score += 60
        if work_env == char["work_env"]: score += 40
        if job == interest_job: score = min(100, score + 10)
        job_fit_scores[job] = score
    return job_fit_scores

# --- 1. 사이드바 – 사용자 입력 ---
with st.sidebar:
    st.header("👤 나의 프로필 설정")
    # key를 추가하여 위젯 상태를 명확하게 관리
    interest_job = st.selectbox("관심 직무", skills_df["직무"].unique(), key="interest_job")
    career_level = st.selectbox("현재 경력 수준", levels_df["jobLevels"].unique(), key="career_level")
    
    st.markdown("---")
    st.header("🧠 나의 성향 진단")
    work_style = st.radio("선호하는 업무 스타일은?", ["분석적이고 논리적", "창의적이고 혁신적", "체계적이고 계획적", "사교적이고 협력적"], horizontal=True, key="work_style")
    work_env = st.radio("선호하는 업무 환경은?", ["독립적으로 일하기", "팀워크 중심", "빠른 변화와 도전", "안정적이고 예측 가능한"], horizontal=True, key="work_env")

# --- 분석 로직 실행 ---
job_fit_scores = calculate_job_fit(work_style, work_env, interest_job)
score_df = pd.DataFrame(job_fit_scores.items(), columns=["직무", "적합도"]).sort_values("적합도", ascending=False).reset_index(drop=True)
top_job = score_df.iloc[0]["직무"]

# --- 2. 타이틀 & 소개 ---
st.markdown('<div class="main-header"><h1>🧠 Job-Fit Insight Dashboard</h1><p>나의 성향과 시장 데이터를 결합한 최적의 커리어 인사이트를 찾아보세요.</p></div>', unsafe_allow_html=True)

# --- 3. 메인 대시보드 (탭 구성) ---
main_tabs = st.tabs(["🚀 나의 맞춤 분석", "📊 시장 동향 분석"])

with main_tabs[0]:
    st.subheader(f"사용자님을 위한 맞춤 직무 분석")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="highlight-card">', unsafe_allow_html=True)
        st.markdown(f"<h4>🏆 최적 추천 직무</h4><h1>{top_job}</h1>", unsafe_allow_html=True)
        st.progress(score_df.iloc[0]["적합도"])
        st.markdown(f"**적합도: {score_df.iloc[0]['적합도']}%**")
        st.markdown(f"_{work_style} 성향과 {work_env} 선호도는 **{top_job}** 직무와 가장 잘 맞습니다._")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        top_job_skills = skills_df[skills_df["직무"] == top_job]
        fig_skill = px.bar(
            top_job_skills.sort_values("빈도", ascending=True),
            x="빈도", y="기술스택", orientation='h',
            title=f"'{top_job}' 직무 핵심 기술 Top 10"
        )
        fig_skill.update_layout(yaxis_title="")
        st.plotly_chart(fig_skill, use_container_width=True)
        
    st.markdown("---")
    st.subheader("🎯 다른 추천 직무들")
    st.dataframe(score_df, use_container_width=True)


with main_tabs[1]:
    st.subheader("대한민국 채용 시장 트렌드 분석")
    market_tabs = st.tabs(["청년 고용지표", "직무별 기술스택", "직무별 경력레벨"])
    
    with market_tabs[0]:
        st.markdown("#### **📊 청년층 고용지표 (15-29세)**")
        
        month_cols = sorted([col.split('_')[0] for col in youth_df.columns if '_실업률' in col], reverse=True)
        selected_month = st.selectbox("조회할 월 선택", month_cols, key="selected_month")

        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.markdown(f'<div class="metric-card"><h4>{selected_month} 실업률</h4><h2>{youth_df[f"{selected_month}_실업률"].mean():.1f}%</h2></div>', unsafe_allow_html=True)
        m_col2.markdown(f'<div class="metric-card"><h4>경제활동인구</h4><h2>{int(youth_df[f"{selected_month}_경제활동인구"].sum()/10000):,} 만명</h2></div>', unsafe_allow_html=True)
        m_col3.markdown(f'<div class="metric-card"><h4>취업자 수</h4><h2>{int(youth_df[f"{selected_month}_취업자"].sum()/10000):,} 만명</h2></div>', unsafe_allow_html=True)

        fig_youth = px.bar(
            youth_df, x="성별", y=f"{selected_month}_실업률", color="성별",
            title=f"{selected_month} 성별 청년층 실업률", text_auto='.1f'
        )
        st.plotly_chart(fig_youth, use_container_width=True)

    with market_tabs[1]:
        st.markdown("#### **🛠️ 직무별 상위 기술스택 TOP 10**")
        job_to_show = st.selectbox("분석할 직무 선택", skills_df["직무"].unique(), key="skill_job")
        filtered_skills = skills_df[skills_df["직무"] == job_to_show]
        fig_skills_market = px.bar(
            filtered_skills.sort_values("빈도"), x="빈도", y="기술스택",
            title=f"'{job_to_show}' 직무 주요 기술스택", orientation='h'
        )
        st.plotly_chart(fig_skills_market, use_container_width=True)

    with market_tabs[2]:
        st.markdown("#### **📈 직무별 공고 경력레벨 분포**")
        fig_levels = px.bar(
            levels_df, x="jobLevels", y="공고수", color="직무",
            title="직무별/경력레벨별 공고 수 비교",
            category_orders={"jobLevels": ["신입", "1~3년", "4~6년", "7~10년"]},
            labels={"jobLevels": "경력 수준", "공고수": "채용 공고 수"}
        )
        st.plotly_chart(fig_levels, use_container_width=True)

# --- 푸터 ---
st.markdown("---")
st.markdown('<div style="text-align: center; color: #666;"><p>🧠 Job-Fit Insight Dashboard | Powered by Streamlit</p></div>', unsafe_allow_html=True)
