import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from connector import Server

print('Initializing server')
server = Server(server_port=5556)

print('Waiting for message....')
received_message = server.receive_message()

print('Received following message:\n\t{}'.format(received_message))

my_reply = 'This is my reply'

print('Sending reply....')
server.send_message(my_reply)

print('Done. Quitting...')
