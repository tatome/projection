#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <list>
#include <math.h>
#include <GL/glut.h>
#include <SOIL.h>

#include <pthread.h>
#include "lens.h"
#include "projector.h"
#include "config.h"
#include "experiment.h"

// OSC connectivity
#define OSCPKT_OSTREAM_OUTPUT
#include "oscpkt/oscpkt.hh"
#include "oscpkt/udp.hh"

using std::cout;
using std::cerr;

using namespace oscpkt;

const int PORT_NUM = 9109;

/* Flags */
int currentbutton = -1;
CAMERA camera;
XYZ origin = {0.0,0.0,0.0};
XYZ focus = {0,0,1};

PIXELA *thetex;
GLuint edgeBlending;

float angle = 0;

void *readerThread(void*);
pthread_mutex_t angleChangeMutex = PTHREAD_MUTEX_INITIALIZER;
bool drawn = false;

std::list<Projector> projectors;

int main(int argc, char **argv)
{
	int i;

	std::string *projectordata;

	pthread_t thread1;
	
	pthread_create(&thread1, NULL, readerThread, NULL);

	/* Parse the command line arguments */
	Projector *projector;
	for (i=1;i<argc;i++) {
		if (strstr(argv[i],"-p") != NULL) {
			projectordata = new std::string(argv[i+1]);
			projector = new Projector(*projectordata);
			projectors.push_back(*(projector));
		}
		fprintf(stderr, "After if.\n");
	}
	fprintf(stderr, "Done initializing projectors.\n");

	/* Set things up and go */
	glutInit(&argc,argv);
	glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);

	glutCreateWindow("Pre-Distorted Scene");
	camera.aperture = aperture;
	camera.screenwidth = screenSize[0];
	camera.screenheight = screenSize[1];
	reshape(camera.screenwidth, camera.screenheight);
	glutReshapeWindow(camera.screenwidth,camera.screenheight);
	glutDisplayFunc(HandleDisplay);
	glutVisibilityFunc(HandleVisibility);
	glutKeyboardFunc(HandleKeyboard);
	glutMotionFunc(HandleMouseMotion);
	glutSetCursor(GLUT_CURSOR_NONE);
	CreateEnvironment();

	/* Load the edge blending image */
	
	edgeBlending = SOIL_load_OGL_texture(
				"blending.png",
				SOIL_LOAD_AUTO,
				SOIL_CREATE_NEW_ID,
				SOIL_FLAG_INVERT_Y
			);
	if(edgeBlending == 0) {
		fprintf(stderr, "ERROR : Failed to load texture %s.\n", "blending.png");
	}

	glutFullScreen();
	if(	initExperiment(argc-1, argv+1) ) {
		/* Ready to go! */
		glutMainLoop();
		return(0);
	} else {
		fprintf(stderr, "Could not initialize experiment code.");
		return(-1);
	}
}

void *readerThread(void*) {
	int rc;
	UdpSocket sock;
	sock.bindTo(PORT_NUM);
	if (!sock.isOk()) {
		cerr << "Error opening port " << PORT_NUM << ": " << sock.errorMessage() << "\n";
	} else {
		cout << "Server started, will listen to packets on port " << PORT_NUM << std::endl;
		PacketReader pr;
		PacketWriter pw;
		while (sock.isOk()) {
			if (sock.receiveNextPacket(30 /* timeout, in ms */)) {
				pr.init(sock.packetData(), sock.packetSize());
				oscpkt::Message *msg;
				while (pr.isOk() && (msg = pr.popMessage()) != 0) {
					int angle;
					if (msg->match("/show").popInt32(angle).isOkNoMoreArgs()) {
						cout << "Server: received /show " << angle << " from " << sock.packetOrigin() << std::endl;

						cout << "angle: " << angle << std::endl;

						rc = pthread_mutex_lock(&angleChangeMutex);

						/* Determine the focal point */
						focus.x = sin(angle * PI / 180.f);
						focus.y = 0;
						focus.z = cos(angle * PI / 180.f);

						rotated();
						pthread_mutex_unlock(&angleChangeMutex);

						cout << " x: " << focus.x << ", z: " << focus.z << std::endl;

						drawn = false;
						while(!drawn) {
							pthread_yield();
						}
											
					} else {
						cout << "Server: unhandled message: " << *msg << "\n";
					}
				}
			}
		}
	}
}

