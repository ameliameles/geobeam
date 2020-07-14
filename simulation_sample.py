#!/usr/bin/env python3

import os
import sys

from simulations import StaticSimulation
from simulations import DynamicSimulation
from simulations import SimulationSet
from geobeam import generate_route
from geobeam import gps_utils

# TODO(ameles) change this to an actual config file and a script that uses those configs to make a simulation set
def main():
    # a 28 minute walk
  location1 = gps_utils.Location(37.417747, -122.086086)
  location2 = gps_utils.Location(37.421624, -122.096472)
  speed = 7  # meters/sec
  frequency = 10  # Hz
  file_name = "userwalking.csv"
  
  user_motion = generate_route.TimedRoute(location1, location2, speed, frequency)
  user_motion.write_route(file_name)

  file_path = os.path.abspath("geobeam/user_motion_files/" + file_name)
  sim_one = DynamicSimulation(600, -2, file_path)
  sim_two = StaticSimulation(60, -2, 27.417747, -112.086086)
  sim_three = StaticSimulation(10, -4, 37.417747, -122.086086)
  simulation_set = SimulationSet([sim_one, sim_two, sim_three])
  simulation_set.run_simulations()


if __name__ == "__main__":
  sys.exit(main())
