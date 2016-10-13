#!/usr/bin/env python
import matplotlib
import os
havedisplay = "DISPLAY" in os.environ
if not havedisplay:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from ConfigParser import ConfigParser
import sys
import argparse
import itertools
import math

#plt.style.use('ggplot')
#matplotlib.rcParams.update({'font.size': 16})
#matplotlib.rcParams.update({'font.weight': 'bold'})
#matplotlib.rcParams.update({'axes.labelweight': 'bold'})
matplotlib.rcParams.update({'text.color': 'black'})

def _magnitude(x):
    return int(math.floor(math.log10(x)))

def _should_use_log(vals):
    magnitudes = set(map(_magnitude, vals))
    return len(magnitudes) > 1 and len([v for v in vals if v < 1]) > 2

def _tolist(comma_separated_list):
    return map(str.strip, comma_separated_list.split(','))

def load_conf(filename):
    config = ConfigParser()
    config.read(filename)
    return config._sections


label_style_hist = {} # keep history of styles for labels
label_order_hist = [] # keep history of the order of labels

markers = itertools.cycle(('o', '^', 'D', 's', '+', 'x', '*' ))
linestyles = itertools.cycle(("-.","--","-",":"))
colors = itertools.cycle(('r', 'g', 'b', 'c', 'm', 'y', 'k'))

def plot_lines(data, xlabel=None, xlim=None, ylabel=None, ylim=None, yscale='linear',
        title=None, label_order=None, conf=None, linewidth=2, markersize=2):
    """Plots a 2D array with the format: [[label, x, y, y-dev]]
    """
    if conf and 'labels' in conf:
        if ylabel in conf['labels']: ylabel = conf['labels'][ylabel]
        if xlabel in conf['labels']: xlabel = conf['labels'][xlabel]

    if conf and 'style' in conf:
        if 'linewidth' in conf['style']: linewidth = conf['style']['linewidth']
        if 'markersize' in conf['style']: markersize = conf['style']['markersize']
        if 'fontsize' in conf['style']: plt.rc('font', size=conf['style']['fontsize'])
        if 'showtitle' in conf['style'] and conf['style']['showtitle'].lower() in ['no', 'false', '0']:
            title = None
        if 'fontweight' in conf['style']:
            plt.rc('font', weight=conf['style']['fontweight'])
            plt.rc('axes', labelweight=conf['style']['fontweight'])

    fig = plt.figure()
    ax = fig.add_subplot(111)

    data = sorted(data, key=lambda r: r[1]) # sort data by x values

    local_label_order = []
    if conf and 'linestyle' in conf:
        for lbl, style in conf['linestyle'].items()[1:]:
            local_label_order.append(lbl)
            label_style_hist[lbl] = dict(zip(['color', 'line', 'marker'], style.split()))

    if not local_label_order:
        local_label_order = [l for l in label_order] if label_order else label_order_hist
    labels = set([r[0] for r in data])
    unseen_labels = [l for l in labels if not l in local_label_order]
    local_label_order += unseen_labels

    handles = []
    all_x, all_y = [], []
    for label in [l for l in local_label_order if l in labels]:
        if not label in label_style_hist:
            label_style_hist[label] = dict(line=linestyles.next(), marker=markers.next(), color=colors.next())

        points = [tuple(r)[1:4] for r in data if r[0] == label]
        x, y, yerr = zip(*points)
        all_x += x
        all_y += y
        handles += ax.errorbar(x, y, yerr=yerr, label=label, linewidth=linewidth, markersize=markersize,
                color=label_style_hist[label]['color'],
                linestyle=label_style_hist[label]['line'], marker=label_style_hist[label]['marker'])

    if not title is None: ax.set_title(title)
    if not xlabel is None: ax.set_xlabel(xlabel)
    if not ylabel is None: ax.set_ylabel(ylabel)

    y1, y2, x1, x2 = min(all_y), max(all_y), min(all_x), max(all_x)
    if xlim: ax.set_xlim(xlim)
    else: ax.set_xlim([x1, x2])
    if ylim: ax.set_ylim(ylim)
    else: ax.set_ylim([0, y2 + (y2-y1)*0.1])

    ax.grid()
    #if _should_use_log(all_x):
    #    ax.set_xscale('symlog', linthreshx=1)
    if yscale: ax.set_yscale(yscale)
    ax.margins(x=0.1)
    handles, labels = ax.get_legend_handles_labels()
    # remove the errorbars
    handles = [h[0] for h in handles]
    #ax.legend(loc='upper left', handles=handles, labels=labels)
    ax.legend(loc='best', fancybox=True, framealpha=0.5, handles=handles, labels=labels)
    fig.tight_layout()
    return fig


if __name__ == '__main__':

    get_lim = lambda s: map(float, s.split(','))

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('filename', help='dat filename without extension',
            type=str, action="store")
    parser.add_argument('--format', '-f', help='output format',
            type=str, action="store", choices=['pdf', 'png'], default='png', required=False)
    parser.add_argument('--xlabel', '-x', help='x-axis label',
            type=str, action="store", default=None, required=False)
    parser.add_argument('--xlim', help='x-axis limits',
            type=get_lim, default=None, required=False)
    parser.add_argument('--ylim', help='y-axis limits',
            type=get_lim, default=None, required=False)
    parser.add_argument('--ylabel', '-y', help='y-axis label',
            type=str, action="store", default=None, required=False)
    parser.add_argument('--yscale', help='y-axis scale',
            type=str, action="store", choices=['linear', 'log', 'symlog'], default='linear', required=False)
    parser.add_argument('--title', '-t', help='title',
            type=str, action="store", default=None, required=False)
    parser.add_argument('--linewidth', '-w', help='line width',
            type=int, action="store", default=None, required=False)
    parser.add_argument('--conf', '-c', help='A python config file with [style] and [labels] sections',
            type=str, required=False, default=None)
    parser.add_argument('--label-order', '-L', help='Comma-separated list of the ordering of labels in the plot',
            type=str, default=None, required=False)
    args = parser.parse_args()

    if args.filename == '-':
        title = '-'
        file_in = sys.stdin
        file_out = 'out.' + args.format
    else:
        file_in = args.filename
        title = os.path.splitext(args.filename)[0]
        file_out = os.path.splitext(args.filename)[0] + '.' + args.format

    data = np.genfromtxt(file_in, delimiter='\t', names=True, dtype=None)

    if args.title is not None: title = args.title if args.title else None

    fig = plot_lines(data, title=title,
            conf = load_conf(args.conf) if args.conf else None,
            linewidth=args.linewidth,
            xlim=args.xlim, ylim=args.ylim,
            xlabel=args.xlabel or data.dtype.names[1],
            ylabel=args.ylabel or data.dtype.names[2],
            yscale=args.yscale,
            label_order=_tolist(args.label_order) if args.label_order else None)

    fig.savefig(file_out)
