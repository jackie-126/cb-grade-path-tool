@echo off
chcp 65001 >nul
echo ============================================
echo   跨境电商智能分析Agent - 一键安装启动
echo ============================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b
)

echo [1/2] 安装依赖...
pip install streamlit pandas openpyxl python-docx plotly -q
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败，请检查网络
    pause
    exit /b
)

echo [2/2] 启动工具...
echo 浏览器将自动打开，如未打开请访问 http://localhost:8501
start http://localhost:8501
python -m streamlit run app.py --server.headless true
pause
