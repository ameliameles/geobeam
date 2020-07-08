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

"""Simulation Classes.

  Typical usage example:

"""

import datetime
import os
import subprocess
import sys
import time

from tools import kbhit


class Simulation():
  """An object for a single GPS Simulation.

  Attributes:
    run_time: simulation duration in seconds
    gain: signal gain for the broadcast by bladeRF board
    process: python subprocess created for the simulation
    process_args: arguments for command to pass into subprocess to run the
    simulation in bladeGPS
  """
  def __init__(self, run_time, gain=-2):
    self.run_time = run_time
    self.gain = gain
    self.process = None
    self.process_args = ["./run_bladerfGPS.sh", "-T", "now", "-d", str(self.run_time)]

  def run_simulation(self):
    #self.process = subprocess.Popen(self.process_args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, cwd="./bladeGPS")
    self.process = subprocess.Popen(self.process_args, stdin=subprocess.PIPE, cwd="./bladeGPS")
    return

  def end_simulation(self):
    while self.process.poll() is None:
      out = self.process.communicate(input="q".encode())
      print("Ending simulation...")
      time.sleep(2)
      if self.process.poll() is None:
        print("Terminating subprocess...")
        self.process.terminate()
        time.sleep(2)
      if self.process.poll() is None:
        print("Killing subprocess...")
        self.process.kill()
        time.sleep(2)
      #output = out[0].decode("utf-8").rstrip("\n")
      #print(output)
      print("Subprocess closed.")
      print("------------------------------------------------")

  def is_running(self):
    return self.process is not None and self.process.poll() is None


class StaticSimulation(Simulation):
  """An object for a single GPS Simulation for a static location.

  Attributes:
    run_time: simulation duration in seconds
    gain: signal gain for the broadcast by bladeRF board
    process: python subprocess created for the simulation
    process_args: arguments for command to pass into subprocess to run the
    simulation in bladeGPS
    latitude: static location latitude in decimal degrees
    longitude: static location longitude in decimal degrees
  """

  def __init__(self, run_time, gain, latitude, longitude):
    Simulation.__init__(self, run_time, gain)
    self.latitude = latitude
    self.longitude = longitude
    coordinate = "%s,%s" % (latitude, longitude)
    self.process_args = ["./run_bladerfGPS.sh", "-l", coordinate, "-T", "now", "-d", str(self.run_time), "-a", str(self.gain)]


class DynamicSimulation(Simulation):
  """An object for a single GPS Simulation for a static location.

  Attributes:
    run_time: simulation duration in seconds
    gain: signal gain for the broadcast by bladeRF board
    process: python subprocess created for the simulation
    process_args: arguments for command to pass into subprocess to run the
    simulation in bladeGPS
    file_path: path to user motion csv file for dynamic route simulation
    either absolutely or relative to the bladeGPS directory
  """
  def __init__(self, run_time, gain, file_path):
    Simulation.__init__(self, run_time, gain)
    self.file_path = file_path
    self.process_args = ["./run_bladerfGPS.sh", "-u", self.file_path, "-T", "now", "-d", str(self.run_time), "-a", str(self.gain)]


class SimulationSet():
  """An object for a set of GPS simulations (that can be dynamic or static).

  Attributes:
    simulations: list of simulation objects in order of desired execution
    current_simulation: simulation object currently being run
    current_simulation_index: index of currently run simulation object in list
    ephemeris_filename: name of ephemeris file being used for the simulations
  """
  def __init__(self, simulations):
    self.simulations = simulations
    self.current_simulation = None
    self.current_simulation_index = None
    # eventually may want to specify a certain ephemeris date file to use & download it
    today = datetime.datetime.now()
    day_of_year = today.strftime("%j")
    year = today.strftime("%Y")
    self.ephemeris_filename = "brdc%s_%s0.%sn" % (year, today, year[2:])

  def run_simulations(self):
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
        break
      elif key_hit == "n" or not simulation_running:
        self.switch_simulation(self.current_simulation_index+1)
      elif key_hit == "p":
        self.switch_simulation(self.current_simulation_index-1)
    self.end_simulations()
    return

  def switch_simulation(self, new_simulation_index):
    if new_simulation_index < len(self.simulations) and new_simulation_index >= 0:
      self.current_simulation_index = new_simulation_index
      self.current_simulation.end_simulation()
      self.current_simulation = self.simulations[self.current_simulation_index]
      self.current_simulation.run_simulation()

  def end_simulations(self):
    print("Simulation set ending...")
    self.current_simulation = None
    self.current_simulation_index = None

def key_pressed():
  keyboard = kbhit.KBHit()
  pressed_char = None
  if keyboard.kbhit():
    pressed_char = keyboard.getch()
    #print(pressed_char)
  keyboard.set_normal_term()
  return pressed_char
