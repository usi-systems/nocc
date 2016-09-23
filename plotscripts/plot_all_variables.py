#!/usr/bin/env python
import os
import sys
import argparse
import matplotlib
havedisplay = "DISPLAY" in os.environ
if not havedisplay:
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from plot_lines import plot_lines
from tsv_to_db import tsvToDb


def _get_ind_var_combinations(cur, ind_vars):
    sql = "SELECT %s FROM t GROUP BY %s" % (','.join(ind_vars), ','.join(ind_vars))
    cur.execute(sql)
    combinations = []
    while True:
        rows = cur.fetchall()
        if len(rows) == 0: break
        combinations += [dict(zip(ind_vars, map(float, vals))) for vals in rows]
    return combinations

def _get_labels(cur, field):
    cur.execute("SELECT DISTINCT %s from t" % field)
    labels = []
    while True:
        rows = cur.fetchall()
        if len(rows) == 0: break
        labels += [r[0] for r in rows]
    return labels


def _get_data(cur, label_field, ind_var, dep_var, fixed_ind_vars):
    sql ="SELECT %s,%s,%s FROM t WHERE %s" % (label_field, ind_var, dep_var,
        ' AND '.join(["%s=%s"%(k,v) for k,v in fixed_ind_vars.iteritems()]))
    cur.execute(sql)
    points_for_label = {}
    data = []
    while True:
        rows = cur.fetchall()
        if len(rows) == 0: break
        #data += [[r[0]] + map(float, r[1:3]) + [0] for r in rows]
        for r in rows:
            lbl, x, y = r[:3]
            if lbl not in points_for_label: points_for_label[lbl] = {}
            if x not in points_for_label[lbl]: points_for_label[lbl][x] = []
            points_for_label[lbl][x].append(float(y))

    for lbl, points in points_for_label.iteritems():
        for x, ys in points.iteritems():
            data.append((lbl, float(x), np.average(ys), np.std(ys)))
    return data


def plot_variables(fh=None, filename=None, out_dir="./",
        label_field='mode', label_order=None,
        independent_vars=None, plot_independent_vars=None, dependent_vars=None):
    assert(fh or filename)
    assert(independent_vars)
    assert(dependent_vars)
    con = tsvToDb(file=fh, filename=filename, table_name='t')
    cur = con.cursor()

    labels = _get_labels(cur, label_field)

    if plot_independent_vars is None: plot_independent_vars = independent_vars
    for ind_var in plot_independent_vars:                                    # Choose an independent variable
        other_ind_vars = [v for v in independent_vars if v != ind_var]  # Find all the other independent variables
        combinations = _get_ind_var_combinations(cur, other_ind_vars)   # Find the combinations of the other ind. vars.
        for dep_var in dependent_vars:
            for fixed_ind_vars in combinations:                         # Fix the other ind. vars. and get the values
                data = _get_data(cur, label_field, ind_var, dep_var, fixed_ind_vars)
                title = "%s vs. %s" % (ind_var, dep_var)
                name = "%s_vs_%s_%s" % (ind_var, dep_var,
                        '_'.join(["%s%s"%(v,k) for k,v in fixed_ind_vars.iteritems()]))
                fig = plot_lines(data, xlabel=ind_var, ylabel=dep_var,
                        title=title, label_order=label_order)
                fig.savefig(os.path.join(out_dir, name + '.png'))
                plt.close(fig)


def _tolist(comma_separated_list):
    return map(str.strip, comma_separated_list.split(','))


if __name__ == '__main__':
    # Example usage:
    # ./plot_all_variables.py -l mode -L forward,early_abort,optimistic_abort -i store_D,num_clients,think,think_var -d elapsed_time results.tsv
    parser = argparse.ArgumentParser(description='Plot various combinations of variables from a TSV file')
    parser.add_argument('filename', help='Path to TSV file, or "-" to use STDIN',
            type=str, action="store")
    parser.add_argument('--out-dir', '-o', help='Directory to save graphs in',
            type=str, action="store", default="out", required=False)
    parser.add_argument('--label', '-l', help='Name of field containing label',
            type=str, action="store", required=True)
    parser.add_argument('--label-order', '-L', help='Comma-separated list of the ordering of labels in the plot',
            type=str, default=None, required=False)
    parser.add_argument('--ind-vars', '-i', help='Comma-separated list of independent variable names',
            type=str, required=True)
    parser.add_argument('--plot-ind-vars', '-I', help='Comma-separated list of independent variables to plot',
            type=str, required=False)
    parser.add_argument('--dep-vars', '-d', help='Comma-separated list of dependent variable names',
            type=str, required=True)
    args = parser.parse_args()

    if not os.path.exists(args.out_dir):
        os.mkdir(args.out_dir)

    plot_variables(
            fh = sys.stdin if args.filename == '-' else None,
            filename = args.filename if args.filename != '-' else None,
            out_dir = args.out_dir,
            label_field = args.label,
            label_order = _tolist(args.label_order) if args.label_order else None,
            independent_vars = _tolist(args.ind_vars),
            plot_independent_vars=_tolist(args.plot_ind_vars) if args.plot_ind_vars else None,
            dependent_vars = _tolist(args.dep_vars))
