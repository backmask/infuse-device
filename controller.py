import pygame
import pygame.locals
import sys
from time import sleep
from infuse import Infuse

class Controller:

  def get_symbol(self, symbolList, idx):
    return symbolList[idx] if len(symbolList) > idx else 's' + str(idx)

  def fill_defaults(self, numAxes, numButton, numCrosses):
    joystickSymbols = ['l', 'r']
    buttonSymbols = ['a', 'b', 'x', 'y']
    crossSymbols = ['l', 'r']

    self.joysticks = []
    self.buttons = []
    self.crosses = []

    for i in xrange(0, numAxes, 2):
      self.joysticks.append({
        'symbol': self.get_symbol(joystickSymbols, i),
        'x': 0,
        'y': 0
      })

    for i in xrange(0, numButton):
      self.buttons.append({
        'symbol': self.get_symbol(buttonSymbols, i),
        'pressed': False
      })

    for i in xrange(0, numCrosses):
      self.crosses.append({
        'symbol': self.get_symbol(crossSymbols, i),
        'x': 0,
        'y': 0
      })

  def read_input(self, input):
    if input.type == pygame.locals.JOYAXISMOTION:
      idx = int(input.axis / 2)
      if input.axis % 2 == 0:
        self.joysticks[idx]['x'] = input.value
      else:
        self.joysticks[idx]['y'] = input.value
    elif input.type == pygame.locals.JOYBUTTONDOWN:
      self.buttons[input.button]['pressed'] = True
    elif input.type == pygame.locals.JOYBUTTONUP:
      self.buttons[input.button]['pressed'] = False
    else:
      print 'Event not handled ' + str(input.type)

  def loop(self):
    print 'Initializing'
    pygame.init()
    pygame.joystick.quit()
    pygame.joystick.init()

    if pygame.joystick.get_count() < 1:
      print 'No controller detected'
      sys.exit(0)

    controller = pygame.joystick.Joystick(0)
    print 'Using ' + controller.get_name()

    controller.init()
    print 'Controller initialized, detected:'
    print '  axes: %d' % controller.get_numaxes()
    print '  buttons: %d' % controller.get_numbuttons()
    print '  crosses: %d' % controller.get_numhats()

    self.fill_defaults(
      controller.get_numaxes(),
      controller.get_numbuttons(),
      controller.get_numhats())

    print 'Connecting to remote'
    infuse = Infuse(('localhost', 2946), {
        'name': 'Wii U controller',
        'family': 'controller',
        'version': 'remote-1.0.0',
        'sensors': ['joystick', 'button', 'nav-cross']
      })
    infuse.connect()

    try:
      while True:
        for e in pygame.event.get():
          self.read_input(e)

        infuse.send({
          'joystick': self.joysticks,
          'button': self.buttons,
          'cross': self.crosses
          })

        sleep(0.01)
    except KeyboardInterrupt:
      pass

    print 'Disconnecting'
    infuse.disconnect()

    print 'Done'


if __name__ == "__main__":
    Controller().loop()