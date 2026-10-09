@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\Start-Foundation.ps1" -ResumeFixture
if errorlevel 1 pause
