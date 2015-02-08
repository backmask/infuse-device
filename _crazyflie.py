from crazyflie.crazycontrol import CrazyControl
import sys
sys.path.append("./crazyflie")

import cflib

if __name__ == "__main__":
  CrazyControl().run()