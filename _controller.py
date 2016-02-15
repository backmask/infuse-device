import sys
from controller.controller import Controller

if __name__ == "__main__":
  if len(sys.argv) > 1 and sys.argv[1] == 'fake':
    Controller().run_fake()
  else:
    Controller().run()
