@echo off
echo Setting up the Python virtual environment... & echo.
python -m venv "%~dp0\qlik-sas-env"
echo.
echo Copying project files to the new directory... & echo.
xcopy /E /I "%~dp0\generated" "%~dp0\qlik-sas-env\generated"
xcopy /E /I "%~dp0\core" "%~dp0\qlik-sas-env\core"
echo.
echo Activating the virtual environment... & echo.
cd /d "%~dp0\qlik-sas-env\Scripts"
call activate
cd ..
echo.
echo Installing required packages... & echo.
python -m pip install --upgrade pip
pip install grpcio
pip install grpcio-tools
pip install numpy
pip install pandas
echo.
echo Creating a new firewall rule for TCP port 50056... & echo.
netsh advfirewall firewall add rule name="Qlik SAS Reader" dir=in action=allow protocol=TCP localport=50056
echo.
echo All done. Run Qlik-SAS-Start.bat to start the SSE Extension Service. & echo.
pause
