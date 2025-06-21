import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path
import glob
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import platform

# --- 1. 페이지 기본 설정 ---
st.set_page_config(
    page_title="Job-Fit Insight Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    db_file = Path(db_path)
    if not db_file.exists():
        st.error(f"데이터베이스 파일('{db_path}')을 찾을 수 없습니다. `setup_database.py`를 먼저 실행해주세요.")
        st.stop()
    return sqlite3.connect(db_file, check_same_thread=False)

def generate_sample_youth_data():
    data = {'성별': ['남성', '여성', '남성', '여성'], '연령계층별': ['15-29세', '15-29세', '30-39세', '30-39세'], '2025.03_실업률': [6.8, 6.1, 3.1, 3.5], '2025.03_경제활동인구': [2450000, 2150000, 3400000, 3100000], '2025.03_취업자': [2283000, 2018000, 3295000, 2990000], '2025.04_실업률': [7.0, 6.3, 3.2, 3.6], '2025.04_경제활동인구': [2460000, 2160000, 3420000, 3120000], '2025.04_취업자': [2287000, 2023000, 3310000, 3010000], '2025.05_실업률': [6.9, 6.2, 3.0, 3.4], '2025.05_경제활동인구': [2470000, 2170000, 3430000, 3130000], '2025.05_취업자': [2299000, 2035000, 3325000, 3020000]}
    return pd.DataFrame(data)

@st.cache_data
def load_data(_conn):
    skills_df = pd.read_sql("SELECT * FROM top10_skills_per_job", _conn)
    levels_df = pd.read_sql("SELECT * FROM joblevel_counts", _conn)
    rallit_df = None
    try:
        csv_files = glob.glob(str(Path("data") / "rallit_*.csv"))
        if csv_files:
            rallit_df = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True).drop_duplicates(subset=['url']).reset_index(drop=True)
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

@st.cache_data
def create_word_cloud(df):
    d = dict(zip(df['기술스택'], df['빈도']))
    system = platform.system()
    font_path = 'NanumGothic.ttf' if Path('NanumGothic.ttf').exists() else ('malgun' if system == 'Windows' else None)
    wc = WordCloud(font_path=font_path, background_color='white', width=400, height=300, colormap='viridis').generate_from_frequencies(d)
    return wc

def show_trend_chart(df, age_group):
    st.markdown(f"#### 📈 {age_group} 고용 시계열 추이 (전체 성별 기준)")
    overall = df[(df["성별"] == "전체") & (df["연령계층별"] == age_group)].sort_values("월")
    if overall.empty: st.info("선택된 연령대의 시계열 데이터가 없습니다."); return
    col = st.selectbox("📊 시계열 항목 선택", ["실업률", "경제활동인구", "취업자"], key="trend_col")
    fig = px.line(overall, x="월", y=col, title=f"{col} 월별 추이", markers=True)
    if col == "실업률": hovertemplate = "<b>월</b>: %{x}<br><b>실업률</b>: %{y:.1f}%"
    else: hovertemplate = f"<b>월</b>: %{{x}}<br><b>{col}</b>: %{{y:,.0f}}명"
    fig.update_traces(line_shape="spline", hovertemplate=hovertemplate)
    st.plotly_chart(fig, use_container_width=True)

# --- [수정] 누락된 데이터 로딩 호출 코드 추가 ---
conn = init_connection()
trend_df, skills_df, levels_df, rallit_df = load_data(conn)

