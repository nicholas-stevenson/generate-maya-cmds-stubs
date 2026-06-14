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
%~dp0.venv\Scripts\stubgen.exe !PYI_FILES! --include-docstrings --output %~dp0out
endlocal
popd

echo Normalising docstring quotes...
%~dp0.venv\Scripts\python.exe -c "import glob; [open(f,'w',encoding='utf-8').write(open(f,encoding='utf-8').read().replace(chr(39)*3, chr(34)*3)) for f in glob.glob(r'%~dp0out\maya\cmds\*.pyi')]"

pause
