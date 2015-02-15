import sys
sys.path.append("lib")

from crazyflie.crazycontrol import CrazyControl

if __name__ == "__main__":
  CrazyControl().run_fake()