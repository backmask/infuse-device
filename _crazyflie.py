import sys
sys.path.append("lib")

from crazyflie.crazycontrol import CrazyControl
from crazyflie.basiclog import DoIt

if __name__ == "__main__":
  CrazyControl().run()
  #DoIt()