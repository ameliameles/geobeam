#!/usr/bin/env python3

# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Classes for Static and Dynamic Simulations, and for Simulation Sets

  Typical usage example:
  sim_one = DynamicSimulation(600, -2, "userwalking.csv")
  sim_two = StaticSimulation(60, -2, 27.417747, -112.086086)
  sim_three = StaticSimulation(20, -4, 37.417747, -122.086086)
  simulation_set = SimulationSet([sim_one, sim_two, sim_three])
"""

import datetime
import subprocess
import time

from tools import kbhit

KEYBOARD = kbhit.KBHit()


class Simulation():
  """An object for a single GPS Simulation.

  Attributes:
    run_time: simulation duration in seconds
    gain: signal gain for the broadcast by bladeRF board
    process: python subprocess created for the simulation
    process_args: arguments for command to pass into subprocess to run the
    simulation in bladeGPS
    start_time: DateTime object for most recent start time
    end_time: DateTime object for most recent end time
  """

  def __init__(self, run_time, gain=-2):
    self.run_time = run_time
    self.gain = gain
    self.process = None
    self.process_args = ["./run_bladerfGPS.sh", "-T", "now", "-d", str(self.run_time)]
    self.start_time = None
    self.end_time = None

  def run_simulation(self):
    """Starts bladeGPS subprocess using given simulation process arguments.
    """
    self.start_time = datetime.datetime.utcnow()
    self.process = subprocess.Popen(self.process_args, stdin=subprocess.PIPE, cwd="./bladeGPS")
    return

  def end_simulation(self):
    """Ends the bladeGPS subprocess.

    Checks if the process is still running, and then attempts to quit (via
    keyboard signal), terminate, and then kill the subprocess in that order
    """
    while self.process.poll() is None:
      self.process.communicate(input="q".encode())
      print("Quitting simulation...")
      if self.process.poll() is None:
        print("Terminating subprocess...")
        self.process.terminate()
        time.sleep(2)
      if self.process.poll() is None:
        print("Killing subprocess...")
        self.process.kill()
        time.sleep(2)
    self.end_time = datetime.datetime.utcnow()
    self.process = None
    print("Subprocess closed.")
    print("------------------------------------------------")

  def is_running(self):
    """Checks if there is bladeGPS subprocess currently running.

    Returns:
      True if there is a running process, false otherwise
    """
    return self.process is not None and self.process.poll() is None


class StaticSimulation(Simulation):
  """An object for a single GPS Simulation for a static location.

  Attributes:
    run_time: simulation duration in seconds
    gain: signal gain for the broadcast by bladeRF board
    process: python subprocess created for the simulation
    process_args: arguments for command to pass into subprocess to run the
    simulation in bladeGPS
    start_time: DateTime object for most recent start time
    end_time: DateTime object for most recent end time
    latitude: static location latitude in decimal degrees
    longitude: static location longitude in decimal degrees
  """

  def __init__(self, run_time, gain, latitude, longitude):
    Simulation.__init__(self, run_time, gain)
    self.latitude = latitude
    self.longitude = longitude
    coordinate = "%s,%s" % (latitude, longitude)
    self.process_args = ["./run_bladerfGPS.sh", "-l", coordinate, "-T", "now",
                         "-d", str(self.run_time), "-a", str(self.gain)]

  def __repr__(self):
    return "StaticSimulation(run_time=%s, gain=%s, latitude=%s, longitude=%s)" % (self.run_time, self.gain, self.latitude, self.longitude)


class DynamicSimulation(Simulation):
  """An object for a single GPS Simulation for a static location.

  Attributes:
    run_time: simulation duration in seconds
    gain: signal gain for the broadcast by bladeRF board
    process: python subprocess created for the simulation
    process_args: arguments for command to pass into subprocess to run the
    simulation in bladeGPS
    start_time: DateTime object for most recent start time
    end_time: DateTime object for most recent end time
    file_name: name user motion csv file for dynamic route simulation
    to be used from the user_motion_files directory
  """

  def __init__(self, run_time, gain, file_name):
    Simulation.__init__(self, run_time, gain)
    self.file_name = file_name
    file_path = "../geobeam/user_motion_files/" + file_name
    self.process_args = ["./run_bladerfGPS.sh", "-u", file_path, "-T", "now",
                         "-d", str(self.run_time), "-a", str(self.gain)]

  def __repr__(self):
    return "DynamicSimulation(run_time=%s, gain=%s, file_name=%s)" % (self.run_time, self.gain, self.file_name)


class SimulationSet():
  """An object for a set of GPS simulations (that can be dynamic or static).

  Attributes:
    simulations: list of simulation objects in order of desired execution
    current_simulation: simulation object currently being run
    current_simulation_index: index of currently run simulation object in list
    log_filename: string for name of file to log into simulation_logs folder
  """

  def __init__(self, simulations):
    self.simulations = simulations
    self.current_simulation = None
    self.current_simulation_index = None
    now = datetime.datetime.utcnow()
    self.log_filename = now.strftime("%Y-%m-%d_%H:%M:%S")

  def run_simulations(self):
    """Starts simulations and navigates through according to user key press.

    Starts the first simulation, and then continuously checks if the current
    simulation is running, and switches to the next or previous based on
    keyboard input. If user presses q or last simulation finishes, it ends
    the simulation set
    """
    self.current_simulation_index = 0
    self.current_simulation = self.simulations[self.current_simulation_index]
    self.current_simulation.run_simulation()
    print("------------------------------------------------")
    print("Press 'n' to go to next sim, 'p' to go to previous sim, or 'q' to quit")
    print("------------------------------------------------")
    while self.current_simulation_index < len(self.simulations):
      simulation_running = self.current_simulation.is_running()
      key_hit = key_pressed()
      if key_hit == "q" or (not simulation_running and self.current_simulation_index >= len(self.simulations)-1):
        self.current_simulation.end_simulation()
        self.log_simulation()
        break
      elif key_hit == "n" or not simulation_running:
        self.switch_simulation(self.current_simulation_index+1)
      elif key_hit == "p":
        self.switch_simulation(self.current_simulation_index-1)
    print("Simulation set ending...")
    self.current_simulation = None
    self.current_simulation_index = None

  def switch_simulation(self, new_simulation_index):
    """Switch to another simulation from the current simulation.

    Ends and logs current simulation, and then begins the new simulation
    and updates current simulation attributes

    Args:
      new_simulation_index: int for index desired simulation to be run
    """
    if new_simulation_index < len(self.simulations) and new_simulation_index >= 0:
      self.current_simulation_index = new_simulation_index
      self.current_simulation.end_simulation()
      self.log_simulation()

      self.current_simulation = self.simulations[self.current_simulation_index]
      self.current_simulation.run_simulation()

  def log_simulation(self):
    """Log start time, end time, type of simulation, and points (if dynamic).

    Logs timestamped file to simulation_logs directory with start and end time,
    whether the simulation was dynamic or static and the initialization arguments.
    If Dynamic, it copies the corresponding lines for that time frame from
    the user motion file used as input
    """
    log_file_path = "simulation_logs/" + self.log_filename

    with open(log_file_path, "a") as logfile:

      logfile.write(str(self.current_simulation) + "\n")
      start = self.current_simulation.start_time.strftime("%Y-%m-%d,%H:%M:%S")
      end = self.current_simulation.end_time.strftime("%Y-%m-%d,%H:%M:%S")
      total_time = (self.current_simulation.end_time - self.current_simulation.start_time).total_seconds()
      logfile.write("Start Time: " + start + "\n")

      if isinstance(self.current_simulation, DynamicSimulation):
        route_file_path = "geobeam/user_motion_files/" + self.current_simulation.file_name
        with open(route_file_path, "r") as route_file:
          lines_to_read = int(total_time*10)  # 10 points per second
          for line, i in zip(route_file, range(lines_to_read)):
            logfile.write(line)

      logfile.write("End Time: " + end + "\n\n")


def key_pressed():
  """Uses Kbhit library to check if user has pressed key.

  Returns:
    a character (string) if a key has been pressed, None otherwise
  """
  pressed_char = None
  if KEYBOARD.kbhit():
    pressed_char = KEYBOARD.getch()
  return pressed_char
