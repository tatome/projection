// ####################################################################
//  Copyright (C) 2013-2014 by Johannes Bauer, The University of 
//  Hamburg
//  http://www.tatome.de
//  This file is part of the projection correction project.
//
//  This is free software; you can redistribute it and/or
//  modify it under the terms of the GNU General Public License as 
//  published by the Free Software Foundation; either  version 2 
//  of the License, or (at your option) any later version.
//
//  This library is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//  Lesser General Public License for more details.
//
//  You should have received a copy of the GNU General Public  License 
//  along with this file; if not, write to the
//  Free Software Foundation, Inc.,
//  51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
// ####################################################################

#include <stdlib.h>
#include <stdio.h>
#include <cstring>
#include <assert.h>

#include "projector.h"

Projector::Projector(std::string datafile) {
	fprintf(stderr, "Initializing projector from file : %s\n", datafile.c_str());
	strcpy(name, datafile.c_str());
	FILE *f = fopen(datafile.c_str(), "rb");
	assert(f);

	assert(fread(&width,  sizeof(int), 1, f));
	assert(fread(&height, sizeof(int), 1, f));
	assert(fread(&iOffset, sizeof(int), 1, f));
	assert(fread(&jOffset, sizeof(int), 1, f));


	azimuthLookupTable = new double[width * height];
	assert(azimuthLookupTable);
	readLookupTable(f, azimuthLookupTable);

	elevationLookupTable = new double[width * height];
	assert(elevationLookupTable);
	readLookupTable(f, elevationLookupTable);

}

Projector::~Projector() {
	delete[] azimuthLookupTable;
	delete[] elevationLookupTable;
}

void
Projector::readLookupTable(FILE *f, double *table) {
	for(int i = 0; i < width; i++) {
		fread(&(table[i * height]), sizeof(double), height, f);
	}
}

void
Projector::transform(int i, int j, double &azimuth, double &elevation) {
	i -= iOffset;
	j -= jOffset;
	azimuth = azimuthLookupTable[i * height + j];
	elevation = elevationLookupTable[i * height + j];
}