/*
	This is where global OpenGL/GLUT settings are made, 
	that is, things that will not change in time 
*/
void CreateEnvironment(void)
{
	glEnable(GL_DEPTH_TEST);
	glDisable(GL_LINE_SMOOTH);
	glDisable(GL_POINT_SMOOTH);
	glDisable(GL_POLYGON_SMOOTH); 
	glDisable(GL_DITHER);
	glDisable(GL_CULL_FACE);
	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);

	glLineWidth(1.0);
	glPointSize(1.0);

	glPolygonMode(GL_FRONT_AND_BACK,GL_FILL);
	glFrontFace(GL_CW);
	glClearColor(0.0,0.0,0.0,0.0);
	glColorMaterial(GL_FRONT_AND_BACK,GL_AMBIENT_AND_DIFFUSE);
	glEnable(GL_COLOR_MATERIAL);
	glPixelStorei(GL_UNPACK_ALIGNMENT,1);
}

void HandleDisplay(void)
{
	int i,j;
	int rc;
	int maxdim;
	XYZ right;
	unsigned int textureid;
	GLfloat white[4] = {1.0,1.0,1.0,1.0};

	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
	glShadeModel(GL_SMOOTH);
	glDrawBuffer(GL_BACK_LEFT);
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	gluPerspective(camera.aperture,1,0.1,10000.0);
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	gluLookAt(0,0,0,
				focus.x,focus.y,focus.z,
				 0,1,0);

	// Can't have anyone changing the data while we're drawing.
	rc = pthread_mutex_lock(&angleChangeMutex);
	MakeExperiment();
	pthread_mutex_unlock(&angleChangeMutex);


	MakeLighting();

	/* Copy the image to be used as a texture */
	maxdim = camera.screenwidth >= camera.screenheight ? camera.screenwidth : camera.screenheight;
	if ((thetex = (PIXELA*) malloc(camera.screenwidth*camera.screenheight*sizeof(PIXELA))) == NULL) {
		fprintf(stderr,"Failed to allocate memory for the texture\n");
		return;
	}
	glReadPixels(0,0,camera.screenwidth,camera.screenheight,GL_RGBA,GL_UNSIGNED_BYTE,thetex);
	glGenTextures(1,&textureid);
	glBindTexture(GL_TEXTURE_2D,textureid);
	glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP);
	glTexParameterf(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP);
	glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR); 
	glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
	glTexImage2D(GL_TEXTURE_2D,0,4,
		//camera.screenwidth,camera.screenheight,
		camera.screenwidth,camera.screenheight,
		0,GL_RGBA,GL_UNSIGNED_BYTE,thetex);
	glTexEnvf(GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE,GL_MODULATE);
	glDrawBuffer(GL_BACK_LEFT);
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	glOrtho(-camera.screenwidth/2,camera.screenwidth/2,
		-camera.screenheight/2,camera.screenheight/2,1.0,10000.0);
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	gluLookAt(0.0,0.0,1.0,0.0,0.0,0.0,0.0,1.0,0.0);
	glNormal3f(0.0,0.0,1.0);
	glColor3f(1.0,1.0,1.0);
	glDisable(GL_LIGHTING);
	glShadeModel(GL_FLAT);
	glLightModelfv(GL_LIGHT_MODEL_AMBIENT,white);
	glPolygonMode(GL_FRONT_AND_BACK,GL_FILL); 
	glEnable(GL_TEXTURE_2D);
	glBindTexture(GL_TEXTURE_2D,textureid);
	CreateGrid();
	EdgeBlend();
	glDisable(GL_TEXTURE_2D);
	glutSwapBuffers();
	glDeleteTextures(1,&textureid);
	free(thetex);

	drawn = true;
}

/*
	Set up the lighing environment
*/
void MakeLighting(void)
{
	GLfloat fullambient[4] = {1.0,1.0,1.0,1.0};
	GLfloat position[4] = {0.0,0.0,0.0,0.0};
	GLfloat ambient[4]  = {0.2,0.2,0.2,1.0};
	GLfloat diffuse[4]  = {1.0,1.0,1.0,1.0};
	GLfloat specular[4] = {0.0,0.0,0.0,1.0};

	/* Turn off all the lights */
	glDisable(GL_LIGHT0);
	glDisable(GL_LIGHT1);
	glDisable(GL_LIGHT2);
	glDisable(GL_LIGHT3);
	glDisable(GL_LIGHT4);
	glDisable(GL_LIGHT5);
	glDisable(GL_LIGHT6);
	glDisable(GL_LIGHT7);
	glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER,GL_TRUE);
	glLightModeli(GL_LIGHT_MODEL_TWO_SIDE,GL_FALSE);

	/* Turn on the appropriate lights */
	glLightModelfv(GL_LIGHT_MODEL_AMBIENT,fullambient);
	glLightfv(GL_LIGHT0,GL_POSITION,position);
	glLightfv(GL_LIGHT0,GL_AMBIENT,ambient);
	glLightfv(GL_LIGHT0,GL_DIFFUSE,diffuse);
	glLightfv(GL_LIGHT0,GL_SPECULAR,specular);
	glEnable(GL_LIGHT0);

	/* Sort out the shading algorithm */
	glShadeModel(GL_SMOOTH);

	/* Turn lighting on */
	glEnable(GL_LIGHTING);
}

