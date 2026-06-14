@echo off
pushd %~dp0

echo Checking for uv...
where uv >nul 2>&1
if errorlevel 1 (
    echo uv not found. Installing via pip...
    python.exe -m pip install uv
    if errorlevel 1 (
        echo.
        echo Failed to install uv via pip.
        echo Install it manually: https://github.com/astral-sh/uv
        popd
        pause
        exit /b 1
    )
)

echo Creating virtual environment at .venv\...
uv venv .venv

echo Installing dependencies...
uv pip install --python .venv\Scripts\python.exe beautifulsoup4 httpx mypy

echo.
echo Setup complete! Virtual environment is at .venv\
echo Run run.bat to fetch docs and generate stubs.
popd
pause
