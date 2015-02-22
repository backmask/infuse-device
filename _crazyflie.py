import sys
sys.path.append("lib")

from crazyflie.crazycontrol import CrazyControl

if __name__ == "__main__":
  if len(sys.argv) > 1 and sys.argv[1] == 'fake':
    CrazyControl().run_fake()
  else:
    CrazyControl().run()