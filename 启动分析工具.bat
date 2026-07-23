@echo off
echo ========================================
echo   跨境电商智能分析Agent 启动中...
echo ========================================
echo.
cd /d D:\smart_agent
start http://localhost:8501
python -m streamlit run app.py --server.port 8501
pause