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
import time
import sys

class Simulation():

  def __init__(self,run_time):
    self.run_time = run_time
    self.process = None
    self.running = False

  def run_simulation(self):
    pass

  def end_simulation(self):
    while self.process.poll() is None:
      time.sleep(20)
      out = self.process.communicate(input='q'.encode())
      print("Ending simulation...")
      time.sleep(2)
      if self.process.poll() is None:
        print("Terminating subprocess...")
        self.process.terminate()
        time.sleep(0.5)
      if self.process.poll() is None:
          print("Killing subprocess...")
          self.process.kill()
      output = out[0].decode('utf-8').rstrip('\n')
      print(output)
      print("Subprocess closed...")
    self.running = False

  def update_status(self):
    if self.process.poll() != None:
      self.running = False

class StaticSimulation(Simulation):

  def __init__(self,run_time, latitude, longitude):
    Simulation.__init__(self,run_time)
    self.latitude = latitude
    self.longitude = longitude

  def run_simulation(self):
    coordinate = "%s,%s" % (self.latitude,self.longitude)
    args = ["./run_bladerfGPS.sh", "-l", coordinate, "-T", "now", "-d", str(self.run_time)]
    #self.process = subprocess.Popen(args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    self.process = subprocess.Popen(args, stdin=subprocess.PIPE, cwd='./bladeGPS')
    self.running = True
    return

class DynamicSimulation(Simulation):

  def __init__(self, run_time):
    Simulation.__init__(self, run_time)

class SimulationSet():

  def __init__(self, simulations):
    self.simulations = simulations
    self.current_simulation = None
    today = datetime.datetime.now()
    day_of_year = today.strftime('%j')
    year = today.strftime('%Y')
    self.ephemeris_filename = "brdc%s_%s0.%sn" % (year, today, year[2:])

  def run_simulations(self):
    self.current_simulation = 0
    sim = self.simulations[self.current_simulation]
    sim.run_simulation()
    while(self.current_simulation < len(self.simulations)):
      sim.update_status()
      #print(self.current_simulation,sim.running)
      if(key_pressed() == 'n' or not sim.running):
        self.current_simulation = self.current_simulation + 1
        if(self.current_simulation < len(self.simulations)):
          sim.end_simulation()
          time.sleep(2)
          sim = self.simulations[self.current_simulation]
          sim.run_simulation()
      if(key_pressed() == 'p'):
        self.current_simulation = self.current_simulation - 1
        if(self.current_simulation >= 0):
          sim.end_simulation()
          time.sleep(2)
          sim = self.simulations[self.current_simulation]
          sim.run_simulation()
      if(key_pressed() == 'q' or (not sim.running and self.current_simulation == len(self.simulations)+1)):
        sim.end_simulation()
        break
    self.end_simulations()
    return

  def next_simulation(self):
    pass

  def previous_simulation(self):
    pass

  def end_simulations(self):
    print("simulation set complete")

def key_pressed():
  return None
def main():
  sim_one = StaticSimulation(30,37.417747,-122.086086)
  sim_two = StaticSimulation(30,27.417747,-112.086086)
  sim_three = StaticSimulation(30,17.417747,-102.086086)
  simulation_set = SimulationSet([sim_one, sim_two, sim_three])
  simulation_set.run_simulations()

if __name__ == "__main__":
  sys.exit(main())
