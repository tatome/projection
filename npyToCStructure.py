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

import struct
import numpy
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-i', dest='infile', required=True)
parser.add_argument('-o', dest='outfile', required=True)
args = parser.parse_args()

data = numpy.load(args.infile)
tables = data['tables']
ioffset,joffset = data['offsets']

with open(args.outfile, 'wb') as outfile:
    outfile.write(struct.pack(
        '=iiii', tables.shape[0], tables.shape[1], ioffset, joffset)
    )

    linefmt = '=' + ('d' * tables.shape[1])
    print(tables.shape)
    for line in tables[:,:,0]:
        outfile.write(struct.pack(linefmt, *line))
    for line in tables[:,:,1]:
        outfile.write(struct.pack(linefmt, *line))