# --- 4. 분석 로직 및 5. 사이드바 UI ---
job_category_map = { "데이터 분석": ["데이터", "분석", "Data", "BI"], "마케팅": ["마케팅", "마케터", "Marketing", "광고", "콘텐츠"], "기획": ["기획", "PM", "PO", "서비스", "Product"], "프론트엔드": ["프론트엔드", "Frontend", "React", "Vue", "웹 개발"], "백엔드": ["백엔드", "Backend", "Java", "Python", "서버", "Node.js"], "AI/ML": ["AI", "ML", "머신러닝", "딥러닝", "인공지능"], "디자인": ["디자인", "디자이너", "Designer", "UI", "UX", "BX", "그래픽"], "영업": ["영업", "Sales", "세일즈", "비즈니스", "Business Development"], "고객지원": ["CS", "CX", "고객", "지원", "서비스 운영"], "인사": ["인사", "HR", "채용", "조직문화", "Recruiting"] }
def calculate_job_fit(work_style, work_env, interest_job):
    job_fit_scores = {}
    for job in job_category_map.keys():
        score = 0
        if "분석" in work_style and any(k in job for k in ["데이터", "AI/ML", "백엔드"]): score += 50
        elif "창의" in work_style and any(k in job for k in ["마케팅", "디자인", "기획"]): score += 50
        if "독립" in work_env and any(k in job for k in ["엔드", "분석", "AI/ML"]): score += 40
        elif "팀워크" in work_env and any(k in job for k in ["기획", "마케팅", "디자인"]): score += 40
        if job == interest_job: score += 15
        job_fit_scores[job] = min(100, score + 5)
    return job_fit_scores

with st.sidebar:
    with st.container(border=True):
        st.header("👤 나의 프로필 설정")
        job_options = sorted(list(job_category_map.keys()))
        interest_job = st.selectbox("관심 직무", job_options, key="interest_job")
        career_options = ["상관 없음", "신입", "1-3년", "4-6년", "7-10년 이상"]
        career_level = st.selectbox("희망 경력 수준", career_options, key="career_level")
    st.write("")
    with st.container(border=True):
        st.header("🧠 나의 성향 진단")
        work_style = st.radio("선호하는 업무 스타일은?", ["분석적이고 논리적", "창의적이고 혁신적", "체계적이고 계획적", "사교적이고 협력적"], key="work_style")
        work_env = st.radio("선호하는 업무 환경은?", ["독립적으로 일하기", "팀워크 중심", "빠른 변화와 도전", "안정적이고 예측 가능한"], key="work_env")

# 6. 메인 로직 실행
job_fit_scores = calculate_job_fit(work_style, work_env, interest_job)
score_df = pd.DataFrame(job_fit_scores.items(), columns=["직무", "적합도"]).sort_values("적합도", ascending=False).reset_index(drop=True)
top_job = score_df.iloc[0]["직무"] if not score_df.empty else "분석 결과 없음"

# 7. 대시보드 본문
st.markdown('<div class="main-header"><h1>🧠 Job-Fit Insight Dashboard</h1><p>나의 성향과 시장 데이터를 결합한 최적의 커리어 인사이트를 찾아보세요.</p></div>', unsafe_allow_html=True)
main_tabs = st.tabs(["🚀 나의 맞춤 분석", "📊 시장 동향 분석"])

