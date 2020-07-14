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
import os
import subprocess
import time

from tools import kbhit

KEYBOARD = kbhit.KBHit()
ONE_SEC = 1


class Simulation():
  """An object for a single GPS Simulation.

  Attributes:
    run_duration: int, simulation duration in seconds
    gain: float, signal gain for the broadcast by bladeRF board
    process: python subprocess created for the simulation
    process_args: arguments for command to pass into subprocess to run the
    simulation in bladeGPS
    start_time: DateTime object for most recent start time
    end_time: DateTime object for most recent end time
  """

  def __init__(self, run_duration=None, gain=None):
    self.run_duration = run_duration
    self.gain = gain
    self.process = None
    self.start_time = None
    self.end_time = None

  def run_simulation(self):
    """Starts bladeGPS subprocess using given simulation process arguments.
    """
    self.start_time = datetime.datetime.utcnow()
    self.process = create_bladeGPS_process(run_duration=self.run_duration, gain=self.gain)
    return

  def end_simulation(self):
    """Ends the bladeGPS subprocess.

    Checks if the process is still running, and then attempts to quit (via
    keyboard signal), terminate, and then kill the subprocess in that order
    """
    while self.process.poll() is None:
      self.end_time = datetime.datetime.utcnow()
      self.process.communicate(input="q".encode())
      print("Quitting simulation...")
      time.sleep(ONE_SEC)
      if self.process.poll() is None:
        print("Terminating subprocess...")
        self.process.terminate()
        time.sleep(ONE_SEC)
      if self.process.poll() is None:
        print("Killing subprocess...")
        self.process.kill()
        time.sleep(ONE_SEC)
    else:
      self.end_time = datetime.datetime.utcnow()
    self.process = None
    print("Subprocess closed.")
    print("------------------------------------------------")

  def is_running(self):
    """Checks if there is bladeGPS subprocess currently running.

    Returns:
      True if there is a running process, False otherwise
    """
    return bool(self.process and self.process.poll() is None)
    
class StaticSimulation(Simulation):
  """An object for a single GPS Simulation for a static location.

  Attributes:
    run_duration: int, simulation duration in seconds
    gain: float, signal gain for the broadcast by bladeRF board
    process: python subprocess created for the simulation
    process_args: arguments for command to pass into subprocess to run the
    simulation in bladeGPS
    start_time: DateTime object for most recent start time
    end_time: DateTime object for most recent end time
    latitude: static location latitude in decimal degrees
    longitude: static location longitude in decimal degrees
  """

  def __init__(self, run_duration, gain, latitude, longitude):
    Simulation.__init__(self, run_duration, gain)
    self.latitude = latitude
    self.longitude = longitude

  def run_simulation(self):
    """Starts bladeGPS subprocess using given simulation process arguments.
    """
    self.start_time = datetime.datetime.utcnow()
    location = "%s,%s" % (self.latitude, self.longitude)
    self.process = create_bladeGPS_process(run_duration=self.run_duration,
                                              gain=self.gain,
                                              location=location)
    return

  def __repr__(self):
    return "StaticSimulation(run_duration=%s, gain=%s, latitude=%s, longitude=%s)" % (self.run_duration, self.gain, self.latitude, self.longitude)


class DynamicSimulation(Simulation):
  """An object for a single GPS Simulation for a static location.

  Attributes:
    run_duration: int, simulation duration in seconds
    gain: float, signal gain for the broadcast by bladeRF board
    process: python subprocess created for the simulation
    process_args: arguments for command to pass into subprocess to run the
    simulation in bladeGPS
    start_time: DateTime object for most recent start time
    end_time: DateTime object for most recent end time
    file_name: absolute file path to user motion csv file for 
    dynamic route simulation
  """

  def __init__(self, run_duration, gain, file_path):
    Simulation.__init__(self, run_duration, gain)
    self.file_path = str(file_path)

  def run_simulation(self):
    """Starts bladeGPS subprocess using given simulation process arguments.
    """
    self.start_time = datetime.datetime.utcnow()
    self.process = create_bladeGPS_process(run_duration=self.run_duration,
                                              gain=self.gain,
                                              dynamic_file_path=self.file_path)
    return

  def __repr__(self):
    return "DynamicSimulation(run_duration=%s, gain=%s, file_name=%s)" % (self.run_duration, self.gain, self.file_path)


