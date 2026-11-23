# T3 + T4: triad classification and triad census
#
# T3: triad_class(a, b, c, edge_set) -> class 1..13 using the fixed 6-bit code
# T4: triad_census(members, dept_edges) -> counts for all 13 classes
#
# Bit layout for an ordering (x0, x1, x2):
#   bit 0: x0 -> x1    bit 1: x0 -> x2    bit 2: x1 -> x0
#   bit 3: x1 -> x2    bit 4: x2 -> x0    bit 5: x2 -> x1

# every way to relabel three nodes, written out so nothing is hidden
ALL_ORDERINGS = ((0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0))

# (from, to) positions for bits 0..5, in the order the project statement fixes
BIT_EDGES = ((0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1))

# the 13 connected canonical codes, sorted ascending -> Class 1..13
CONNECTED_CODES = [3, 6, 7, 10, 11, 15, 21, 23, 25, 27, 30, 31, 63]

CLASS_OF_CODE = {}
for position in range(len(CONNECTED_CODES)):
    CLASS_OF_CODE[CONNECTED_CODES[position]] = position + 1


# ---------------------------------------------------------------------------
# T3: canonical code and triad class
# ---------------------------------------------------------------------------

def encode_ordering(x0, x1, x2, edge_set):
    # turn one specific labelling of the three nodes into a 6-bit integer
    labelled = (x0, x1, x2)
    code = 0
    for bit in range(6):
        src = labelled[BIT_EDGES[bit][0]]
        dst = labelled[BIT_EDGES[bit][1]]
        if (src, dst) in edge_set:
            code += 1 << bit
    return code


def canonical_code(a, b, c, edge_set):
    # same triad under all 6 relabellings; the smallest integer is its "name"
    nodes = (a, b, c)
    best = None
    for order in ALL_ORDERINGS:
        code = encode_ordering(nodes[order[0]], nodes[order[1]], nodes[order[2]], edge_set)
        if best is None or code < best:
            best = code
    return best


def triad_class(a, b, c, edge_set):
    code = canonical_code(a, b, c, edge_set)
    if code not in CLASS_OF_CODE:
        # codes 0, 1, 5 are the disconnected orbits - the census never asks for these
        raise ValueError("triad (%s, %s, %s) is not connected (code %d)" % (a, b, c, code))
    return CLASS_OF_CODE[code]


def check_64_to_16_to_13():
    # brute-force all 64 labelled configurations on nodes 0, 1, 2 and make sure
    # they collapse into 16 orbits, 13 of which are exactly our connected codes
    orbit_codes = set()
    for pattern in range(64):
        fake_edges = set()
        for bit in range(6):
            if pattern & (1 << bit):
                fake_edges.add(BIT_EDGES[bit])
        orbit_codes.add(canonical_code(0, 1, 2, fake_edges))

    disconnected = []
    for code in sorted(orbit_codes):
        if code not in CLASS_OF_CODE:
            disconnected.append(code)

    print("64 labelled configurations -> %d orbits" % len(orbit_codes))
    print("Disconnected orbit codes   :", disconnected)
    assert len(orbit_codes) == 16
    assert len(disconnected) == 3
    for code in CONNECTED_CODES:
        assert code in orbit_codes


# ---------------------------------------------------------------------------
# Hand-worked example (T3 deliverable)
#
# Triad on nodes a, b, c with edges:  a -> b,  b -> a,  a -> c
# (a and b email each other; a also emails c; c never replies)
#
#   ordering   x0 x1 x2   bits set (edge)                          code
#   (0,1,2)    a  b  c    b0 a->b, b1 a->c, b2 b->a                1+2+4   =  7
#   (0,2,1)    a  c  b    b0 a->c, b1 a->b, b4 b->a                1+2+16  = 19
#   (1,0,2)    b  a  c    b0 b->a, b2 a->b, b3 a->c                1+4+8   = 13
#   (1,2,0)    b  c  a    b1 b->a, b4 a->b, b5 a->c                2+16+32 = 50
#   (2,0,1)    c  a  b    b2 a->c, b3 a->b, b5 b->a                4+8+32  = 44
#   (2,1,0)    c  b  a    b3 b->a, b4 a->c, b5 a->b                8+16+32 = 56
#
#   minimum = 7  ->  7 is the 3rd code in [3, 6, 7, ...]  ->  Class 3
# ---------------------------------------------------------------------------

HAND_EXAMPLE_EDGES = {("a", "b"), ("b", "a"), ("a", "c")}
HAND_EXAMPLE_CODES = (7, 19, 13, 50, 44, 56)  # worked out above, same ordering order


