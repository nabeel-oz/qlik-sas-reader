@echo off
cd "%~dp0\qlik-sas-env\Scripts"
call activate
cd ..\core
python __main__.py
pause