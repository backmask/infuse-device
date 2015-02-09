from infuse import Infuse
from time import sleep
import logging

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig

logging.basicConfig(level=logging.INFO)

class CrazyControl:

  def _init(self):
    print 'Initializing'
    self._cf = Crazyflie()
    self._cf.connected.add_callback(self._connected)
    self._cf.disconnected.add_callback(self._disconnected)
    self._cf.connection_failed.add_callback(self._connection_failed)
    self._cf.connection_lost.add_callback(self._connection_lost)
    cflib.crtp.init_drivers(enable_debug_driver=False)

  def _get_device(self):
    print "Scanning interfaces"
    available = cflib.crtp.scan_interfaces()
    if len(available) == 0:
      return False

    print "Crazyflies found:"
    for i in available:
      print i[0]

    return available[0][0]

  def _attach(self, link_uri):
    print 'Attaching to %s' % link_uri
    self._cf.open_link(link_uri)
    self.is_connected = True

  def _connected(self, link_uri):
    print "Connected to %s" % link_uri
    self._setup_logger()

  def _setup_logger(self):
    print "Setting up logger"
    lg = LogConfig(name="Stabilizer", period_in_ms=10)
    lg.add_variable("stabilizer.roll", "float")
    lg.add_variable("stabilizer.pitch", "float")
    lg.add_variable("stabilizer.yaw", "float")
    lg.add_variable("stabilizer.thrust", "uint16_t")

    self._cf.log.add_config(lg)
    if lg.valid:
      lg.data_received_cb.add_callback(self._on_telemetry_update)
      lg.error_cb.add_callback(self._on_telemetry_error)
      lg.start()
      print("Done")
    else:
      print("Error setting up logger")

  def _setup_remote(self):
    print 'Connecting to remote'
    self._infuse = Infuse(('localhost', 2946), {
        'name': 'Crazyflie',
        'family': 'flight.copter',
        'version': 'crazyflie-1.0.0',
        'sensors': ['gyroscope', 'thrust', 'barometer']
      })
    self._infuse.connect()

  def _connection_failed(self, link_uri, msg):
    print "Connection to %s failed: %s" % (link_uri, msg)
    self.is_connected = False

  def _connection_lost(self, link_uri, msg):
    print "Connection to %s lost: %s" % (link_uri, msg)

  def _disconnected(self, link_uri):
    print "Disconnected from %s" % link_uri
    self.is_connected = False

  def _on_telemetry_update(self, timestamp, data, logconf):
    self._infuse.send({
      'gyroscope': {
        'roll': data['stabilizer.roll'],
        'pitch': data['stabilizer.pitch'],
        'yaw': data['stabilizer.yaw'],
      },
      'thrust': data['stabilizer.thrust']
    })

  def _on_telemetry_error(self, logconf, msg):
    print "Error when logging %s: %s" % (logconf.name, msg)

  def _loop(self):
    try:
      while self.is_connected:
        sleep(0.02)
    except KeyboardInterrupt:
      pass
    print 'Done'

  def run(self):
    self._init()
    device = self._get_device()
    if device == False:
      print 'No device found, exiting'
      return
    self._setup_remote()
    self._attach(device)
    self._loop()

    print 'Disconnecting'
    self._cf.close_link()
    self._infuse.disconnect()