with main_tabs[0]:
    st.subheader(f"사용자님을 위한 맞춤 직무 분석")
    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        st.markdown('<div class="highlight-card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown(f"<h4>🏆 최적 추천 직무</h4><h1>{top_job}</h1>", unsafe_allow_html=True)
        progress_value = score_df.iloc[0]["적합도"]
        st.progress(int(progress_value) / 100)
        st.markdown(f"**적합도: {progress_value}%**")
        st.markdown(f"👉 **'{work_style}'** 성향과 **'{work_env}'** 환경을 선호하는 당신에게는 **'{top_job}'** 직무가 가장 잘 맞아요!")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        skills_to_show = skills_df[skills_df["직무"] == top_job]
        fallback_used = False
        if skills_to_show.empty:
            skills_to_show = skills_df[skills_df["직무"] == interest_job]
            fallback_used = True
        
        if not skills_to_show.empty:
            if fallback_used: st.info(f"'{top_job}'의 스킬 정보가 없어, 관심 직무 **'{interest_job}'**의 정보를 대신 표시합니다.")
            
            skill_tabs = st.tabs(["📊 기술 스택 빈도", "☁️ 워드 클라우드"])
            with skill_tabs[0]:
                fig_skill = px.bar(skills_to_show.sort_values("빈도", ascending=True), x="빈도", y="기술스택", orientation='h', title=f"'{interest_job if fallback_used else top_job}' 핵심 기술")
                fig_skill.update_layout(yaxis_title="", height=400)
                st.plotly_chart(fig_skill, use_container_width=True)
            with skill_tabs[1]:
                try:
                    wc = create_word_cloud(skills_to_show)
                    fig, ax = plt.subplots()
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)
                except Exception as e:
                    st.error("워드 클라우드 생성 중 오류가 발생했습니다. 한글 폰트가 지원되지 않는 환경일 수 있습니다.")
        else:
            with st.container(border=True):
                st.warning(f"'{top_job}' 직무의 상세 스킬 정보가 아직 준비되지 않았습니다.")
                st.write("다른 직무의 기술 트렌드가 궁금하신가요?")
                st.info("상단의 **'시장 동향 분석'** 탭을 클릭하여 **'기술 스택'**을 확인해보세요!")
    
    st.markdown("---")
    st.subheader("📌 나에게 맞는 Rallit 채용공고")
    if rallit_df is not None:
        required_cols = ['title', 'jobLevels']
        if all(col in rallit_df.columns for col in required_cols):
            search_keywords = job_category_map.get(interest_job, [interest_job])
            keyword_regex = '|'.join(search_keywords)
            job_mask = rallit_df["title"].str.contains(keyword_regex, case=False, na=False)
            if career_level == "상관 없음": career_mask = pd.Series(True, index=rallit_df.index)
            elif career_level == "신입": career_mask = rallit_df["jobLevels"].str.contains("신입|경력 무관|신입~", case=False, na=False)
            else: career_mask = rallit_df["jobLevels"].str.contains(career_level.replace('-','~'), case=False, na=False)
            filtered_jobs = rallit_df[job_mask & career_mask]
            top_jobs = filtered_jobs.head(5)
            if not top_jobs.empty:
                for _, row in top_jobs.iterrows():
                    st.markdown(f"""
                    <div class="job-posting-card">
                        <a href="{row['url']}" target="_blank">{row['title']}</a>
                        <p>🏢 **회사:** {row.get('companyName', '정보 없음')} | 📍 **지역:** {row.get('addressRegion', '정보 없음')}</p>
                        <p>🛠️ **기술스택:** {row.get('jobSkillKeywords', '정보 없음')}</p>
                    </div>""", unsafe_allow_html=True)
            else: st.info(f"'{interest_job}' 직무와 '{career_level}' 수준에 맞는 채용 공고를 찾지 못했습니다.")
        else: st.error(f"Rallit 데이터 파일에 필수 컬럼('title', 'jobLevels')이 없습니다. CSV 파일의 컬럼명을 확인해주세요.")
    else: st.warning("❗ 랠릿 채용공고 데이터를 불러올 수 없습니다. `data` 폴더에 `rallit_*.csv` 파일이 있는지 확인해주세요.")

