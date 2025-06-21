#!/usr/bin/env python3
"""
Job-Fit 대시보드 실행 스크립트
"""

import subprocess
import sys
import os

def main():
    """대시보드를 실행합니다."""
    print("🚀 Job-Fit 대시보드를 시작합니다...")
    print("📊 브라우저에서 http://localhost:8501 을 열어주세요.")
    print("⏹️  종료하려면 Ctrl+C를 누르세요.")
    print("-" * 50)
    
    try:
        # Streamlit 앱 실행
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "job_fit_dashboard.py",
            "--server.port=8501",
            "--server.address=localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 대시보드를 종료합니다.")
    except Exception as e:
        print(f"❌ 오류가 발생했습니다: {e}")
        print("💡 requirements.txt의 패키지들이 설치되어 있는지 확인해주세요.")

if __name__ == "__main__":
    main() 