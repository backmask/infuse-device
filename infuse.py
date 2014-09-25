import json
import socket

class Infuse:

  def __init__(self, address, description):
    description['method'] = '/bootstrap/device'
    self.address = address;
    self.bootstrapMessage = json.JSONEncoder().encode(description)
    pass

  def connect(self):
    self.socket = socket.create_connection(self.address, 1000)
    self.socket.send(self.bootstrapMessage)

  def disconnect(self):
    self.socket.close()

  def send(self, data):
    self.socket.send(json.JSONEncoder().encode(data))