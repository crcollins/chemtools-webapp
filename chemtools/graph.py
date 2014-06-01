from constants import CORE_COMBO, CORE_FREE


class Tree(object):
    def __init__(self, value, parent=None):
        self.parent = parent
        self.value = value
        self.children = []

    def add(self, value):
        new = Tree(value, parent=self)
        self.children.append(new)
        return new

    def search(self):
        if self.parent is not None:
            parent_value = self.parent.value
        else:
            parent_value = None

        atoms = []
        for bond in self.value.bonds:
            for atom in bond.atoms:
                if atom != self.value and atom != parent_value:
                    node = self.add(atom)
                    atoms.append(node)
        return atoms

    def get_common_parent(self, node):
        if self == node:
            return self.parent

        visited = []
        nodes = [self, node]
        i = 0
        while nodes[0] != nodes[1]:
            if nodes[i] in visited:
                break
            if nodes[i].parent is not None:
                visited.append(nodes[i])
                nodes[i] = nodes[i].parent
            i = (i + 1) % 2

        parent = nodes[i]
        return parent

    def get_common_set(self, parent, node):
        nodes = [self]
        while nodes[-1].parent != parent:
            nodes.append(nodes[-1].parent)

        temp_nodes = [node]
        while temp_nodes[-1].parent != parent:
            temp_nodes.append(temp_nodes[-1].parent)

        return nodes + [parent] + temp_nodes[::-1]

    def __str__(self, level=0):
        ret = "    " * level + str((self.value.id, self.value.element)) + '\n'
        for child in self.children:
            ret += child.__str__(level+1)
        return ret



def breadth_first_search(molecule):
    point = molecule.atoms[0]
    tree = Tree(point)
    visited = [tree.value]
    points = tree.search()

    links = []
    while points:
        point = points.pop(0)
        if point.value not in visited:
            visited.append(point.value)
            points.extend(point.search())
        else:
            link = sorted([point.value, point.parent.value], key=lambda x: x.id)
            links.append((link, point))
    return links, tree


def graph_distance(molecule, start, end):
    point = start
    tree = Tree(point)
    visited = {tree.value: 0}
    points = tree.search()

    while points:
        point = points.pop(0)
        if point.value not in visited:
            parent = point.parent.value
            visited[point.value] = visited[parent] + 1
            points.extend(point.search())
        if point.value is end:
            return visited[point.value]
    return None


def print_links(links):
    return [[(f.id, f.element) for f in x] for x,y in links]


def get_cycles(links, tree):
    sorted_links = sorted(links, key=lambda y: [x.id for x in y[0]])
    cycles = []
    link_nodes = []
    for i in xrange(len(sorted_links)/2):
        first = sorted_links[2*i][1].parent
        second = sorted_links[2*i+1][1].parent
        link_nodes.extend([first, second])

        parent = first.get_common_parent(second)
        common_set = first.get_common_set(parent, second)
        temp = [x for x in common_set]
        cycles.append(temp)
    return cycles, link_nodes


def prune_cycles(cycles, link_nodes):
    link_set = set(link_nodes)
    final = []
    for cycle in cycles:
        temp = [x in link_set for x in cycle]
        if sum(temp) <= 2:
            final.append(cycle)
            continue

        # [Link1, 0, Link2, 1, 2, Link2, Link1]
        # goes to [Link1, 0, Link2, Link2, Link1]
        start = temp.index(True, 1) + 1     # +1 include the second True value
        end = temp[::-1].index(True, 1) + 1
        final.append(cycle[:start] + cycle[-end:])
    return final


def get_fused_cycles(cycles):
    cycle_sets = [set([x.value.id for x in y]) for y in cycles]
    sets = []
    used = []
    notused = []
    for i, cycle1 in enumerate(cycle_sets):
        temp = [i]
        if i in used:
            continue
        full_cycle = cycle1
        for j, cycle2 in enumerate(cycle_sets):
            if i >= j:
                continue
            if full_cycle & cycle2:
                full_cycle |= cycle2
                temp.append(j)
        if len(temp) > 1:
            sets.append(temp)
            used.extend(temp)
        else:
            notused.append(i)

    temp1 = [[cycles[x] for x in y] for y in sets]
    temp2 = [[cycles[x]] for x in notused]
    return temp1 + temp2


