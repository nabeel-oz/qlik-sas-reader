# Installing without Internet access

Follow these steps to install this Server-Side Extension (SSE) on an offline Windows machine.

You will need an alternate Windows machine with Internet access to prepare the files, and a way to transfer these files to the target machine.

## Prepare the installation files
Use a Windows machine with Internet access for these steps.

1. Download the Python 3.6 offline [executable installer](https://www.python.org/ftp/python/3.6.7/python-3.6.7-amd64.exe) and copy it to the target machine.
2. Download the Python packages required for this project.
    - The Python version on this machine should match the target machine.
    - Download the required packages from a terminal using pip.
        ```
        pip download grpcio grpcio-tools numpy pandas sas7bdat
        ```
    - Copy the package files to the target machine into a folder named `offline`.
3. Download the [latest release](https://github.com/nabeel-oz/qlik-sas-reader/releases) for this SSE and copy it to the target machine.
4. Download `Qlik-SAS-Init Offline.bat` from the project's repository on GitHub under `offline-install`. 

## Install on the offline machine
1. Install Python 3.6 using the offline executable. Remember to select the option to add Python to your PATH environment variable.
2. Extract the latest release for this SSE to a location of your choice. 
3. Place the `offline` folder with the Python package files into the same location.
4. Copy `Qlik-SAS-Init Offline.bat` to the same location, right click and chose 'Run as Administrator'. 
5. Continue with the installation steps in the main [documentation](../README.md#installation).