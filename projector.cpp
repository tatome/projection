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
