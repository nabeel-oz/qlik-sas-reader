import argparse
import json
import logging
import logging.config
import os
import sys
import time
from concurrent import futures

# Add Generated folder to module path.
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(PARENT_DIR, 'generated'))

import ServerSideExtension_pb2 as SSE
import grpc

# Import libraries for added functions
import numpy as np
import pandas as pd
from _sas_reader import SASReader

# Set the default port for this SSE Extension
_DEFAULT_PORT = '50056'

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
_MINFLOAT = float('-inf')


class ExtensionService(SSE.ConnectorServicer):
    """
    A SSE-plugin to provide Python data science functions for Qlik.
    """

    def __init__(self, funcdef_file):
        """
        Class initializer.
        :param funcdef_file: a function definition JSON file
        """
        self._function_definitions = funcdef_file
        os.makedirs('logs', exist_ok=True)
        log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logger.config')
        logging.config.fileConfig(log_file)
        logging.info('Logging enabled')

    @property
    def function_definitions(self):
        """
        :return: json file with function definitions
        """
        return self._function_definitions

    @property
    def functions(self):
        """
        :return: Mapping of function id and implementation
        """
        return {
            0: '_read_sas'
        }

    """
    Implementation of added functions.
    """
    
    @staticmethod
    def _read_sas(request, context):
        """
        Read SAS files stored as either XPORT or SAS7BDAT format files.
        :
        :param request: an iterable sequence of RowData
        :param context:
        :return: the SAS file as row data
        :Qlik expression examples:
        :<AAI Connection Name>.Read_SAS('data/airline.sas7bdat', 'format=sas7bdat')
        """
        # Get a list from the generator object so that it can be iterated over multiple times
        request_list = [request_rows for request_rows in request]
            
        # Create an instance of the SASReader class
        # This will take the SAS file information from Qlik and prepare the data to be read
        reader = SASReader(request_list, context)
        
        # Read the SAS data file. This returns a Pandas Data Frame or an interator if the file is to be read in chunks
        response = reader.read()
        
        if isinstance(response, pd.DataFrame):
            # Convert the response to a list of rows
            response_list = response.values.tolist()

            # We convert values to type SSE.Dual, and group columns into a iterable
            response_rows = []

            for row in response_list:
                response_rows.append(ExtensionService._get_duals(row))

            # Values are then structured as SSE.Rows
            response_rows = [SSE.Row(duals=duals) for duals in response_rows]      

            # Yield Row data as Bundled rows
            yield SSE.BundledRows(rows=response_rows)
        
        else:
             for chunk in response:
                # Convert the chunk to a list of rows
                response_list = chunk.values.tolist()

                # We convert values to type SSE.Dual, and group columns into a iterable
                response_rows = []

                for row in response_list:
                    response_rows.append(ExtensionService._get_duals(row))

                # Values are then structured as SSE.Rows
                response_rows = [SSE.Row(duals=duals) for duals in response_rows]      

                # Yield Row data as Bundled rows
                yield SSE.BundledRows(rows=response_rows)
    
    @staticmethod
    def _get_duals(row):
        """
        Transforms one row to an iterable of duals.
        :param result: one row of data
        :return: one row of data as an iterable of duals
        """
        # Transform the row to an iterable of Dual data
        duals = []
        for i, col in enumerate(row):
            
            # if the value is null:
            if pd.isnull(col):
                duals.append(SSE.Dual(numData=np.NaN, strData='/x00'))
                
            # if the value is numeric:
            elif isinstance(col, (int, float)):
                duals.append(SSE.Dual(numData=col, strData=str(col)))
            
            # if the value is a string:
            else:
                duals.append(SSE.Dual(numData=np.NaN, strData=str(col)))
        return iter(duals)
    
    @staticmethod
    def _get_function_id(context):
        """
        Retrieve function id from header.
        :param context: context
        :return: function id
        """
        metadata = dict(context.invocation_metadata())
        header = SSE.FunctionRequestHeader()
        header.ParseFromString(metadata['qlik-functionrequestheader-bin'])

        return header.functionId
    
    """
    Implementation of rpc functions.
    """

    def GetCapabilities(self, request, context):
        """
        Get capabilities.
        Note that either request or context is used in the implementation of this method, but still added as
        parameters. The reason is that gRPC always sends both when making a function call and therefore we must include
        them to avoid error messages regarding too many parameters provided from the client.
        :param request: the request, not used in this method.
        :param context: the context, not used in this method.
        :return: the capabilities.
        """
        logging.info('GetCapabilities')

        # Create an instance of the Capabilities grpc message
        # Enable(or disable) script evaluation
        # Set values for pluginIdentifier and pluginVersion
        capabilities = SSE.Capabilities(allowScript=False,
                                        pluginIdentifier='NAF Python Toolbox',
                                        pluginVersion='v1.2.0')

        # If user defined functions supported, add the definitions to the message
        with open(self.function_definitions) as json_file:
            # Iterate over each function definition and add data to the Capabilities grpc message
            for definition in json.load(json_file)['Functions']:
                function = capabilities.functions.add()
                function.name = definition['Name']
                function.functionId = definition['Id']
                function.functionType = definition['Type']
                function.returnType = definition['ReturnType']

                # Retrieve name and type of each parameter
                for param_name, param_type in sorted(definition['Params'].items()):
                    function.params.add(name=param_name, dataType=param_type)

                logging.info('Adding to capabilities: {}({})'.format(function.name,
                                                                     [p.name for p in function.params]))

        return capabilities

    def ExecuteFunction(self, request_iterator, context):
        """
        Call corresponding function based on function id sent in header.
        :param request_iterator: an iterable sequence of RowData.
        :param context: the context.
        :return: an iterable sequence of RowData.
        """
        # Retrieve function id
        func_id = self._get_function_id(context)
        logging.info('ExecuteFunction (functionId: {})'.format(func_id))

        return getattr(self, self.functions[func_id])(request_iterator, context)

    """
    Implementation of the Server connecting to gRPC.
    """

    def Serve(self, port, pem_dir):
        """
        Server
        :param port: port to listen on.
        :param pem_dir: Directory including certificates
        :return: None
        """
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        SSE.add_ConnectorServicer_to_server(self, server)

        if pem_dir:
            # Secure connection
            with open(os.path.join(pem_dir, 'sse_server_key.pem'), 'rb') as f:
                private_key = f.read()
            with open(os.path.join(pem_dir, 'sse_server_cert.pem'), 'rb') as f:
                cert_chain = f.read()
            with open(os.path.join(pem_dir, 'root_cert.pem'), 'rb') as f:
                root_cert = f.read()
            credentials = grpc.ssl_server_credentials([(private_key, cert_chain)], root_cert, True)
            server.add_secure_port('[::]:{}'.format(port), credentials)
            logging.info('*** Running server in secure mode on port: {} ***'.format(port))
        else:
            # Insecure connection
            server.add_insecure_port('[::]:{}'.format(port))
            logging.info('*** Running server in insecure mode on port: {} ***'.format(port))

        server.start()
        try:
            while True:
                time.sleep(_ONE_DAY_IN_SECONDS)
        except KeyboardInterrupt:
            server.stop(0)

class AAIException(Exception):
    """
    Custom exception call to pass on information error messages
    """
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', nargs='?', default=_DEFAULT_PORT)
    parser.add_argument('--pem_dir', nargs='?')
    parser.add_argument('--definition_file', nargs='?', default='functions.json')
    args = parser.parse_args()

    # need to locate the file when script is called from outside it's location dir.
    def_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.definition_file)

    calc = ExtensionService(def_file)
    calc.Serve(args.port, args.pem_dir)
