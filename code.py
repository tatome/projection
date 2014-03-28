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

import numpy
import itertools

import logging
logger = logging.getLogger(__name__)

class Code(object):
    """ 
    Generates a simple binary code of words of a certain length in which 
    every code word has equally many ones and zeros (if the length is even).
    """
    def __init__(self, bits):
        
        self.code = list(itertools.combinations(range(bits), bits/2))
        self.lookupMap = dict(zip(self.code,itertools.count()))
        self.wordlength = bits
    
    def encode(self, n):
        if n > len(self.code):
            raise (
				ValueError,
				"This code has only %d elements.  Requested: %d." % (len(self.code), n)
			)
        return self.code[n]

    def lookup(self, c):
        """
        c -- a tuple of indices.

        return the number in whose binary code exactly the indices in c are
		ones.
        """
        c = tuple(sorted(c))
        if c in self.lookupMap:
            return self.lookupMap[c]
        else:
            return None

def codeForLength(n):
    """ Create a code with a certain number of words. """
    logger.debug("Creating code for %d words.", n)
    def codeLength(k):
        l = len(list(itertools.combinations(range(k), k/2)))
        return l

    for k in range(n):
        if codeLength(k) >= n:
            return Code(k)

class CodeImageIterator(object):
    """ 
    Generates a sequence of cv2 images (binary arrays) in which numbered pixels
    flicker their respective number in a binary code.
    """
    def __init__(self, size, stepsize):
        """
        size -- size of the image -- tuple (width,height) of ints.
        stepsize -- only one in every stepsize pixels horizontally and 
			vertically flickers its code.
        """
        self.stepsize = stepsize
        self.imageSize = size
        self.size = size[0] + size[0] % stepsize, size[1] + size[1] % stepsize
        self.code = codeForLength((size[0] / stepsize) * (size[1] / stepsize))
        self.counter = 0
    
    def ravel(self,x,y):
        x /= self.stepsize
        y /= self.stepsize
        return self.size[0] / self.stepsize * y + x

    def unravel(self, number):
        x = (number % (self.size[0] / self.stepsize)) * self.stepsize
        y = (number / (self.size[0] / self.stepsize)) * self.stepsize
        return x,y
    
    def generator(self):
        """
            returns a generator of images.
        """
        for counter in range(self.code.wordlength):
            def brightP(x, y):
                if x % self.stepsize == 0  and y % self.stepsize == 0:
                    i = self.ravel(x,y)
                    return 1. if counter in self.code.encode(i) else 0.
                else:
                    return 0.
            yield (
				numpy.array([[brightP(x,y) 
					for x in range(self.imageSize[0])] 
						for y in range(self.imageSize[1])])
			)
    
    def allPixels(self):
        i,j = numpy.mgrid[0:self.imageSize[1],0:self.imageSize[0]]
        return ((i % self.stepsize == 0) & (j % self.stepsize == 0)).astype(float)

    def lookupPixel(self, word):
        """
        word : tuple of indices of ones in a word.   
        return the horizontal and vertical index of the pixel with the given 
		code.
        """
        number = self.code.lookup(word)
        if number is not None:
            x,y = self.unravel(number)
            return x, y
        else:
            return None

if __name__ == "__main__":
    # simple test: display images one after another.
    logging.basicConfig(level=logging.DEBUG)
    import cv2
    i = CodeImageIterator((1280,800), 10)
    for im in i.generator():
        cv2.imshow("bits", im)
        cv2.waitKey()
