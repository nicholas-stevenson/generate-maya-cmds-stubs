pushd %~dp0

set CMDS_STUBS_SOURCE_DIR=%~dp0\source
set CMDS_STUBS_TARGET_DIR=%~dp0\target
set CMDS_STUBS_LONG_ARGS=1
set CMDS_STUBS_SHORT_ARGS=0
set CMDS_STUBS_FORCE_OVERWRITE=1
.venv\Scripts\python.exe fetch_docs.py
.venv\Scripts\python.exe main.py

echo.
echo Generating .pyi stubs...
if exist out\maya rmdir /s /q out\maya
pushd target
setlocal enabledelayedexpansion
set PYI_FILES=
for %%F in (maya\cmds\*.py) do set "PYI_FILES=!PYI_FILES! maya\cmds\%%~nxF"
%~dp0.venv\Scripts\stubgen.exe !PYI_FILES! --output %~dp0out
endlocal
popd

pause