with main_tabs[1]:
    st.subheader("대한민국 채용 시장 트렌드 분석")
    market_tabs = st.tabs(["고용 동향", "기술 스택", "경력 분포"])
    with market_tabs[0]:
        if not trend_df.empty:
            age_options = sorted(trend_df["연령계층별"].unique())
            selected_age = st.selectbox("🔎 연령 계층 선택", age_options, index=age_options.index("15-29세") if "15-29세" in age_options else 0)
            st.markdown(f"#### **📊 {selected_age} 고용지표**")
            month_options = sorted(trend_df["월"].unique(), reverse=True)
            selected_month = st.selectbox("🗓️ 조회할 월 선택", month_options, key="selected_month_v4")
            filtered_trend = trend_df[trend_df['연령계층별'] == selected_age]
            try:
                current_overall = filtered_trend[(filtered_trend["월"] == selected_month) & (filtered_trend["성별"] == "전체")].iloc[0]
                current_unemployment_rate, current_active_pop_k, current_employed_pop_k = current_overall['실업률'], current_overall['경제활동인구'] / 1000, current_overall['취업자'] / 1000
                delta_unemployment, delta_active, delta_employed = None, None, None
                prev_month_index = month_options.index(selected_month) + 1
                if prev_month_index < len(month_options):
                    prev_month = month_options[prev_month_index]
                    prev_overall = filtered_trend[(filtered_trend["월"] == prev_month) & (filtered_trend["성별"] == "전체")].iloc[0]
                    delta_unemployment = f"{current_unemployment_rate - prev_overall['실업률']:.1f}%p"
                    delta_active = f"{(current_active_pop_k - prev_overall['경제활동인구']/1000):,.0f} 천명"
                    delta_employed = f"{(current_employed_pop_k - prev_overall['취업자']/1000):,.0f} 천명"
                m_col1, m_col2, m_col3 = st.columns(3)
                m_col1.metric(label="실업률 (전체)", value=f"{current_unemployment_rate:.1f}%", delta=delta_unemployment, delta_color="inverse")
                m_col2.metric(label="경제활동인구 (단위: 천명)", value=f"{current_active_pop_k:,.0f}", delta=delta_active)
                m_col3.metric(label="취업자 수 (단위: 천명)", value=f"{current_employed_pop_k:,.0f}", delta=delta_employed)
                st.markdown("---")
                gender_data = filtered_trend[(filtered_trend["월"] == selected_month) & (filtered_trend["성별"] != "전체")]
                fig_youth = px.bar(gender_data, x="성별", y="실업률", color="성별", title=f"{selected_month} 성별 실업률", text_auto='.1f', color_discrete_map={'남성': '#1f77b4', '여성': '#ff7f0e'})
                fig_youth.update_traces(textposition='outside')
                st.plotly_chart(fig_youth, use_container_width=True)
                st.markdown("---")
                show_trend_chart(trend_df, selected_age)
            except IndexError: st.warning(f"'{selected_age}', '{selected_month}'에 대한 데이터가 없습니다. 다른 조건을 선택해주세요.")
        else: st.warning("고용지표 데이터를 불러오지 못했습니다.")
    with market_tabs[1]:
        st.markdown("#### **🛠️ 직무별 상위 기술스택 TOP 10**")
        job_to_show = st.selectbox("분석할 직무 선택", sorted(skills_df["직무"].unique()), key="skill_job")
        filtered_skills = skills_df[skills_df["직무"] == job_to_show]
        fig_skills_market = px.bar(filtered_skills.sort_values("빈도"), x="빈도", y="기술스택", title=f"'{job_to_show}' 직무 주요 기술스택", orientation='h')
        st.plotly_chart(fig_skills_market, use_container_width=True)
    with market_tabs[2]:
        st.markdown("#### **📈 직무별 공고 경력레벨 분포**")
        c1, c2 = st.columns(2)
        with c1:
            fig_levels = px.bar(levels_df, x="jobLevels", y="공고수", color="직무", title="전체 직무별 경력 분포", category_orders={"jobLevels": ["JUNIOR", "MIDDLE", "SENIOR"]}, labels={"jobLevels": "경력 수준", "공고수": "채용 공고 수"})
            st.plotly_chart(fig_levels, use_container_width=True)
        with c2:
            st.markdown("#### **🎯 특정 직무 경력 분포**")
            selected_pie_job = st.selectbox("직무 선택", sorted(levels_df["직무"].unique()), key="pie_job")
            single_job_levels = levels_df[levels_df['직무'] == selected_pie_job]
            if not single_job_levels.empty:
                fig_pie = px.pie(single_job_levels, names='jobLevels', values='공고수', title=f"'{selected_pie_job}' 직무 경력 분포", hole=0.3)
                fig_pie.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info(f"'{selected_pie_job}' 직무에 대한 경력 분포 데이터가 없습니다.")

# 8. 푸터
st.markdown("---")
st.markdown('<div style="text-align: center; color: #666;"><p>🧠 Job-Fit Insight Dashboard | Powered by Streamlit</p></div>', unsafe_allow_html=True)
