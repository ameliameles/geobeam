# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License")
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

"""Extract Geolocation Points from GPX File.
"""
import os

import xml.etree.ElementTree as ET

#prefix url in xml file
PREFIX_URL = "{http://www.topografix.com/GPX/1/1}"

class GpxFileParser: 

    #TODO: TBD(@lynnzl) replace with variable file path
    def parse_file(self, file_path):
        """
        Traverses the xml tree and extract all the needed datafields for analysis

        Args:
          filename: name of the xml file

        Returns:
          a GpsDataSet
        """
        file_type = self._get_file_type(file_path)
        
        if file_type == ".xml" or file_type == ".gpx":
          with open(file_path, 'r') as gpx_file:
              gpx_tree = ET.parse(gpx_file)
              
          root = gpx_tree.getroot()

          # Create the gpx gpsmetadata
          #gpx_metadata = self.parse_gpx_metadata(root, PREFIX_URL)

          # parse to get list of gps location points
          gpx_points = self.parse_gpx_trkpts(root, PREFIX_URL)

          return gpx_points

        else:
            print('Invalid file type. Accepted: xml, gpx. Received: ' + file_type)
            return None

    def _get_file_type(self, file_path):
        """
        Get the file type
        """
        file_type = os.path.splitext(file_path)[1]

        if file_type is None:
            print("File has no extension")
            return None

        return file_type

    def parse_gpx_metadata(self, root, prefix):
        """
        Helper function to parse metadata information in xml file
        """
        # Get metadata information
        metadata = root.find(prefix + 'metadata')
        if metadata is None:
            print('Metadata is None, could not be parsed.')
            return None


        # Parse metadata information
        device, identifier, manufacturer, model = "", "", "", ""
        tz_starttime = None

        for data in metadata.iter():
            if data.tag == prefix + 'device':
                device = data.text
            elif data.tag == prefix + 'id':
                identifier = data.text
            elif data.tag == prefix + 'manufacturer':
                manufacturer = data.text
            elif data.tag == prefix + 'model':
                model = data.text
            elif data.tag == prefix + 'time':
                tz_starttime = self.parse_time(data.text)

        # Parse end timestamp
        endtimestr = root.find(prefix + 'time').text
        tz_endtime = self.parse_time(endtimestr)

        #return GpsMetaData(device, identifier, manufacturer, model, tz_starttime, tz_endtime)


    def parse_gpx_trkpts(self, root, prefix) -> []:
        """
        Helper function to parse trkpts in xml file
        """
        gpx_points = []

        trk = root.find(prefix + 'trk')
        if trk is None:
            print('trk is None, could not parse trkpts.')
            return None

        trkseg = trk.find(prefix + 'trkseg')
        if trkseg is None:
            print('trkseg is None, could not parse trkpts.')
            return None

        if len(trkseg) == 0:
            print('trkseg is empty, could not parse trkpts.')
            return None

        # Get the start location
        first_trkpt = trkseg[0]
        prev_altitude = 0

        # Get every track point information
        for trkpt in trkseg:
            # Get the latitude and longitude
            lat = float(trkpt.get('lat'))
            lon = float(trkpt.get('lon'))

            # if no altitude value, make it same as previous point's altitude
            altitude = prev_altitude

            for data in trkpt.iter():
               if data.tag == prefix + 'ele':
                  altitude = float(data.text)
                  prev_altitude = altitude

            current_location = (lat, lon, altitude)
            gpx_points.append(current_location)

        return gpx_points
