import json
import socket
from threading import Thread

class Infuse:

  def __init__(self, address, description, recv_callback):
    description['method'] = '/bootstrap/device'
    self.address = address;
    self.bootstrapMessage = json.JSONEncoder().encode(description)
    self.buffer = False
    self.recv_callback = recv_callback
    self.thread = Thread(target = self._listen)

  def connect(self):
    self.socket = socket.create_connection(self.address, 1000)
    self.socket.send(self.bootstrapMessage)
    self.thread.start()

  def disconnect(self):
    self.socket.shutdown(socket.SHUT_RDWR)
    self.socket.close()
    self.thread.join()

  def send(self, data):
    self.socket.send(json.JSONEncoder().encode(data))

  def _listen(self):
    while self._recv():
      pass

  def _recv(self):
    try:
      buf = self.socket.recv(1024)
    except socket.timeout:
      return True

    if not buf:
      return False

    if self.buffer:
      buf = self.buffer + buf

    decoded = json.JSONDecoder().raw_decode(buf)

    if decoded[1] > 0:
      self.recv_callback(decoded[0])
      if decoded[1] == len(buf):
        self.buffer = False
      else:
        self.buffer = buf[decoded[1]:]
    else:
      self.buffer = buf

    return True