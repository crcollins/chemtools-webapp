import math
import numpy


def get_axis_rotation_matrix(axis, theta):
    # http://stackoverflow.com/questions/6721544/circular-rotation-around-an-arbitrary-axis
    ct = math.cos(theta)
    nct = 1 - ct
    st = math.sin(theta)
    r = numpy.linalg.norm(axis)
    ux = axis[0, 0] / r
    uy = axis[1, 0] / r
    uz = axis[2, 0] / r
    rot = numpy. matrix([
        [ct+ux**2*nct, ux*uy*nct-uz*st, ux*uz*nct+uy*st],
        [uy*ux*nct+uz*st, ct+uy**2*nct, uy*uz*nct-ux*st],
        [uz*ux*nct-uy*st, uz*uy*nct+ux*st, ct+uz**2*nct],
    ])
    return rot


def get_angles(vector):
    x = vector[0, 0]
    y = vector[1, 0]
    z = vector[2, 0]
    r = numpy.linalg.norm(vector)
    azimuth = math.atan2(y, x)
    altitude = math.asin(z / r)
    return azimuth, altitude


def get_full_rotation_matrix(vector, azimuth, altitude):
    xyaxis = vector[:2, 0]
    zaxis = numpy.matrix([0, 0,  1]).T
    raxis = numpy.cross(zaxis.T, xyaxis.T)
    rotz = get_axis_rotation_matrix(numpy.matrix(raxis).T, altitude)
    rotxy = get_axis_rotation_matrix(-zaxis, azimuth)
    return rotxy * rotz


def project_plane(normal, vec):
    n = normal / numpy.linalg.norm(normal)
    return vec - (vec.T * n)[0,0] * n


def angle_between(vec1, vec2):
    dot = (vec1.T * vec2)[0, 0]
    len1 = numpy.linalg.norm(vec1)
    len2 = numpy.linalg.norm(vec2)

    val = dot / (len1 * len2)
    try:
        return math.acos(val)
    except:
        # Note: This hack is required because sometimes the floating point
        # operations lose precision leading to sitations where -1.00000002 is
        # passed to acos which is not feasable, the quick fix is to just
        # constrain this value to the correct range.
        return -math.acos(min(max(val,1), -1))


def new_point(coord1=None, radius=None, coord2=None, angle=None, coord3=None, dihedral=None):
    if coord1 is None:
        return numpy.matrix([0., 0., 0.]).T

    coord = coord1 + numpy.matrix([radius, 0., 0.]).T
    if coord2 is None:
        return coord

    axis = numpy.cross((coord2 - coord1).T, (coord - coord1).T).T
    if not numpy.abs(axis).sum():
        # Note: This hack is required for things that are highly planar (ie
        # Benzene). As expected the cross product of such vectors is < 0, 0, 0>
        # ; however, this does not account for the sign of the zero! This extra
        # bit of information determines which side of the zero point to go from
        # and can mean the difference in the correct result and garbage.
        if float(axis[2,0]) is -0.0:
            axis = numpy.matrix([0., 0.,  -1.]).T
        else:
            axis = numpy.matrix([0., 0.,  -1.]).T
    curr_angle = angle_between(coord2 - coord1, coord - coord1)
    rot = get_axis_rotation_matrix(axis, math.radians(angle) - curr_angle)
    coord = rot * (coord - coord1) + coord1
    if coord3 is None:
        return coord

    axis = (coord2 - coord1)
    curr_angle = angle_between(project_plane(axis, coord3 - coord2), project_plane(axis, coord -  coord1))
    rot = get_axis_rotation_matrix(axis, math.radians(dihedral) - curr_angle)
    coord = rot * (coord - coord1) + coord1
    return coord


def replace_geom_vars(string):
    geom, variables = string.split("\n\n")
    if variables:
        d = dict([x.strip().split() for x in variables.split('\n') if x])

    for key, value in d.items():
        geom = geom.replace(key, value)
    return geom


def convert_zmatrix_to_cart(string):
    elems = []
    coords = []
    for i, line in enumerate(x for x in string.split('\n') if x):
        items = line.split()
        elems.append(items[0])
        use = items[1:7]
        use[0::2] = [coords[int(x)-1] for x in use[0::2]]
        use[1::2] = [float(x) for x in use[1::2]]
        point = new_point(*use)
        coords.append(point)

    new_string = ''
    for elem, coord in zip(elems, coords):
        new_string += " %s %0.8f %0.8f %0.8f\n" % tuple([elem] + coord.T.tolist()[0])
    return new_string
