import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path
import glob # --- [추가] 파일 패턴 검색을 위해 glob 라이브러리 임포트 ---

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
        background: linear-gradient(90deg, #1f4e79 0%, #2980b9 100%); padding: 1.5rem; border-radius: 10px; color: white; margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa; padding: 1rem; border-radius: 10px; border-left: 5px solid #2980b9; margin-bottom: 1rem;
    }
    .highlight-card {
        background: white; padding: 1.5rem; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #ff6b35;
    }
    /* --- [추가] 채용 공고 카드를 위한 CSS --- */
    .job-posting-card {
        background: #ffffff; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 1rem; border: 1px solid #e9ecef;
    }
    .job-posting-card a {
        text-decoration: none; color: #1f4e79; font-weight: bold; font-size: 1.1em;
    }
    .job-posting-card p {
        margin: 0.3rem 0; color: #495057; font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)


# --- 데이터베이스 연결 및 데이터 로딩 ---
@st.cache_resource
def init_connection(db_path="data/job_fit_insight.db"):
    db_file = Path(db_path)
    if not db_file.exists():
        st.error(f"데이터베이스 파일('{db_path}')을 찾을 수 없습니다. `setup_database.py`를 먼저 실행해주세요.")
        st.stop()
    return sqlite3.connect(db_file, check_same_thread=False)

@st.cache_data
def load_data(_conn):
    youth_df = pd.read_sql("SELECT * FROM youth_summary", _conn)
    skills_df = pd.read_sql("SELECT * FROM top10_skills_per_job", _conn)
    levels_df = pd.read_sql("SELECT * FROM joblevel_counts", _conn)
    
    # --- [수정] 랠릿 채용공고 CSV 파일들을 로드하는 로직 ---
    rallit_df = None
    try:
        data_path = Path("data")
        csv_files = glob.glob(str(data_path / "rallit_*.csv"))
        if csv_files:
            df_list = [pd.read_csv(file) for file in csv_files]
            rallit_df = pd.concat(df_list, ignore_index=True)
            # 불필요한 열 제거 및 데이터 정리 (선택사항)
            rallit_df = rallit_df.drop_duplicates(subset=['url'])
    except FileNotFoundError:
        print("Warning: Rallit CSV 파일들을 찾을 수 없습니다.") # 개발자용 로그
    except Exception as e:
        print(f"Error loading Rallit CSVs: {e}")

    return youth_df, skills_df, levels_df, rallit_df

conn = init_connection()
youth_df, skills_df, levels_df, rallit_df = load_data(conn)


# --- 개인 맞춤 분석 로직 ---
# --- [추가] 스마트한 직무 매칭을 위한 카테고리 맵 ---
job_category_map = {
    "데이터 분석": ["데이터", "분석", "Data", "BI"],
    "마케팅": ["마케팅", "마케터", "Marketing", "광고"],
    "기획": ["기획", "PM", "PO", "서비스"],
    "프론트엔드": ["프론트엔드", "Frontend", "React", "Vue"],
    "백엔드": ["백엔드", "Backend", "Java", "Python", "서버"],
    "AI/ML": ["AI", "ML", "머신러닝", "딥러닝", "인공지능"],
    "디자인": ["디자인", "디자이너", "Designer", "UI", "UX", "BX"],
    "영업": ["영업", "Sales", "세일즈", "비즈니스"],
    "고객지원": ["CS", "CX", "고객", "지원", "서비스 운영"],
    "인사": ["인사", "HR", "채용", "조직문화"]
}
job_characteristics = {job: {"work_style": "분석적이고 논리적", "work_env": "독립적으로 일하기"} for job in job_category_map.keys()} # 예시 단순화

def calculate_job_fit(work_style, work_env, interest_job):
    job_fit_scores = {}
    # ... (기존 로직 유지) ...
    for job, char in job_characteristics.items():
        score = 0
        # 이 부분은 실제 서비스에 맞게 세밀하게 조정 필요
        if "분석" in work_style and "데이터" in job: score += 50
        elif "창의" in work_style and ("마케팅" in job or "디자인" in job): score += 50
        if "독립" in work_env and ("엔드" in job or "분석" in job): score += 40
        elif "팀워크" in work_env and ("기획" in job or "마케팅" in job): score += 40
        if job == interest_job: score = min(100, score + 20)
        job_fit_scores[job] = score + 10 # 기본 점수
    return job_fit_scores

# --- 1. 사이드바 – 사용자 입력 ---
with st.sidebar:
    st.header("👤 나의 프로필 설정")
    job_options = sorted(list(job_category_map.keys()))
    interest_job = st.selectbox("관심 직무", job_options, key="interest_job")
    career_options = ["상관 없음", "신입", "1-3년", "4-6년", "7-10년 이상"]
    career_level = st.selectbox("희망 경력 수준", career_options, key="career_level")
    
    st.markdown("---")
    st.header("🧠 나의 성향 진단")
    # ... (기존 로직 유지) ...
    work_style = st.radio("선호하는 업무 스타일은?", ["분석적이고 논리적", "창의적이고 혁신적", "체계적이고 계획적", "사교적이고 협력적"], horizontal=True, key="work_style")
    work_env = st.radio("선호하는 업무 환경은?", ["독립적으로 일하기", "팀워크 중심", "빠른 변화와 도전", "안정적이고 예측 가능한"], horizontal=True, key="work_env")


# --- 분석 로직 실행 ---
job_fit_scores = calculate_job_fit(work_style, work_env, interest_job)
score_df = pd.DataFrame(job_fit_scores.items(), columns=["직무", "적합도"]).sort_values("적합도", ascending=False).reset_index(drop=True)
top_job = score_df.iloc[0]["직무"] if not score_df.empty else "분석 결과 없음"

# --- 2. 타이틀 & 소개 ---
st.markdown('<div class="main-header"><h1>🧠 Job-Fit Insight Dashboard</h1><p>나의 성향과 시장 데이터를 결합한 최적의 커리어 인사이트를 찾아보세요.</p></div>', unsafe_allow_html=True)

# --- 3. 메인 대시보드 (탭 구성) ---
main_tabs = st.tabs(["🚀 나의 맞춤 분석", "📊 시장 동향 분석"])

with main_tabs[0]:
    st.subheader(f"사용자님을 위한 맞춤 직무 분석")
    
    col1, col2 = st.columns(2)
    with col1:
        # ... (기존 추천 로직 카드 유지) ...
        st.markdown('<div class="highlight-card">', unsafe_allow_html=True)
        st.markdown(f"<h4>🏆 최적 추천 직무</h4><h1>{top_job}</h1>", unsafe_allow_html=True)
        progress_value = score_df.iloc[0]["적합도"]
        st.progress(int(progress_value) / 100)
        st.markdown(f"**적합도: {progress_value}%**")
        st.markdown(f"👉 **'{work_style}'** 성향과 **'{work_env}'** 환경을 선호하는 당신에게는 **'{top_job}'** 직무가 가장 잘 맞아요!")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # ... (기존 스킬 정보 로직 유지) ...
        skills_to_show = skills_df[skills_df["직무"] == top_job]
        chart_title = f"'{top_job}' 직무 핵심 기술"
        if skills_to_show.empty:
            skills_to_show = skills_df[skills_df["직무"] == interest_job]
            if not skills_to_show.empty:
                st.info(f"'{top_job}'의 스킬 정보가 없어, 관심 직무 **'{interest_job}'**의 정보를 대신 표시합니다.")
                chart_title = f"'{interest_job}' 직무 핵심 기술 (관심 직무)"
        if not skills_to_show.empty:
            fig_skill = px.bar(skills_to_show.sort_values("빈도", ascending=True), x="빈도", y="기술스택", orientation='h', title=chart_title)
            fig_skill.update_layout(yaxis_title="")
            st.plotly_chart(fig_skill, use_container_width=True)
        else:
            st.warning(f"'{top_job}' 및 '{interest_job}' 직무에 대한 상세 스킬 정보가 아직 준비되지 않았습니다.")
        
    # --- [추가] 랠릿 채용공고 추천 섹션 ---
    st.markdown("---")
    st.subheader("📌 나에게 맞는 Rallit 채용공고")

    if rallit_df is not None:
        # 1. 직무 필터링 (스마트 매칭)
        search_keywords = job_category_map.get(interest_job, [interest_job])
        keyword_regex = '|'.join(search_keywords)
        job_mask = rallit_df["직무"].str.contains(keyword_regex, case=False, na=False)
        
        # 2. 경력 필터링 (유연한 매칭)
        if career_level == "상관 없음":
            career_mask = pd.Series(True, index=rallit_df.index) # 모든 공고 선택
        elif career_level == "신입":
            career_mask = rallit_df["jobLevels"].str.contains("신입|경력 무관", case=False, na=False)
        else: # "1-3년" 등
            # '년'을 제거하고 숫자만 비교하는 등 더 정교화 가능
            career_mask = rallit_df["jobLevels"].str.contains(career_level.replace('-','~'), case=False, na=False)
            
        filtered_jobs = rallit_df[job_mask & career_mask]
        top_jobs = filtered_jobs.head(5)

        if not top_jobs.empty:
            for _, row in top_jobs.iterrows():
                st.markdown(f"""
                <div class="job-posting-card">
                    <a href="{row['url']}" target="_blank">{row['title']}</a>
                    <p>🏢 **회사:** {row['companyName']} | 📍 **지역:** {row.get('addressRegion', '정보 없음')}</p>
                    <p>🛠️ **기술스택:** {row.get('jobSkillKeywords', '정보 없음')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"'{interest_job}' 직무와 '{career_level}' 수준에 맞는 채용 공고를 찾지 못했습니다.")
    else:
        st.warning("❗ 랠릿 채용공고 데이터를 불러올 수 없습니다. `data` 폴더에 `rallit_*.csv` 파일이 있는지 확인해주세요.")


with main_tabs[1]:
    # ... (시장 동향 분석 탭은 기존과 동일)
    st.subheader("대한민국 채용 시장 트렌드 분석")
    # ... (이하 모든 코드 동일)

# --- 푸터 ---
st.markdown("---")
st.markdown('<div style="text-align: center; color: #666;"><p>🧠 Job-Fit Insight Dashboard | Powered by Streamlit</p></div>', unsafe_allow_html=True)
