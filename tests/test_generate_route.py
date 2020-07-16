import unittest
from unittest.mock import patch
from unittest.mock import call
from unittest.mock import Mock
from unittest.mock import mock_open
import geobeam

class MockLocation():

  def __init__(self, latitude, longitude, altitude=0):
    self.latitude = latitude
    self.longitude = longitude
    self.altitude = altitude

  def get_lat_lon_tuple(self):
    return (self.latitude, self.longitude)

class RouteTest(unittest.TestCase):

  def setUp(self):
    self.location1 = (26.10000, 86.10299)
    self.location2 = (26.105345, 86.10344)
    self.location3 = (26.23334, 86.23432)
    self.altitudes = [5.11, 4.3, 7.4]
    self.distances = [5, 10]
    self.polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"

  @patch('geobeam.generate_route.Location')
  @patch('geobeam.generate_route.request_elevations')
  @patch('geobeam.generate_route.request_directions')
  def test_create_route(self, mock_directions_request, mock_elevations_request, mock_location):
    start_location_mock = mock_location
    end_location_mock = mock_location
    location_list = [self.location1,self.location2,self.location3]
    mock_location.get_lat_lon_tuple.side_effect = [self.location1, self.location3]
    mock_directions_request.return_value = (location_list, self.distances, self.polyline)
    mock_elevations_request.return_value = self.altitudes

    route = geobeam.generate_route.Route(start_location_mock, end_location_mock)

    mock_directions_request.assert_called_once_with(self.location1, self.location3)
    mock_elevations_request.assert_called_once_with(location_list)
    # TODO(ameles) replace with actual patch for the class
    calls = [call(self.location1[0], self.location1[1], self.altitudes[0]),
             call(self.location2[0], self.location2[1], self.altitudes[1]),
             call(self.location3[0], self.location3[1], self.altitudes[2])]
    mock_location.assert_has_calls(calls)
    self.assertEqual(len(route.route),3)
    self.assertEqual(route.distances, self.distances)
    self.assertEqual(route.polyline, self.polyline)

  @patch('geobeam.generate_route._write_to_csv')
  @patch('geobeam.generate_route.Location')
  @patch('geobeam.generate_route.Route.create_route')
  def test_write_route(self, mock_create_route, mock_location, mock_write_to_csv):
    filename = "writeroutetest.csv"
    test_xyz = [(-2849585.509, 4655993.331, 3287769.376),
                (-2694180.667, -4297222.330, 3854325.576),
                (1694180.667, -3297222.330, 2854325.576)]
    test_route = geobeam.generate_route.Route(mock_location,mock_location)
    mock_location().get_xyz_tuple.side_effect = test_xyz
    test_route.route = [mock_location(self.location1),
                        mock_location(self.location2),
                        mock_location(self.location3)]
    test_route.write_route(filename)
    mock_write_to_csv.assert_called_once_with("geobeam/user_motion_files/writeroutetest.csv", test_xyz)

