from OpenGL.GL import *
from PIL import Image
import numpy as np
import ctypes as c
import PPG
null = c.c_void_p(0)
import time


class BlockGrid(object):
    def pyramid(self, width, height, corner, zoff=1):
        for i in range(width):
            for j in range(height):
                """ make into a pyramid """
                blockh = min(zoff + height/2. - np.abs(i - height/2.),
                             zoff + width/2. - np.abs(j - width/2.))
                self.blockdata[i+corner[0]][j+corner[1]] = (i+corner[0], j+corner[1], blockh, 1.0)
                self.blocktexs[i+corner[0]][j+corner[1]] = 2

    def plane(self, width, height, level, corner):
        for i in range(width):
            for j in range(height):
                """ make the plane """
                self.blockdata[i+corner[0]][j+corner[1]] = (i, j, level, 1.0)
                self.blocktexs[i+corner[0]][j+corner[1]] = 1

    def __init__(self, program, width, height):
        """
        """
        """ store the program for later use """
        self.program = program
        """ initialize references to locations in video? memory """
        self.blockbuf = 0
        """ build the block data """
        self.blockdata = np.ones((width, height, 4), dtype="float32")
        self.blocktexs = np.ones((width, height, 1), dtype="float32")
        self.blockdata = np.multiply(self.blockdata, 10)
        self.plane(width, height, 5, (0, 0))
        self.pyramid(20, 20, (width/5, height/4), 5)
        self.pyramid(10, 10, (int(4*width/5.), int(4*height/5.)), 10)


        """ buffer the block texture atlas """
        self.blocktexture = Texture(Image.open("resources/textureatlas.bmp"))
        self.blocktexture.buffer()

    def buffer(self):
        """ assign a real reference to the buffer id and put the block data
            into the memory slot it points to """
        self.blockbuf = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.blockbuf)
        glBufferData(GL_ARRAY_BUFFER, self.blockdata[:, :], GL_STATIC_DRAW)
        self.texidsbuf = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.texidsbuf)
        glBufferData(GL_ARRAY_BUFFER, self.blocktexs[:, :], GL_STATIC_DRAW)

    def bindtoinput(self, vertsnum, texsnum):
        """
            :param attributenum: the layout location of the vertex attribute we are going
            to bind the block data to. The method binds the block data to the vertex attribute
            in the program.
        """
        glEnableVertexAttribArray(texsnum)
        glBindBuffer(GL_ARRAY_BUFFER, self.texidsbuf)
        glVertexAttribPointer(
            texsnum, 1, GL_FLOAT, GL_FALSE, 0, null
        )

        glEnableVertexAttribArray(vertsnum)
        glBindBuffer(GL_ARRAY_BUFFER, self.blockbuf)
        glVertexAttribPointer(
            vertsnum, 4, GL_FLOAT, GL_FALSE, 0, null
        )

    def draw(self, viewmatrix, campos):
        """
            draw the blocks
        """
        glUseProgram(self.program)
        self.bindtoinput(0, 1)
        glBindBuffer(GL_ARRAY_BUFFER, self.blockbuf)

        """ bind uniform values """
        self.blocktexture.bindtouv(self.program, "TextureAtlas")
        binduniform(self.program, "Transform", viewmatrix, dtype="Mat4fv")
        binduniform(self.program, "campos", campos, dtype="float3")

        """ the blocks are really just points - the geometry shader turns them into hexagonal prisms """
        glDrawArrays(GL_POINTS, 0, self.blockdata.size/4)
        glDisableVertexAttribArray(0)


