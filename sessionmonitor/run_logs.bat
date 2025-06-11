@echo off
cd /d "C:\Users\jawad\sessionmonitor"
call project_env\Scripts\activate.bat
python extract_logs.py
