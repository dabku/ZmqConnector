import unittest
import threading
import time
import random
import string
from connector.ZmqConnector import Client, Server


class FunctionalTestsBase(unittest.TestCase):
    str_tests = ['', 'a', '1', '\'', "'", '"', '\n', 'abc', '123', 'x' * (10 ** 6), 'abc\n\t\'\"']
    num_tests = [1, 0, -1, 0.1, -0.1, 10 ** 6, 0.1 * 10 ** 6]
    long_msg = 'x' * 10 ** 6

    @classmethod
    def tearDownClass(cls):
        time.sleep(1)
        cls.server.close()

    def send_message(self, msg, retries, timeout):
        return self.client.send_message(msg, retries=retries, timeout=timeout)

    @staticmethod
    def random_string(length=1024):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


class FunctionalTests(FunctionalTestsBase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(server_port=5556, address='localhost')
        cls.server = Server(server_port=5556)
        cls.run_tests = True

        def server_worker(server):
            while True:
                try:
                    message = server.receive_message()
                    server.send_message({'response': message})
                except server.SocketClosed:
                    pass

        cls.server_thread = threading.Thread(target=server_worker, args=(cls.server,))
        cls.server_thread.setDaemon(True)
        cls.server_thread.start()
        time.sleep(1)


class FunctionalTestsBasic(FunctionalTests):

    def test_text(self):
        tests = self.str_tests
        for msg in tests:
            with self.subTest(value=msg):
                response = self.send_message(msg, 0, 1000)
                self.assertNotEqual(response, None)
                self.assertEqual(msg, response['response'])

    def test_numbers(self):
        tests = self.num_tests
        for msg in tests:
            with self.subTest(value=msg):
                response = self.send_message(msg, 0, 1000)
                self.assertNotEqual(response, None)
                self.assertEqual(msg, response['response'])

    def test_advanced_types(self):
        tests = [self.str_tests, self.num_tests, {'data': self.str_tests}, (self.str_tests, self.num_tests), None]
        for msg in tests:
            with self.subTest(value=msg):
                response = self.send_message(msg, 0, 1000)
                self.assertNotEqual(response, None)
                self.assertEqual(msg, response['response'])

    def test_stream(self):
        msg = 'x'*10**6
        for i in range(100):
            response = self.send_message(msg, 0, 1000)
            self.assertNotEqual(response, None)
            self.assertEqual(msg, response['response'])


class FunctionalTestsMoodySrv(FunctionalTestsBase):
    @classmethod
    def setUpClass(cls):
        cls.client = Client(server_port=5556, address='localhost')
        cls.server = Server(server_port=5556)
        cls.run_tests = True

        def server_worker(server):
            counter = 0
            while True:
                try:
                    message = server.receive_message()
                    counter += 1
                    if counter % 5 == 0:
                        time.sleep(1)
                    server.send_message({'response': message})

                except server.SocketClosed:
                    pass

        cls.server_thread = threading.Thread(target=server_worker, args=(cls.server,))
        cls.server_thread.setDaemon(True)
        cls.server_thread.start()
        time.sleep(1)


class FunctionalTestsFails(FunctionalTestsMoodySrv):
    def test_server_operation_for_tests(self):
        fails = 0
        for i in range(15):
            try:
                self.send_message('short', 0, 750)
            except Client.SendTimeout:
                fails += 1
        self.assertEqual(fails, 3)

    def test_retries(self):
        for i in range(15):
            msg = self.random_string()
            response = self.send_message(msg, 10, 500)
            self.assertEqual(msg, response['response'])

    def test_short_timeout(self):
        for i in range(15):
            self.assertRaises(Client.SendTimeout, self.send_message, self.long_msg, 0, 1)