/*
	Deal with plain key strokes
*/
void HandleKeyboard(unsigned char key,int x, int y)
{
	switch (key) {
	case ESC:									 /* Quit */
	case 'Q':
	case 'q': 
		exit(0); 
		break;
	}
}


/*
	How to handle visibility
*/
void HandleVisibility(int visible)
{
	if (visible == GLUT_VISIBLE)
		glutIdleFunc(HandleIdle);
	else
		glutIdleFunc(NULL);
}

/*
	What to do on an idle event
*/
void HandleIdle(void)
{
	glutPostRedisplay();
}

/*
	Handle a window reshape/resize
*/
void reshape(int w,int h)
{
	fprintf(stderr, "Reshape to %d, %d\n", w, h);
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glutReshapeWindow(w,h);
	glViewport(0,0,(GLsizei)w,(GLsizei)h);
	camera.screenwidth = w;
	camera.screenheight = h;
}

/*
	Handle mouse motion
*/
void HandleMouseMotion(int x,int y)
{
	static int xlast=-1,ylast=-1;
	int dx,dy;

	dx = x - xlast;
	dy = y - ylast;
	if (dx < 0)		dx = -1;
	else if (dx > 0) dx =  1;
	if (dy < 0)		dy = -1;
	else if (dy > 0) dy =  1;

	xlast = x;
	ylast = y;
}

/*
	Form the grid with distorted texture coordinates
*/
void CreateGrid(void)
{
	// define corners of quad.
	static const int idisps[] = {0,1,1,0};
	static const int jdisps[] = {0,0,1,1};
	static const int n = 5;

	int i,j,disp;
	int idisp, jdisp;
	double x,y;

	glDisable(GL_BLEND);
	glDisable(GL_DEPTH_TEST);
	glBegin(GL_QUADS);
		

	for (std::list<Projector>::iterator projector = projectors.begin(); projector != projectors.end(); ++projector) {

		for (i = (*projector).getIOffset();i + n < ((*projector).getIOffset() + (*projector).getWidth()); i+=n) {
			for (j=(*projector).getJOffset();j + n < ((*projector).getJOffset() + (*projector).getHeight()); j+=n) {
				// iterate over corners of quad.
				for(disp = 0; disp < 4; disp++) {
					idisp = i + n * idisps[disp];
					jdisp = j + n * jdisps[disp];

					(*projector).transform(idisp,jdisp,x,y);
					glTexCoord2f(x,y);
					glVertex3f(idisp - screenSize[0]/2.0,screenSize[1]/2.0 - jdisp,0.0);
				}
			}
		}
	}
	glEnd();
}

void EdgeBlend() {
	/* Apply edge blending texture. */
	glEnable(GL_BLEND);
	glBindTexture(GL_TEXTURE_2D,edgeBlending);
	glBlendFunc(GL_DST_COLOR, GL_ZERO);
	glBegin(GL_QUADS);
		glTexCoord2f(0,0);
		glVertex3f(-screenSize[0]/2,-screenSize[1]/2,0.0);

		glTexCoord2f(1,0);
		glVertex3f(screenSize[0]/2,-screenSize[1]/2,0.0);

		glTexCoord2f(1,1);
		glVertex3f(screenSize[0]/2,screenSize[1]/2,0.0);

		glTexCoord2f(0,1);
		glVertex3f(-screenSize[0]/2,screenSize[1]/2,0.0);
	glEnd();
}


/*-------------------------------------------------------------------------
	Normalise a vector
*/
void Normalise(XYZ *p)
{
	double length;

	length = sqrt(p->x * p->x + p->y * p->y + p->z * p->z);
	if (length != 0) {
		p->x /= length;
		p->y /= length;
		p->z /= length;
	} else {
		p->x = 0;
		p->y = 0;
		p->z = 0;
	}
}

