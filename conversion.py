# -*- coding: utf-8 -*-

# ####################################################################
#  Copyright (C) 2013-2014 by Johannes Bauer, The University of 
#  Hamburg
#  http://www.tatome.de
#  This file is part of the projection correction project.
#
#  This is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as 
#  published by the Free Software Foundation; either  version 2 
#  of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU General Public  License 
#  along with this file; if not, write to the
#  Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
# ####################################################################

import numpy
import math
import logging

logger = logging.getLogger(__name__)

class Conversion(object):
    """ 
    Implements conversion of camera image coordinates to viewing angles.
    """
    def __init__(self, imageSize, yaw, vergence, roll, focallength):
        """
        imageSize -- size of the camera image.
        yaw -- rotation of the camera around the y axis..
        vergence -- rotation of the camera around the (rotated) x axis.
        roll -- rotation of the camera around the (rotated) z axis.
        """
        norm = numpy.array([[1,0,0],
                            [0,1,0],
                            [0,0,1]], dtype=numpy.float64)
        logger.debug(
            "Conversion with yaw %f, vergence %f, roll %f, focal length %f", 
            yaw, vergence, roll, focallength
        )

        self.x = self.rotate(norm[0], norm[1], yaw)
        self.y = self.rotate(norm[1], self.x, -vergence)
        self.normal = numpy.cross(self.x,self.y) * focallength
        self.imageSize = imageSize
        logger.debug("x: %s\ny: %s\nz: %s",  self.x,self.y,self.normal)
    
    def __vectorLength__(self, vector):
        return numpy.sqrt(numpy.sum(numpy.square(vector), axis=0))
    
    def rotate(self, v, k, theta):
        '''
        Returns k rotated around v by angle theta (in radians)
        '''
        cth = math.cos(theta)
        return v * cth + numpy.cross(k,v) * math.sin(theta)

    def convert(self, point):
        """
        point -- (2 x n) array of horizontal and vertical image coordinates.
        returns viewing angles of the image coordinates.
        """
        x,y = point
        x -= self.imageSize[0]/2
        y -= self.imageSize[1]/2

        def extend(a):
            return numpy.tile(a,(3,1)).transpose()
        initial = (extend(x)*self.x + extend(y)*self.y + self.normal).transpose()
        length = self.__vectorLength__(initial)
        yaw = numpy.arctan2(initial[0],initial[2])
        vergence = numpy.arcsin(initial[1]/length)

        return (yaw,vergence)
