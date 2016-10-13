#!/usr/bin/env python
import matplotlib
import os
havedisplay = "DISPLAY" in os.environ
if not havedisplay:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sys
import argparse
import itertools
import math

def _magnitude(x):
    return int(math.floor(math.log10(x)))

def _should_use_log(vals):
    magnitudes = set(map(_magnitude, vals))
    return len(magnitudes) > 1 and len([v for v in vals if v < 1]) > 2


label_style_hist = {} # keep history of styles for labels
label_order_hist = [] # keep history of the order of labels

markers = itertools.cycle(('+', 'x', '*', 's', 'D'))
linestyles = itertools.cycle(("-.","--","-",":"))

def plot_lines(data, xlabel=None, ylabel=None, title=None, label_order=None):
    """Plots a 2D array with the format: [[label, x, y, y-dev]]
    """
    fig = plt.figure()
    ax = fig.add_subplot(111)

    data = sorted(data, key=lambda r: r[1]) # sort data by x values

    local_label_order = label_order_hist if label_order is None else [l for l in label_order]
    labels = set([r[0] for r in data])
    unseen_labels = [l for l in labels if not l in local_label_order]
    local_label_order += unseen_labels

    handles = []
    all_x, all_y = [], []
    for label in [l for l in local_label_order if l in labels]:
        if not label in label_style_hist:
            label_style_hist[label] = dict(line=linestyles.next(), marker=markers.next())

        points = [r[1:4] for r in data if r[0] == label]
        x, y, yerr = zip(*points)
        all_x += x
        all_y += y
        handles += ax.errorbar(x, y, yerr=yerr, label=label, linewidth=3,
                linestyle=label_style_hist[label]['line'], marker=label_style_hist[label]['marker'])

    if not title is None: ax.set_title(title)
    if not xlabel is None: ax.set_xlabel(xlabel)
    if not ylabel is None: ax.set_ylabel(ylabel)
    y1, y2, x1, x2 = min(all_y), max(all_y), min(all_x), max(all_x)
    ax.set_ylim([0, y2 + (y2-y1)*0.1])
    ax.set_xlim([x1, x2])
    ax.grid()
    #if _should_use_log(all_x):
    #    ax.set_xscale('symlog', linthreshx=1)
    ax.margins(x=0.1)
    handles, labels = ax.get_legend_handles_labels()
    # remove the errorbars
    handles = [h[0] for h in handles]
    #ax.legend(loc='upper left', handles=handles, labels=labels)
    ax.legend(loc='best', fancybox=True, framealpha=0.5, handles=handles, labels=labels)
    fig.tight_layout()
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('filename', help='dat filename without extension',
            type=str, action="store")
    parser.add_argument('--xlabel', '-x', help='x-axis label',
            type=str, action="store", default=None, required=False)
    parser.add_argument('--ylabel', '-y', help='y-axis label',
            type=str, action="store", default=None, required=False)
    args = parser.parse_args()

    if args.filename == '-':
        title = '-'
        file_in = sys.stdin
        file_out = 'out.png'
    else:
        file_in = args.filename
        title = os.path.splitext(args.filename)[0]
        file_out = os.path.splitext(args.filename)[0] + '.png'
    data = np.genfromtxt(file_in, delimiter='\t', names=None, dtype=None)

    fig = plot_lines(data, xlabel=args.xlabel, ylabel=args.ylabel, title=title)
    fig.savefig(file_out)
