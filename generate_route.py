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

"""Generate a route that can be made into a User Motion File based on two locations.

Leave one blank line.  The rest of this docstring should contain an
overall description of the module or program.  Optionally, it may also
contain a brief description of exported classes and functions and/or usage
examples.

  Typical usage example:

  foo = ClassFoo()
  bar = foo.FunctionBar()
"""

import sys
import csv
from datetime import datetime
import pprint

from map_requests import request_directions,request_elevations
from gps_utils import lla_to_xyz


#average in meters per second
TRANSPORT_SPEEDS = { "walking": 1.4, "running": 2, "biking": 3}

class Location(object):
  """An object for a location (in the form of a set of coordinates)

  Attributes:
      latitude: A float for the latitude of the location in Decimal Degrees
      longitude A float for the longitude of the location in Decimal Degrees
  """

  def __init__(self,latitude,longitude,altitude=None):
    self.latitude = latitude
    self.longitude = longitude
    self.altitude = altitude
    self.x = None
    self.y = None
    self.z = None

  def get_lat_lon_tuple(self):
    return (self.latitude,self.longitude)

  def get_xyz_tuple(self):
    return (self.x,self.y,self.z)

  def add_XYZ(self):
    self.x,self.y,self.z = lla_to_xyz(self.latitude,self.longitude,self.altitude)

  def __repr__(self):
    return 'Location(%s, %s, %s)' % (self.latitude, self.longitude, self.altitude)

class Route(object):
  """An object for a route based on the input of a start and ending location

  Attributes:
      start_location: a Location object for the start of the route
      end_location: a Location object for the end of the route
      route: a list of Location objects for each point on the route
      distances: a list of distances between each pair of consecutive locations
      durations: a list of durations between each pair of consecutive locations
      polyline: an encoded format for the route given by the Maps API for ease of drawing
  """

  def __init__(self, start_location, end_location):
    self.start_location = start_location
    self.end_location = end_location
    self.route = []
    self.distances = []
    self.durations = []
    self.polyline = None

  def create_route(self):
    locations,self.distances,self.durations,self.polyline = request_directions(self.start_location.get_lat_lon_tuple(),self.end_location.get_lat_lon_tuple())
    route = []
    for location in locations:
      latitude = location[0]
      longitude = location[1]
      route.append(Location(latitude,longitude))
    self.route = route
    self.add_altitudes()
  
  def add_altitudes(self):
    locations = []
    for location in self.route:
      locations.append(location.get_lat_lon_tuple())
    elevations = request_elevations(locations)
    for location,elevation in zip(self.route,elevations):
      location.altitude = elevation
      location.add_XYZ()

  def write_route(self,file_name):
    write_array = []
    for location in self.route:
      write_array.append(location.get_xyz_tuple())
    write_to_csv(file_name,write_array)

class TimedRoute(Route):
  """An object for a route that has a desired speed and point frequency

  Attributes:
      start_location: a Location object for the start of the route
      end_location: a Location object for the end of the route
      speed: how fast the person moves through the route
      frequency: how many points per second the timed route should have (Hz)
      route: a list of Location objects for each point on the route
      distances: a list of distances between each pair of consecutive locations
      durations: a list of durations between each pair of consecutive locations
      polyline: an encoded format for the route given by the Maps API for ease of drawing
  """
  def __init__(self, start_location, end_location,speed,frequency):
    Route.__init__(self,start_location,end_location)
    self.speed = speed
    self.frequency = frequency

  def create_route(self):
    Route.create_route(self)
    self.upsample_route()
  
  def upsample_route(self):
    points_per_meter = self.frequency/self.speed
    new_route = []

    # fill 0.1-0.9s with the same location as 1.0s
    for i in range(1, 10):
      new_route.append(self.route[0])

    for i in range(len(self.distances)):
      distance = self.distances[i]
      start_point = self.route[i]
      end_point = self.route[i+1]

      points_needed = int(distance*points_per_meter)-1
      latitude_delta = (end_point.latitude-start_point.latitude) / points_needed
      longitude_delta = (end_point.longitude-start_point.longitude) / points_needed
      altitude_delta = (end_point.altitude-start_point.altitude) / points_needed
      for j in range(points_needed):
        new_point = Location(start_point.latitude + latitude_delta*j, 
                      start_point.longitude + longitude_delta*j, 
                      start_point.altitude + altitude_delta*j)
        new_point.add_XYZ()
        new_route.append(new_point)
    new_route.append(self.route[-1])
    self.route = new_route
    self.duration = [1/self.frequency for x in range(len(new_route)-1)]
    self.distances = [1/points_per_meter for x in range(len(new_route)-1)]

  def write_route(self,file_name):
    write_array = []
    time = 0.0
    for location in self.route:
      write_array.append(("%.1f" % (time,),)+location.get_xyz_tuple())
      time = time + (1/self.frequency)
    write_to_csv(file_name,write_array)

def write_to_csv(file_name,value_array):
  with open(file_name, "w") as csv_file:
    csv.writer(csv_file).writerows(value_array)

def main():
  location1 = Location(37.417747,-122.086086)
  location2 = Location(37.421624, -122.096472)
  '''
  route = Route(location1,location2)
  route.create_route()
  route.add_altitudes()
  route.write_route("routetestfile.csv")
  '''
  user_motion = TimedRoute(location1,location2,TRANSPORT_SPEEDS["walking"],10)
  user_motion.create_route()
  user_motion.write_route("usermotiontestfile.csv")
if __name__ == '__main__':
	sys.exit(main())
