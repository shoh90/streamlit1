#!/usr/bin/env python3
"""
Job-Fit Insight Dashboard 실행 스크립트
"""
import subprocess
import sys
from pathlib import Path

def main():
    dashboard_file = "job_fit_dashboard.py"
    db_file = Path("data/job_fit_insight.db")

    if not db_file.exists():
        print(f"❌ 오류: 데이터베이스 파일('{db_file}')을 찾을 수 없습니다.")
        print("💡 'setup_database.py'를 먼저 실행하여 데이터베이스를 생성해주세요.")
        print("👉 python setup_database.py")
        sys.exit(1)

    print("🚀 Job-Fit Insight Dashboard를 시작합니다...")
    print("📊 브라우저에서 http://localhost:8501 을 열어주세요.")
    print("⏹️  종료하려면 Ctrl+C를 누르세요.")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            dashboard_file,
            "--server.port=8501",
            "--server.address=localhost"
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 대시보드를 종료합니다.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
