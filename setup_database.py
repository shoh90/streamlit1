import sqlite3
import pandas as pd
from pathlib import Path

def create_db_and_tables(db_path="data/job_fit_insight.db"):
    """SQLite 데이터베이스와 테이블을 생성하고 초기 데이터를 삽입합니다."""
    
    # data 디렉토리 생성
    Path("data").mkdir(exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f"'{db_path}' 데이터베이스에 연결되었습니다.")

    # --- 1. youth_summary 테이블 생성 ---
    cursor.execute("DROP TABLE IF EXISTS youth_summary")
    cursor.execute("""
    CREATE TABLE youth_summary (
        id INTEGER PRIMARY KEY,
        성별 TEXT,
        "2025.03_실업률" REAL, "2025.03_경제활동인구" INTEGER, "2025.03_취업자" INTEGER,
        "2025.04_실업률" REAL, "2025.04_경제활동인구" INTEGER, "2025.04_취업자" INTEGER,
        "2025.05_실업률" REAL, "2025.05_경제활동인구" INTEGER, "2025.05_취업자" INTEGER
    )
    """)
    youth_data = [
        ('남성', 6.8, 2450000, 2283000, 7.0, 2460000, 2287000, 6.9, 2470000, 2299000),
        ('여성', 6.1, 2150000, 2018000, 6.3, 2160000, 2023000, 6.2, 2170000, 2035000)
    ]
    cursor.executemany("INSERT INTO youth_summary (성별, '2025.03_실업률', '2025.03_경제활동인구', '2025.03_취업자', '2025.04_실업률', '2025.04_경제활동인구', '2025.04_취업자', '2025.05_실업률', '2025.05_경제활동인구', '2025.05_취업자') VALUES (?,?,?,?,?,?,?,?,?,?)", youth_data)
    print("'youth_summary' 테이블 생성 및 데이터 삽입 완료.")

    # --- 2. top10_skills_per_job 테이블 생성 ---
    cursor.execute("DROP TABLE IF EXISTS top10_skills_per_job")
    cursor.execute("""
    CREATE TABLE top10_skills_per_job (
        id INTEGER PRIMARY KEY,
        직무 TEXT NOT NULL,
        기술스택 TEXT NOT NULL,
        빈도 INTEGER NOT NULL
    )
    """)
    skills_data = pd.read_csv(pd.io.common.StringIO("""
직무,기술,중요도
데이터 분석,SQL,95
데이터 분석,Python,92
데이터 분석,Tableau,85
데이터 분석,통계 지식,83
데이터 분석,데이터 시각화,80
프론트엔드,JavaScript,98
프론트엔드,React,95
프론트엔드,HTML/CSS,93
프론트엔드,TypeScript,88
프론트엔드,Git,80
백엔드,Java/Spring,97
백엔드,데이터베이스,96
백엔드,API 설계,91
백엔드,클라우드(AWS/GCP),89
백엔드,Linux,85
기획,서비스 기획,94
기획,UX/UI 이해,90
기획,데이터 기반 의사결정,88
기획,기획서 작성,85
기획,시장 조사,82
AI/ML,Python,99
AI/ML,머신러닝/딥러닝,98
AI/ML,수학/통계,92
AI/ML,TensorFlow/PyTorch,90
AI/ML,데이터 전처리,88
    """))
    skills_data.rename(columns={'기술': '기술스택', '중요도': '빈도'}, inplace=True)
    skills_data.to_sql('top10_skills_per_job', conn, if_exists='append', index=False)
    print("'top10_skills_per_job' 테이블 생성 및 데이터 삽입 완료.")

    # --- 3. joblevel_counts 테이블 생성 ---
    cursor.execute("DROP TABLE IF EXISTS joblevel_counts")
    cursor.execute("""
    CREATE TABLE joblevel_counts (
        id INTEGER PRIMARY KEY,
        직무 TEXT NOT NULL,
        jobLevels TEXT NOT NULL,
        공고수 INTEGER NOT NULL
    )
    """)
    levels_data = pd.read_csv(pd.io.common.StringIO("""
직무,경력수준,공고수
데이터 분석,신입,120
데이터 분석,1~3년,250
데이터 분석,4~6년,150
프론트엔드,신입,90
프론트엔드,1~3년,350
프론트엔드,4~6년,220
백엔드,신입,80
백엔드,1~3년,400
백엔드,4~6년,280
기획,신입,150
기획,1~3년,280
기획,4~6년,200
AI/ML,신입,50
AI/ML,1~3년,180
AI/ML,4~6년,250
    """))
    levels_data.rename(columns={'경력수준': 'jobLevels'}, inplace=True)
    levels_data.to_sql('joblevel_counts', conn, if_exists='append', index=False)
    print("'joblevel_counts' 테이블 생성 및 데이터 삽입 완료.")

    conn.commit()
    conn.close()
    print("데이터베이스 설정이 완료되었습니다.")

if __name__ == "__main__":
    create_db_and_tables()