def show_hand_example():
    nodes = ("a", "b", "c")
    print("Edges: a->b, b->a, a->c")
    print("  ordering   x0 x1 x2   bits            code")

    smallest = None
    for k in range(6):
        order = ALL_ORDERINGS[k]
        x0 = nodes[order[0]]
        x1 = nodes[order[1]]
        x2 = nodes[order[2]]
        code = encode_ordering(x0, x1, x2, HAND_EXAMPLE_EDGES)

        bits_text = ""
        for bit in range(6):
            if code & (1 << bit):
                bits_text += "b%d " % bit

        print("  %s  %s  %s  %s   %-14s  %2d" % (order, x0, x1, x2, bits_text, code))
        # the program must agree with the table we did on paper
        assert code == HAND_EXAMPLE_CODES[k]
        if smallest is None or code < smallest:
            smallest = code

    result = triad_class("a", "b", "c", HAND_EXAMPLE_EDGES)
    print("  minimum code = %d  ->  Class %d" % (smallest, result))
    assert smallest == 7
    assert result == 3


# ---------------------------------------------------------------------------
# T4: triad census
# ---------------------------------------------------------------------------

def build_undirected_adj(members, dept_edges):
    # direction does not matter for "is this triad connected?"
    undirected_adj = {}
    for node in members:
        undirected_adj[node] = set()
    for (u, v) in dept_edges:
        undirected_adj[u].add(v)
        undirected_adj[v].add(u)
    return undirected_adj


def triad_census(members, dept_edges):
    edge_set = set(dept_edges)
    undirected_adj = build_undirected_adj(members, dept_edges)

    motif_tallies = {}
    for cls in range(1, 14):
        motif_tallies[cls] = 0

    # a connected triad always has a node touching the other two, so looking at
    # pairs of neighbours around every centre finds each one at least once
    seen_triads = set()
    for centre in undirected_adj:
        neighbours = sorted(undirected_adj[centre])
        for i in range(len(neighbours)):
            for j in range(i + 1, len(neighbours)):
                trio = sorted((centre, neighbours[i], neighbours[j]))
                key = (trio[0], trio[1], trio[2])

                # a fully-linked triad shows up from all 3 centres - count it once
                if key in seen_triads:
                    continue
                seen_triads.add(key)

                cls = triad_class(key[0], key[1], key[2], edge_set)
                motif_tallies[cls] += 1

    return motif_tallies


def print_census_table(label_a, tallies_a, label_b, tallies_b):
    print("  Class  Code  %12s  %12s" % (label_a, label_b))
    total_a = 0
    total_b = 0
    for cls in range(1, 14):
        print("  %5d  %4d  %12d  %12d" % (cls, CONNECTED_CODES[cls - 1], tallies_a[cls], tallies_b[cls]))
        total_a += tallies_a[cls]
        total_b += tallies_b[cls]
    print("  %-11s %12d  %12d" % ("Total", total_a, total_b))


if __name__ == "__main__":
    from main import (ROLL_NUMBERS, EDGES_PATH, LABELS_PATH, group_number,
                      load_email_edges, load_departments, count_internal_edges,
                      rank_top_departments, pair_from_number, department_subgraph)

    print("=" * 60)
    print("T3: triad_class - hand-worked example")
    print("=" * 60)
    show_hand_example()
    print()
    check_64_to_16_to_13()

    print()
    print("=" * 60)
    print("T4: triad census of both departments")
    print("=" * 60)

    # redo the T1 selection so the departments always follow from R
    R = group_number(ROLL_NUMBERS)
    edge_list = load_email_edges(EDGES_PATH)
    dept_of = load_departments(LABELS_PATH)
    top20 = rank_top_departments(count_internal_edges(edge_list, dept_of), 20)
    pair = pair_from_number(R % 190, 20)
    dept_a = top20[pair[0]]
    dept_b = top20[pair[1]]

    members_a, edges_a = department_subgraph(edge_list, dept_of, dept_a)
    members_b, edges_b = department_subgraph(edge_list, dept_of, dept_b)

    tallies_a = triad_census(members_a, edges_a)
    tallies_b = triad_census(members_b, edges_b)

    print()
    print("R = %d, A = dept %d (%d nodes, %d edges), B = dept %d (%d nodes, %d edges)"
          % (R, dept_a, len(members_a), len(edges_a), dept_b, len(members_b), len(edges_b)))
    print()
    print_census_table("A (dept %d)" % dept_a, tallies_a, "B (dept %d)" % dept_b, tallies_b)
