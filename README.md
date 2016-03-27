projection
==========

Distortion correction for complex multi-projector systems.

The basic idea behind it is to project a series of black/white patterns at a
screen, once for each available projector, and record those patterns with a 
camera.  The patterns are chosen such that each pixel of a projector flashes 
a unique on/off code.  This can be used to compute a regression model for the
relationship between the position of a pixel in the projected image and the
position on the screen.  This software uses this regression model to generate
binary mapping files which can be used in OpenGL programs to pre-distort an
image such that it will appear undistorted to the camera, when projected.

This is currently not a complete program (or even great code), but rather 
a framework which may be filled in by the user or just used for inspiration.

It is also not complete, yet: I'm adding parts as I'm describing the 
project on my website and cleaning up the code to make it presentable to the 
general public.

In particular, no implementation of a camera module is included as that is 
likely to be specific to a given hardware setup.  detection.py still imports 
_our_ camera implementation and will therefore fail if called, unless a 
camera is implemented.

See http://www.tatome.de for a way to contact me.
