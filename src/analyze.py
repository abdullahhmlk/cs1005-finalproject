# T6 + T7: Z-scores against the degree-preserving null model, and the chart
#
# R = 1941 -> 39 random networks per department, 8 x edges swap attempts each.
# Random network i (i = 0..38) uses seed R + i, so the run starts from seed R
# and every network is different but reproducible.

import math
import os

import matplotlib
matplotlib.use("Agg")  # write straight to a file, no window needed
import matplotlib.pyplot as plt

from main import (ROLL_NUMBERS, EDGES_PATH, LABELS_PATH, PROJECT_DIR, group_number,
                  load_email_edges, load_departments, count_internal_edges,
                  rank_top_departments, pair_from_number, department_subgraph)
from triads import triad_census, CONNECTED_CODES
from randomize import randomize


def null_model_tallies(members, dept_edges, num_random, attempts, base_seed):
    # one census per random network; random_runs[k] is the census of network k
    random_runs = []
    total_accepted = 0
    for i in range(num_random):
        shuffled_edges, accepted = randomize(dept_edges, attempts, base_seed + i)
        total_accepted += accepted
        random_runs.append(triad_census(members, shuffled_edges))

    acceptance = total_accepted / (num_random * attempts)
    return random_runs, acceptance


def z_scores(real_tallies, random_runs):
    n = len(random_runs)
    mean_of = {}
    sigma_of = {}
    z_of = {}

    for cls in range(1, 14):
        total = 0
        for run in random_runs:
            total += run[cls]
        mu = total / n

        # population standard deviation: divide by N, not N - 1
        squared = 0.0
        for run in random_runs:
            squared += (run[cls] - mu) ** 2
        sigma = math.sqrt(squared / n)

        # a class that never varies across random graphs carries no signal
        if sigma == 0:
            z = 0.0
        else:
            z = (real_tallies[cls] - mu) / sigma

        mean_of[cls] = mu
        sigma_of[cls] = sigma
        z_of[cls] = z

    return mean_of, sigma_of, z_of


def label_for(z):
    if z > 2:
        return "motif"
    if z < -2:
        return "anti-motif"
    return ""


def print_department_detail(title, real_tallies, mean_of, sigma_of, z_of):
    print(title)
    print("  Class  Code   Real      Mean     Sigma         Z")
    for cls in range(1, 14):
        print("  %5d  %4d  %5d  %8.2f  %8.2f  %8.2f  %s"
              % (cls, CONNECTED_CODES[cls - 1], real_tallies[cls],
                 mean_of[cls], sigma_of[cls], z_of[cls], label_for(z_of[cls])))
    print()


def print_z_table(label_a, z_a, label_b, z_b):
    print("  Class  Code  %20s  %20s" % (label_a, label_b))
    for cls in range(1, 14):
        cell_a = "%8.2f %-11s" % (z_a[cls], label_for(z_a[cls]))
        cell_b = "%8.2f %-11s" % (z_b[cls], label_for(z_b[cls]))
        print("  %5d  %4d  %20s  %20s" % (cls, CONNECTED_CODES[cls - 1], cell_a, cell_b))


