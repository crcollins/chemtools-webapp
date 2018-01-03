import math
import numpy

from constants import BOND_LENGTHS


def get_axis_rotation_matrix(axis, theta):
    # http://stackoverflow.com/questions/6721544/circular-rotation-around-an-arbitrary-axis
    ct = math.cos(theta)
    nct = 1 - ct
    st = math.sin(theta)
    r = numpy.linalg.norm(axis)
    ux = axis[0, 0] / r
    uy = axis[1, 0] / r
    uz = axis[2, 0] / r
    rot = numpy.matrix([
        [ct + ux ** 2 * nct, ux * uy * nct - uz * st, ux * uz * nct + uy * st],
        [uy * ux * nct + uz * st, ct + uy ** 2 * nct, uy * uz * nct - ux * st],
        [uz * ux * nct - uy * st, uz * uy * nct + ux * st, ct + uz ** 2 * nct],
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
    return vec - (vec.T * n)[0, 0] * n


def angle_between(vec1, vec2):
    dot = (vec1.T * vec2)[0, 0]
    cross = numpy.cross(vec1.T, vec2.T)
    norm = numpy.linalg.norm(cross)
    # This is more numerically stable than the expected equation
    # angle = acos((a * b) / (|a| * |b|))
    return math.atan2(norm, dot)


def get_dihedral(axis, coord1, coord2, coord3, coord4):
    plane1 = project_plane(axis, coord4 - coord3)
    plane2 = project_plane(axis, coord1 - coord2)
    return angle_between(plane1, plane2)


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
        # The string comparison is required because that is the only way to
        # determine if it is negative zero.
        if str(axis[2, 0]) == '-0.0':
            axis = numpy.matrix([0., 0.,  -1.]).T
        else:
            axis = numpy.matrix([0., 0.,  -1.]).T
    curr_angle = angle_between(coord2 - coord1, coord - coord1)
    rot = get_axis_rotation_matrix(axis, math.radians(angle) - curr_angle)
    coord = rot * (coord - coord1) + coord1
    if coord3 is None:
        return coord

    axis = (coord2 - coord1)
    curr_angle = get_dihedral(axis, coord, coord1, coord2, coord3)
    r_dihedral = math.radians(dihedral)

    neg_rotation_amount = math.radians(dihedral) - curr_angle
    neg_rot = get_axis_rotation_matrix(axis, neg_rotation_amount)
    neg_coord = neg_rot * (coord - coord1) + coord1
    neg_angle = get_dihedral(axis, neg_coord, coord1, coord2, coord3)
    neg_val = max(neg_angle, r_dihedral) - min(neg_angle, r_dihedral)
    if neg_val > math.pi:
        neg_val = (2 * math.pi) - neg_angle

    pos_rotation_amount = curr_angle - math.radians(dihedral)
    pos_rot = get_axis_rotation_matrix(axis, pos_rotation_amount)
    pos_coord = pos_rot * (coord - coord1) + coord1
    pos_angle = get_dihedral(axis, pos_coord, coord1, coord2, coord3)
    pos_val = max(pos_angle, r_dihedral) - min(pos_angle, r_dihedral)
    if pos_val > math.pi:
        pos_val = (2 * math.pi) - pos_angle

    if pos_val < neg_val:
        coord = pos_coord
    else:
        coord = neg_coord
    return coord


def replace_geom_vars(geom, variables):
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
        use[0::2] = [coords[int(x) - 1] for x in use[0::2]]
        use[1::2] = [float(x) for x in use[1::2]]
        point = new_point(*use)
        coords.append(point)

    new_string = ''
    for elem, coord in zip(elems, coords):
        new_string += " %s %0.8f %0.8f %0.8f\n" % tuple(
            [elem] + coord.T.tolist()[0])
    return new_string


def get_bond(element1, element2, dist):
    for key in ["3", "2", "Ar", "1"]:
        try:
            if dist < (BOND_LENGTHS[element1][key] + BOND_LENGTHS[element2][key]):
                return key
        except KeyError:
            continue


def calculate_bonds(string):
    temp = [x.split() for x in string.split('\n') if x.strip()]
    atoms = [[ele, float(x), float(y), float(z)] for ele, x, y, z in temp]

    bonds = []
    for i, atom1 in enumerate(atoms):
        for j, atom2 in enumerate(atoms[i + 1:]):
            j += i + 1
            element1, xyz1 = atom1[0], atom1[1:]
            element2, xyz2 = atom2[0], atom2[1:]

            dist = sum((x - y) ** 2 for (x, y) in zip(xyz1, xyz2)) ** 0.5

            bond = get_bond(element1, element2, dist)
            if bond is not None:
                bonds.append("%d %d %s" % (i + 1, j + 1, bond))
    return "\n".join(bonds)


def factorize(n):
    max_val = int(n ** 0.5) + 1
    temp = set(reduce(list.__add__, ([i, n / i]
                                     for i in xrange(1, max_val) if not n % i)))
    return sorted(list(temp))


def find_repeating(string):
    '''
    >>> find_repeating("4")
    ('4', 1)
    >>> find_repeating("44")
    ('4', 2)
    >>> find_repeating("4444")
    ('4', 4)
    >>> find_repeating("4a4a")
    ('4a', 2)
    >>> find_repeating("4ab4ab4ab")
    ('4ab', 3)
    >>> find_repeating("4ab4ab5")
    ('4ab4ab5', 1)
    >>> find_repeating("4ab54ab5")
    ('4ab5', 2)
    '''
    for factor in factorize(len(string)):
        items = [string[x:x + factor] for x in xrange(0, len(string), factor)]
        if all(items[0] == x for x in items):
            break
    return string[:factor], len(string) / factor
