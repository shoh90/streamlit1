import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# 페이지 설정
st.set_page_config(
    page_title="Job-Fit 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2980b9 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2980b9;
        margin: 0.5rem 0;
    }
    .job-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #ff6b35;
    }
    .growth-path {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------
# 1. 사이드바 – 사용자 입력
# ------------------------
with st.sidebar:
    st.markdown("## 🔍 나의 기본 정보")
    
    # 기본 정보 입력
    region = st.selectbox(
        "거주 지역을 선택하세요", 
        ["서울", "경기", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
    )
    
    interest_job = st.selectbox(
        "관심 직무", 
        ["데이터 분석", "마케팅", "기획", "프론트엔드", "백엔드", "AI/ML", "디자인", "영업", "고객지원", "인사", "재무", "법무"]
    )
    
    career_level = st.radio(
        "경력 수준", 
        ["신입", "1~3년", "4~6년", "7~10년", "10년 이상"]
    )
    
    education = st.selectbox(
        "학력", 
        ["고등학교", "전문대학", "대학교", "대학원"]
    )
    
    # 성향 진단 문항 (간단 버전)
    st.markdown("### 🧠 성향 진단")
    st.markdown("**나의 업무 스타일은?**")
    work_style = st.radio(
        "업무 스타일",
        ["분석적이고 논리적", "창의적이고 혁신적", "체계적이고 계획적", "사교적이고 협력적"]
    )
    
    st.markdown("**선호하는 업무 환경은?**")
    work_env = st.radio(
        "업무 환경",
        ["독립적으로 일하기", "팀워크 중심", "빠른 변화와 도전", "안정적이고 예측 가능한"]
    )

# ------------------------
# 2. 타이틀 & 소개
# ------------------------
st.markdown("""
<div class="main-header">
    <h1>📊 Job-Fit 대시보드</h1>
    <p>직무 적합도 진단 + 지역 기반 고용지표 + 추천 채용 연계까지<br>
    <strong>AI 기반 맞춤 채용 플랫폼 대시보드</strong>입니다.</p>
</div>
""", unsafe_allow_html=True)

# ------------------------
# 3. 고용지표 기반 지역 진단
# ------------------------
st.markdown("## 📌 지역 고용 진단 요약")

# 고용지표 데이터
region_data = {
    "서울": {"실업률": 6.4, "청년 고용률": 57.2, "평균 연봉": 4200, "고용 성장률": 2.1},
    "경기": {"실업률": 5.9, "청년 고용률": 59.3, "평균 연봉": 3800, "고용 성장률": 3.2},
    "부산": {"실업률": 7.1, "청년 고용률": 54.5, "평균 연봉": 3500, "고용 성장률": 1.8},
    "대구": {"실업률": 6.9, "청년 고용률": 53.8, "평균 연봉": 3400, "고용 성장률": 1.5},
    "인천": {"실업률": 5.7, "청년 고용률": 58.9, "평균 연봉": 3600, "고용 성장률": 2.8},
    "광주": {"실업률": 6.2, "청년 고용률": 56.1, "평균 연봉": 3300, "고용 성장률": 2.0},
    "대전": {"실업률": 5.8, "청년 고용률": 58.2, "평균 연봉": 3500, "고용 성장률": 2.5},
    "울산": {"실업률": 5.5, "청년 고용률": 60.1, "평균 연봉": 4200, "고용 성장률": 1.9},
    "세종": {"실업률": 4.8, "청년 고용률": 62.3, "평균 연봉": 3800, "고용 성장률": 4.1},
    "강원": {"실업률": 6.8, "청년 고용률": 52.4, "평균 연봉": 3000, "고용 성장률": 1.2},
    "충북": {"실업률": 6.1, "청년 고용률": 55.7, "평균 연봉": 3200, "고용 성장률": 2.3},
    "충남": {"실업률": 5.9, "청년 고용률": 56.8, "평균 연봉": 3300, "고용 성장률": 2.7},
    "전북": {"실업률": 6.5, "청년 고용률": 54.2, "평균 연봉": 3100, "고용 성장률": 1.9},
    "전남": {"실업률": 6.7, "청년 고용률": 53.1, "평균 연봉": 3000, "고용 성장률": 1.6},
    "경북": {"실업률": 6.3, "청년 고용률": 55.3, "평균 연봉": 3200, "고용 성장률": 2.0},
    "경남": {"실업률": 6.0, "청년 고용률": 56.9, "평균 연봉": 3400, "고용 성장률": 2.4},
    "제주": {"실업률": 7.2, "청년 고용률": 51.8, "평균 연봉": 3200, "고용 성장률": 1.3}
}

if region in region_data:
    r = region_data[region]
    
    # 메트릭 카드들
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>청년 고용률</h4>
            <h2>{r['청년 고용률']}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>지역 실업률</h4>
            <h2>{r['실업률']}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>평균 연봉</h4>
            <h2>{r['평균 연봉']:,}만원</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4>고용 성장률</h4>
            <h2>{r['고용 성장률']}%</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # 지역별 고용지표 비교 차트
    st.markdown("### 📈 지역별 고용지표 비교")
    
    # 선택된 지역과 다른 지역들 비교
    comparison_data = []
    for reg, data in region_data.items():
        comparison_data.append({
            "지역": reg,
            "청년 고용률": data["청년 고용률"],
            "실업률": data["실업률"],
            "선택여부": "선택" if reg == region else "기타"
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    fig = px.scatter(
        comparison_df, 
        x="실업률", 
        y="청년 고용률",
        color="선택여부",
        size="청년 고용률",
        hover_data=["지역"],
        title=f"{region} 지역 고용지표 분석",
        color_discrete_map={"선택": "#ff6b35", "기타": "#2980b9"}
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# ------------------------
# 4. 직무 적합도 분석 결과
# ------------------------
st.markdown("## ✅ 직무 적합도 분석 결과")

# 성향 기반 직무 적합도 계산
def calculate_job_fit(work_style, work_env, interest_job):
    base_scores = {
        "데이터 분석": {"분석적이고 논리적": 20, "창의적이고 혁신적": 10, "체계적이고 계획적": 15, "사교적이고 협력적": 5},
        "마케팅": {"분석적이고 논리적": 15, "창의적이고 혁신적": 20, "체계적이고 계획적": 10, "사교적이고 협력적": 15},
        "기획": {"분석적이고 논리적": 15, "창의적이고 혁신적": 20, "체계적이고 계획적": 20, "사교적이고 협력적": 10},
        "프론트엔드": {"분석적이고 논리적": 15, "창의적이고 혁신적": 15, "체계적이고 계획적": 10, "사교적이고 협력적": 10},
        "백엔드": {"분석적이고 논리적": 20, "창의적이고 혁신적": 10, "체계적이고 계획적": 15, "사교적이고 협력적": 5},
        "AI/ML": {"분석적이고 논리적": 25, "창의적이고 혁신적": 15, "체계적이고 계획적": 10, "사교적이고 협력적": 5},
        "디자인": {"분석적이고 논리적": 10, "창의적이고 혁신적": 25, "체계적이고 계획적": 10, "사교적이고 협력적": 10},
        "영업": {"분석적이고 논리적": 10, "창의적이고 혁신적": 10, "체계적이고 계획적": 15, "사교적이고 협력적": 25},
        "고객지원": {"분석적이고 논리적": 10, "창의적이고 혁신적": 5, "체계적이고 계획적": 15, "사교적이고 협력적": 25},
        "인사": {"분석적이고 논리적": 15, "창의적이고 혁신적": 10, "체계적이고 계획적": 20, "사교적이고 협력적": 15},
        "재무": {"분석적이고 논리적": 25, "창의적이고 혁신적": 5, "체계적이고 계획적": 20, "사교적이고 협력적": 5},
        "법무": {"분석적이고 논리적": 25, "창의적이고 혁신적": 5, "체계적이고 계획적": 20, "사교적이고 협력적": 5}
    }
    
    job_fit_scores = {}
    for job in base_scores.keys():
        base_score = base_scores[job][work_style]
        
        # 관심 직무 보너스
        if job == interest_job:
            base_score += 15
        
        # 경력 수준에 따른 조정
        if career_level == "신입":
            base_score += 5
        elif career_level == "1~3년":
            base_score += 10
        elif career_level == "4~6년":
            base_score += 15
        elif career_level == "7~10년":
            base_score += 20
        else:
            base_score += 25
        
        # 최대 100점으로 제한
        job_fit_scores[job] = min(100, base_score)
    
    return job_fit_scores

job_fit_score = calculate_job_fit(work_style, work_env, interest_job)

# 직무 적합도 차트
score_df = pd.DataFrame({
    "직무": list(job_fit_score.keys()),
    "적합도": list(job_fit_score.values())
})

# 상위 5개 직무만 표시
top_jobs = score_df.nlargest(5, "적합도")

fig = px.bar(
    top_jobs, 
    x="직무", 
    y="적합도", 
    color="적합도",
    text="적합도",
    range_y=[0, 100],
    color_continuous_scale="viridis",
    title="직무별 적합도 분석 (상위 5개)"
)
fig.update_traces(texttemplate='%{text}%', textposition='outside')
fig.update_layout(height=400)
st.plotly_chart(fig, use_container_width=True)

# 상세 분석 결과
st.markdown("### 📋 상세 분석 결과")
top_job = top_jobs.iloc[0]["직무"]
top_score = top_jobs.iloc[0]["적합도"]

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="job-card">
        <h3>🏆 최적 직무: {top_job}</h3>
        <h2>적합도: {top_score}%</h2>
        <p><strong>분석:</strong> {work_style}한 성향과 {work_env}한 환경 선호도가 {top_job} 직무와 높은 매칭도를 보입니다.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="job-card">
        <h3>📊 관심 직무: {interest_job}</h3>
        <h2>적합도: {job_fit_score[interest_job]}%</h2>
        <p><strong>분석:</strong> 현재 관심을 보이는 {interest_job} 직무도 {job_fit_score[interest_job]}%의 적합도를 보입니다.</p>
    </div>
    """, unsafe_allow_html=True)

# ------------------------
# 5. 직무별 교육 경로 제안
# ------------------------
st.markdown("## 🎓 성장 경로 추천")

# 교육 경로 데이터
education_paths = {
    "데이터 분석": {
        "기초": ["파이썬 기초", "통계학 기초", "Excel 고급 활용"],
        "중급": ["판다스/시각화", "SQL 실습", "데이터 전처리"],
        "고급": ["머신러닝 기초", "포트폴리오 프로젝트", "실무 데이터 분석"],
        "추천강의": "패스트캠퍼스 데이터 부트캠프",
        "예상기간": "3-6개월",
        "예상비용": "150-300만원"
    },
    "마케팅": {
        "기초": ["마케팅 원론", "소비자 행동론", "디지털 마케팅 기초"],
        "중급": ["SNS 마케팅", "콘텐츠 마케팅", "데이터 분석"],
        "고급": ["브랜드 전략", "마케팅 캠페인 기획", "실무 프로젝트"],
        "추천강의": "구글 디지털 마케팅 과정",
        "예상기간": "2-4개월",
        "예상비용": "50-150만원"
    },
    "기획": {
        "기초": ["서비스 기획 기초", "UX/UI 기초", "시장 분석"],
        "중급": ["기획서 작성법", "Notion 활용", "프로토타이핑"],
        "고급": ["실무 기획안 작성", "A/B 테스트", "성과 분석"],
        "추천강의": "숨고 서비스 기획 입문",
        "예상기간": "3-5개월",
        "예상비용": "100-200만원"
    },
    "프론트엔드": {
        "기초": ["HTML/CSS", "JavaScript 기초", "반응형 웹"],
        "중급": ["React/Vue.js", "TypeScript", "상태관리"],
        "고급": ["성능 최적화", "포트폴리오 제작", "실무 프로젝트"],
        "추천강의": "코딩애플 React 완전정복",
        "예상기간": "4-8개월",
        "예상비용": "100-300만원"
    },
    "백엔드": {
        "기초": ["Java/Python 기초", "데이터베이스", "네트워크 기초"],
        "중급": ["Spring/Django", "API 설계", "보안 기초"],
        "고급": ["클라우드 서비스", "성능 최적화", "실무 프로젝트"],
        "추천강의": "인프런 Spring Boot 강의",
        "예상기간": "6-12개월",
        "예상비용": "150-400만원"
    }
}

if top_job in education_paths:
    path = education_paths[top_job]
    
    st.markdown(f"""
    <div class="growth-path">
        <h3>🚀 {top_job} 성장 로드맵</h3>
        <p><strong>추천 강의:</strong> {path['추천강의']}</p>
        <p><strong>예상 기간:</strong> {path['예상기간']} | <strong>예상 비용:</strong> {path['예상비용']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📚 기초 단계")
        for item in path["기초"]:
            st.markdown(f"- {item}")
    
    with col2:
        st.markdown("### 🔧 중급 단계")
        for item in path["중급"]:
            st.markdown(f"- {item}")
    
    with col3:
        st.markdown("### 🎯 고급 단계")
        for item in path["고급"]:
            st.markdown(f"- {item}")

# ------------------------
# 6. 채용 공고 매칭 결과
# ------------------------
st.markdown("## 📬 매칭된 채용 공고")

# 채용 공고 데이터
job_posts_data = {
    "데이터 분석": [
        {"회사": "에이아이랩", "직무": "데이터 분석가", "지역": region, "매칭점수": 89, "연봉": "3500-4500", "경력": "1-3년"},
        {"회사": "넥스트마켓", "직무": "데이터 사이언티스트", "지역": region, "매칭점수": 84, "연봉": "4000-5500", "경력": "3-5년"},
        {"회사": "데이터프렌즈", "직무": "비즈니스 분석가", "지역": region, "매칭점수": 76, "연봉": "3000-4000", "경력": "신입-3년"}
    ],
    "마케팅": [
        {"회사": "브랜드원", "직무": "디지털 마케터", "지역": region, "매칭점수": 92, "연봉": "3200-4200", "경력": "1-3년"},
        {"회사": "콘텐츠랩", "직무": "콘텐츠 마케터", "지역": region, "매칭점수": 87, "연봉": "2800-3800", "경력": "신입-2년"},
        {"회사": "마케팅플러스", "직무": "브랜드 매니저", "지역": region, "매칭점수": 79, "연봉": "3500-5000", "경력": "3-7년"}
    ],
    "기획": [
        {"회사": "서비스랩", "직무": "서비스 기획자", "지역": region, "매칭점수": 91, "연봉": "3500-5000", "경력": "2-5년"},
        {"회사": "플랫폼코", "직무": "프로덕트 매니저", "지역": region, "매칭점수": 85, "연봉": "4000-6000", "경력": "3-6년"},
        {"회사": "기획스튜디오", "직무": "비즈니스 기획자", "지역": region, "매칭점수": 78, "연봉": "3000-4500", "경력": "1-4년"}
    ],
    "프론트엔드": [
        {"회사": "웹스튜디오", "직무": "프론트엔드 개발자", "지역": region, "매칭점수": 88, "연봉": "3500-5000", "경력": "1-4년"},
        {"회사": "앱팩토리", "직무": "React 개발자", "지역": region, "매칭점수": 82, "연봉": "3200-4500", "경력": "2-5년"},
        {"회사": "웹랩", "직무": "Vue.js 개발자", "지역": region, "매칭점수": 75, "연봉": "2800-4000", "경력": "신입-3년"}
    ],
    "백엔드": [
        {"회사": "서버랩", "직무": "백엔드 개발자", "지역": region, "매칭점수": 86, "연봉": "3800-5500", "경력": "2-5년"},
        {"회사": "API스튜디오", "직무": "Java 개발자", "지역": region, "매칭점수": 80, "연봉": "3500-5000", "경력": "3-6년"},
        {"회사": "백엔드팩토리", "직무": "Python 개발자", "지역": region, "매칭점수": 73, "연봉": "3000-4500", "경력": "1-4년"}
    ]
}

# 기본 채용 공고 (직무가 매칭되지 않는 경우)
default_posts = [
    {"회사": "스타트업A", "직무": "다양한 직무", "지역": region, "매칭점수": 70, "연봉": "2500-3500", "경력": "신입-3년"},
    {"회사": "중소기업B", "직무": "신입 채용", "지역": region, "매칭점수": 65, "연봉": "2200-3200", "경력": "신입"},
    {"회사": "대기업C", "직무": "인턴십", "지역": region, "매칭점수": 60, "연봉": "2000-2500", "경력": "신입"}
]

# 채용 공고 표시
if top_job in job_posts_data:
    job_posts = job_posts_data[top_job]
else:
    job_posts = default_posts

job_posts_df = pd.DataFrame(job_posts)

# 채용 공고 테이블
for idx, post in job_posts_df.iterrows():
    st.markdown(f"""
    <div class="job-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4>🏢 {post['회사']}</h4>
                <p><strong>직무:</strong> {post['직무']} | <strong>지역:</strong> {post['지역']}</p>
                <p><strong>연봉:</strong> {post['연봉']}만원 | <strong>경력:</strong> {post['경력']}</p>
            </div>
            <div style="text-align: right;">
                <h3 style="color: #ff6b35;">{post['매칭점수']}%</h3>
                <p>매칭 점수</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ------------------------
# 7. 리포트 다운로드
# ------------------------
st.markdown("## 📥 나의 고용 리포트")

# 리포트 생성
report_data = {
    "생성일": datetime.now().strftime("%Y-%m-%d"),
    "사용자정보": {
        "지역": region,
        "관심직무": interest_job,
        "경력수준": career_level,
        "학력": education
    },
    "분석결과": {
        "최적직무": top_job,
        "적합도": top_score,
        "관심직무적합도": job_fit_score[interest_job]
    },
    "지역고용지표": region_data[region] if region in region_data else {},
    "매칭공고": job_posts
}

# JSON 형태로 리포트 생성
report_json = json.dumps(report_data, ensure_ascii=False, indent=2)

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="📄 JSON 리포트 다운로드",
        data=report_json,
        file_name=f"job_fit_report_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json"
    )

with col2:
    # 간단한 텍스트 리포트 생성
    text_report = f"""
Job-Fit 분석 리포트
생성일: {datetime.now().strftime('%Y년 %m월 %d일')}

📋 기본 정보
- 거주 지역: {region}
- 관심 직무: {interest_job}
- 경력 수준: {career_level}
- 학력: {education}

🎯 분석 결과
- 최적 직무: {top_job} (적합도: {top_score}%)
- 관심 직무 적합도: {job_fit_score[interest_job]}%

📊 지역 고용 현황
- 청년 고용률: {region_data[region]['청년 고용률']}%
- 실업률: {region_data[region]['실업률']}%
- 평균 연봉: {region_data[region]['평균 연봉']:,}만원

💼 추천 채용 공고
"""
    
    for post in job_posts[:3]:
        text_report += f"- {post['회사']}: {post['직무']} (매칭점수: {post['매칭점수']}%)\n"
    
    st.download_button(
        label="📝 텍스트 리포트 다운로드",
        data=text_report,
        file_name=f"job_fit_report_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

# ------------------------
# 8. 추가 기능
# ------------------------
st.markdown("## 🔍 추가 분석")

# 성향별 직무 분포 차트
st.markdown("### 🧠 성향별 직무 분포")
personality_jobs = {
    "분석적이고 논리적": ["데이터 분석", "백엔드", "AI/ML", "재무", "법무"],
    "창의적이고 혁신적": ["마케팅", "기획", "디자인", "프론트엔드"],
    "체계적이고 계획적": ["기획", "인사", "재무", "백엔드"],
    "사교적이고 협력적": ["영업", "고객지원", "마케팅", "인사"]
}

personality_data = []
for personality, jobs in personality_jobs.items():
    for job in jobs:
        personality_data.append({
            "성향": personality,
            "직무": job,
            "적합도": job_fit_score.get(job, 50)
        })

personality_df = pd.DataFrame(personality_data)

fig = px.treemap(
    personality_df,
    path=["성향", "직무"],
    values="적합도",
    color="적합도",
    color_continuous_scale="viridis",
    title="성향별 직무 적합도 분포"
)
fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

# 푸터
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>📊 Job-Fit 대시보드 | AI 기반 맞춤 채용 플랫폼</p>
    <p>지역 고용지표 + 직무 적합도 + 성장 경로 추천</p>
</div>
""", unsafe_allow_html=True) 