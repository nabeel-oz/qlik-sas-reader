# Load SAS Datasets to Qlik
This Python Server Side Extension (SSE) for Qlik helps load SAS datasets stored in SAS7BDAT or XPORT files.

The files are read using the [Pandas library](https://pandas.pydata.org/pandas-docs/stable/io.html?highlight=sas7bdatreader#sas-formats).

For more information on Qlik Server Side Extensions see [qlik-oss](https://github.com/qlik-oss/server-side-extension).

**Disclaimer:** This project has been started by me in a personal capacity and is not supported by Qlik. 


## Pre-requisites

- Qlik Sense Enterprise or Qlik Sense Desktop
- Python 3.4 or above


## Installation

1. Get Python from [here](https://www.python.org/downloads/). Remember to select the option to add Python to your PATH environment variable.

2. Download this git repository or get the [latest release](https://github.com/nabeel-qlik/qlik-sas-reader/releases/) and extract it to a location of your choice. The machine where you are placing this repository should have access to a local or remote Qlik Sense instance.

3. Double click `Qlik-SAS-Init.bat` in the repository files and let it do it's thing. You can open this file in a text editor to review the commands that will be executed. If everything goes smoothly you will see a Python virtual environment being set up and some packages being installed. Once the execution completes, do a quick scan of the log to see everything installed correctly. The libraries imported are: `grpcio`, `numpy`, `pandas`. Also, check that the `core` and `generated` directories have been moved successfully to the newly created `qlik-sas-env` directory.

4. Now whenever you want to start this Python service you can run `Qlik-SAS-Start.bat`. If you get an error or no output in the terminal, check your firewall's inbound settings. You may need an inbound rule to open up port `50056`. If you need to change the port you can do so in the file `core\__main__.py` by opening the file with a text editor, changing the value of the `_DEFAULT_PORT` variable, and then saving the file.

5. Now you need to [set up an Analytics Connection in Qlik Sense Enterprise](https://help.qlik.com/en-US/sense/February2018/Subsystems/ManagementConsole/Content/create-analytic-connection.htm) or [update the Settings.ini file in Qlik Sense Desktop](https://help.qlik.com/en-US/sense/February2018/Subsystems/Hub/Content/Introduction/configure-analytic-connection-desktop.htm).

6. Finally restart the Qlik Sense engine service for Qlik Sense Enterprise or close and reopen Qlik Sense Desktop. This step may not be required if you are using Qlik Sense April 2018.


## Usage

This SSE is meant to be used through the Qlik Sense Load Editor. 

First you need to specify the path for the file and any additional arguments. We do this by creating a temporary input table in Qlik.

```
TempInputs:
LOAD * INLINE [
     'Path', 'Args'
     '..\..\data\sample.sas7bdat', 'debug=true, chunksize=1000'
];
```

In the example above the SAS7BDAT file has been placed in a subfolder called 'data' in the root directory of this SSE. You can also use absolute paths.

The data can then be loaded using the `LOAD...EXTENSION` syntax using the Read_SAS function provided by this SSE:

```
[SAS Dataset]:
LOAD *
EXTENSION SAS.Read_SAS(TempInputs{Path, Args});
```

In the example above the analytic connection has been named as `SAS`. This is an arbitrary name and will depend on your configuration.

If you want a preview of the field names, you can use the `debug=true` argument. This will enable the logging features of the SSE with information printed to the terminal and a log file. The log files can be found in the `qlik-sas-reader\qlik-sas-env\core\logs\` directory. 

For large files you will need to specify the `chunksize` parameter. This allows the file to be read iteratively without hitting memory and row limits. 

The optional parameters below can be included in the second string in the input table.  

| Keyword | Description | Sample Values | Remarks |
| --- | --- | --- | --- |
| debug | Flag to output additional information to the terminal and logs | `true`, `false` | Information will be printed to the terminal and a log file: `..\qlik-sas-env\core\logs\SAS Reader Log <n>.txt`. <br/><br/>Particularly useful is looking at the sample output to see how the file is structured. |
| format | The format of the file | `xport`, `sas7bdat` | If the format is not specified, it will be inferred. |
| encoding | Encoding for text data | `utf-8` | If the encoding is not specified, Pandas returns the text as raw bytes. This could be cleaned up in Qlik if desired. |
| chunksize | Read file chunksize lines at a time | `1000` | This is useful when reading large files. If specified, the file is read iteratively. |
