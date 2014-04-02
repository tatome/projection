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
    outfile.write(struct.pack('=iiii', tables.shape[0], tables.shape[1], ioffset, joffset))
    linefmt = '=' + ('d' * tables.shape[1])
    print(tables.shape)
    for line in tables[:,:,0]:
        outfile.write(struct.pack(linefmt, *line))
    for line in tables[:,:,1]:
        outfile.write(struct.pack(linefmt, *line))