class Texture(object):
    def __init__(self, pilimage):
        self.texid = 0
        #FIXME: self.mode never gets used and it should be the GL_MODE for use in buffering.
        self.mode = pilimage.mode
        self.size = pilimage.size
        """ this isn't necessary """
        self.tex = pilimage.convert("RGBA").tobytes()

    def bindtouv(self, program, uniformvalue):
        """
        :param program: the program to bind the texture to
        :param uniformvalue: the name of the uniform sampler the texture will bind to
        """
        """ typical binding routine """
        uvloc = glGetUniformLocation(program, uniformvalue)
        if uvloc >= 0:
            glActiveTexture(GL_TEXTURE0)
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texid)
            glUniform1i(uvloc, 0)

    def buffer(self):
        if self.texid:
            glDeleteTextures(self.texid)
        self.texid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texid)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, self.size[0], self.size[1], 0,
            GL_RGBA, GL_UNSIGNED_BYTE, self.tex)
        """ magnification filtering. Linear filtering is poor but that is irrelevant """
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        """ this says that the texture will automatically shift to prevent gaps between pixels """
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)


class FPSCam(object):
    def __init__(self):
        self.position = np.array([0, 0, 0], dtype="float32")
        self.xangle = np.pi/3
        self.zangle = float(0)

    def viewmatrix(self):
        return PPG.nlookat(self.position,
                           (np.sin(self.zangle), np.cos(self.zangle), -np.sin(self.xangle)),
                           (0, 0, 1))

    def move(self, value):
        self.position = np.add(self.position,
                               np.multiply(-value,
                                           PPG.normalvec([np.sin(self.zangle),
                                                          np.cos(self.zangle),
                                                          -np.sin(self.xangle)])))

    def orthmove(self, value):
        self.position = np.add(self.position,
                               np.multiply(-value,
                                           PPG.normalvec([np.cos(self.zangle), -np.sin(self.zangle), 0])))


class IVBO(object):
    def __init__(self, data, vertdim):
        """
        :param data: a list, first index is the vertex data (numpy array of floats, unshaped)
                    second index is the indexing set (numpy array, unsigned short integers (dtype=UINT16))
        :param vertdim: dimension of the vertices.
        """
        self.vertices = data[0]
        self.indices = data[1]
        self.vertbuf = 0
        self.indexbuf = 0
        self.vertdim = vertdim

    def buffer(self):
        self.vertbuf = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertbuf)
        glBufferData(GL_ARRAY_BUFFER, self.vertices, GL_STATIC_DRAW)
        self.indexbuf = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.indexbuf)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices, GL_STATIC_DRAW)

    def bindverts(self, attributenum):
        glEnableVertexAttribArray(attributenum)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertbuf)
        glVertexAttribPointer(
            attributenum, self.vertdim, GL_FLOAT, GL_FALSE, 0, null
        )

    def draw(self):
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.indexbuf)
        glDrawElements(GL_TRIANGLES, self.indices.size, GL_UNSIGNED_SHORT, null)


class SkyDome(IVBO):

    def buildplane(self):
        verts = np.zeros((4, 4), dtype="float32")
        indices = np.zeros((2, 3), dtype="uint16")
        verts[0] = [-1, -1, 1, 1]
        verts[1] = [1, -1, 1, 1]
        verts[2] = [-1, 1, 1, 1]
        verts[3] = [1, 1, 1, 1]
        indices[0] = [3, 0, 2]
        indices[1] = [3, 0, 1]
        return verts, indices

    def sunpath(self):
        """
        TODO: Position on earth. Time of year. Axial tilt.
        :param tod: time of day
        :return: position of sun.
        """
        return [(np.pi/2)*(1-np.sign(np.sin(self.time))), np.pi/2*np.cos(self.time)]

    def __init__(self, skyprogram, lod=15):
        """ This code builds an indexed hemisphere around 0 """
        IVBO.__init__(self, self.buildplane(), 4)
        self.program = skyprogram
        self.atmosphere = Atmosphere()
        self.time = np.pi/2
        self.timer = time.time()/10

    def render(self, cam, persp):
        self.todcounter = time.time()/10 - self.timer
        if self.todcounter > .005:
            #TODO: in this case render (the whole thing) to a framebuffer. Then read the thing later.
            self.time = np.mod((self.time + self.todcounter), 2*np.pi)
            self.timer = time.time()/10
        glUseProgram(self.program)
        self.bindverts(0)
        binduniform(self.program, "lookangles", [cam.zangle, cam.xangle], "float2")
        binduniform(self.program, "FOV", persp.fov, "float2")

        binduniform(self.program, "sunangle", self.sunpath(), "float2")
        self.atmosphere.setbindings(self.program)
        glDisable(GL_DEPTH_TEST)
        IVBO.draw(self)
        glEnable(GL_DEPTH_TEST)