def create_bladeGPS_process(run_duration=None,
                                   gain=None,
                                   location=None,
                                   dynamic_file_path=None):
  """Returns list of args that make up the specified bladeGPS command.
  
  Args:
    run_duration: int, time in seconds for how long simulation should run
    gain: float, signal gain for the broadcast by bladeRF board
    location: string, "%s,%s" % (latitude, longitude)
    file_path: string, absolute file path to user motion csv file for 
    dynamic route simulation
  Returns:
    list of strings, each of which is an element of the command
    when put together and space-separated
  """
  command = ["./run_bladerfGPS.sh", "-T", "now"]
  if run_duration:
    command.append("-d")
    command.append(str(run_duration))
  if gain:
    command.append("-a")
    command.append(str(gain))
  if location:
    command.append("-l")
    command.append(location)
  elif dynamic_file_path:
    command.append("-u")
    command.append(dynamic_file_path)
  process = subprocess.Popen(command, stdin=subprocess.PIPE, cwd="./bladeGPS")
  return process

class SimulationSet():
  """An object for a set of GPS simulations (that can be dynamic or static).

  Attributes:
    simulations: list of simulation objects in order of desired execution
    current_simulation_index: index of currently run simulation object in list
    log_filename: string for name of file to log into simulation_logs folder
  """

  def __init__(self, simulations):
    self.simulations = simulations
    self.current_simulation_index = None
    now = datetime.datetime.utcnow()
    self.log_filename = now.strftime("GPSSIM-%Y-%m-%d_%H:%M:%S")

  def run_simulations(self):
    """Starts simulations and navigates through according to user key press.

    Starts the first simulation, and then continuously checks if the current
    simulation is running, and switches to the next or previous based on
    keyboard input. If user presses q or last simulation finishes, it ends
    the simulation set
    """
    print("------------------------------------------------")
    print("Press 'n' to go to next sim, 'p' to go to previous sim, or 'q' to quit")
    print("------------------------------------------------")

    self.switch_simulation(0)
    while self.current_simulation_index < len(self.simulations):
      current_simulation = self.get_current_simulation()
      simulation_running = current_simulation.is_running()
      key_hit = key_pressed()
      if not simulation_running and self.current_simulation_index >= len(self.simulations)-1:
        current_simulation.end_simulation()
        self.log_simulation()
        break
      elif key_hit == "q" or key_hit == "Q":
        current_simulation.end_simulation()
        self.log_simulation()
        break
      elif (key_hit == "n" or key_hit == "N") or not simulation_running:
        self.switch_simulation(self.current_simulation_index+1)
      elif key_hit == "p" or key_hit == "P":
        self.switch_simulation(self.current_simulation_index-1)
    print("Simulation set ending...")
    self.current_simulation_index = None

  def get_current_simulation(self):
    """Gets current simulation object.

    Returns:
      current simulation object if set has been started, None otherwise
    """
    if self.current_simulation_index is not None:
      return self.simulations[self.current_simulation_index]
    else:
      return None

  def switch_simulation(self, new_simulation_index):
    """Switch to another simulation from the current simulation.

    Ends and logs current simulation, and then begins the new simulation
    and updates current simulation attributes

    Args:
      new_simulation_index: int for index desired simulation to be run
    """
    if new_simulation_index < len(self.simulations) and new_simulation_index >= 0:
      current_simulation = self.get_current_simulation()
      if (current_simulation):
        current_simulation.end_simulation()
        self.log_simulation()
      new_simulation = self.simulations[new_simulation_index]
      new_simulation.run_simulation()
      self.current_simulation_index = new_simulation_index
    elif new_simulation_index < 0:
      print("\nAlready on first simulation")
    else:
      print("\nAlready on last simulation")

  def log_simulation(self):
    """Log start time, end time, type of simulation, and points (if dynamic).

    Logs timestamped file to simulation_logs directory with start and end time,
    whether the simulation was dynamic or static and the initialization arguments.
    If Dynamic, it copies the corresponding lines for that time frame from
    the user motion file used as input
    """
    log_file_path = "simulation_logs/" + self.log_filename

    with open(log_file_path, "a") as logfile:
      current_simulation = self.get_current_simulation()
      logfile.write(str(current_simulation) + "\n")
      start_time = current_simulation.start_time
      end_time = current_simulation.end_time
      total_time = (end_time-start_time).total_seconds()
      logfile.write("Start Time: " + start_time.strftime("%Y-%m-%d,%H:%M:%S") + "\n")

      if isinstance(current_simulation, DynamicSimulation):
        route_file_path = current_simulation.file_path
        with open(route_file_path, "r") as route_file:
          lines_to_read = int(total_time*10)  # 10 points per second
          for _ in range(lines_to_read):
            logfile.write(next(route_file))

      logfile.write("End Time: " + end_time.strftime("%Y-%m-%d,%H:%M:%S") + "\n\n")

def key_pressed():
  """Uses Kbhit library to check if user has pressed key.

  Returns:
    a character (string) if a key has been pressed, None otherwise
  """
  pressed_char = None
  if KEYBOARD.kbhit():
    pressed_char = KEYBOARD.getch()
  return pressed_char

