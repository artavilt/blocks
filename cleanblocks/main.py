"""
This module contains the code to draw a block grid.
A block is just a basic set of triangles forming an isometric view of
a hexagon. The drawing routine for a block is essentially
1: Receive a package containing the texture data. Which textures are on the block?
2: Draw the block. Should there be a 3-dimensional aspect to the blocks? Yes, thats the point
    of this.
"""

import pyglet as pg
import glObjects as glo
from PPG import *
from OpenGL.GL import *
import time

import ctypes as c
null = c.c_void_p(0)


class windowcore(pg.window.Window):
    def __init__(self):

        """ initialize pyglet stuff """
        pg.window.Window.__init__(self, fullscreen=True)
        """ compile the shaders """
        program = glo.compileprogram("shaders/blockvert.glsl", "shaders/blockfrag.glsl", {}, {}, "shaders/blockgeo.glsl")
        """ instantiate and buffer a block grid """
        self.blocks = glo.BlockGrid(program, 200, 200)
        self.skydome = glo.SkyDome(glo.compileprogram("shaders/skyvert.glsl", "shaders/skyfrag.glsl", {"NUM_SAMPLES":"5"}, {}), 80)
        self.blocks.buffer()
        self.skydome.buffer()

        """ set GL initial configuration """
        glEnable(GL_DEPTH_TEST)
        glDepthMask(GL_TRUE)
        glDepthFunc(GL_LEQUAL)
        glDepthRange(0.0, 2.0)

        """ Set up the perspective matrix """
        self.persp = glo.PerspectiveData((self.screen.width/300, self.screen.height/300), (10, 800))

        """ the lookat matrix """
        self.cam = glo.FPSCam()
        self.cam.position = [-50, -50, -20]


        """ the matrix we feed to the geometry shader """
        self.outmat = np.identity(4, dtype="float32")

    def on_draw(self):
        self.clear()
        self.outmat = np.dot(self.persp.matrix, self.cam.viewmatrix())  # the camera and perspective matrices
        #print self.outmat
        """ draw initialization """
        glClearDepth(1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        """ draw the skydome """
        self.skydome.render(self.cam, self.persp)

        """ draw the blocks """
        self.blocks.draw(self.outmat, self.cam.position)


class mainwindow(windowcore):
    # setting up some sanitation between pyglet functionality and
    # gl functionality (its not perfect)
    def __init__(self):
        windowcore.__init__(self)
        self.set_exclusive_mouse()
        self.viewangle = (0, 0)
        self.moving = 0
        self.lr = 0
        self.movespeed = .6

    def on_mouse_motion(self, x, y, dx, dy):
        dx, dy = np.multiply((dx, dy), .005)
        self.cam.zangle = np.mod(self.cam.zangle + dx, 2*np.pi)
        self.cam.xangle += dy
        self.cam.xangle = max(-twopi/4, min(twopi/4, self.cam.xangle))

    def on_key_press(self, symbol, modifiers):
        if symbol == pg.window.key.W:
            self.moving = self.movespeed
        elif symbol == pg.window.key.S:
            self.moving = -self.movespeed
        elif symbol == pg.window.key.D:
            self.lr = self.movespeed
        elif symbol == pg.window.key.A:
            self.lr = -self.movespeed

    def on_key_release(self, symbol, modifiers):
        if symbol == pg.window.key.W:
            self.moving = 0
        elif symbol == pg.window.key.S:
            self.moving = 0
        elif symbol == pg.window.key.D:
            self.lr = 0
        elif symbol == pg.window.key.A:
            self.lr = 0
        elif symbol == pg.window.key.ESCAPE:
            pg.app.exit()

    def on_draw(self):
        self.cam.move(self.moving)
        self.cam.orthmove(self.lr)
        windowcore.on_draw(self)

    def render(self, t):
        pass


if __name__ == "__main__":
    window = mainwindow()

    label = pg.text.Label("Hello World")
    glClearColor(.5, .5, .5, 1.0)

    pg.clock.schedule_interval(window.render, 1.0/60)
    pg.app.run()