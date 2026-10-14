@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 -m cleanroomcheck serve --open-browser
  goto done
)
where python >nul 2>&1
if not errorlevel 1 (
  python -m cleanroomcheck serve --open-browser
  goto done
)
echo Python 3.10以上をインストールしてから再実行してください。
:done
pause
