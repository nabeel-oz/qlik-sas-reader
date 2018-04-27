@echo off
echo Setting up the Python virtual environment... & echo.
python -m venv "%~dp0\qlik-sas-env"
echo.
echo Moving project files to the new directory... & echo.
move generated "%~dp0\qlik-sas-env"
move core "%~dp0\qlik-sas-env"
echo.
echo Activating the virtual environment... & echo.
cd /d "%~dp0\qlik-sas-env\Scripts"
call activate
cd ..
echo.
echo Installing required packages... & echo.
python -m pip install --upgrade pip
pip install grpcio
pip install numpy
pip install pandas
echo.
echo All done. Run Qlik-SAS-Start.bat to start the SSE Extension Service. & echo.
pause