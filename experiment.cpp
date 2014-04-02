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
void rotated(void) {};


typedef struct {
   double r,g,b;
} COLOUR;

/*
	Create the grometry for the mesh
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
