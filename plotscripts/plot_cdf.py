#!/usr/bin/env python
import numpy as np
import sys
import matplotlib
import itertools
import os
havedisplay = "DISPLAY" in os.environ
if not havedisplay:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import csv
import argparse
from plot_lines import load_conf

#matplotlib.rcParams.update({'font.size': 22})

def _tolist(comma_separated_list):
    return map(str.strip, comma_separated_list.split(','))

def _get_data(fh, lbl_field, data_field):
    reader = csv.DictReader(fh, delimiter='\t')
    data = {}
    for row in reader:
        data[row[lbl_field]] = map(float, row[data_field].split(','))
    return data

get_lim = lambda s: map(float, s.split(','))

parser = argparse.ArgumentParser(description='Plot multiple CDFs from a TSV')
parser.add_argument('filename', help='Path to TSV file, or "-" to use STDIN',
        nargs='?', type=str)
parser.add_argument('--out-dir', '-o', help='Directory to save graphs in',
        type=str, action="store", default="plots", required=False)
parser.add_argument('--format', '-f', help='output format',
        type=str, action="store", choices=['pdf', 'png'], default='png', required=False)
parser.add_argument('--values', '-v', help='Name of field containing values for CDF',
        type=str, action="store", required=True)
parser.add_argument('--label', '-l', help='Name of field containing label',
        type=str, action="store", required=True)
parser.add_argument('--label-order', '-L', help='Comma-separated list of the ordering of labels in the plot',
        type=str, default=None, required=False)
parser.add_argument('--conf', '-c', help='A python config file with [style] and [labels] sections',
        type=str, required=False, default=None)
parser.add_argument('--xlim', help='x-axis limits',
        type=get_lim, default=None, required=False)
parser.add_argument('--xlabel', '-x', help='x axis label', type=str, default=None, required=False)
parser.add_argument('--ylabel', '-y', help='y axis label', type=str, default=None, required=False)
parser.add_argument('--title', '-t', help='plot title', type=str, default=None, required=False)
args = parser.parse_args()


if not args.filename or args.filename == '-':
    data = _get_data(sys.stdin, args.label, args.values)
else:
    with open(args.filename, 'r') as f:
        data = _get_data(f, args.label, args.values)

linewidth, markersize = 2, 4

conf = load_conf(args.conf) if args.conf else None
if conf and 'style' in conf:
    if 'linewidth' in conf['style']: linewidth = conf['style']['linewidth']
    if 'markersize' in conf['style']: markersize = conf['style']['markersize']
    if 'fontsize' in conf['style']: plt.rc('font', size=conf['style']['fontsize'])
    if 'fontweight' in conf['style']:
        plt.rc('font', weight=conf['style']['fontweight'])
        plt.rc('axes', labelweight=conf['style']['fontweight'])

xlabel = args.xlabel
if not xlabel and conf and 'units' in conf:
    if args.values in conf['units']: xlabel = conf['units'][args.values]

line_styles = {}
ordered_labels = []
if conf and 'linestyle' in conf:
    for lbl, style in conf['linestyle'].items()[1:]:
        ordered_labels.append(lbl)
        line_styles[lbl] = dict(zip(['color', 'line', 'marker'], style.split()))

if not ordered_labels:
    ordered_labels = _tolist(args.label_order) if args.label_order else []

ordered_labels += [l for l in data.keys() if l not in ordered_labels]

#plt.style.use('ggplot')
fig = plt.figure(1)
ax = fig.add_subplot(111)

linestyles = itertools.cycle(("-.","--","-",":"))

all_vals = []
for lbl in [l for l in ordered_labels if l in data]:
    vals = sorted(data[lbl])
    all_vals += vals
    ecdf = np.arange(len(vals))/float(len(vals))*100

    label_name = lbl
    if conf and 'labels' in conf:
        if lbl in conf['labels']: label_name = conf['labels'][lbl]

    ax.plot(vals, ecdf, label=label_name, linewidth=linewidth,
            color=line_styles[lbl]['color'] if lbl in line_styles else None,
            #linestyle=line_styles[lbl]['line'] if lbl in line_styles else linestyles.next())
            linestyle=linestyles.next())

if args.xlim: ax.set_xlim(args.xlim)
else:         ax.set_xlim((0, max(all_vals)))

ax.yaxis.set_ticks(np.arange(0, 110, 10))
if args.title: ax.set_title(args.title)
ax.set_xlabel(xlabel if xlabel else args.values)
ax.set_ylabel(args.ylabel if args.ylabel is not None else 'CDF (%)')
ax.grid()
ax.margins(x=0.1)
handles, labels = ax.get_legend_handles_labels()
ax.legend(loc='best', fancybox=True, framealpha=0.5, handles=handles, labels=labels)

outfilename = os.path.join(args.out_dir, args.values + '_cdf.' + args.format)
plt.tight_layout()
fig.savefig(outfilename)

