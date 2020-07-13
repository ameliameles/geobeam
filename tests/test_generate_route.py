import unittest
#from unittest import mock
from unittest.mock import patch
from unittest.mock import call
import geobeam

class MockLocation():

  def __init__(self, latitude, longitude, altitude=0):
    self.latitude = latitude
    self.longitude = longitude
    self.altitude = altitude

  def latitude(self):
    return self.latitude
  def longitude(self):
    return self.longitude
  def altitude(self):
    return self.altitude

class RouteTest(unittest.TestCase):

  @patch('geobeam.generate_route.Location')
  @patch('geobeam.generate_route.request_elevations')
  @patch('geobeam.generate_route.request_directions')
  def test_create_route(self, mock_directions_request, mock_elevations_request, mock_location):
    location1 = (26.10000, 86.10299)
    location2 = (26.105345, 86.10344)
    location3 = (26.23334, 86.23432)
    altitudes = [5.11, 4.3, 7.4]
    distances = [5, 10, 15]

    start_location_mock = mock_location(location1[0],location1[1])
    end_location_mock = mock_location(location2[0],location2[1])
    mock_directions_request.return_value = ([location1,location2,location3], distances, "_p~iF~ps|U_ulLnnqC_mqNvxq`@")
    mock_elevations_request.return_value = altitudes

    route = geobeam.generate_route.Route(start_location_mock, end_location_mock)

    mock_directions_request.assert_called_once()
    mock_elevations_request.assert_called_once()
    # TODO(ameles) replace with actual patch for the class
    calls = [call(location1[0], location1[1], altitudes[0]),
             call(location2[0], location2[1], altitudes[1]),
             call(location3[0], location3[1], altitudes[2])]
    mock_location.assert_has_calls(calls)
    self.assertEqual(len(route.route),3)


if __name__ == '__main__':
    unittest.main()
