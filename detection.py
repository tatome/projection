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
#  published by the Free Software Foundation; either version 2 
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

import collections

import numpy
import cv2
import cv

import instarCamera
import code

import logging
logger = logging.getLogger(__name__)

windowtitle = "Projection Detection"

class Detector(object):
    """ Main class for gathering data about projection distortion. """

    def __init__(self, camera, screenSize, projectorSize, projectorOffset, stepsize):
        """ 
        parameters
        ==========
        camera -- an object of a class with a method takeSnapshot(), which 
            returns an cv2 image.
        screenSize -- dimensions of the portion of the projection image to 
            be probed : a tuple (width,height) of ints.
        projectorSize -- dimensions of the whole projection image : a tuple 
            (width,height) of ints.
        projectorOffset -- offset of the portiion of the projection image 
            to be probed : a tuple (i,j) of ints.
        stepsize -- size of vertical and horizontal steps between pixels 
            to be probed. (stepsize = 10 -- one pixel in a 10x10 square is 
            probed.)
        """
        self.camera = camera
        self.projectorSize = projectorSize
        self.projectorOffset = projectorOffset
        self.screenSize = screenSize
        self.stepsize = stepsize
        self.mapping = collections.defaultdict(tuple)
        self.remapping = {}
        self.imageIterator = code.CodeImageIterator(projectorSize, stepsize)
        self.projector_image = numpy.zeros(
                (screenSize[1], screenSize[0]), dtype=numpy.float
        )

        self.viewport = self.projector_image[
            projectorOffset[1]:projectorOffset[1]+projectorSize[1],
            projectorOffset[0]:projectorOffset[0]+projectorSize[0]
        ]

    def takeSnapshot(self):
        """ use the camera to take and return a snapshot """
        image = self.camera.takeSnapshot()
        image = numpy.average(image, axis=2)
        return image

    def handleImage(self, step, image):
        """ use the information in the given image. """
        image = (image - self.dark_baseline) / self.bright_baseline

        image = (image > 0.1) & (self.mask)
        cv2.imwrite('/tmp/pixels.png', image * 255.)
        idx = numpy.nonzero(image)
        logger.debug("%d white pixels.", idx[0].shape[0])
        for idxy,idxx in zip(idx[0],idx[1]):
            self.mapping[(idxx, idxy)] += (step,)

    def detect(self):
        """
        project images, take and process pictures to get projector pixel to 
        camera pixel mappings.
        """
        cv.NamedWindow(windowtitle,cv.CV_WINDOW_NORMAL)
        cv.ResizeWindow(windowtitle,self.screenSize[0],self.screenSize[1])
        cv.SetWindowProperty(windowtitle, 0, cv.CV_WINDOW_FULLSCREEN)
        cv2.imshow(windowtitle, self.projector_image)
        cv2.waitKey(500)
        self.dark_baseline = self.takeSnapshot()

        # light up only everything that's within the current projector's
        # part of the projected image.
        self.projector_image[:] = 0
        self.viewport[:] = .3
        cv2.imshow(windowtitle, self.projector_image)
        cv2.waitKey(500)
        allpixels = self.takeSnapshot()
        self.bright_baseline = allpixels - self.dark_baseline
        cv2.imwrite('/tmp/allpixels.png', allpixels)
        self.mask = self.bright_baseline > 30
        cv2.imwrite('/tmp/mask.png', self.mask * 250.)
        
        self.projector_image[:] = 0

        if self.mask.any():
            for step,im in enumerate(self.imageIterator.generator()):
                self.viewport[:] = im
                cv2.imshow(windowtitle, self.projector_image)
                cv2.waitKey(500)
                image = self.takeSnapshot()
                self.handleImage(step, image)
            self.postProcess()
        else:
            logger.info("No visible pixels. Skipping detection for this camera pose and projector.")
    
    def postProcess(self):
        """
        use the information gathered to infer projector pixel to camera pixel 
        mappings.
        """
        tempMapping = collections.defaultdict(list)
        discarded = 0
        for x,y in self.mapping:
            pixel = self.imageIterator.lookupPixel(self.mapping[x,y])
            if pixel:
                i,j = pixel
                if i < self.projectorSize[0] and j < self.projectorSize[1]:
                    logger.debug("Valid Pixel within range: %s", (pixel))
                    i = pixel[0] + self.projectorOffset[0]
                    j = pixel[1] + self.projectorOffset[1]
                    tempMapping[i, j].append((x,y))
                else:
                    logger.debug("Invalid Pixel out of range: %s", (pixel))
                    discarded += 1
            else:
                discarded += 1

        for pixel in tempMapping:
            pixx = numpy.median([i for i,j in tempMapping[pixel]])
            pixy = numpy.median([j for i,j in tempMapping[pixel]])
            self.remapping[pixx,pixy] = pixel

        logger.debug(
            'Found mappings for %d pixels. Discarded %d.',
            len(self.remapping), discarded
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest = 'config', default = 'config.yaml')
    args = parser.parse_args()

    import yaml
    config = yaml.load(open(args.config))
    stepsize = config['detection']['stepsize']
    screenSize = config['screen']['width'],config['screen']['height']
    cameraSize = config['camera']['width'], config['camera']['height']
    cam = instarCamera.instarCamera()

    blank_image = numpy.zeros((screenSize[1], screenSize[0]), dtype=numpy.float)
    cv.NamedWindow(windowtitle,cv.CV_WINDOW_NORMAL)
    cv.ResizeWindow(windowtitle,screenSize[0],screenSize[1])
    cv.SetWindowProperty(windowtitle, 0, cv.CV_WINDOW_FULLSCREEN)
    cv2.imshow(windowtitle, blank_image)
    cv2.waitKey(50)

    data = []
    for shot in config['detection']['shots']:
        cam.rotateTo(shot['angles'])
        for projector in shot['projectors']:
            projectorConfig = config['projectors'][projector]
            projectorSize = projectorConfig['width'],projectorConfig['height']
            projectorOffset = projectorConfig['iOffset'],projectorConfig['jOffset']
            detector = Detector(camera=cam, 
                                screenSize=screenSize, 
                                projectorSize=projectorSize, 
                                projectorOffset=projectorOffset, 
                                stepsize=stepsize)
            detector.detect()

            for x,y in detector.remapping:
                i,j = detector.remapping[x,y]
                data.append((x,y,i,j) + tuple(shot['angles']))

    outfilename = 'distortion.npz'
    logger.info("Done.  Writing data to %s.", outfilename)
    numpy.savez(outfilename, data=data, config=yaml.dump(config))
