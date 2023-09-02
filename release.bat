pushd %~dp0

rmdir /s /q /f %~dp0/release
mkdir %~dp0/release

set CMDS_STUBS_FORCE_OVERWRITE=1

set CMDS_STUBS_SOURCE_DIR=%~dp0\source\2023

set CMDS_STUBS_TARGET_DIR=%~dp0\release\2023\both\
set CMDS_STUBS_LONG_ARGS=1
set CMDS_STUBS_SHORT_ARGS=1
python.exe main.py

set CMDS_STUBS_TARGET_DIR=%~dp0\release\2023\long\
set CMDS_STUBS_LONG_ARGS=1
set CMDS_STUBS_SHORT_ARGS=0
python.exe main.py

set CMDS_STUBS_TARGET_DIR=%~dp0\release\2023\short\
set CMDS_STUBS_LONG_ARGS=0
set CMDS_STUBS_SHORT_ARGS=1
python.exe main.py



set CMDS_STUBS_SOURCE_DIR=%~dp0\source\2024

set CMDS_STUBS_TARGET_DIR=%~dp0\release\2024\both\
set CMDS_STUBS_LONG_ARGS=1
set CMDS_STUBS_SHORT_ARGS=1
python.exe main.py

set CMDS_STUBS_TARGET_DIR=%~dp0\release\2024\long\
set CMDS_STUBS_LONG_ARGS=1
set CMDS_STUBS_SHORT_ARGS=0
python.exe main.py

set CMDS_STUBS_TARGET_DIR=%~dp0\release\2024\short\
set CMDS_STUBS_LONG_ARGS=0
set CMDS_STUBS_SHORT_ARGS=1
python.exe main.py