class Atmosphere(object):
    """ This is basically just a struct for the atmospheric constants in skydome.
        I'm also going to put a binding function in here.
    """
    def __init__(self):
        self.scatsym = 0.999  # scattering symmetry
        self.sunintensity = 4
        self.rayleighscaledepth = 0.4
        self.sunwavelength = (.65, .7, .7)
        self.planetradius = .999

    def setbindings(self, program):
        binduniform(program, "sunwavelength", self.sunwavelength, "float3")
        binduniform(program, "g", self.scatsym, "float")
        binduniform(program, "g2", self.scatsym*self.scatsym, "float")


class PerspectiveData(object):
    """ another structure, this one just stores aspect ratio data.
    """
    def __init__(self, screendim, nearfar):
        self.matrix = PPG.persp(screendim, nearfar)
        xfov = 2*np.arctan(screendim[0]/float(2*nearfar[0]))
        zfov = 2*np.arctan(screendim[1]/float(2*nearfar[0]))
        self.fov = np.array([xfov, zfov], dtype="float32")
        self.aspect = screendim[0]/float(screendim[1])


def binduniform(program, uniform, value, dtype):
    uniloc = glGetUniformLocation(program, uniform)
    #FIXME: why not pass the actual FUNCTION glUniformXX instead of the dtype? (or something like that)
    # its more complicated then that: different types want different args passed in.
    # It would take some thinking to get that operational.
    if uniloc >= 0:
        if dtype == "int":
            glUniform1i(uniloc, value)
        elif dtype == "Mat4fv":
            glUniformMatrix4fv(uniloc, 1, GL_TRUE, value)
        elif dtype == "float3":
            glUniform3f(uniloc, float(value[0]), float(value[1]), float(value[2]))
        elif dtype == "float":
            glUniform1f(uniloc, float(value))
        elif dtype == "float2":
            glUniform2f(uniloc, float(value[0]), float(value[1]))
        else:
            print "Your function doesn't support bindings of type %s yet" % dtype
    else:
        print "%s not bound." % uniform


def compileprogram(vshaderpath, fshaderpath, vshadervars, fshadervars, gshaderpath="", gshadervars={}):
    """
    :param vshader: vertex shader
    :param fshader: fragment shader
    :param vshadervars: dictionary of replacement variables in the vshader
    :param fshadervars: dictionary of replacement variables in the fshader
    :return: a basic glsl program
    """
    def shaderbuilder(shaderpath, shadervars, shadertype):
        shader = open(shaderpath).read()
        """ replace the compile-time variables in the shaders """
        for hotkey in shadervars.keys():
            shader = shader.replace("<%s>" % hotkey, shadervars[hotkey])
        """ create a reference to the shader, compile the shader """
        shaderid = glCreateShader(shadertype)
        glShaderSource(shaderid, shader)
        glCompileShader(shaderid)
        log = glGetShaderInfoLog(shaderid)
        if log:
            print 'Vertex Shader: ', log
        """ give the shader back to the main routine """
        return shaderid

    program = glCreateProgram()
    vshaderid = shaderbuilder(vshaderpath, vshadervars, GL_VERTEX_SHADER)
    fshaderid = shaderbuilder(fshaderpath, fshadervars, GL_FRAGMENT_SHADER)
    glAttachShader(program, vshaderid)
    glAttachShader(program, fshaderid)
    if gshaderpath:
        gshaderid = shaderbuilder(gshaderpath, gshadervars, GL_GEOMETRY_SHADER)
        glAttachShader(program, gshaderid)
    glLinkProgram(program)
    return program
