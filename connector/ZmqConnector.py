import zmq
import logging
import pickle
import zlib

logger = logging.getLogger(__name__)


class ZeromqConnector:
    def __init__(self):
        self.socket = None
        self.context = zmq.Context()

    def initialize_socket(self):
        raise NotImplementedError

    def _send_zipped_pickle(self, obj, protocol=-1):
        """
        pickle an object and zip the pickle before sending it to socket
        :param obj: object to send
        :param protocol: pickling protocol

        :return: None
        """
        p = pickle.dumps(obj, protocol)
        z = zlib.compress(p)
        self.socket.send(z)

    def _recv_zipped_pickle(self, flags=0):
        """
        receive a message from, decompress and unpickle it
        :param flags: zeroMQ socket flag

        :return: decompressed and unpickled object
        """
        z = self.socket.recv(flags)
        p = zlib.decompress(z)
        up = pickle.loads(p)
        return up

    def receive_message(self, blocking=True):
        """
        receive a message from socket
        By default it's blocking execution until message appears on socket
        :param blocking: blocking mode

        :return: message from socket
        """
        try:
            if blocking:
                return self._recv_zipped_pickle()
            else:
                return self._recv_zipped_pickle(flags=zmq.NOBLOCK)
        except zmq.error.ContextTerminated:
            raise self.SocketClosed
        except AttributeError as e:
            if self.socket is None:
                raise self.SocketClosed
            raise e

    def send_message_nowait(self, message):
        """
        sends message without any timeouts and retry functionalities
        :param message: massage to send
        :return: None
        """
        self._send_zipped_pickle(message)

    def send_message(self, message, retries=0, timeout=1000):
        """
        Sends message to server, provides retry and timeout functionality.
        Each retry uses it's own timeout, that is 4 retries with 1000 timeout will take approx 5 seconds
        (1 initial send try and 4 retries). Failure to receive response back form the Server will cause to reinitialize
        socket because of the request-response pattern
        :param message: object to send
        :param retries: number of retries
        :param timeout: timeout time in milliseconds
        :return: response from server or None if it failed
        """

        retries_left = retries + 1
        while retries_left:
            try:
                self.send_message_nowait(message)
            except zmq.error.ContextTerminated:
                raise self.SocketClosed
            socks = dict(self.poll.poll(timeout))
            if socks.get(self.socket) == zmq.POLLIN:
                reply = self.receive_message()
                if not reply:
                    break
                else:
                    return reply
            else:
                logger.debug("No response from server")
                self.socket.setsockopt(zmq.LINGER, 0)
                self.socket.close()
                self.poll.unregister(self.socket)
                retries_left -= 1
                # reinitialize socket
                self.initialize_socket()
                self.poll.register(self.socket, zmq.POLLIN)
                if retries_left <= 0:
                    logger.debug('Out of retries, aborting...')
                    raise self.SendTimeout
        return None

    def close(self):
        """
        Closes socet and terminates the context
        :return: None
        """
        self.socket.close()
        self.socket = None
        self.context.term()
        self.context = None

    class NoMessage(Exception):
        """
        Exception raised when no message is received in non-blocking mode.
        """
        pass

    class SocketClosed(Exception):
        """
        Exception raised whenever socket is terminated and there was an attempt to send or receive
        """
        pass

    class SendTimeout(Exception):
        """
        Exception raised when sending task run out of retries and timed out
        """


class Server(ZeromqConnector):
    """
     Server class that receives and replies to messages on certain port
    """
    def __init__(self, server_port):
        """
        Initializes the Server class on localhost with specified port
        :param server_port: port of Server
        """
        ZeromqConnector.__init__(self)
        self.address = "tcp://*:{}".format(server_port)
        self.socket = None
        self.initialize_socket()

    def initialize_socket(self):
        """
        Initializes server socket
        :return: None
        """
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(self.address)

    def send_message(self, message, **kwargs):
        """
        Sends response from Server to Client. It does not support retries or timeouts,
        use Client to handle improper response
        :param message: message to send
        :param kwargs: not used
        :return: None
        """
        self.send_message_nowait(message)


class Client(ZeromqConnector):
    """
    Client class to send and receive responses from server.
    """
    def __init__(self, server_port, address='localhost'):
        """
        Initializez the Client class o
        :param server_port: Port of Server
        :param address: Address of Server
        """
        ZeromqConnector.__init__(self)
        self.address = "tcp://{}:{}".format(address, server_port)
        self.socket = None
        self.initialize_socket()
        self.poll = zmq.Poller()
        self.poll.register(self.socket, zmq.POLLIN)

    def initialize_socket(self):
        """
        Initializes Client socket
        :return: None
        """
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(self.address)
