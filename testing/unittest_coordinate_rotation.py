"""
A unit testing module for coordinate system rotation.

Functions/methods tested:
  coordinate_rotation.adjust_lon_range  
  coordinate_rotation.rotation_matrix
  coordinate_rotation.rotate_spherical
  coordinate_rotation.switch_regular_axes

Improvements/comments:
1. I'm not sure that tests of no rotation are valid.

"""

import unittest

from math import pi, sqrt
import numpy

import os
import sys

module_dir = os.path.join(os.environ['HOME'], 'modules')
sys.path.insert(0, module_dir)
import coordinate_rotation as rot
import netcdf_io as nio

import pdb


##########################
## unittest test clases ##
##########################

class testLonAdjust(unittest.TestCase):
    """Test class for testing the adjustment of longitude values."""

    def setUp(self):
        """Define the test data."""        

        self.data_degrees = numpy.array([0., 360., 378., 60., -30., -810.])
        self.data_radians = numpy.array([0., 2*pi, 2.1*pi, pi/3., -pi/6., -4.5*pi])


    def test_degrees_start0(self):
        """Test for data in degrees, start point = 0.0 [test for success]"""
        
        result = rot.adjust_lon_range(self.data_degrees, radians=False, start=0.0)
        answer = [0.0, 0.0, 18.0, 60.0, 330.0, 270.0] 
        numpy.testing.assert_array_equal(result, answer)


    def test_degrees_start180(self):
        """Test for data in degrees, start point = -180 [test for success]"""

        result = rot.adjust_lon_range(self.data_degrees, radians=False, start=-180.0)
        answer = [0., 0., 18., 60., -30., -90.] 
        numpy.testing.assert_array_equal(result, answer)	
    
    
    def test_radians_start0(self):
        """Test for data in radians, start point = 0.0 [test for success]"""

        result = rot.adjust_lon_range(self.data_radians, start=0.0)
        answer = [0., 0., 0.1*pi, pi/3., (11./6.)*pi, 1.5*pi] 
        numpy.testing.assert_array_equal(result, answer)        
        
        
    def test_radians_start180(self):
        """Test for data in radians, start point = -pi [test for success]"""

        result = rot.adjust_lon_range(self.data_radians, start=-pi)
        answer = [0., 0., 0.1*pi, pi/3., -pi/6., -0.5*pi] 
        numpy.testing.assert_array_equal(result, answer)	        


class testTransformationMatrix(unittest.TestCase):
    """Test class for the transformation matrix used
    in coordinate system rotations."""

    def setUp(self):
        """Define the sets of Euler angles (phi, theta, psi) to be tested"""

        self.angles = [[0.0, 0.0, 0.0],
                       [2 * pi, 2 * pi, 2 * pi],
                       [pi, pi, pi],
                       [0.0, 0.5 * pi, 0.3*pi],
                       [0.4 * pi, 1.2 * pi, 1.7 * pi]]

                        
    def test_no_rotation(self):
        """Test no rotation for psi = theta = psi = 0.0 [test for success]"""

        for phi, theta, psi in self.angles[0:2]:
            for inv in [True, False]:
                result = rot.rotation_matrix(phi, theta, psi, inverse=inv)
                numpy.testing.assert_allclose(result, numpy.identity(3), rtol=1e-07, atol=1e-07)
                

    def test_known_value(self):
        """Test the rotation matrix for a known answer (derived by hand) [test for success]"""
        
        phi, theta, psi = [pi/4., pi/3., pi/6.]
        result = rot.rotation_matrix(phi, theta, psi, inverse=True) #False
        
        a = sqrt(3.0) / 2
        b = 0.5
        c = 1 / sqrt(2.0)
        answer = numpy.empty([3,3])
        answer[0, 0] = (a * c) - (b * c * b)
        answer[0, 1] = (a * c) + (b * c * b)
        answer[0, 2] = b * a
        answer[1, 0] = -(b * c) - (b * c * a)
        answer[1, 1] = -(b * c) + (b * c * a)
        answer[1, 2] = a * a
        answer[2, 0] = a * c
        answer[2, 1] = -(a * c)
        answer[2, 2] = b

        numpy.testing.assert_allclose(result, answer, rtol=1e-07, atol=1e-07) 


    def test_known_inverse(self):
        """Test the inverse rotation matrix for a known answer (derived by hand) [test for success]"""
        
        phi, theta, psi = [pi / 4, pi / 3, pi / 6]
        result = rot.rotation_matrix(phi, theta, psi, inverse=False) #True
        
        a = sqrt(3.0) / 2
        b = 0.5
        c = 1 / sqrt(2.0)
        answer = numpy.empty([3,3])
        answer[0, 0] = (a * c) - (b * c * b)
        answer[0, 1] = -(b * c) - (b * c * a)
        answer[0, 2] = a * c
        answer[1, 0] = (a * c) + (b * c * b)
        answer[1, 1] = -(b * c) + (b * c * a)
        answer[1, 2] = -(a * c)
        answer[2, 0] = a * b
        answer[2, 1] = a * a
        answer[2, 2] = b

        numpy.testing.assert_allclose(result, answer, rtol=1e-07, atol=1e-07) 


    def test_invalid_input(self):
        """Test input angles outside of [0, 2*pi] [test for failure]"""

        self.assertRaises(AssertionError, rot.rotation_matrix, 0.0, pi, 6.5)


    def test_identity(self):
        """The transformation matrix, multiplied by its inverse, 
        should return the identity matrix [test for sanity]"""

        for phi, theta, psi in self.angles:
            A = rot.rotation_matrix(phi, theta, psi, inverse=False)
            Ainv = rot.rotation_matrix(phi, theta, psi, inverse=True)
            product = numpy.dot(A, Ainv)

            numpy.testing.assert_allclose(product, numpy.identity(3), rtol=1e-07, atol=1e-07)


