import pygame
import pygame.locals
import sys
from time import sleep
from lib.infuse import Infuse
from lib.signalgenerator import OscillatingSignal
from .keymap import keymap

class Controller(object):

  def __init__(self):
    self.key_map = False
    self.joysticks = False
    self.joysticks_map = False
    self.buttons = False
    self.crosses = False

  def get_symbol(self, symbol_list, idx):
    return symbol_list[idx] if len(symbol_list) > idx else 's' + str(idx)

  def fill_defaults(self, num_axes, num_buttons, num_crosses):
    cross_symbols = ['l', 'r']

    self.joysticks = []
    self.joysticks_map = {}
    self.buttons = []
    self.crosses = []

    for i in range(0, num_axes):
      symbol = self.key_map['joysticks'][i]['symbol']
      if symbol in self.joysticks_map:
        continue

      self.joysticks.append({
        'symbol': self.key_map['joysticks'][i]['symbol'],
        'x': 0,
        'y': 0
      })
      self.joysticks_map[symbol] = len(self.joysticks) - 1

    for i in range(0, num_buttons):
      self.buttons.append({
        'symbol': self.key_map['buttons'][i],
        'pressed': False
      })

    for i in range(0, num_crosses):
      self.crosses.append({
        'symbol': self.get_symbol(cross_symbols, i),
        'x': 0,
        'y': 0
      })

  def read_input(self, input):
    if input.type == pygame.locals.JOYAXISMOTION:
      joy_map = self.key_map['joysticks'][input.axis]
      idx = self.joysticks_map[joy_map['symbol']]
      prop = joy_map['property']
      self.joysticks[idx][prop] = input.value
    elif input.type == pygame.locals.JOYBUTTONDOWN:
      self.buttons[input.button]['pressed'] = True
    elif input.type == pygame.locals.JOYBUTTONUP:
      self.buttons[input.button]['pressed'] = False
    else:
      print('Event not handled ' + str(input.type))

  def recv_callback(self, data):
    print(data)

  def init(self):
    print('Initializing')
    pygame.init()
    pygame.joystick.quit()
    pygame.joystick.init()

    if pygame.joystick.get_count() < 1:
      print('No controller detected')
      sys.exit(0)
    else:
      print('Dectected %d controller(s)' % pygame.joystick.get_count())
      for i in range(0, pygame.joystick.get_count()):
        print('  - ' + pygame.joystick.Joystick(i).get_name())

    controller = pygame.joystick.Joystick(0)
    print('')
    print('Using ' + controller.get_name())

    self.key_map = keymap.map_controller(controller.get_name())
    if not self.key_map:
      print('Key map not found')
      return False

    controller.init()
    if controller.get_numaxes() > len(self.key_map['joysticks']):
      print('Invalid keymap, expected at least %d joysticks' % controller.get_numaxes())
      return False

    print('Controller initialized, detected:')
    print('  axes: %d' % controller.get_numaxes())
    print('  buttons: %d' % controller.get_numbuttons())
    print('  crosses: %d' % controller.get_numhats())

    self.fill_defaults(
      controller.get_numaxes(),
      controller.get_numbuttons(),
      controller.get_numhats())

    return True

  def connect(self):
    print('')
    self.infuse = Infuse(('server', 2946), {
        'name': 'Wii U controller',
        'family': 'controller',
        'version': 'remote-1.0.0',
        'sensors': ['joystick', 'button', 'nav-cross']
      }, self.recv_callback)
    self.infuse.connect()

  def loop(self):
    self.connect()

    try:
      while True:
        for evt in pygame.event.get():
          self.read_input(evt)

        self.infuse.send({
          'joystick': self.joysticks,
          'button': self.buttons,
          'cross': self.crosses
          })

        sleep(0.02)
    except KeyboardInterrupt:
      pass

    print('Disconnecting')
    self.infuse.disconnect()

    print('Done')

  def run(self):
    if self.init():
      self.loop()

  def run_fake(self):
    self.joysticks = [{
        'symbol': symbol,
        'x': 0,
        'y': 0
      } for symbol in ['l', 'r']]

    self.buttons = [{
        'symbol': symbol,
        'pressed': False
      } for symbol in ['a', 'b', 'lt', 'rt', 'l', 'r', 'start', 'select']]

    self.connect()

    thrust_generator = OscillatingSignal(-1, 0, 0.035)
    lx_generator = OscillatingSignal(-1, 1, 0.015)
    ly_generator = OscillatingSignal(-1, 1, 0.02)

    try:
      while True:
        self.joysticks[0]['x'] = lx_generator.next()
        self.joysticks[0]['y'] = ly_generator.next()
        self.joysticks[1]['y'] = thrust_generator.next()

        self.infuse.send({
          'joystick': self.joysticks,
          'button': self.buttons,
          'cross': self.crosses
          })

        sleep(0.02)
    except KeyboardInterrupt:
      pass

    print('Disconnecting')
    self.infuse.disconnect()

    print('Done')
