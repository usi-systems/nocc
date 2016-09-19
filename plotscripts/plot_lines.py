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
    for label in [l for l in local_label_order if l in labels]:
        if not label in label_style_hist:
            label_style_hist[label] = dict(line=linestyles.next(), marker=markers.next())

        points = [r for r in data if r[0] == label]
        x = [p[1] for p in points]
        y = [p[2] for p in points]
        handles += ax.plot(x, y, label=label,
                linestyle=label_style_hist[label]['line'], marker=label_style_hist[label]['marker'])

    if not title is None: ax.set_title(title)
    if not xlabel is None: ax.set_xlabel(xlabel)
    if not ylabel is None: ax.set_ylabel(ylabel)
    ax.grid()
    ax.margins(x=0.1)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(loc='upper left', handles=handles, labels=labels)
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
