import unittest
import threading
import time
from connector.ZmqConnector import Client, Server


class FunctionalTests(unittest.TestCase):
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

    @classmethod
    def tearDownClass(cls):
        time.sleep(1)
        cls.server.close()

    def send_message(self, msg, retries, timeout):
        return self.client.send_message(msg, retries=retries, timeout=timeout)


class FunctionalTestsBasic(FunctionalTests):
    str_tests = ['', 'a', '1', '\'', "'", '"', '\n', 'abc', '123', 'x' * (10 ** 6), 'abc\n\t\'\"']
    num_tests = [1, 0, -1, 0.1, -0.1, 10**6, 0.1*10**6]

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
        for i in range(10**3):
            response = self.send_message(msg, 0, 1000)
            self.assertNotEqual(response, None)
            self.assertEqual(msg, response['response'])



