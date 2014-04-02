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

#define ABS(x) (x < 0 ? -(x) : (x))
#define MIN(x,y) (x < y ? x : y)
#define MAX(x,y) (x > y ? x : y)
#define SIGN(x) (x < 0 ? (-1) : 1)
#define MODULUS(p) (sqrt(p.x*p.x + p.y*p.y + p.z*p.z))
#define CROSSPROD(p1,p2,p3) \
	   p3.x = p1.y*p2.z - p1.z*p2.y; \
	   p3.y = p1.z*p2.x - p1.x*p2.z; \
	   p3.z = p1.x*p2.y - p1.y*p2.x

typedef struct {
	double aperture;     /* Camera aperture         */
	int screenheight,screenwidth;
} CAMERA;

void HandleDisplay(void);
void CreateEnvironment(void);
void MakeMesh(void);
void MakeSphere(void);
void MakeExperiment(void);
void rotated(void);
void MakeLighting(void);
void HandleKeyboard(unsigned char key,int x, int y);
void HandleVisibility(int vis);
void reshape(int,int);
void HandleMouseMotion(int,int);
void HandlePassiveMotion(int,int);
void HandleIdle(void);
void CreateGrid(void);
void EdgeBlend(void);
void Normalise(XYZ *);

#define DTOR            0.0174532925
#define RTOD            57.2957795
#define TWOPI           6.283185307179586476925287
#define PI              3.141592653589793238462643
#define PID2            1.570796326794896619231322
#define ESC 27

#ifndef FALSE
#define FALSE 0
#define TRUE 1
#endif
