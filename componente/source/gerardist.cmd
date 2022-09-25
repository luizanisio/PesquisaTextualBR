@echo off
python .\pesquisabr_testes.py 
echo Verifique o resultado dos testes e tecle algo....
pause 
rd /s /q .\dist
python setup.py sdist 
rd /s /q .\pesquisabr.egg-info

FOR /f "delims=" %%A in ('"dir /b dist\*.gz"') do @(
    pip install "dist\%%A"
)
