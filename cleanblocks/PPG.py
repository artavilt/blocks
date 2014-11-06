import numpy as np
import numbers

""" helpful constants """
twopi = 2*np.pi  # saves a common operation


def vertex_on_circle(angle, dim=2, scale=1, center=(0, 0), z=0):
    if dim == 2:
        return [scale*np.cos(angle)+center[0], scale*np.sin(angle)+center[1], 1.]
    else:
        return [scale*np.cos(angle)+center[0], scale*np.sin(angle)+center[1], z, 1.]


def translate(vec, dim=3):
    if dim == 3:
        return np.array([[1, 0, 0, vec[0]],
                [0, 1, 0, vec[1]],
                [0, 0, 1, vec[2]],
                [0, 0, 0, 1]], dtype="float32")
    else:
        return [[1, 0, vec[0]],
                [0, 1, vec[1]],
                [0, 0, 1]]


def scale(mag, dim=3):
    if dim == 3:
        if type(mag) is list:  #FIXME: I am sure there is a better way of doing this
            return [[float(mag[0]), 0, 0, 0],
                    [0, float(mag[1]), 0, 0],
                    [0, 0, float(mag[2]), 0],
                    [0, 0, 0, 1]]
        else:
            return [[float(mag), 0, 0, 0],
                    [0, float(mag), 0, 0],
                    [0, 0, float(mag), 0],
                    [0, 0, 0, 1]]


def persp(winsize, nf, dim=3):
    """
    Assumptions: 2D: Device coordinates (eye coordinates) have
    (0,0) at the top left corner. z is just normalized.
    This is because in 2D I like to pretend the screen is a big bitmap.

    3D: I am not going to bother explaining what is going on here.
        It is relatively simple but this was incredibly painful to implement
        on top of poorly written code.
        It is dull mathematics. One thing to note: If you are using your own
        geometry shader you MUST do some sort of clipping plane check
        on the output, because if you don't you will get weird artifacts around the near
        plane because of the asymptotic behavior.

    :param winsize: width, height
    :return: device coordinates normalized to the x,y axis
    """

    w = np.true_divide(2, winsize[0])
    h = np.true_divide(2, winsize[1])
    n, f = nf
    if dim == 3:
        return np.array([[w*n, 0, 0, 0],
                [0, h*n, 0, 0],
                [0, 0, -(n+f)/float(f-n), -2*n*f/float(f-n)],
                [0, 0, -1, 0]], dtype="float32")

    else:
        return [[2*w, 0, -1],
                [0, -2*h, 1],
                [0, 0, 1]]


def lookat(eye, center, up):
    """
    :param eye: The location in world coordinates of the eye.
    :param center: The centre of the frustum in world coordinates.
    :param up: The vector orthogonal to the plane the camera is sitting on.
    :return: a matrix which translates "world coordinates" into "camera coordinates"
    """

    """ If I change "up", but leave eye and center constant, it will rotate what is
        visible on the screen.

        BTW ."""

    f = normalvec(np.subtract(center, eye))  # f is the z-vector "in".
    up = normalvec(up)                       # the up vector.
    s = np.cross(f, up)               # this is the "right vector." It is orthogonal to up and f
    u = np.cross(normalvec(s), f)
    m = [[s[0], s[1], s[2], 0],       # left to right is orthogonal to in and up
         [u[0], u[1], u[2], 0],       # y is up, so use the up vector.
         [-f[0], -f[1], -f[2], 0],    # z is in
         [0, 0, 0, 1]]
    return np.dot(m, translate(eye))  # you move the whole thing over so that eye is central.


def nlookat(pos, center, up):
    # this just specifies position, and two of the basis vectors (z and y)
    f = normalvec(center)
    up = normalvec(up)
    s = np.cross(f, up)
    u = np.cross(normalvec(s), f)   # why normalvec(s)
    m = np.array([[s[0], s[1], s[2], 0],     # left to right is orthogonal to in and up
         [u[0], u[1], u[2], 0],     # y is up, so use the up vector.
         [-f[0], -f[1], -f[2], 0],  # z is in
         [0, 0, 0, 1]], dtype="float32")
    return np.dot(m, translate(pos))


def magnitude(vector):
    return np.sqrt(np.sum([i**2 for i in vector])).astype("float")


def normalvec(vector):
    norm = magnitude(vector)
    if norm > 0:
        return np.array(np.true_divide(vector, magnitude(vector)), dtype="float32")
    else:
        return vector


def qmult(quat1, quat2):
    # this is faster than the geometric calculation apparently
    return np.array([(quat1[3]*quat2[0] + quat1[0]*quat2[3] + quat1[1]*quat2[2]) - quat1[2]*quat2[1],
                     quat1[3]*quat2[1] + quat1[1]*quat2[3] + quat1[2]*quat2[0] - quat1[0]*quat2[2],
                     quat1[3]*quat2[2] + quat1[2]*quat2[3] + quat1[0]*quat2[1] - quat1[1]*quat2[0],
                     quat1[3]*quat2[3] - quat1[0]*quat2[0] - quat1[1]*quat2[1] - quat1[2]*quat2[2]], dtype="float32")


def qconj(quat1, quat2):
    try:
        return qmult(qmult(quat1, quat2), [-quat1[0], -quat1[1], -quat1[2], quat1[3]])
    except IndexError:
        return qmult(qmult(quat1, (quat2[0], quat2[1], quat2[2], 0)),
                           [-quat1[0], -quat1[1], -quat1[2], quat1[3]])


def qrotation(axis, angle):
    a = np.multiply(np.sin(angle/2), normalvec(axis))
    return [a[0], a[1], a[2], np.cos(angle/2)]


def qtomat(quat):
    # copying from some fastish algorithm on the internet. Matrix is equivalent to quaternion conjugation (for units)
    xx = quat[0]**2
    xy = quat[0]*quat[1]
    xz = quat[0]*quat[2]
    xw = quat[0]*quat[3]
    yy = quat[1]**2
    yz = quat[1]*quat[2]
    yw = quat[1]*quat[3]
    zz = quat[2]**2
    zw = quat[2]*quat[3]
    mat = np.identity(4, dtype="float32")
    mat[0][0] = 1 - 2*(yy + zz)
    mat[0][1] = 2 * (xy-zw)
    mat[0][2] = 2 * (xz+yw)
    mat[1][0] = 2 * (xy + zw)
    mat[1][1] = 1 - 2 * (xx + zz)
    mat[1][2] = 2 * (yz - xw)
    mat[2][0] = 2 * (xz - yw)
    mat[2][1] = 2 * (yz + xw)
    mat[2][2] = 1 - 2 * (xx + yy)
    return mat
