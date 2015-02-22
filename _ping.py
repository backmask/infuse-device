from lib.infuse import Infuse
from time import sleep

def recv_callback(d):
  print d

if __name__ == "__main__":
  infuse = Infuse(('localhost', 2946), {
        'name': 'Ping',
        'family': 'ping',
        'version': 'ping-1.0.0',
        'sensors': ['button']
      }, recv_callback)
  infuse.connect()

  try:
    while True:
      infuse.send("ping")
      sleep(10)
  except KeyboardInterrupt:
    pass

  print 'Disconnecting'
  infuse.disconnect()

  print 'Done'