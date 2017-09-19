import math
import base64

import cairo
import numpy

from project.utils import StringIO
from graph import get_cycles, prune_cycles, get_fused_cycles, sort_fused_cycles, identify_core
from graph import Tree, breadth_first_search, graph_distance
from utils import calculate_bonds
from structure import from_xyz


def bfs_fill(start, ignore):
    tree = Tree(start)
    visited = [tree.value]
    visited.extend(ignore)

    points = tree.search()

    other_atoms = []
    while points:
        point = points.pop(0)
        if point.value not in visited:
            other_atoms.append(point)
            visited.append(point.value)
            points.extend(point.search())
    return other_atoms


def get_core_indices(cycles):
    types = []
    for cycle_group in cycles:
        lengths = [len(x) for x in cycle_group]
        if lengths == [5, 6, 5] or lengths == [6, 5]:
            core = identify_core(cycle_group)
            types.append((core, cycle_group))
    return types


def get_group_indices(mol):
    links, tree = breadth_first_search(mol)

    cycles, link_nodes = get_cycles(links, tree)
    pruned_cycles = prune_cycles(cycles, link_nodes)
    fused = get_fused_cycles(pruned_cycles)
    sorted_cycles = sort_fused_cycles(fused)

    results = get_core_indices(sorted_cycles)
    if len(results) != 1:
        raise ValueError("Something is not right with this structure")
    
    core_name, filtered_cycles = results[0]
    left_ring, center_ring, right_ring = filtered_cycles

    def get_joint(ring1, ring2):
        return set([x.value.id for x in ring1]) & set([x.value.id for x in ring2])

    link_ids = get_joint(left_ring, center_ring) | get_joint(center_ring, right_ring)
    vert_seeds = [x.value for x in center_ring if x.value.id not in link_ids] 
    horz_seeds = [x.value for x in left_ring + right_ring if x.value.id not in link_ids]

    def check_atoms(atoms, ids):
        return atoms[0].id in ids or atoms[1].id in ids

    horz_seeds = [x for x in horz_seeds if not any(check_atoms(y.atoms, link_ids) for y in x.bonds)]

    ignore_idxs = [x.value for x in sum(filtered_cycles, [])]
    # sum to collect all end nodes (should be 2 for each)
    vert_nodes = sum([bfs_fill(x, ignore_idxs) for x in vert_seeds], [])
    horz_nodes = sum([bfs_fill(x, ignore_idxs) for x in horz_seeds], [])
    # subtract 1 because it was 1 indexed
    return [x.value.id - 1 for x in vert_nodes], [x.value.id - 1 for x in horz_nodes]


def get_coordinates(f):
    with f:
        coords = []
        state = 0
        for line in f:
            if "Coordinates" in line:
                state = 1
                continue

            if "------------" in line and state == 1:
                state = 2
                continue

            if "------------" in line and state == 2:
                break

            if state != 2:
                continue

            parts = line.strip().split()
            coords.append([float(x) for x in parts[3:]])
    return coords

                
def get_numbers(f):
    with f:

        collect = False
        orb_values = []
        occupied_orbs = []
        last_orb_count = -1
        num_basis = -1
        atom_idxs = []
        elements = []

        for line in f:
            if "NBasis=" in line:
                num_basis = int(line.strip().split()[1])
                orb_values = [[] for i in xrange(num_basis)]
                atom_idxs = [-1 for i in xrange(num_basis)]

            if "Molecular Orbital Coefficients:" in line:
                collect = True
                continue
            if "Density Matrix:" in line:
                break
            if not collect:
                continue

            if "Eigenvalues --" in line:
                continue

            data = line.strip().split()
            if data[0] in ('V', 'O'):
                temp = [x == 'O' for x in data]
                occupied_orbs.extend(temp)
                last_orb_count = len(temp)
                continue

            if len(data) < last_orb_count + 1 or last_orb_count == -1:
                # This skips the line that counts orbital numbers
                continue
            if "1S" in data:
                # This is one indexed
                atom_idx = int(data[1]) - 1
                if len(elements) == atom_idx:
                    elements.append(data[2])

            # This is one indexed
            idx = int(data[0]) - 1
            numbers = [float(x) for x in data[-last_orb_count:]]
            orb_values[idx].extend(numbers) 
            atom_idxs[idx] = atom_idx
    return atom_idxs, elements, orb_values, occupied_orbs


def get_homo_index(occupied_orbs):
    for i, x in enumerate(occupied_orbs):
        if not x:
            return i - 1


def calculate_groups(values, atom_idxs, vert_idxs, horz_idxs):
    valuesq = [x ** 2 for x in values]
    vert = sum(x for i, x in zip(atom_idxs, valuesq) if i in vert_idxs)
    horz = sum(x for i, x in zip(atom_idxs, valuesq) if i in horz_idxs)
    total = vert + horz
    return total, vert, 100 * vert / total, horz, 100 * horz / total


def draw(xvals, yvals, vert, horz):
    offset = 0.25
    scale = 10
    mins = numpy.array([min(xvals), min(yvals)])
    maxs = numpy.array([max(xvals), max(yvals)])
    dimensions = maxs - mins + 2 * offset
    mins = mins - offset
    dimensions *= scale

    WIDTH = int(dimensions[1])
    HEIGHT = int(dimensions[0])

    f = StringIO()
    surface = cairo.SVGSurface(f, WIDTH, HEIGHT)
    ctx = cairo.Context(surface)

    ctx.scale(scale, scale)
    ctx.rotate(math.pi / 2)
    # hack to fix the translation from the rotation
    ctx.translate(0, -dimensions[1] / scale)
    ctx.translate(-mins[0], -mins[1])
    ctx.set_line_width(0.1)

    for i, (x, y) in enumerate(zip(xvals, yvals)):
        if i in vert:
            color = (0, 255, 0)
        elif i in horz:
            color = (255, 0, 0)
        else:
            color = (0, 0, 255)

        ctx.set_source_rgb(*color)
        ctx.arc(x, y, 0.25, 0, 2 * math.pi)
        ctx.fill()
    surface.write_to_png(f)
    # THIS IS REQUIRED BECAUSE OF ISSUES WITH CAIRO. 
    del surface
    del ctx
    #############
    string = "data:image/png;base64,"
    string += base64.b64encode(f.getvalue())
    return string


def compute_axes_percents(f):
    data = f.read() 
    coords = get_coordinates(StringIO(data))
    atom_idxs, elements, orb_values, occupied_orbs = get_numbers(StringIO(data))
    body = '\n'.join("%s %f %f %f" % (ele, x, y, z) for ele, (x, y, z) in zip(elements, coords))
    bonds = calculate_bonds(body)
    mol = from_xyz(StringIO(body + "\n\n" + bonds))

    vert_idxs, horz_idxs = get_group_indices(mol)
    vert_idxs = set(vert_idxs)
    horz_idxs = set(horz_idxs)
    center_idxs = [i for i in xrange(len(coords)) if i not in vert_idxs and i not in horz_idxs]

    homo_idx = get_homo_index(occupied_orbs)
    homo_values = [x[homo_idx] for x in orb_values]
    lumo_values = [x[homo_idx + 1] for x in orb_values]

    homo_res = calculate_groups(homo_values, atom_idxs, vert_idxs, horz_idxs)
    lumo_res = calculate_groups(lumo_values, atom_idxs, vert_idxs, horz_idxs)
    # X and Y coordinates are flipped in Gaussian files
    image = draw([x[1] for x in coords], [x[0] for x in coords], vert_idxs, horz_idxs)
    return ("HOMO", ) + homo_res, ("LUMO", ) + lumo_res, image 
