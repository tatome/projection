#!/usr/bin/env python
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

import math

import re
import os

import collections

import numpy
import csv
import yaml

import logging

import conversion

logger = logging.getLogger(__name__)

class Converter(object):
    """
    Encapsulates the process of guessing relative viewing angles between 
    shots, converting pixel coordinates to absolute viewing angles, and
    separating data from different projectors, and dumping the result into
    projector-specific files.
    Assumes an approximately linear lens.
    """

    def __init__(self, config):
        """
        config -- a nested dictionary specifying parameters of screen and
                  camera.
        """
        self.config = config
        self.focallength = config['camera']['focallength']
    
    def setFocallength(self, focallength):
        self.focallength = focallength
    
    def __selectByOffset__(self, data, offsets):
        truths = (data[:,4] == offsets[0]) * (data[:,5] == offsets[1])
        return data[numpy.where(truths)][:,0:4]

    def convert(self, data):
        """
        Main method of this class.  See class comment.

        data -- (Nx6) array of sightings of pixels in various shots.
                Entries should be (x,y,i,j,yaw,verg), where 
                
                    x,y are horizontal and vertical coordinates in the camera
                        image

                    i,j are horizontal and vertical coordinates in the 
                        projected image

                    yaw,verg are nominal horizontal and vertical angles of 
                        camera rotation in the respective shot.  These are 
                        used only to identify mappings belonging to the same 
                        shot: We don't trust these values but rather estimate 
                        them for all but the one shot where yaw=verg=0, which
                        is the anchor relative to which all other angles are 
                        estimated.
        """
        imageSize = self.config['camera']['width'],self.config['camera']['height']
        screenSize = self.config['screen']['width'],self.config['screen']['height']

        # This could be tweaked/estimated in case the camera doesn't
        # rotate along the chip's horizontal axis.
        roll = 0.0

        dataset = {} # perspective -> list of mappings

        neutralConversion = conversion.Conversion(
            imageSize, 0, 0, roll, self.focallength
        )

        # sort offsets such that we start near the center and move our way
        # outward.  A more sophisticated algorithm could be thought of, but
        # this works in practice (as long as there is sufficient overlap
        # between shots.
        allOffsets = set(tuple(d[4:6]) for d in data)
        allOffsets = sorted(allOffsets, key=lambda p: (p[0]**2+p[1]**2))
        for offsets in allOffsets:
            datapoints = self.__selectByOffset__(data, offsets)

            datapoints.transpose()[0:2] = neutralConversion.convert(
                datapoints[:,0:2].transpose()
            )

            dataset[offsets] = datapoints

        # create one array marking mapped pixels per perspective
        for offsets,datapoints in dataset.iteritems():
            points = numpy.zeros(screenSize + (2,), dtype=float)
            hits = numpy.zeros(screenSize + (2,), dtype=int)
            for x,y,i,j in datapoints:
                points[i,j] = (x,y)
                hits[i,j] = True,True
            dataset[offsets] = (points, hits)

        # Determine yaw, verg of each perspective wrt. 0,0 perspective,
        # integrate datasets.
        globalMapping,globalHits = dataset[0.,0.]
        del(dataset[0.,0.])
        def integrate(mappingArray, hits):
            # guess the camera rotation wrt. (0,0)
            guessYaw,guessVerg = guessOffsets((globalMapping,globalHits),(mappingArray,hits))
            if guessYaw is not None and guessVerg is not None:
                logger.info(
                    "Before: Guess for nominal offsets %s: (%f, %f)", offsets,
                     math.degrees(guessYaw), math.degrees(guessVerg)
                )

                mappingArray[:,:,0] += guessYaw
                mappingArray[:,:,1] += guessVerg
                guessYaw,guessVerg = guessOffsets((globalMapping,globalHits),(mappingArray, hits))

                # Compute average of viewing angles of projected pixels under different camera
                # rotations.
                globalMapping[:,:,:] = (globalMapping * globalHits + mappingArray * hits)
                globalHits[:,:,:] = globalHits + hits
                globalMapping[:,:,:] /= globalHits + (globalHits == 0)
            else:
                logger.info("Cannot map data for nominal offsets %s: too little overlap.", offsets)

        def guessOffsets((zeroDist,zeroHits),(dist,hits)):
            """
            Guess the camera rotation (the offset) between straight ahead 
            ((0,0) rotation) and a given set of observed projector coordinate 
            to camera image mappings.

            zeroDist -- collection of projector coordinates and corresponding
                viewing angles relative to (0,0).
            zeroHist -- array of ints in which non-zero indicate pixels which are
                mapped in zeroDist
            dist -- collection of projector coordinates and corresponding 
                viewing angles under the camera rotation to be estimated.
            hits -- bitmap marking those pixels in the projected image which
                have a mapping under dist.
            """

            # determine overlap
            overlap = zeroHits * hits
            overlap = numpy.nonzero(overlap[:,:,0])
            logger.debug("Number of overlapping pixels: %d", len(overlap[0]))
            if len(overlap[0]) > 20:
                diffs = zeroDist - dist
                yawDiffs = diffs[:,:,0][overlap]
                vergDiffs  = diffs[:,:,1][overlap]
                guessYaw = numpy.mean(yawDiffs)    # mean of longitudinal differences
                guessVerg  = numpy.mean(vergDiffs)    # mean of latitudinal differences
                return guessYaw, guessVerg
            else:
                logger.warn("No overlap.")
                return None,None
            
        for offsets in sorted(dataset, key=lambda p: (abs(p[0]),abs(p[1]))):
            logger.debug("Integrating data from offsets %s", offsets)
            mappingArray,hits = dataset[offsets]
            integrate(mappingArray, hits)

        # write outfiles, create visualization
        pconfig = config['projectors']
        for projector in pconfig:
            logger.info("Writing data for projector %s" % projector)
            iOffset = pconfig[projector]['iOffset']
            jOffset = pconfig[projector]['jOffset']
            width = pconfig[projector]['width']
            height = pconfig[projector]['height']
            with open(config['combinedDistortionFilePattern'] % projector, 'w') as outfile:
                writer = csv.writer(outfile)
                for i,j in numpy.transpose(numpy.nonzero(globalHits[:,:,0])):
                    if iOffset <= i < iOffset + width and jOffset <= j < jOffset + height:
                        x,y = globalMapping[i,j]
                        writer.writerow([x,y,i,j])


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger('conversion').setLevel(logging.INFO)
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='configfile', type=str, default='config.yaml')
    parser.add_argument('-i', dest='infile', type=str, required=True)
    args = parser.parse_args()

    config = yaml.load(open(args.configfile))

    converter = Converter(config)

    infile = numpy.load(args.infile)
    converter.convert(infile['data'])
