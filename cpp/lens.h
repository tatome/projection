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

#ifndef LENS_H
#define LENS_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <GL/glut.h>

	typedef struct {
	   double x,y,z;
	} XYZ;
	typedef struct {
	   unsigned char r,g,b,a;
	} PIXELA;

	typedef struct {
		double aperture;
		int screenheight,screenwidth;
	} CAMERA;

	void HandleDisplay(void);
	void CreateEnvironment(void);
	void MakeExperiment(void);
	void MakeLighting(void);
	void HandleKeyboard(unsigned char key,int x, int y);
	void HandleVisibility(int vis);
	void reshape(int,int);
	void HandleIdle(void);
	void CreateGrid(void);
	void EdgeBlend(void);

#define ESC 27

#ifndef FALSE
#define FALSE 0
#define TRUE 1
#endif
#endif