def draw_chart(R, dept_a, z_a, dept_b, z_b, out_path):
    # light chart surface + two categorical slots (blue, orange) that stay
    # apart for colour-blind readers; the legend names them too
    surface = "#fcfcfb"
    ink = "#0b0b0b"
    muted = "#898781"
    gridline = "#e1e0d9"
    baseline = "#c3c2b7"
    colour_a = "#2a78d6"
    colour_b = "#eb6834"

    classes = []
    heights_a = []
    heights_b = []
    for cls in range(1, 14):
        classes.append(cls)
        heights_a.append(z_a[cls])
        heights_b.append(z_b[cls])

    bar_width = 0.38
    left_x = []
    right_x = []
    for cls in classes:
        # small surface-coloured gap between the two bars of a class
        left_x.append(cls - bar_width / 2 - 0.01)
        right_x.append(cls + bar_width / 2 + 0.01)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    fig.patch.set_facecolor(surface)
    ax.set_facecolor(surface)

    ax.bar(left_x, heights_a, width=bar_width, color=colour_a, label="Dept %d (A)" % dept_a, zorder=3)
    ax.bar(right_x, heights_b, width=bar_width, color=colour_b, label="Dept %d (B)" % dept_b, zorder=3)

    # significance thresholds
    ax.axhline(2, color=ink, linestyle="--", linewidth=1, zorder=2)
    ax.axhline(-2, color=ink, linestyle="--", linewidth=1, zorder=2)
    ax.axhline(0, color=baseline, linewidth=1, zorder=2)
    ax.text(13.62, 2, " Z = +2", va="center", ha="left", color=muted, fontsize=9)
    ax.text(13.62, -2, " Z = -2", va="center", ha="left", color=muted, fontsize=9)

    ax.set_xticks(classes)
    ax.set_xlim(0.4, 13.6)
    ax.set_xlabel("Triad class", color=ink)
    ax.set_ylabel("Z-score", color=ink)
    ax.set_title("Triad motif Z-scores: Dept %d vs Dept %d  (R = %d)" % (dept_a, dept_b, R),
                 color=ink, fontsize=13, pad=12)

    # quiet axes so the bars do the talking
    ax.grid(axis="y", color=gridline, linewidth=0.8, zorder=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(baseline)
    ax.tick_params(colors=muted, length=0)

    legend = ax.legend(frameon=False, loc="upper left")
    for text in legend.get_texts():
        text.set_color(ink)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor=surface)
    plt.close(fig)


def main():
    R = group_number(ROLL_NUMBERS)
    num_random = 20 + (R % 31)
    swap_multiplier = 5 + (R % 6)

    edge_list = load_email_edges(EDGES_PATH)
    dept_of = load_departments(LABELS_PATH)
    top20 = rank_top_departments(count_internal_edges(edge_list, dept_of), 20)
    pair = pair_from_number(R % 190, 20)
    dept_a = top20[pair[0]]
    dept_b = top20[pair[1]]

    members_a, edges_a = department_subgraph(edge_list, dept_of, dept_a)
    members_b, edges_b = department_subgraph(edge_list, dept_of, dept_b)
    attempts_a = swap_multiplier * len(edges_a)
    attempts_b = swap_multiplier * len(edges_b)

    print()
    print("=" * 60)
    print("T5/T6: null model and Z-scores  (R = %d)" % R)
    print("=" * 60)
    print("Random networks per department : %d  (seeds %d .. %d)" % (num_random, R, R + num_random - 1))
    print("Dept %d: %d edges -> %d swap attempts per network" % (dept_a, len(edges_a), attempts_a))
    print("Dept %d: %d edges -> %d swap attempts per network" % (dept_b, len(edges_b), attempts_b))

    real_a = triad_census(members_a, edges_a)
    real_b = triad_census(members_b, edges_b)

    runs_a, accept_a = null_model_tallies(members_a, edges_a, num_random, attempts_a, R)
    runs_b, accept_b = null_model_tallies(members_b, edges_b, num_random, attempts_b, R)
    print("Degree asserts passed for all %d random networks" % (2 * num_random))
    print("Swap acceptance rate: dept %d = %.1f%%, dept %d = %.1f%%"
          % (dept_a, 100 * accept_a, dept_b, 100 * accept_b))
    print()

    mean_a, sigma_a, z_a = z_scores(real_a, runs_a)
    mean_b, sigma_b, z_b = z_scores(real_b, runs_b)

    print_department_detail("Department A (dept %d)" % dept_a, real_a, mean_a, sigma_a, z_a)
    print_department_detail("Department B (dept %d)" % dept_b, real_b, mean_b, sigma_b, z_b)

    print("Z-scores (|Z| > 2 is significant):")
    print_z_table("A (dept %d)" % dept_a, z_a, "B (dept %d)" % dept_b, z_b)

    print()
    print("=" * 60)
    print("T7: chart")
    print("=" * 60)
    results_dir = os.path.join(PROJECT_DIR, "results")
    if not os.path.isdir(results_dir):
        os.makedirs(results_dir)
    out_path = os.path.join(results_dir, "motif_zscores_R%d.png" % R)
    draw_chart(R, dept_a, z_a, dept_b, z_b, out_path)
    print("Saved", out_path)


if __name__ == "__main__":
    main()
