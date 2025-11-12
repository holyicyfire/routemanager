@echo off
cd /d "%~dp0"
powershell -WindowStyle Hidden -Command "Start-Process python -ArgumentList 'route_manager.py' -Verb RunAs"