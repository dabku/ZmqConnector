# we are adding library root to python path, so you don't have to run anything prior
# it will allow us to import module
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from connector import Server
import logging
import time
import random

if __name__ == '__main__':
    logger = logging.getLogger('connector.ZmqConnector')
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s%(levelname)8s()|%(filename)s:%(lineno)s - %(funcName)20s() - %(message)s')

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    server = Server(server_port=5556)

    while True:
        print('Waiting for message')
        message = server.receive_message()
        print('Received emssage: {}'.format(message))
        if int(message['my_value']) < 5:
            print('Rreplying...')
            server.send_message({'response': message['my_value']})
        elif message['my_value'] < 10:
            sleep_time = random.randint(0, 2)
            print('Simulating short delay, sleeping for {}'.format(sleep_time))
            time.sleep(sleep_time)
            print('Replying...')
            server.send_message({'response': message['my_value']})
        elif message['my_value'] < 15:
            sleep_time = random.randint(3, 5)
            print('Simulating big delay, sleeping for {}'.format(sleep_time))
            time.sleep(sleep_time)
            print('Replying...')
            server.send_message({'response': message['my_value']})
        else:
            break