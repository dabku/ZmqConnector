import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from connector import Client
import threading
import queue
import logging
import time


def client_worker(client, q):
    while True:
        msg = q.get()
        print('Sending message and waiting for response')
        try:
            response = client.send_message(msg, retries=1, timeout=3000)
            print('response: {}'.format(response))
        except Client.SendTimeout:
            print('Timeout we could put message back to queue')
            #q.put(msg)
            #continue
        q.task_done()


if __name__ == '__main__':
    logger = logging.getLogger('connector.ZmqConnector')
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s%(levelname)8s()|%(filename)s:%(lineno)s - %(funcName)20s() - %(message)s')

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    q = queue.Queue()
    client = Client(server_port=5556, address='localhost')
    client_thread = threading.Thread(target=client_worker, args=(client, q,))
    client_thread.setDaemon(True)
    client_thread.start()

    # we will put 16 messages to outgoing queue with 1 second delay
    for i in range(16):
        time.sleep(1)
        message = {'my_value': i}
        q.put(message)

    # wait for all messages to be handled
    q.join()
