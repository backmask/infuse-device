from infuse import Infuse
from time import sleep
from signalgenerator import OscillatingSignal
import logging

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig

logging.basicConfig(level=logging.INFO)
MAX_THRUST = 65365.0
MAX_MOTOR_SPEED = 65365.0
MAX_BATTERY = 4.2
MIN_BATTERY = 3.0

class CrazyControl(object):

  def __init__(self):
    self.target = {
      'gyro': [0, 0, 0],
      'thrust': 0
    }
    self._cf = False

  def _init(self):
    print 'Initializing'
    self._cf = Crazyflie()
    self._cf.connected.add_callback(self._connected)
    self._cf.disconnected.add_callback(self._disconnected)
    self._cf.connection_failed.add_callback(self._connection_failed)
    self._cf.connection_lost.add_callback(self._connection_lost)
    cflib.crtp.init_drivers(enable_debug_driver=False)

  @classmethod
  def _get_device(cls):
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

  def _attachConfig(self, lg, update_callback):
    self._cf.log.add_config(lg)
    if lg.valid:
      lg.data_received_cb.add_callback(update_callback)
      lg.error_cb.add_callback(self._on_telemetry_error)
      lg.start()
    else:
      print("Error setting up logger")

  def _setup_logger(self):
    print "Setting up logger"
    lg = LogConfig(name="Stabilizer", period_in_ms=10)
    lg.add_variable("stabilizer.roll", "float")
    lg.add_variable("stabilizer.pitch", "float")
    lg.add_variable("stabilizer.yaw", "float")
    lg.add_variable("baro.aslLong", "float")
    self._attachConfig(lg, self._on_stabilizer_update)

    lg = LogConfig(name="Stabilizer", period_in_ms=100)
    lg.add_variable("stabilizer.thrust", "uint16_t")
    lg.add_variable("motor.m1", "int32_t")
    lg.add_variable("motor.m2", "int32_t")
    lg.add_variable("motor.m3", "int32_t")
    lg.add_variable("motor.m4", "int32_t")
    self._attachConfig(lg, self._on_telemetry_update)

    lg = LogConfig(name="Status", period_in_ms=1000)
    lg.add_variable("pm.vbat", "float")
    self._attachConfig(lg, self._on_status_update)

  def _setup_remote(self):
    print 'Connecting to remote'
    self._infuse = Infuse(('localhost', 2946), {
        'name': 'Crazyflie',
        'family': 'flight.quadcopter',
        'version': 'crazyflie-1.0.0',
        'sensors': ['gyroscope', 'thrust', 'barometer'],
        'reader': ['flight.command']
      }, self._read_control)
    self._infuse.connect()

  def _connection_failed(self, link_uri, msg):
    print "Connection to %s failed: %s" % (link_uri, msg)
    self.is_connected = False

  def _connection_lost(self, link_uri, msg):
    print "Connection to %s lost: %s" % (link_uri, msg)

  def _disconnected(self, link_uri):
    print "Disconnected from %s" % link_uri
    self.is_connected = False

  def _on_stabilizer_update(self, timestamp, data, logconf):
    self._send_stabilizer(
      data['stabilizer.roll'],
      data['stabilizer.pitch'],
      data['stabilizer.yaw'],
      data['baro.aslLong'])

  def _on_telemetry_update(self, timestamp, data, logconf):
    self._send_telemetry([
        data['stabilizer.thrust'] / MAX_THRUST,
        data['motor.m1'] / MAX_MOTOR_SPEED,
        data['motor.m2'] / MAX_MOTOR_SPEED,
        data['motor.m3'] / MAX_MOTOR_SPEED,
        data['motor.m4'] / MAX_MOTOR_SPEED
      ])

  def _on_status_update(self, timestamp, data, logconf):
    self._send_status(self._interpolate(data['pm.vbat'], MIN_BATTERY, MAX_BATTERY))

  def _send_stabilizer(self, roll, pitch, yaw, barometer):
    self._infuse.send({
      'gyroscope': {
        'roll': roll,
        'pitch': pitch,
        'yaw': yaw,
      },
      'barometer.asl': {
        'value': barometer
      }
    })

  def _send_telemetry(self, thrust):
    self._infuse.send({
      'thrust': [
        { 'symbol': 'avg', 'value': thrust[0]},
        { 'symbol': 'm1', 'value': thrust[1] },
        { 'symbol': 'm2', 'value': thrust[2] },
        { 'symbol': 'm3', 'value': thrust[3] },
        { 'symbol': 'm4', 'value': thrust[4] },
      ]
    })

  def _send_status(self, battery):
    self._infuse.send({
      'battery': { 'symbol': 'main', 'value': battery }
    })

  def _read_control(self, packet):
    if 'dataUid' in packet and packet['dataUid'] == 'flight.command':
      self.target['thrust'] = packet['data']['thrust']
      self.target['gyro'][0] = packet['data']['roll']
      self.target['gyro'][1] = packet['data']['pitch']
      self.target['gyro'][2] = packet['data']['yaw']
      self._exec_control(self.target)

  def _exec_control(self, control):
    self._cf.commander.send_setpoint(
      self.target['gyro'][0],
      self.target['gyro'][1],
      self.target['gyro'][2],
      self.target['thrust'] * MAX_THRUST)

  def _on_telemetry_error(self, logconf, msg):
    print "Error when logging %s: %s" % (logconf.name, msg)

  @classmethod
  def _interpolate(cls, v, v_min, v_max):
    v_i = (v - v_min) / (v_max - v_min)
    return min(1, max(0, v_i))

  def _loop(self):
    try:
      while self.is_connected:
        sleep(3)
    except KeyboardInterrupt:
      pass
    print 'Done'

  def run_fake(self):
    import random
    print 'Running with fake data'

    idx = 0
    yaw = OscillatingSignal(-180, 180, random.random)
    roll = OscillatingSignal(-180, 180, random.random)
    pitch = OscillatingSignal(-90, 90, random.random)
    motors = [
      OscillatingSignal(0, 1, lambda: random.random() * 0.01),
      OscillatingSignal(0, 1, lambda: random.random() * 0.01),
      OscillatingSignal(0, 1, lambda: random.random() * 0.01),
      OscillatingSignal(0, 1, lambda: random.random() * 0.01)
    ]
    battery = OscillatingSignal(0.01, 1, lambda: random.random() * 0.1)
    barometer_asl = OscillatingSignal(120, 122, lambda: random.random() * 0.1)

    self._cf = FakeCommander()
    self._setup_remote()

    try:
      while True:
        for motor in motors:
          motor.next()

        idx += 1

        self._send_stabilizer(
          yaw.next(),
          pitch.next(),
          roll.next(),
          barometer_asl.next()
        )

        if idx % 10 == 0:
          self._send_telemetry([
            (motors[0].value + motors[1].value + motors[2].value + motors[3].value) / 4.0,
            motors[0].value,
            motors[1].value,
            motors[2].value,
            motors[3].value
          ])
        if idx % 100 == 0:
          idx = 0
          self._send_status(battery.next())
        sleep(0.01)
    except KeyboardInterrupt:
      pass
    finally:
      print 'Disconnecting'
      self._infuse.disconnect()
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

class FakeCommander(object):

  def __init__(self):
    self.commander =  type('command', (object,), {
      'send_setpoint': self._exec_cmd
    })

  @classmethod
  def _exec_cmd(cls, roll, pitch, yaw, thrust):
    print 'roll:%f, pitch:%f, yaw:%f, thrust:%f' % (roll, pitch, yaw, thrust)
