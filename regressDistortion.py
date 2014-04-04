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

import random
import numpy
import time
import logging
import argparse
import yaml
import csv
import itertools
import collections

from multiprocessing import Pool

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser("Generates a lookup table for distortion correction.")
parser.add_argument('-i', dest='infilename', type=str, required=True)
parser.add_argument('-n', dest='numpyOutfilename', type=str, required=True)
args = parser.parse_args()

config = yaml.load(open('config.yaml'))
iOffset = config['projectors'][args.infilename]['iOffset']
jOffset = config['projectors'][args.infilename]['jOffset']

projectionImageSize = (
    config['projectors'][args.infilename]['width'], 
    config['projectors'][args.infilename]['height']
)

logger.info("loading distortion")

distortion = None
with open("correctedDistortion-" + args.infilename + ".csv", "r") as distfile:
    reader = csv.reader(distfile)
    distortion = numpy.array([map(float, line) for line in reader], dtype=float)
    distortion[:,2] -= iOffset
    distortion[:,3] -= jOffset
    
logger.info("Preprocessing")

# get unique ij -> xy mappings
pointsToX = collections.defaultdict(list)
pointsToY = collections.defaultdict(list)
for x in distortion:
    pointsToX[(x[2],x[3])].append(x[0])
    pointsToY[(x[2],x[3])].append(x[1])

distortion = numpy.array([
    (numpy.median(pointsToX[k]),numpy.median(pointsToY[k]), k[0], k[1]) 
        for k in pointsToX
])


### Want to approximate a function which maps each point on the screen to 
### angles from the camera using a linear combination of 2D Gaussians 
### and a constant.

# how many 2D Gaussians to use to approximate that function:
blobsteps = config['regression']['blobsteps']

# how wide to make the 2D Gaussians
sigma = (
    config['regression']['sigma']*projectionImageSize[0], 
    config['regression']['sigma']*projectionImageSize[1]
)

# how far outside of the image to place the outermost 2D Gaussian
blobspread = config['regression']['blobspread']

# compute center of 2D Gaussians:
gaussianCentersHorizontal = numpy.linspace(
    -blobspread * projectionImageSize[0], 
    (1 + blobspread) * projectionImageSize[0], 
    blobsteps
)

gaussianCentersVertical = numpy.linspace(
    -blobspread*projectionImageSize[1], 
    (1 + blobspread) * projectionImageSize[1], 
    blobsteps
)

gaussianCenters = numpy.meshgrid(gaussianCentersHorizontal, gaussianCentersVertical)
gaussianCenters = (
    gaussianCenters[0].reshape((blobsteps**2,1)),
    gaussianCenters[1].reshape((blobsteps**2,1))
)


### Mashinery to apply basis functions to data
twoSigmaSq = (2*sigma[0]**2), (2*sigma[1]**2)
def applyBasisFunctions(i,j):
    """ Applies basis functions unweighted, doesn't aggregate """
    idiffs = i-gaussianCenters[0]
    jdiffs = j-gaussianCenters[1]
    g = numpy.exp(-(idiffs**2 / twoSigmaSq[0] + jdiffs**2 / twoSigmaSq[1])).T
    if len(g.shape) == 2:
        p0 = numpy.ones((g.shape[0],1))
    else:
        p0 = 1
    return numpy.concatenate((p0, g), axis=1)

def linmodel(parameters):
    """ 
    Creates a function mapping image coordinates to _one_ 
    (vertical or horizontal) angle.
    """
    def model(i,j):
        d = parameters * applyBasisFunctions(i,j)
        # sum over last axis (axis 0 if i and j are scalars,
        # axis 1 otherwise)
        return d.sum(axis=len(d.shape)-1)
    return model

# prepare input to least-squares approximation (lstsq):
# lstsq finds good parameters P to solve A * P = B approximately
A = applyBasisFunctions(distortion[:,2], distortion[:,3])
B = distortion[:,0:2]

logger.info("starting regression/outlier removal cycle.")
iterations = config['regression']['iterations']
good_entries = numpy.arange(len(distortion))
for iteration in range(iterations):
    logger.info("iteration %d of %d", iteration + 1, iterations)
    logger.info("carrying out linear regression.")
    logger.info("Number of samples: %d", len(good_entries))
    samplesize = 200000

    sample = good_entries
    if len(good_entries) > samplesize:
        logger.info("Sampling down to %s" % samplesize)
        # numpy <  1.7.0 doesn't have random.choice and I don't have 
        # numpy >= 1.7.0
        sample = numpy.random.permutation(sample)[:samplesize]

    Asmall = A[sample]
    Bsmall = B[sample]
    
    b = numpy.linalg.lstsq(Asmall,Bsmall)[0]

    yawparams = b[:,0]
    vergparams = b[:,1]

    logger.debug('x parameters: %s', yawparams)
    logger.debug('y parameters: %s', vergparams)

    # yawmodel and vergmodel are models for the transformation of pixels in 
    # projector space to angles in camera space.
    yawmodel = linmodel(yawparams)
    vergmodel = linmodel(vergparams)

    if iteration < iterations:
        # calculate error, remove data points which don't fit the model
        # (possible outliers.)
        d = distortion[good_entries]
        absYawError = numpy.abs(yawmodel(d[:,2], d[:,3]) - d[:,0])
        meanAbsYawError = numpy.mean(absYawError)
        logger.debug("Yaw error: %f", meanAbsYawError)
        absVergError = numpy.abs(vergmodel(d[:,2], d[:,3]) - d[:,1])
        meanAbsVergError = numpy.mean(absVergError)
        logger.debug("Verg error: %f", meanAbsVergError)

        bad_entries = (2 * meanAbsYawError < absYawError) & \
                        (2 * meanAbsVergError < absVergError)

        logger.debug("Removing %d entries from data.", bad_entries.sum())
        good_entries = good_entries[(1-bad_entries).astype(bool)]


# Ultimately, we want to know where in the projected image to put each
# pixel in a 3D rendered image (a texture in OpenGL).
def projectorToAngleToTexture(model):
    """
    Returns a function which maps a given position in projector space to a 
    position in the texture to be pre-distorted.
    """
    aperture = numpy.radians(config['opengl_setup']['aperture'])
    scale = .5/numpy.tan(.5*aperture)
    def conversion(i,j):
        # determine the angles to which the projector space position is projected
        angles = model(i,j)
        # return the coordinates in source image space corresponding to those angles
        return numpy.tan(angles) * scale + .5
    return conversion

# Use the linear models generated above to pre-compute lookup tables for
# later use in OpenGL code.
indices = numpy.mgrid[0:projectionImageSize[0], 0:projectionImageSize[1]]
i = indices[0].ravel()
j = indices[1].ravel()
logger.info("Calculating horizontal mapping.")
xmodel = projectorToAngleToTexture(yawmodel)
xtable = xmodel(i,j).reshape(projectionImageSize)
logger.debug("Extremal values: %f, %f", xtable.min(), xtable.max())

logger.info("Calculating vertical mapping.")
ymodel = projectorToAngleToTexture(vergmodel)
ytable = ymodel(i,j).reshape(projectionImageSize)
logger.debug("Extremal values: %f, %f", ytable.min(), ytable.max())

# Save our hard work's fruit.
if args.numpyOutfilename:
    with open(args.numpyOutfilename, 'wb') as outfile:
        numpy.savez(outfile, offsets = (iOffset,jOffset), tables = numpy.dstack((xtable,ytable)))

logger.info("Done.")
