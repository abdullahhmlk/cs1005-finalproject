# CS1005 Discrete Structures - Fall 2026
# Finding Network Motifs in an Email Network (SNAP email-Eu-core)
#
# Group roll numbers: 25m-0502, 25k-0935, 25k-0504
# R = 0502 + 0935 + 0504 = 1941
#
# Derived parameters:
#   Pair number      = R mod 190            = 41  -> (i, j) = (2, 7)
#   Department A     = top20[2]             (printed at runtime)
#   Department B     = top20[7]             (printed at runtime)
#   Random networks  = 20 + (R mod 31)      = 20 + 19 = 39
#   Swap attempts    = (5 + (R mod 6)) * E  = 8 * (edges in the subgraph)
#   Random seed      = R                    = 1941

import gzip
import os

ROLL_NUMBERS = ["25m-0502", "25k-0935", "25k-0504"]

# paths are built from this file's location so the script works from any folder
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SRC_DIR)
EDGES_PATH = os.path.join(PROJECT_DIR, "data", "email-Eu-core.txt.gz")
LABELS_PATH = os.path.join(PROJECT_DIR, "data", "email-Eu-core-department-labels.txt.gz")


# ---------------------------------------------------------------------------
# T1: load, clean, rank departments, derive parameters
# ---------------------------------------------------------------------------

def group_number(roll_numbers):
    # only the last 4 digits count, so "25m-0502" contributes 502
    total = 0
    for roll in roll_numbers:
        last_four = roll[-4:]
        total += int(last_four)
    return total


def load_email_edges(path):
    raw_lines = 0
    self_loops = 0
    duplicates = 0
    edge_set = set()
    edge_list = []

    with gzip.open(path, "rt") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) < 2:
                continue  # blank line at end of file
            raw_lines += 1
            u = int(parts[0])
            v = int(parts[1])

            # someone emailing themselves is not a link between two people
            if u == v:
                self_loops += 1
                continue
            # keep the graph simple: one (u, v) edge no matter how many emails
            if (u, v) in edge_set:
                duplicates += 1
                continue

            edge_set.add((u, v))
            edge_list.append((u, v))

    print("Raw edge lines read     :", raw_lines)
    print("Self-loops removed      :", self_loops)
    print("Duplicate edges removed :", duplicates)
    print("Edges in simple graph   :", len(edge_list))
    return edge_list


def load_departments(path):
    dept_of = {}
    with gzip.open(path, "rt") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) < 2:
                continue
            node = int(parts[0])
            dept = int(parts[1])
            dept_of[node] = dept
    return dept_of


def count_internal_edges(edge_list, dept_of):
    # an edge is internal only if sender and receiver share a department
    internal_count = {}
    for dept in dept_of.values():
        internal_count[dept] = 0

    for (u, v) in edge_list:
        if u not in dept_of or v not in dept_of:
            continue
        if dept_of[u] != dept_of[v]:
            continue
        internal_count[dept_of[u]] += 1
    return internal_count


def rank_top_departments(internal_count, how_many):
    # ranking key: most internal edges first, ties go to the smaller dept ID.
    # sorting by (-edges, dept) gives exactly that order.
    ranking_keys = []
    for dept in internal_count:
        ranking_keys.append((-internal_count[dept], dept))
    ranking_keys.sort()

    top_list = []
    for k in range(how_many):
        top_list.append(ranking_keys[k][1])
    return top_list


def pair_from_number(pair_number, list_size):
    # walk the pairs (0,1), (0,2), ..., (18,19) in order until we hit our number
    counter = 0
    for i in range(list_size):
        for j in range(i + 1, list_size):
            if counter == pair_number:
                return (i, j)
            counter += 1
    return None


# ---------------------------------------------------------------------------
# T2: induced subgraph of one department
# ---------------------------------------------------------------------------

def department_subgraph(edge_list, dept_of, dept):
    members = set()
    for node in dept_of:
        if dept_of[node] == dept:
            members.add(node)

    dept_edges = []
    for (u, v) in edge_list:
        # both endpoints must be inside, otherwise the edge leaves the department
        if u in members and v in members:
            dept_edges.append((u, v))
    return members, dept_edges


def describe_subgraph(label, dept, members, dept_edges):
    # isolated members still belong to V_D, but it is useful to know how many there are
    touched = set()
    for (u, v) in dept_edges:
        touched.add(u)
        touched.add(v)
    isolated = len(members) - len(touched)

    print("Department", label, "= dept", dept)
    print("   Nodes (members)       :", len(members))
    print("   Nodes with >= 1 edge  :", len(touched))
    print("   Isolated members      :", isolated)
    print("   Edges (internal)      :", len(dept_edges))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("T1: data cleaning and group parameters")
    print("=" * 60)

    R = group_number(ROLL_NUMBERS)
    edge_list = load_email_edges(EDGES_PATH)
    dept_of = load_departments(LABELS_PATH)

    node_ids = set()
    for (u, v) in edge_list:
        node_ids.add(u)
        node_ids.add(v)
    for node in dept_of:
        node_ids.add(node)
    print("Nodes (people)          :", len(node_ids))
    print("Departments             :", len(set(dept_of.values())))

    internal_count = count_internal_edges(edge_list, dept_of)
    top20 = rank_top_departments(internal_count, 20)

    print()
    print("Top-20 departments by internal edges:")
    print("  index  dept  internal_edges")
    for idx in range(len(top20)):
        dept = top20[idx]
        print("  %5d  %4d  %14d" % (idx, dept, internal_count[dept]))

    pair_number = R % 190
    pair = pair_from_number(pair_number, 20)
    i = pair[0]
    j = pair[1]
    dept_a = top20[i]
    dept_b = top20[j]
    num_random = 20 + (R % 31)
    swap_multiplier = 5 + (R % 6)
    seed = R

    print()
    print("Group parameters:")
    print("  Roll numbers           :", ", ".join(ROLL_NUMBERS))
    print("  R                      :", R)
    print("  Pair number (R mod 190):", pair_number, "->", pair)
    print("  Department A           : top20[%d] = dept %d" % (i, dept_a))
    print("  Department B           : top20[%d] = dept %d" % (j, dept_b))
    print("  Random networks        : 20 + (R mod 31) =", num_random)
    print("  Swap attempts          : (5 + (R mod 6)) x edges =", swap_multiplier, "x edges")
    print("  Random seed            :", seed)

    print()
    print("=" * 60)
    print("T2: induced department subgraphs")
    print("=" * 60)

    members_a, edges_a = department_subgraph(edge_list, dept_of, dept_a)
    members_b, edges_b = department_subgraph(edge_list, dept_of, dept_b)

    describe_subgraph("A", dept_a, members_a, edges_a)
    print("   Swap attempts per net :", swap_multiplier * len(edges_a))
    describe_subgraph("B", dept_b, members_b, edges_b)
    print("   Swap attempts per net :", swap_multiplier * len(edges_b))

    # cross-check: the subgraph edge count must agree with the T1 ranking count
    assert len(edges_a) == internal_count[dept_a]
    assert len(edges_b) == internal_count[dept_b]


if __name__ == "__main__":
    main()
