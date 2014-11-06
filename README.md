This program creates a basic hexeled terrain which you can navigate around.
It uses PyOpenGL.

The hexels are generated from a 2 dimensional array of floats (PyOpenGL seems to have issues sending anythin other than float32 into the graphics pipeline.) The geometry shader spins each point of the array into a hexagonal prism which is then textured by the fragment shader. The geometry shader only generates faces on the visible side of the prism.

There is also an extremely broken skyplane which dynamically generated a rising and setting sun. This problem actually requires quite a bit more thought than I've given it, the current set up treats every viewing angle as if it was the horizon, which creates problems which become more apparent as mid-day approaches. I relied heavily on Sam O'Neill's white paper "Accurate Atmospheric Scattering" for this, but tried for my own interpretation of the problem (and failed.)

You can move about the environment using standard FPS controls (Mouse and WASD.)
