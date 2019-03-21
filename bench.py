#!/usr/bin/env python3

#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import datetime
import json
import math
import os.path
import platform
import string
import subprocess
import sys

import distro
import numpy as np

import _shared


def platform_info():
    machine = platform.machine()
    processor = platform.processor()
    system = platform.system()

    cpuinfo_f = '/proc/cpuinfo'

    if (processor in {machine, 'unknown'} and os.path.exists(cpuinfo_f)):
        with open(cpuinfo_f, 'rt') as f:
            for line in f:
                if line.startswith('model name'):
                    _, _, p = line.partition(':')
                    processor = p.strip()
                    break

    if 'Linux' in system:
        distname, distversion, distid = distro.linux_distribution()
        distribution = '{} {}'.format(distname, distversion).strip()

    else:
        distribution = None

    data = {
        'cpu': processor,
        'arch': machine,
        'system': '{} {}'.format(system, platform.release()),
        'distribution': distribution
    }

    return data


def weighted_quantile(values, quantiles, weights):
    """Very close to np.percentile, but supports weights.

    :param values: np.array with data
    :param quantiles: array-like with many quantiles needed,
           quantiles should be in [0, 1]!
    :param weights: array-like of the same length as `array`
    :return: np.array with computed quantiles.
    """
    values = np.array(values)
    quantiles = np.array(quantiles)
    weights = np.array(weights)
    if not (np.all(quantiles >= 0) and np.all(quantiles <= 1)):
        raise ValueError('quantiles should be in [0, 1]')

    weighted_quantiles = np.cumsum(weights) - 0.5 * weights
    weighted_quantiles -= weighted_quantiles[0]
    weighted_quantiles /= weighted_quantiles[-1]

    return np.interp(quantiles, weighted_quantiles, values)


percentiles = [25, 50, 75, 90, 99, 99.99]


def calc_latency_stats(queries, duration, min_latency, max_latency,
                       latency_stats, output_format='text'):
    arange = np.arange(len(latency_stats))

    mean_latency = np.average(arange, weights=latency_stats)
    variance = np.average((arange - mean_latency) ** 2, weights=latency_stats)
    latency_std = math.sqrt(variance)
    latency_cv = latency_std / mean_latency

    percentile_data = []

    quantiles = weighted_quantile(arange, [p / 100 for p in percentiles],
                                  weights=latency_stats)

    for i, percentile in enumerate(percentiles):
        percentile_data.append((percentile, round(quantiles[i] / 100, 3)))

    data = dict(
        duration=round(duration, 2),
        queries=queries,
        qps=round(queries / duration, 2),
        latency_min=round(min_latency / 100, 3),
        latency_mean=round(mean_latency / 100, 3),
        latency_max=round(max_latency / 100, 3),
        latency_std=round(latency_std / 100, 3),
        latency_cv=round(latency_cv * 100, 2),
        latency_percentiles=percentile_data
    )

    return data


def process_results(results):
    try:
        lat_data = json.loads(results)
    except json.JSONDecodeError as e:
        print('could not process benchmark results: {}'.format(e),
              file=sys.stderr)
        print(results, file=sys.stderr)
        sys.exit(1)

    data = []
    for queries_bench in lat_data['data']:
        benchname = queries_bench['benchmark']
        bench = _shared.BENCHMARKS[benchname]

        data_bench = []
        for query_bench in queries_bench['queries']:
            d = calc_latency_stats(
                query_bench['nqueries'],
                queries_bench['duration'],
                query_bench['min_latency'],
                query_bench['max_latency'],
                np.array(query_bench['latency_stats']))

            d['queryname'] = query_bench['queryname']
            data_bench.append(d)

        data.append({
            'benchmark': benchname,
            'title': bench.title,
            'variations': data_bench,
        })

    return data


def format_report_html(data, target_file):
    tpl_path = os.path.join(os.path.dirname(__file__), 'report', 'report.html')

    with open(tpl_path, 'r') as f:
        tpl = string.Template(f.read())

    platform = '{system} ({dist}, {arch}) on {cpu}'.format(
        system=data['platform']['system'],
        dist=data['platform']['distribution'],
        arch=data['platform']['arch'],
        cpu=data['platform']['cpu'],
    )

    output = tpl.safe_substitute(
        __BENCHMARK_DATE__=data['date'],
        __BENCHMARK_DURATION__=data['duration'],
        __BENCHMARK_CONCURRENCY__=data['concurrency'],
        __BENCHMARK_PLATFORM__=platform,
        __BENCHMARK_DATA__=json.dumps(data),
    )

    with open(target_file, 'wt') as f:
        f.write(output)


def run_benchmarks(args, argv):
    python_args = None

    for benchname in args.benchmarks:
        bench = _shared.BENCHMARKS[benchname]
        if bench.language == 'python':
            python_args = [
                'python', 'bench_python.py', '--json', '__tmp.json'
            ] + argv

    try:
        agg_data = []
        if python_args:
            subprocess.run(
                python_args, stdout=sys.stdout, stderr=sys.stderr, check=True)

            with open('__tmp.json', 'rt') as f:
                data = process_results(f.read())
                agg_data.extend(data)
    finally:
        if os.path.exists('__tmp.json'):
            os.unlink('__tmp.json')

    return agg_data


def main():
    args, argv = _shared.parse_args(
        prog_desc='EdgeDB Databases Benchmark',
        out_to_html=True,
        out_to_json=True)

    benchmarks_data = run_benchmarks(args, argv)

    date = datetime.datetime.now().strftime('%c')
    plat_info = platform_info()
    report_data = {
        'date': date,
        'duration': args.duration,
        'platform': plat_info,
        'concurrency': args.concurrency,
        'querynames': args.queries,
        'benchmarks': benchmarks_data,
    }

    if args.html:
        format_report_html(report_data, args.html)

    if args.json:
        with open(args.json, 'wt') as f:
            f.write(json.dumps(report_data))


if __name__ == '__main__':
    main()
