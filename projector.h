#ifndef PROJECTOR
#define PROJECTOR

#include <string>
#include <stdio.h>

class Projector {
	public:
		Projector(std::string datafile);
		~Projector();

		void transform(int i, int j, double &azimuth, double &elevation);
		int getWidth() const {return width;};
		int getHeight() const {return height;};
		int getIOffset() const {return iOffset;};
		int getJOffset() const {return jOffset;};

	private:
		void readLookupTable(FILE *f, double *ptr);

		char name[255];
		int width;
		int height;
		int iOffset;
		int jOffset;
		double *azimuthLookupTable;
		double *elevationLookupTable;
};

#endif
