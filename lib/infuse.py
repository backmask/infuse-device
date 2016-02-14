import json
import socket
from threading import Thread
from time import sleep
import traceback

class Infuse(object):

  def __init__(self, address, description, recv_callback):
    description['method'] = '/bootstrap/device'
    self.address = address
    self.bootstrap_message = description
    self.buffer = False
    self.socket = False
    self.user_disconnected = False
    self.recv_callback = recv_callback
    self.thread = Thread(target=self._listen)

  def connect(self):
    self.thread.start()

  def disconnect(self):
    self.user_disconnected = True
    try:
      self.socket.shutdown(socket.SHUT_RDWR)
      self.socket.close()
    except:
      pass
    self.thread.join()

  def send(self, data):
    if self.socket:
      try:
        for chunk in json.JSONEncoder().iterencode(data):
          self.socket.send(chunk.encode('utf-8'))
      except socket.error:
        pass

  def _listen(self):
    while True:
      print('Connecting')
      try:
        self.socket = socket.create_connection(self.address, 1000)
        self.send(self.bootstrap_message)
      except Exception as e:
        traceback.print_exc()
        self.socket = False
        sleep(1)

      print('Connected')
      while self._recv():
        pass

      if self.user_disconnected:
        break

  def _recv(self):
    if not self.socket:
      return False

    try:
      buf = self.socket.recv(1024)
    except socket.timeout:
      return True
    except:
      return False

    if not buf:
      return False

    if self.buffer:
      self.buffer += buf
    else:
      self.buffer = buf

    self._parse_buffer()
    return True

  def _parse_buffer(self):
    try:
      decoded = json.JSONDecoder().raw_decode(self.buffer.decode('UTF-8'))
    except ValueError as e:
      return

    if decoded[1] > 0:
      self.recv_callback(decoded[0])
      if decoded[1] == len(self.buffer):
        self.buffer = False
      else:
        self.buffer = self.buffer[decoded[1]:]
        self._parse_buffer()
