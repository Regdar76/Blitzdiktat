@echo off
cd /d "%~dp0"
set BLITZTEXT_DEBUG=1
python main.py %*
