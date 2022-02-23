import sys
import time
import json
import socketserver
import configparser
import traceback

class UERouterServer():

    def __init__(self,cmd_content: dict):
        #-------------------------------------------------------------------------
        #  First Route
        #
        

        #-------------------------------------------------------------------------
        #  Initialization
        #
        print("\nInitializing UERouter\n")


    def start(self,cmd_content: dict):
        
        #-------------------------------------------------------------------------
        #  Blah Blah
        #
        print("\nInitializing UERouter\n")                
            #raise Exception("WARNING: some STA Nodes configuration could not be found.\n")
                

    def tear_down(self) -> None:
        """
        Stop the UERouterServer
        """
        

class MyTCPServer(socketserver.TCPServer):

    def __init__(self, address, request_handler_class):
        self.address = address
        self.request_handler_class = request_handler_class
        self.allow_reuse_address = True
        super().__init__(self.address, self.request_handler_class)


class TCPHandler(socketserver.StreamRequestHandler):
    """
    The request handler class for our server.
    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def run_command(self, msg:dict) -> dict:
        
        cmd_str = msg['command']
        result = ''        
        try:
            if cmd_str == 'init':

                # Init the UERouter
                content = msg['content']
                self._ue_router = UERouterServer(cmd_content=msg['content'])

            elif cmd_str == 'start':
                # start the UERouter
                if self._ue_router != None:
                    self._ue_router.start(cmd_content=msg['content'])
                else:
                    raise Exception('UERouter uninitialized.')

            elif cmd_str == 'tear_down':
                
                # tear down the network 
                if self._ue_router != None:
                    self._ue_router.tear_down()
                    self._ue_router = None
                    self._stop = True
                else:
                    result = 'UERouter does not exist'

            
            else:
                
                # Wrong command
                raise Exception('Wrong command') 
            
            result_dict = {'outcome':'success', 'content': result }
            return result_dict
        
        except Exception as e:
            # record the error trace
            exc_info = sys.exc_info()
            trace = ''.join(traceback.format_exception(*exc_info))
            print(trace)
            result_dict = {'outcome':'failed','content':{'msg':str(e),'trace':trace }}
            return result_dict


    def handle(self):
        self.allow_reuse_address = True
        self._stop = False
        self._ue_router = None
        while True:
            # reveive the json msg and make a dict
            msg = self.rfile.readline().strip()
            msg_dict = json.loads(msg)
            print(msg)

            # handle the command and send back the result
            result = self.run_command(msg_dict)
            self.wfile.write(str(json.dumps(result)).encode('utf-8'))
            if self._stop:
                self._stop = False
                break

HOST, PORT = "localhost", 50505

print('hello buddy')
# Create the server, binding to localhost on port 12221
with MyTCPServer((HOST, PORT), TCPHandler) as server:
    server.serve_forever()


exit(0)