class testRotateSpherical(unittest.TestCase):
    """Test class for rotations in spherical coordinates."""

#    def test_zero_rotation(self):
#        """[test for success]"""
#    
#        phi, theta, psi = rot.north_pole_to_rotation_angles(90, 0)
#
#        lat_axis = numpy.arange(-90, 100, 10)
#	lon_axis = numpy.arange(0, 360, 10)
#	lats, lons = nio.coordinate_pairs(lat_axis, lon_axis) 
#	
#	# Set the poles to zero (not worried if it fails at poles) 
#	lons_answer = lons
#	lons_answer[0:len(lon_axis)] = 0.0
#	lons_answer[-len(lon_axis):] = 0.0
#	
#        latsrot, lonsrot = rot.rotate_spherical(lats, lons, phi, theta, psi, invert=False)
#	
#        numpy.testing.assert_allclose(latsrot, lats, rtol=1e-03, atol=1e-03)
#        numpy.testing.assert_allclose(lonsrot, lons_answer, rtol=1e-03, atol=1e-03)

    
    def test_pure_phi(self):
        """Test pure rotations about the original z-axis (phi).
        For z-axis rotations, the simpliest place to test is the
        equator, as the specified rotation angle will correspond
        exactly to the change in longitude.
        
        Negative phi values correspond to a positive longitudinal 
        direction.
        
	"""
	
        phi = -50
        lats = numpy.array([0, 0, 0, 0, 0])
        lons = numpy.array([0, 65, 170, 230, 340])
        lons_answer = numpy.array([310, 15, 120, 180, 290])
	
        latsrot, lonsrot = rot.rotate_spherical(lats, lons, phi, 0, 0, invert=False)
        
        numpy.testing.assert_allclose(lats, latsrot, rtol=1e-07, atol=1e-07)
        numpy.testing.assert_allclose(lons_answer, lonsrot, rtol=1e-03, atol=1e-03)


    def test_pure_theta(self):
        """Test pure rotations about the original x-axis (theta).
        
        For x-axis rotations, the simpliest place to test is the
        90/270 longitude circle, as the specified rotation angle 
        will correspond exactly to the change in latitude (to visualise
        the rotations, draw a vertical crossection of that circle).
	
        """

        theta = 60
        lats = numpy.array([70, 70, 40, -32, -45, -80])
        lons = numpy.array([90, 270, -90, 90, -90, 90])
        lats_answer = numpy.array([50, 10, -20, 28, -75, -20])
        lons_answer = numpy.array([270, 270, 270, 90, 90, 90])
		
        latsrot, lonsrot = rot.rotate_spherical(lats, lons, 0, theta, 0, invert=False)
        
        numpy.testing.assert_allclose(lats_answer, latsrot, rtol=1e-03, atol=1e-03)
        numpy.testing.assert_allclose(lons_answer, lonsrot, rtol=1e-03, atol=1e-03)
	

    def test_pure_psi(self):
        """Test pure rotations about the final z-axis (psi)."""

        pass


class testSwitchAxes(unittest.TestCase):
    """Test the complete switch of axes"""

    def setUp(self):
        """Set axes"""

        self.lat_axis = numpy.arange(-90, 92.5, 2.5)
	self.lon_axis = numpy.arange(0.0, 362.5, 2.5)
	self.lats, self.lons = nio.coordinate_pairs(self.lat_axis, self.lon_axis)
	self.nlats = len(self.lat_axis)
	self.nlons = len(self.lon_axis)


    def test_no_switch_basic(self):
        """Test for no shift in the north pole, using a basic test
	dataset of all ones [test for success].

        """
        
	data = numpy.ones([self.nlats, self.nlons])
        result = rot.switch_regular_axes(data, self.lats, self.lons, self.lat_axis, self.lon_axis, [90, 0], invert=False)
        
	numpy.testing.assert_allclose(result, data, rtol=1e-07, atol=1e-07)
    
    
#    def test_no_switch_data(self):
#        """Test for no shift in the north pole, using real data [test for success]."""
#        
#	data = nio.InputData('/work/dbirving/datasets/Merra/data/va_Merra_250hPa_monthly_native.nc', 'va', 
#	                     time=('1979-01-01', '1979-01-29', 'none'),
#			     latitude=(-85, 85))
#        lat_axis = data.data.getLatitude()[:]
#	lon_axis = data.data.getLongitude()[:]
#	lats, lons = nio.coordinate_pairs(lat_axis, lon_axis)
#	
#	result = rot.switch_regular_axes(data.data, lats, lons, lat_axis, lon_axis, [90, 0], invert=False)
#        
#	numpy.testing.assert_allclose(result, data.data, rtol=0, atol=0.5)
#    
    
    def test_np_0N_180E(self):
        """Test for new north pole at 0N, 180E [test for success].
        (corresponds to a swap of the lat and lon coordinates of each point?)

        """
        
        pass


    def test_np_90S_0E(self):
        """Test for new north pole at 90S, 0E [test for success].
        (corresponds to change in sign of latitude values)

        """
        
        data = numpy.zeros([self.nlats, self.nlons])
        for index in range(0, self.nlats):
            data[index, :] = self.lat_axis[index] * -1
      
        answer = data * -1
	result = rot.switch_regular_axes(data, self.lats, self.lons, self.lat_axis, self.lon_axis, [-90, 0], invert=False)

        numpy.testing.assert_allclose(result, answer, rtol=0.0, atol=0.4)


if __name__ == '__main__':
    unittest.main()
    
