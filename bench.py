#!/usr/bin/env python3

#
# Copyright (c) 2019 MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import datetime
import itertools
import json
import math
import os
import os.path
import pathlib
import platform
import random
import string
import subprocess
import sys

import distro
import jinja2
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
        distribution = '{} {}'.format(distro.name(), distro.version()).strip()
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
                       latency_stats, samples, *, output_format='text'):
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

    if samples:
        random.shuffle(samples)
        samples = samples[:3]

    data = dict(
        duration=round(duration, 2),
        queries=queries,
        qps=round(queries / duration, 2),
        latency_min=round(min_latency / 100, 3),
        latency_mean=round(mean_latency / 100, 3),
        latency_max=round(max_latency / 100, 3),
        latency_std=round(latency_std / 100, 3),
        latency_cv=round(latency_cv * 100, 2),
        latency_percentiles=percentile_data,
        samples=samples[:3] if samples else None
    )

    return data


def _geom_mean(values):
    p = 1
    root = 0
    for val in values:
        p *= val
        root += 1

    if root != 0:
        return p ** (1.0 / root)
    else:
        return 0


def mean_latency_stats(data):
    pivot = {}
    for bench in itertools.chain.from_iterable(data.values()):
        pivot.setdefault(bench["implementation"], []).append(bench)

    mean_data = []

    for impl, var in pivot.items():
        mean_data.append(dict(
            implementation=impl,
            duration=round(_geom_mean(v['duration'] for v in var), 2),
            queries=round(_geom_mean(v['queries'] for v in var), 2),
            qps=round(_geom_mean(v['qps'] for v in var), 2),
            latency_min=round(_geom_mean(v['latency_min'] for v in var), 3),
            latency_mean=round(_geom_mean(v['latency_mean'] for v in var), 3),
            latency_max=round(_geom_mean(v['latency_max'] for v in var), 3),
            latency_std=round(_geom_mean(v['latency_std'] for v in var), 3),
            latency_cv=round(_geom_mean(v['latency_cv'] for v in var), 2),
            latency_percentiles=[
                (
                    p,
                    round(
                        _geom_mean(
                            v['latency_percentiles'][i][1] for v in var
                        ),
                        3
                    )
                ) for i, p in enumerate(percentiles)
            ]
        ))

    return {'mean': mean_data, **data}


def process_results(lat_data, results):
    for bench_data in lat_data['data']:
        impl_name = bench_data['benchmark']
        impl = _shared.IMPLEMENTATIONS[impl_name]

        for query_bench in bench_data['queries']:
            d = calc_latency_stats(
                query_bench['nqueries'],
                bench_data['duration'],
                query_bench['min_latency'],
                query_bench['max_latency'],
                np.array(query_bench['latency_stats']),
                query_bench.get('samples'))

            d["implementation"] = impl.title

            results.setdefault(query_bench['queryname'], []).append(d)


def format_report_html(data, target_file, sort=True):
    tpl_dir = pathlib.Path(__file__).parent / 'docs'
    tpl_path = tpl_dir / 'TEMPLATE.html'

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(tpl_dir),
    )

    with open(tpl_path) as f:
        tpl = env.from_string(f.read())

    platform = '{system} ({dist}, {arch}) on {cpu}'.format(
        system=data['platform']['system'],
        dist=data['platform']['distribution'],
        arch=data['platform']['arch'],
        cpu=data['platform']['cpu'],
    )

    params = dict(
        __BENCHMARK_DATE__=data['date'],
        __BENCHMARK_DURATION__=data['duration'],
        __BENCHMARK_CONCURRENCY__=data['concurrency'],
        __BENCHMARK_NETLATENCY__=data['netlatency'],
        __BENCHMARK_IMPLEMENTATIONS__=data['implementations'],
        __BENCHMARK_DESCRIPTIONS__=data['benchmarks_desc'],
        __BENCHMARK_PLATFORM__=platform,
        __BENCHMARK_DATA__={
            b: json.dumps(v) for b, v in data['benchmarks'].items()
        },
        __BENCHMARK_SORT__='true' if sort else 'false',
    )

    output = tpl.render(**params)

    target_file.write(output)


