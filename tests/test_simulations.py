from datetime import datetime
import unittest
from unittest.mock import patch
from unittest.mock import call
from unittest.mock import Mock
from unittest.mock import mock_open

import geobeam

class SimulationTest(unittest.TestCase):

  def setUp(self):
    self.run_duration = 100
    self.gain = -2
    self.start_time = datetime(2020,8,15,5,0,0)
    self.end_time = datetime(2020,8,15,5,0,10)

  @patch('geobeam.simulations.datetime.datetime')
  @patch('geobeam.simulations.create_bladeGPS_process')
  def test_run_simulation(self, mock_create_bladeGPS_process, mock_datetime):
    mock_datetime.utcnow.return_value = self.start_time
    test_simulation = geobeam.simulations.Simulation(self.run_duration, self.gain)
    test_simulation.run_simulation()
    self.assertEqual(test_simulation._start_time, self.start_time)
    mock_datetime.utcnow.assert_called_once()
    mock_create_bladeGPS_process.assert_called_once_with(run_duration=self.run_duration, gain=self.gain)

  @patch('geobeam.simulations.time')
  @patch('builtins.print')
  @patch('geobeam.simulations.datetime.datetime')
  @patch('geobeam.simulations.subprocess')
  def test_end_simulation_running_quit(self, mock_subprocess, mock_datetime, 
                                       mock_print, mock_time):
    mock_datetime.utcnow.return_value = self.end_time
    mock_subprocess.poll.side_effect = [0,0]

    test_simulation = geobeam.simulations.Simulation(self.run_duration, self.gain)
    test_simulation._process = mock_subprocess
    test_simulation.is_running = Mock(side_effect = [True, False])
    test_simulation.end_simulation()

    self.assertEqual(test_simulation._process, None)
    self.assertEqual(test_simulation._end_time, self.end_time)

    mock_subprocess.communicate.assert_called_once()
    mock_subprocess.terminate.assert_not_called()
    mock_subprocess.kill.assert_not_called()
    self.assertEqual(mock_subprocess.poll.call_count, 2)

    self.assertEqual(mock_time.sleep.call_count, 1)

  @patch('geobeam.simulations.time')
  @patch('builtins.print')
  @patch('geobeam.simulations.datetime.datetime')
  @patch('geobeam.simulations.subprocess')
  def test_end_simulation_running_terminate(self, mock_subprocess, mock_datetime, 
                                            mock_print, mock_time):
    mock_datetime.utcnow.return_value = self.end_time
    mock_subprocess.poll.side_effect = [None,0]

    test_simulation = geobeam.simulations.Simulation(self.run_duration, self.gain)
    test_simulation._process = mock_subprocess
    test_simulation.is_running = Mock(side_effect = [True, False])
    test_simulation.end_simulation()

    self.assertEqual(test_simulation._process, None)
    self.assertEqual(test_simulation._end_time, self.end_time)

    mock_subprocess.communicate.assert_called_once()
    mock_subprocess.terminate.assert_called_once()
    mock_subprocess.kill.assert_not_called()
    self.assertEqual(mock_subprocess.poll.call_count, 2)

    self.assertEqual(mock_time.sleep.call_count, 2)

  @patch('geobeam.simulations.time')
  @patch('builtins.print')
  @patch('geobeam.simulations.datetime.datetime')
  @patch('geobeam.simulations.subprocess')
  def test_end_simulation_running_terminate_and_kill(self, mock_subprocess, 
                                                     mock_datetime, mock_print, mock_time):
    mock_datetime.utcnow.return_value = self.end_time
    mock_subprocess.poll.side_effect = [None,None]

    test_simulation = geobeam.simulations.Simulation(self.run_duration, self.gain)
    test_simulation._process = mock_subprocess
    test_simulation.is_running = Mock(side_effect = [True, False])
    test_simulation.end_simulation()

    self.assertEqual(test_simulation._process, None)
    self.assertEqual(test_simulation._end_time, self.end_time)

    mock_subprocess.communicate.assert_called_once()
    mock_subprocess.terminate.assert_called_once()
    mock_subprocess.kill.assert_called_once()
    self.assertEqual(mock_subprocess.poll.call_count, 2)

    self.assertEqual(mock_time.sleep.call_count, 3)

  @patch('geobeam.simulations.time')
  @patch('builtins.print')
  @patch('geobeam.simulations.datetime.datetime')
  @patch('geobeam.simulations.subprocess')
  def test_end_simulation_done_running(self, mock_subprocess, mock_datetime, 
                                       mock_print, mock_time):
    mock_datetime.utcnow.return_value = self.end_time

    test_simulation = geobeam.simulations.Simulation(self.run_duration, self.gain)
    test_simulation._process = mock_subprocess
    test_simulation.is_running = Mock(return_value=False)
    test_simulation.end_simulation()

    self.assertEqual(test_simulation._process, None)
    self.assertEqual(test_simulation._end_time, self.end_time)

    mock_subprocess.communicate.assert_not_called()
    mock_subprocess.terminate.assert_not_called()
    mock_subprocess.kill.assert_not_called()
    mock_subprocess.poll.assert_not_called()
    mock_time.sleep.assert_not_called()

  @patch('geobeam.simulations.datetime.datetime')
  @patch('geobeam.simulations.subprocess')
  def test_is_running(self, mock_subprocess, mock_datetime):
    # current process is running
    test_simulation = geobeam.simulations.Simulation(self.run_duration, self.gain)
    test_simulation._process = mock_subprocess
    mock_subprocess.poll.return_value = None
    result = test_simulation.is_running()
    self.assertTrue(result)

    # no current process
    test_simulation = geobeam.simulations.Simulation(self.run_duration, self.gain)
    test_simulation._process = None
    mock_subprocess.poll.return_value = 0
    result = test_simulation.is_running()
    self.assertFalse(result)

    # no current process
    test_simulation = geobeam.simulations.Simulation(self.run_duration, self.gain)
    test_simulation._process = None
    mock_subprocess.poll.return_value = None
    result = test_simulation.is_running()
    self.assertFalse(result)

    # current process already finished
    test_simulation = geobeam.simulations.Simulation(self.run_duration, self.gain)
    test_simulation._process = mock_subprocess
    mock_subprocess.poll.return_value = 0
    result = test_simulation.is_running()
    self.assertFalse(result)
