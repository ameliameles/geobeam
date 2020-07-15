import unittest
#from unittest import mock
from unittest.mock import patch
from unittest.mock import call
from unittest.mock import Mock
import geobeam

class MockLocation():

  def __init__(self, latitude, longitude, altitude=0):
    self.latitude = latitude
    self.longitude = longitude
    self.altitude = altitude

  def get_lat_lon_tuple(self):
    return (self.latitude, self.longitude)

class RouteTest(unittest.TestCase):

  @patch('geobeam.generate_route.Location')
  @patch('geobeam.generate_route.request_elevations')
  @patch('geobeam.generate_route.request_directions')
  def test_create_route(self, mock_directions_request, mock_elevations_request, mock_location):
    location1 = (26.10000, 86.10299)
    location2 = (26.105345, 86.10344)
    location3 = (26.23334, 86.23432)
    altitudes = [5.11, 4.3, 7.4]
    distances = [5, 10]
    polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"

    start_location_mock = mock_location
    end_location_mock = mock_location
    mock_location.get_lat_lon_tuple.side_effect = [location1, location3]
    mock_directions_request.return_value = ([location1,location2,location3], distances, polyline)
    mock_elevations_request.return_value = altitudes

    route = geobeam.generate_route.Route(start_location_mock, end_location_mock)

    mock_directions_request.assert_called_once_with(location1, location3)
    mock_elevations_request.assert_called_once_with([location1, location2, location3])
    # TODO(ameles) replace with actual patch for the class
    calls = [call(location1[0], location1[1], altitudes[0]),
             call(location2[0], location2[1], altitudes[1]),
             call(location3[0], location3[1], altitudes[2])]
    mock_location.assert_has_calls(calls)
    self.assertEqual(len(route.route),3)
    self.assertEqual(route.distances, distances)
    self.assertEqual(route.polyline, polyline)


class TimedRouteTest(unittest.TestCase):

  def mock_location_side_effect(self, latitude, longitude, altitude=0):
    return MockLocation(latitude, longitude, altitude)

  @patch('geobeam.generate_route.TimedRoute.upsample_route')
  @patch('geobeam.generate_route.Location')
  @patch('geobeam.generate_route.request_elevations')
  @patch('geobeam.generate_route.request_directions')
  def test_create_route(self, mock_directions_request, mock_elevations_request, mock_location, mock_upsample_route):
    location1 = (26.10000, 86.10299)
    location2 = (26.105345, 86.10344)
    location3 = (26.23334, 86.23432)
    altitudes = [5.11, 4.3, 7.4]
    distances = [5, 10]
    polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    speed = 7 #meters per second
    frequency = 10 #Hz

    start_location_mock = mock_location
    end_location_mock = mock_location
    mock_location.get_lat_lon_tuple.side_effect = [location1, location3]
    mock_directions_request.return_value = ([location1,location2,location3], distances, polyline)
    mock_elevations_request.return_value = altitudes

    route = geobeam.generate_route.TimedRoute(start_location_mock, end_location_mock, speed, frequency)

    mock_directions_request.assert_called_once_with(location1, location3)
    mock_elevations_request.assert_called_once_with([location1, location2, location3])
    mock_upsample_route.assert_called_once()

    calls = [call(location1[0], location1[1], altitudes[0]),
             call(location2[0], location2[1], altitudes[1]),
             call(location3[0], location3[1], altitudes[2])]
    mock_location.assert_has_calls(calls)
    self.assertEqual(len(route.route),3)

  @patch('geobeam.generate_route.Location')
  @patch('geobeam.generate_route.request_elevations')
  @patch('geobeam.generate_route.request_directions')
  def test_upsample_route(self, mock_directions_request, mock_elevations_request, mock_location):
    location1 = (26.10000, 86.10299)
    location2 = (26.105345, 86.10344)
    location3 = (26.23334, 86.23432)
    location_list = [location1,location2,location3]
    altitudes = [5.11, 4.3, 7.4]
    distances = [5, 10]
    polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    speed = 10 #meters per second
    frequency = 10 #Hz

    mock_location.side_effect = self.mock_location_side_effect
    start_location_mock = mock_location(location1[0],location1[1])
    end_location_mock = mock_location(location3[0], location3[1])
    mock_directions_request.return_value = (location_list, distances, polyline)
    mock_elevations_request.return_value = altitudes

    route = geobeam.generate_route.TimedRoute(start_location_mock, end_location_mock, speed, frequency)
    # number of new points and original start points plus extra ten cycles of first point and last end point
    test_point_count = sum([int(distance*frequency/speed)-1 for distance in distances]) + 11
    test_upsampled_distances = [speed/frequency for x in range(test_point_count-1)]
    self.assertEqual(len(route.route), test_point_count)
    self.assertEqual(route.distances, test_upsampled_distances)

  @patch('geobeam.generate_route.Location')
  @patch('geobeam.generate_route.request_elevations')
  @patch('geobeam.generate_route.request_directions')
  def test_upsample_route_no_downsample(self, mock_directions_request, mock_elevations_request, mock_location):
    location1 = (26.10000, 86.10299)
    location2 = (26.105345, 86.10344)
    location3 = (26.23334, 86.23432)
    location_list = [location1,location2,location3]
    altitudes = [5.11, 4.3, 7.4]
    distances = [5, 10]
    polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    speed = 10 #meters per second
    frequency = 1 #Hz
    
    mock_location.side_effect = self.mock_location_side_effect
    start_location_mock = mock_location(location1[0],location1[1])
    end_location_mock = mock_location(location3[0], location3[1])
    mock_directions_request.return_value = (location_list, distances, polyline)
    mock_elevations_request.return_value = altitudes

    route = geobeam.generate_route.TimedRoute(start_location_mock, end_location_mock, speed, frequency)

    test_point_count = 13  # 10 extra cycles of first point plus 3 original points
    self.assertEqual(len(route.route), test_point_count)


if __name__ == '__main__':
    unittest.main()
