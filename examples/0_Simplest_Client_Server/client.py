import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from connector import Client

input("\nMake sure that the server is started for this example and hit enter\n")

print('Initializing client on local address')
client = Client(server_port=5556, address='localhost')

my_message = "This is my message"
print('Will send following message:\n\t{}'.format(my_message))

print('Sending message and waiting for response...')
response = client.send_message(my_message)

print('Got following response:\n\t{}'.format(response))
print('Done. Quitting...')
