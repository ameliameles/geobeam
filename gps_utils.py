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

"""Utilities for doing operations on GPS locations.
"""

import math

# World Geodetic System defined constants
WGS84_EARTH_RADIUS = 6378137.0
WGS84_ECCENTRICITY = 0.0818191908426


def lla_to_xyz(latitude, longitude, altitude):
  """Convert a single lat/lng/alt coordinate to ECEF coordinate system.

  Produces earth-centered, earth-fixed (ecef) coordinates and was
  adapted from c code in bladeGPS:
  https://github.com/osqzss/bladeGPS/blob/master/gpssim.c

  Args:
    latitude: latitude float
    longitude: longitude float
    altitude: altitude float

  Returns:
    location in ecef format (x,y,z)
  """
  eccentricity_sq = WGS84_ECCENTRICITY**2
  latitude_radians = latitude * (3.14159265358979/180)
  longitude_radians = longitude * (3.14159265358979/180)

  cos_latitude = math.cos(latitude_radians)
  sin_latitude = math.sin(latitude_radians)
  cos_longitude = math.cos(longitude_radians)
  sin_longitude = math.sin(longitude_radians)
  n_vector = WGS84_EARTH_RADIUS/math.sqrt(1.0-(WGS84_ECCENTRICITY*sin_latitude)**2)

  x = (n_vector + altitude)*cos_latitude*cos_longitude
  y = (n_vector + altitude)*cos_latitude*sin_longitude
  z = ((1.0-eccentricity_sq)*n_vector + altitude)*sin_latitude
  return (x, y, z)
