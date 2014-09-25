import pygame
import pygame.locals
import sys
from time import sleep
from infuse import Infuse

class Controller:

  def fill_defaults(self, numAxes, numButton, numCrosses):
    self.joysticks = [(0, 0)] * numAxes
    self.buttons = [False] * numButton
    self.crosses = [(0, 0)] * numCrosses

  def read_input(self, input):
    if input.type == pygame.locals.JOYAXISMOTION:
      idx = int(input.axis / 2)
      if input.axis % 2 == 0:
        self.joysticks[idx] = (input.value, self.joysticks[idx][1])
      else:
        self.joysticks[idx] = (self.joysticks[idx][0], input.value)
    elif input.type == pygame.locals.JOYBUTTONDOWN:
      self.buttons[input.button] = True
    elif input.type == pygame.locals.JOYBUTTONUP:
      self.buttons[input.button] = False
    elif input.type == pygame.locals.JOYHATMOTION:
      self.joysticks[input.hat] = input.value
    else:
      print 'Event not handled ' + input.type

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
          'joysticks': self.joysticks,
          'buttons': self.buttons,
          'crosses': self.crosses
          })

        sleep(0.01)
    except KeyboardInterrupt:
      pass

    print 'Disconnecting'
    infuse.disconnect()

    print 'Done'


if __name__ == "__main__":
    Controller().loop()