def sort_fused_cycles(cycles):
    sorted_cycles = []
    for fused_cycle in cycles:
        means = []
        if len(fused_cycle) == 1:
            sorted_cycles.append(fused_cycle)
            continue

        # max of three rings, maybe generallize later
        sets = [set([x.value.id for x in ring]) for ring in fused_cycle]

        if len(sets) == 2:
            if len(sets[0]) >= len(sets[1]):
                ordering = [0, 1]
            else:
                ordering = [1, 0]
        else:
            if not (sets[0] & sets[1]):
                ordering = [0, 2, 1]
            else:
                if len(sets[0]) == len(sets[2]):
                    ordering = [0, 1, 2]
                else:
                    ordering  = [2, 0, 1]
        temp = [fused_cycle[i] for i in ordering]
        sorted_cycles.append(temp)
    return sorted_cycles


def identify_cycle_types(molecule, cycles):
    types = []
    for cycle_group in cycles:
        lengths = [len(x) for x in cycle_group]
        if len(lengths) == 3:
            if lengths == [5, 6, 5]:
                core = identify_core(molecule, cycle_group)
                types.append(core)
            elif lengths == [6, 5, 6]:
                types.append("7")
            else:
                raise ValueError("Ring of type 10 is not valid")
                types.append("10")
        elif len(lengths) == 2:
            if lengths == [6, 5]:
                core = identify_core(molecule, cycle_group)
                types.append(core)
            else:
                types.append("9")
        else:
            ring_type = identify_single_ring(cycle_group[0])
            types.append(ring_type)
    return types


def identify_core(molecule, fused_cycle):
    pairs = []
    for ring in fused_cycle:
        temp = []
        for node in ring:
            ele = node.value.element
            children = [x for x in node.children if x.value.element == "H"]
            temp.append((node.value, (ele, len(children))))
        pairs.append(temp)
    if len(pairs) == 2:
        side, _ = identify_core_side(pairs[1])
        start = "E/Z"
    else:
        side1, name_atoms1 = identify_core_side(pairs[0])
        side2, name_atoms2 = identify_core_side(pairs[2])
        dist = graph_distance(molecule, name_atoms1[0], name_atoms2[0])
        if dist == 4:
            start = 'C'
        elif dist == 5:
            start = 'T'
        side = side1
    return start + side


def identify_core_side(pairs):
    core_elements = set(sum(CORE_COMBO, []))
    lower, upper = [zip(x,y) for x, y in zip(CORE_COMBO, CORE_FREE)]

    results = []
    name_atoms = []
    for atom, pair in pairs:
        if pair in lower:
            results.append(pair)
            name_atoms.append(atom)

    for atom, pair in pairs:
        if pair in upper:
            # This is used to remove a single Carbon on the end
            temp1 = (name_atoms[0], results[0])
            temp2 = (atom, pair)
            dist = (pairs.index(temp1) - pairs.index(temp2)) % len(pairs)
            if dist in [2, 3]:
                results.append(pair)
                name_atoms.append(atom)

    return ''.join([x[0] for x in results]), name_atoms


def identify_single_ring(ring):
    elements = [x.value.element for x in ring]
    ring_type = '4'
    if 'S' in elements:
        ring_type = '5'
    elif 'N' in elements:
        if elements.count('N') > 1:
            ring_type = '8'
        else:
            ring_type = '6'
    return ring_type


def run_name(name):
    from chemtools import gjfwriter
    mol = gjfwriter.GJFWriter(name).molecule
    already, tree = breadth_first_search(mol)
    cycles, link_nodes = get_cycles(already, tree)
    pruned = prune_cycles(cycles, link_nodes)
    fused = get_fused_cycles(pruned)
    sorted_cycles = sort_fused_cycles(fused)
    # for z in sorted_cycles:
    #     for y in z:
    #         print [(x.value.id, x.value.element) for x in y]
    #     print
    # print "FINAL:",
    temp = identify_cycle_types(mol, sorted_cycles)
    # print temp
    return set(identify_cycle_types(mol, sorted_cycles))


