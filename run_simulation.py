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

"""Run simulations.

  Typical usage example:

"""

import datetime
import os
import subprocess
import sys
import time

from tools import kbhit


class Simulation():

  def __init__(self, run_time, gain=-2):
    self.run_time = run_time
    self.gain = gain
    self.process = None
    self.running = False
    self.process_args = ["./run_bladerfGPS.sh", "-T", "now", "-d", str(self.run_time)]

  def run_simulation(self):
    #self.process = subprocess.Popen(self.process_args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, cwd="./bladeGPS")
    self.process = subprocess.Popen(self.process_args, stdin=subprocess.PIPE, cwd="./bladeGPS")
    self.running = True
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
    self.running = False

  def update_status(self):
    if self.process.poll() is not None:
      self.running = False


class StaticSimulation(Simulation):

  def __init__(self, run_time, gain, latitude, longitude):
    Simulation.__init__(self, run_time, gain)
    self.latitude = latitude
    self.longitude = longitude
    coordinate = "%s,%s" % (latitude, longitude)
    self.process_args = ["./run_bladerfGPS.sh", "-l", coordinate, "-T", "now", "-d", str(self.run_time), "-a", str(self.gain)]


class DynamicSimulation(Simulation):

  def __init__(self, run_time, gain, file_path):
    Simulation.__init__(self, run_time, gain)
    self.file_path = file_path
    self.process_args = ["./run_bladerfGPS.sh", "-u", self.file_path, "-T", "now", "-d", str(self.run_time), "-a", str(self.gain)]


class SimulationSet():

  def __init__(self, simulations):
    self.simulations = simulations
    self.current_simulation = None
    self.current_simulation_number = None
    # eventually may want to specify a certain ephemeris date file to use & download it
    today = datetime.datetime.now()
    day_of_year = today.strftime("%j")
    year = today.strftime("%Y")
    self.ephemeris_filename = "brdc%s_%s0.%sn" % (year, today, year[2:])

  def run_simulations(self):
    self.current_simulation_number = 0
    self.current_simulation = self.simulations[self.current_simulation_number]
    self.current_simulation.run_simulation()
    print('Hit n to go to next sim, p to go to previous sim, or q to quit')
    while self.current_simulation_number < len(self.simulations):
      self.current_simulation.update_status()
      key_hit = key_pressed()
      # print(self.current_simulation,self.current_simulation.running)
      if key_hit == "q" or (not self.current_simulation.running and self.current_simulation_number == len(self.simulations)+1):
        self.current_simulation.end_simulation()
        break
      elif key_hit == "n" or not self.current_simulation.running:
        self.switch_simulation(self.current_simulation_number+1)
      elif key_hit == "p":
        self.switch_simulation(self.current_simulation_number-1)
    self.end_simulations()
    return

  def switch_simulation(self, new_simulation_number):
    if new_simulation_number < len(self.simulations) and new_simulation_number >= 0:
      self.current_simulation_number = new_simulation_number
      self.current_simulation.end_simulation()
      self.current_simulation = self.simulations[self.current_simulation_number]
      self.current_simulation.run_simulation()

  def end_simulations(self):
    print("Simulation set ending...")


def key_pressed():
  keyboard = kbhit.KBHit()
  pressed_char = None
  if keyboard.kbhit():
      pressed_char = keyboard.getch()
      print(pressed_char)
  keyboard.set_normal_term()
  return pressed_char

def main():
  sim_one = StaticSimulation(30, -2, 37.417747, -122.086086)
  sim_two = StaticSimulation(30, -2, 27.417747, -112.086086)
  # sim_three = StaticSimulation(30,-2, 17.417747,-102.086086)
  sim_three = DynamicSimulation(30, -2, "../userbiking.csv")
  simulation_set = SimulationSet([sim_one, sim_two, sim_three])
  simulation_set.run_simulations()


if __name__ == "__main__":
  sys.exit(main())
