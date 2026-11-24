# T5: degree-preserving randomization by double-edge swaps
#
# One attempt: pick edges (a, b) and (c, d), try to rewire them into (a, d) and (c, b).
# Every node keeps the same number of outgoing and incoming edges, because
# a still sends one edge, d still receives one, and the same goes for c and b.

import random


def degree_counts(edges):
    out_degree = {}
    in_degree = {}
    for (u, v) in edges:
        if u not in out_degree:
            out_degree[u] = 0
        if v not in in_degree:
            in_degree[v] = 0
        out_degree[u] += 1
        in_degree[v] += 1
    return out_degree, in_degree


def randomize(edges, attempts, seed):
    # own generator, so each network depends only on its seed
    rng = random.Random(seed)

    # fresh copy every time - the original department graph is never touched
    edge_pool = list(edges)
    edge_set = set(edges)
    accepted = 0

    for attempt in range(attempts):
        first = rng.randrange(len(edge_pool))
        second = rng.randrange(len(edge_pool))
        a, b = edge_pool[first]
        c, d = edge_pool[second]

        # prevent self-loops after the swap
        if a == d or c == b:
            continue
        # prevent parallel edges after the swap. this also rejects picking the
        # same edge twice, or two edges that share a sender, since (c, b) or
        # (a, d) is then an edge that is already there
        if (a, d) in edge_set or (c, b) in edge_set:
            continue

        edge_set.remove((a, b))
        edge_set.remove((c, d))
        edge_set.add((a, d))
        edge_set.add((c, b))
        edge_pool[first] = (a, d)
        edge_pool[second] = (c, b)
        accepted += 1

    # the whole point of the null model: same in/out degree for every node
    orig_out, orig_in = degree_counts(edges)
    new_out, new_in = degree_counts(edge_pool)
    for node in orig_out:
        assert new_out.get(node, 0) == orig_out[node], "out-degree changed at node %d" % node
    for node in orig_in:
        assert new_in.get(node, 0) == orig_in[node], "in-degree changed at node %d" % node
    # and no node gained edges it never had
    assert len(new_out) == len(orig_out)
    assert len(new_in) == len(orig_in)

    # still a simple graph: no self-loops, no duplicates
    assert len(edge_set) == len(edge_pool)
    for (u, v) in edge_pool:
        assert u != v

    return edge_pool, accepted
