// ####################################################################
//  Copyright (C) 2013-2014 by Johannes Bauer, The University of 
//  Hamburg
//  http://www.tatome.de
//  This file is part of the projection correction project.
//
//  Adapted, with permission, from Paul Bourke's lens correction code:
//  http://paulbourke.net/miscellaneous/lenscorrection/
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

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdarg.h>

#include <GL/glut.h>
#include <SOIL.h>

#include "experiment.h"

// Dumb experiment; no initialization or rotation handling necessary.
int initExperiment(int args, char **argv) {return 1;};

typedef struct {
   double r,g,b;
} COLOUR;

/*
	Create the geometry for the mesh
*/
void MakeExperiment(void)
{
	const static float depth = 100.f;
	int i,j,n=4,w=64;
	COLOUR colour;
	double wmax;

	wmax = sqrt(w*w+(double)w*w);

	for (i=-w;i<=w;i+=n) {
		glBegin(GL_LINES);
		for (j=-w;j<w;j+=n) {
			colour.r = (i + w) / (2.0 * w);
			colour.g = 1;
			colour.b = (w - j) / (2.0 * w);
			glColor3f(colour.r,colour.g,colour.b);
			glVertex3f((float)i,(float)j,   depth);
			glVertex3f((float)i,(float)j+n, depth);
		}
		glEnd();
	}
	for (j=-w;j<=w;j+=n) {
		glBegin(GL_LINES);
		for (i=-w;i<w;i+=n) {
			colour.r = (i + w) / (2.0 * w);
			colour.g = 1;
			colour.b = (w - j) / (2.0 * w);
			glColor3f(colour.r,colour.g,colour.b);
			glVertex3f((float)i,(float)j,   depth);
			glVertex3f((float)i+n,(float)j, depth);
		}
		glEnd();
	}
}