def run_benchmarks(args, argv):
    lang_args = {}
    for benchname in args.benchmarks:
        bench = _shared.IMPLEMENTATIONS[benchname]
        if bench.language == 'python':
            lang_args['python'] = [
                'python', 'bench_python.py', '--json', '__tmp.json'
            ] + argv
        elif bench.language == 'go':
            lang_args['go'] = [
                'python', 'bench_go.py', '--json', '__tmp.json'
            ] + argv
        elif bench.language == 'js':
            lang_args['js'] = [
                'python', 'bench_js.py', '--json', '__tmp.json'
            ] + argv
        elif bench.language == 'dart':
            lang_args['dart'] = [
                'python', 'bench_dart.py', '--json', '__tmp.json'
            ] + argv
        else:
            raise ValueError('unsupported host language: {}'.format(
                bench.language))

    try:
        agg_data = {}
        for cmd in lang_args.values():
            subprocess.run(
                cmd, stdout=sys.stdout, stderr=sys.stderr, check=True)

            with open('__tmp.json', 'rt') as f:
                # Read the raw data from the file
                results = f.read()
                try:
                    raw_data = json.loads(results)
                except json.JSONDecodeError as e:
                    print('could not process benchmark results: {}'.format(e),
                          file=sys.stderr)
                    print(results, file=sys.stderr)
                    sys.exit(1)

                process_results(raw_data, agg_data)
    finally:
        if os.path.exists('__tmp.json'):
            os.unlink('__tmp.json')

    return mean_latency_stats(agg_data)


def main():
    args, argv = _shared.parse_args(
        prog_desc='EdgeDB Databases Benchmark',
        out_to_html=True,
        out_to_json=True)

    if any(b.startswith('edgedb') for b in args.benchmarks):
        print(__file__)
        project_info_proc = subprocess.run(
            ["edgedb", "project", "info", "--json"],
            text=True,
            capture_output=True,
        )
        if project_info_proc.returncode != 0:
            print(
                f"`edgedb project` returned"
                f" {project_info_proc.returncode}. Please run"
                f" `make load-edgedb`, or initialize the EdgeDB"
                f" project directly",
                file=sys.stderr,
            )
            return 1

        project_info = json.loads(project_info_proc.stdout)
        args.edgedb_instance = project_info["instance-name"]
        os.environ["EDGEDB_INSTANCE"] = args.edgedb_instance

        instance_status_proc = subprocess.run(
            ["edgedb", "instance", "status", "--json", args.edgedb_instance],
            text=True,
            capture_output=True,
        )
        if (instance_status_proc.returncode != 0 and
                instance_status_proc.returncode != 3):
            print(
                f"`edgedb instance status` returned"
                f" {instance_status_proc.returncode}. Please run"
                f" `make load-edgedb`, or initialize the EdgeDB"
                f" project directly",
                file=sys.stderr,
            )
            return 1

        instance_status = json.loads(instance_status_proc.stdout)
        args.edgedb_port = int(instance_status["port"])
        argv.extend(("--edgedb-port", str(args.edgedb_port)))

    benchmarks_data = run_benchmarks(args, argv)

    date = datetime.datetime.now().strftime('%c')
    plat_info = platform_info()
    report_data = {
        'date': date,
        'duration': args.duration,
        'netlatency': args.net_latency,
        'platform': plat_info,
        'concurrency': args.concurrency,
        'benchmarks': benchmarks_data,
        'benchmarks_desc': _shared.BENCHMARKS,
        'implementations': [
            _shared.IMPLEMENTATIONS[benchname].title
            for benchname in args.benchmarks
        ]
    }

    if args.html:
        with open(args.html, 'wt') as f:
            format_report_html(report_data, f)

    if args.json:
        with open(args.json, 'wt') as f:
            f.write(json.dumps(report_data))

    return 0


if __name__ == '__main__':
    sys.exit(main())
