@echo off
d:
cd /d "%~dp0"
start %windir%\System32\cmd.exe "/K" g:\Anaconda3\Scripts\activate.bat luiz
