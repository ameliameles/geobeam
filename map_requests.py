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

"""Handles requests and parsing of Google Maps API calls

  Typical usage example:

  directions = request_directions((37.417747,-122.086086),(37.421624, -122.096472))
  elevations = request_elevations([(37.417747,-122.086086),(37.421624, -122.096472),(37.45634, -121.046592)])
"""

import googlemaps
from datetime import datetime
import pprint
from config import api_key

API_KEY = api_key
gmaps = googlemaps.Client(key=API_KEY)

def request_directions(start_location,end_location):
  """request directions from start_location to end_location

  Args:
    start_location: tuple of floats (lat, lon) for starting point
    end_location: tuple of floats (lat, lon) for ending point
  Returns:
    a list of directions in the deserialized Maps API response format 
    https://developers.google.com/maps/documentation/directions/intro#DirectionsResponses
  """ 
  now = datetime.now()
  directions_response= gmaps.directions(start_location, end_location, mode="walking", departure_time=now)
  parsed_directions_response = parse_directions_response(directions_response)
  return parsed_directions_response

def parse_directions_response(directions_response):
  """Extract basic information relevant to route from the response.

  Args:
    directions_response: list of directions in the deserialized Maps API response format
  Returns:
    if a valid route is found a tuple containing:
      a list of the (lat,lon) points on the route
      a list of distances between those points (in meters)
      a list of durations between those points (in seconds)
      a string of the encoded polyline that can be plotted to show the route
    otherwise: a message that no routes were found
  """
  if len(directions_response) > 0:
    route_response = directions_response[0]
    route_points = []
    route_distances = []
    route_durations = []
    route_polyline = route_response["overview_polyline"]["points"]

    legs = route_response["legs"]
    first_point = (legs[0]["steps"][0]["start_location"]["lat"], legs[0]["steps"][0]["start_location"]["lng"])
    route_points.append(first_point)

    for leg in legs:
      for step in leg["steps"]:
        new_point = (step["end_location"]["lat"], step["end_location"]["lng"])
        new_distance = step["distance"]["value"]  #distance from step's start to end in meters
        new_duration = step["duration"]["value"]  #duration from step's start to end in seconds
        route_points.append(new_point)
        route_distances.append(new_distance)
        route_durations.append(new_duration)

    return (route_points, route_distances, route_durations, route_polyline)

  else:
    raise ValueError("no routes between start and end points, try new points")

def request_elevations(locations):
  """Request elevations for a list of (lat,lon) coordinates.

  Args:
    locations: list of (lat,lon)
  Returns:
    a list of elevation responses in the deserialized Elevation API response format in order of input locations
  """
  elevations_response= gmaps.elevation(locations)
  parsed_elevations_response = parse_elevations_response(elevations_response)
  return parsed_elevations_response

def parse_elevations_response(elevations_response):
  """Extract elevation values in order from API response.

  Args:
    elevations_response: list of elevation responses in the deserialized Elevation API response format
  Returns:
    a list of elevations in the same order as given response
  """
  elevations = []
  for result in elevations_response:
    elevations.append(result["elevation"])
  return elevations

def print_reponse(response):
  pp = pprint.PrettyPrinter(depth=6)
  pp.pprint(reponse)
