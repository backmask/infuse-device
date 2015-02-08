from cflib.crtp.crtp import Crtp
from cflib.crazyflie import Crazyflie
from lib.infuse import Infuse
from time import sleep

class CrazyControl:

  def _attach(self, link_uri):
    print 'Attaching to %s' % link_uri
    self._cf.open_link(link_uri)
    self.is_connected = True

  def _get_device(self):
    print "Scanning interfaces"
    available = Crtp.scan_interfaces()

    print "Crazyflies found:"
    for i in available:
      print i[0]

    return False if len(available) == 0 else available[0][0]

  def _init(self):
    print 'Initializing'
    self._cf = Crazyflie()
    self._cf.connected.add_callback(self._connected)
    self._cf.disconnected.add_callback(self._disconnected)
    self._cf.connection_failed.add_callback(self._connection_failed)
    self._cf.connection_lost.add_callback(self._connection_lost)
    Crtp.init_drivers(enable_debug_driver=False)

  def _connected(self, link_uri):
    print "Connected to %s" % link_uri
    print "Listing available parameters"
    p_toc = self._cf.param.toc.toc
    for group in sorted(p_toc.keys()):
      print "{}".format(group)
      for param in sorted(p_toc[group].keys()):
        print "\t{}".format(param)
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
      #self._lg_stab.error_cb.add_callback(self._stab_log_error)
      lg.start()
      print("Done")
    else:
      print("Error setting up logger")

  def _connection_failed(self, link_uri, msg):
    print "Connection to %s failed: %s" % (link_uri, msg)
    self.is_connected = False

  def _connection_lost(self, link_uri, msg):
    print "Connection to %s lost: %s" % (link_uri, msg)

  def _disconnected(self, link_uri):
    print "Disconnected from %s" % link_uri
    self.is_connected = False

  def _on_telemetry_update(self, timestamp, data):
    print data

  def _loop(self):
    print 'Connecting to remote'
    infuse = Infuse(('localhost', 2946), {
        'name': 'Crazyflie',
        'family': 'flight.copter',
        'version': 'crazyflie-1.0.0',
        'sensors': ['gyroscope']
      })
    infuse.connect()

    try:
      while self.is_connected:
        sleep(0.02)
    except KeyboardInterrupt:
      pass

    print 'Disconnecting'
    infuse.disconnect()
    self._cf.close_link()

    print 'Done'

  def run(self):
    self._init()
    device = self._get_device()
    if device == False:
      print 'No device found, exiting'
      return
    self._attach(device)
    self._loop()