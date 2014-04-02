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