class TimedRouteTest(unittest.TestCase):

  def setUp(self):
    self.location1 = (26.10000, 86.10299)
    self.location2 = (26.105345, 86.10344)
    self.location3 = (26.23334, 86.23432)
    self.altitudes = [5.11, 4.3, 7.4]
    self.distances = [5, 10]
    self.polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"

  def mock_location_side_effect(self, latitude, longitude, altitude=0):
    return MockLocation(latitude, longitude, altitude)

  @patch('geobeam.generate_route.TimedRoute.upsample_route')
  @patch('geobeam.generate_route.Location')
  @patch('geobeam.generate_route.request_elevations')
  @patch('geobeam.generate_route.request_directions')
  def test_create_route(self, mock_directions_request, mock_elevations_request, mock_location, mock_upsample_route):
    location_list = [self.location1,self.location2,self.location3]
    speed = 7 #meters per second
    frequency = 10 #Hz

    start_location_mock = mock_location
    end_location_mock = mock_location
    mock_location.get_lat_lon_tuple.side_effect = [self.location1, self.location3]
    mock_directions_request.return_value = (location_list, self.distances, self.polyline)
    mock_elevations_request.return_value = self.altitudes

    route = geobeam.generate_route.TimedRoute(start_location_mock, end_location_mock, speed, frequency)

    mock_directions_request.assert_called_once_with(self.location1, self.location3)
    mock_elevations_request.assert_called_once_with([self.location1, self.location2, self.location3])
    mock_upsample_route.assert_called_once()

    calls = [call(self.location1[0], self.location1[1], self.altitudes[0]),
             call(self.location2[0], self.location2[1], self.altitudes[1]),
             call(self.location3[0], self.location3[1], self.altitudes[2])]
    mock_location.assert_has_calls(calls)
    self.assertEqual(len(route.route),3)

  @patch('geobeam.generate_route.Location')
  @patch('geobeam.generate_route.request_elevations')
  @patch('geobeam.generate_route.request_directions')
  def test_upsample_route(self, mock_directions_request, mock_elevations_request, mock_location):
    location_list = [self.location1,self.location2,self.location3]
    speed = 10 #meters per second
    frequency = 10 #Hz

    mock_location.side_effect = self.mock_location_side_effect
    start_location_mock = mock_location(self.location1[0],self.location1[1])
    end_location_mock = mock_location(self.location3[0], self.location3[1])
    mock_directions_request.return_value = (location_list, self.distances, self.polyline)
    mock_elevations_request.return_value = self.altitudes

    route = geobeam.generate_route.TimedRoute(start_location_mock, end_location_mock, speed, frequency)
    # number of new points and original start points plus extra ten cycles of first point and last end point
    test_point_count = sum([int(distance*frequency/speed)-1 for distance in self.distances]) + 11
    test_upsampled_distances = [speed/frequency for x in range(test_point_count-1)]
    self.assertEqual(len(route.route), test_point_count)
    self.assertEqual(route.distances, test_upsampled_distances)

  @patch('geobeam.generate_route.Location')
  @patch('geobeam.generate_route.request_elevations')
  @patch('geobeam.generate_route.request_directions')
  def test_upsample_route_no_downsample(self, mock_directions_request, mock_elevations_request, mock_location):
    location_list = [self.location1,self.location2,self.location3]
    polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    speed = 10 #meters per second
    frequency = 1 #Hz
    
    mock_location.side_effect = self.mock_location_side_effect
    start_location_mock = mock_location(self.location1[0],self.location1[1])
    end_location_mock = mock_location(self.location3[0], self.location3[1])
    mock_directions_request.return_value = (location_list, self.distances, self.polyline)
    mock_elevations_request.return_value = self.altitudes

    route = geobeam.generate_route.TimedRoute(start_location_mock, end_location_mock, speed, frequency)

    test_point_count = 13  # 10 extra cycles of first point plus 3 original points
    self.assertEqual(len(route.route), test_point_count)

  @patch('geobeam.generate_route._write_to_csv')
  @patch('geobeam.generate_route.Location')
  @patch('geobeam.generate_route.TimedRoute.create_route')
  def test_write_route(self, mock_create_route, mock_location, mock_write_to_csv):
    filename = "writeroutetest.csv"
    speed = 10 #meters per second
    frequency = 10 #Hz
    test_xyz = [(-2849585.509, 4655993.331, 3287769.376),
                (-2694180.667, -4297222.330, 3854325.576),
                (1694180.667, -3297222.330, 2854325.576)]
    expected_write_array = [('0.0', -2849585.509, 4655993.331, 3287769.376),
                            ('0.1', -2694180.667, -4297222.330, 3854325.576),
                            ('0.2', 1694180.667, -3297222.330, 2854325.576)]
    test_route = geobeam.generate_route.TimedRoute(mock_location,mock_location, speed, frequency)
    mock_location().get_xyz_tuple.side_effect = test_xyz
    test_route.route = [mock_location(self.location1),
                              mock_location(self.location2),
                              mock_location(self.location3)]
    test_route.write_route(filename)
    mock_write_to_csv.assert_called_once_with("geobeam/user_motion_files/writeroutetest.csv", expected_write_array)

class CSVWriterTest(unittest.TestCase):

  @patch('geobeam.generate_route.csv')
  def test_write_to_csv(self, mock_csv):
    open_mock = mock_open()
    expected_write_array = [('0.0', -2849585.509, 4655993.331, 3287769.376),
                            ('0.1', -2694180.667, -4297222.330, 3854325.576),
                            ('0.2', 1694180.667, -3297222.330, 2854325.576)]
    with patch("geobeam.generate_route.open", open_mock, create=True):
      geobeam.generate_route._write_to_csv("geobeam/user_motion_files/test.csv", expected_write_array)
    open_mock.assert_called_with("geobeam/user_motion_files/test.csv", "w")
    mock_csv.writer.assert_called_once()
    mock_csv.writer().writerows.assert_called_once_with(expected_write_array)
if __name__ == '__main__':
    unittest.main()
