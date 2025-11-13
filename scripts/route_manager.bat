@echo off
cd /d "%~dp0.."
rem Change to project root directory (parent of scripts folder)
powershell -WindowStyle Hidden -Command "Start-Process python -ArgumentList 'route_manager.py' -Verb RunAs"