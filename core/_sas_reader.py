import os
import sys
import time
import string
import locale
import numpy as np
import pandas as pd
import ServerSideExtension_pb2 as SSE

# Add Generated folder to module path
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(PARENT_DIR, 'generated'))

class SASReader:
    """
    A class to read SAS datasets for Qlik.
    """
    
    # Counter used to name log files for instances of the class
    log_no = 0
    
    def __init__(self, request, context):
        """
        Class initializer.
        :param request: an iterable sequence of RowData
        :param context:
        :param variant: a string to indicate the request format
        :Sets up the input data frame and parameters based on the request
        """
               
        # Set the request and context variables for this object instance
        self.request = request
        self.context = context
        
        # Extract the file path from the request list
        self.filepath = self.request[0].rows[0].duals[0].strData
        
        # Extract additional arguments from the request list
        try:
            kwargs = self.request[0].rows[0].duals[1].strData
        except IndexError:
            kwargs = None
        
        # Set parameters from the additional arguments
        self._set_params(kwargs)
        
        # Parameters are output to the log if debug = true
        if self.debug:
            self._print_log(1)
    
    def read(self):
        """
        Read the SAS dataset and return as a Pandas Data Frame or an iterator to read the file in chunks.
        """
        
        # Send metadata on the result to Qlik
        self._send_table_description()
        
        # Read the SAS dataset
        return pd.read_sas(self.filepath, **self.read_sas_kwargs)
    
    def _set_params(self, kwargs):
        """
        Set input parameters based on the request.
        :
        :Parameters implemented for the pandas.read_sas() function are: format, encoding, chunksize
        :More information here: 
        :https://pandas.pydata.org/pandas-docs/stable/generated/pandas.read_sas.html
        :https://pandas.pydata.org/pandas-docs/stable/io.html?highlight=sas7bdatreader#sas-formats
        :
        :Additional parameters used are: debug
        """
        
        # Set default values which will be used if arguments are not passed
        
        # SSE parameters:
        self.debug = False
        # pandas.read_sas parameters:
        self.format = None
        self.encoding = None
        self.chunksize = None
        self.iterator = None
                
        # Set optional parameters
        
        # If the key word arguments were included in the request, get the parameters and values
        if len(kwargs) > 0:
            
            # The parameter and values are transformed into key value pairs
            args = kwargs.translate(str.maketrans('', '', string.whitespace)).split(",")
            self.kwargs = dict([arg.split("=") for arg in args])
            
            # Make sure the key words are in lower case
            self.kwargs = {k.lower(): v for k, v in self.kwargs.items()}
            
            # Set the debug option for generating execution logs
            # Valid values are: true, false
            if 'debug' in self.kwargs:
                self.debug = 'true' == self.kwargs['debug'].lower()
            
            # Set the format of the file, if none is specified it is inferred.
            # Options are: xport, sas7bdat
            if 'format' in self.kwargs:
                self.format = self.kwargs['format'].lower()
            
            # Encoding for text data. If None, text data are stored as raw bytes.
            if 'encoding' in self.kwargs:
                self.encoding = self.kwargs['encoding']
                
            # Read file chunksize lines at a time.
            if 'chunksize' in self.kwargs:
                self.chunksize = int(self.kwargs['chunksize'])
                self.iterator = True
        
        # Set up a list of possible key word arguments for the pandas.read_sas() function
        read_sas_params = ['format', 'encoding', 'chunksize', 'iterator']
        
        # Create dictionary of key word arguments for the pandas.read_sas() function
        self.read_sas_kwargs = self._populate_dict(read_sas_params)
        
    def _populate_dict(self, params):
        """
        Populate a dictionary based on a list of parameters. 
        The parameters should already exist in this object.
        """
        
        output_dict = {}
        
        for prop in params:
            if getattr(self, prop) is not None:
                output_dict[prop] = getattr(self, prop)
        
        return output_dict
    
    def _send_table_description(self):
        """
        Send the table description to Qlik as meta data.
        Only used when the SSE is called from the Qlik load script.
        """
        
        # Set up the table description to send as metadata to Qlik
        self.table = SSE.TableDescription()
        self.table.name = "SAS_Dataset"
        
        # Read the SAS dataset to get column headers
        sample_response = pd.read_sas(self.filepath, format=self.format, encoding=self.encoding, chunksize=5)
        
        # Get the first chunk of data as a Pandas DataFrame
        self.sample_data = sample_response.__next__()
        
        # Set field names based on the DataFrame
        for col in self.sample_data.columns.tolist():
            # Set up fields for the table
            self.table.fields.add(name=col)
        
        if self.debug:
            self._print_log(2)
        
        # Send table description
        table_header = (('qlik-tabledescription-bin', self.table.SerializeToString()),)
        self.context.send_initial_metadata(table_header)
    
    def _print_log(self, step):
        """
        Output useful information to stdout and the log file if debugging is required.
        :step: Print the corresponding step in the log
        """
        
        if step == 1:
            # Increment log counter for the class. Each instance of the class generates a new log.
            self.__class__.log_no += 1
             
            # Create a log file for the instance
            # Logs will be stored in ..\logs\SAS Reader Log <n>.txt
            self.logfile = os.path.join(os.getcwd(), 'logs', 'SAS Reader Log {}.txt'.format(self.log_no))
            
            # Output log header
            sys.stdout.write("SAS Reader Log: {0} \n\n".format(time.ctime(time.time())))
            
            # Output the request parameters to the terminal
            sys.stdout.write("Key word arguments: {0}\n\n".format(self.kwargs))
            sys.stdout.write("pandas.read_sas parameters: {0}\n\n".format(self.read_sas_kwargs))
            
            # Output the same information to the log file
            with open(self.logfile,'w') as f:
                f.write("SAS Reader Log: {0} \n\n".format(time.ctime(time.time())))
                f.write("Key word arguments: {0}\n\n".format(self.kwargs))
                f.write("pandas.read_sas parameters: {0}\n\n".format(self.read_sas_kwargs))                
                        
        elif step == 2:         
            # Print the sample data to the terminal
            sys.stdout.write("\nSAMPLE DATA: {0} rows x cols\n\n".format(self.sample_data.shape))
            sys.stdout.write("{0} \n\n".format(self.sample_data.to_string()))
            
            # Print the table description if the call was made from the load script
            sys.stdout.write("\nTABLE DESCRIPTION SENT TO QLIK:\n\n{0} \n\n".format(self.table))
                        
            with open(self.logfile,'a') as f:
                # Write the sample data to the log file
                f.write("\nSAMPLE DATA: {0} rows x cols\n\n".format(self.sample_data.shape))
                f.write("{0} \n\n".format(self.sample_data.to_string()))           
                
                # Write the table description to the log file
                f.write("\nTABLE DESCRIPTION SENT TO QLIK:\n\n{0} \n\n".format(self.table))
            
    