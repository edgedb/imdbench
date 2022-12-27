import json
import typing
import _shared
import subprocess
import pathlib

import numpy as np


class Result(typing.NamedTuple):

    benchmark: str
    queryname: str
    nqueries: int
    duration: int
    min_latency: int
    avg_latency: int
    max_latency: int
    latency_stats: typing.List[int]
    samples: typing.List[str]


def run_query(ctx, benchmark, queryname):
    dirn = pathlib.Path(__file__).resolve().parent
    proj_dir = dirn / '_dotnet' / 'EdgeDB.Net.IMDBench'

    opts = [
        '--concurrency', ctx.concurrency,
        '--duration', ctx.duration,
        '--timeout', ctx.timeout,
        '--warmup-time', ctx.warmup_time,
        '--output-format', 'json',
        '--host', ctx.db_host,
        '--nsamples', 10,
        '--number-of-ids', ctx.number_of_ids,
        '--query', queryname,
        '--target', benchmark,
    ]

    if benchmark.startswith('edgedb'):
        opts.extend(('--port', ctx.edgedb_port))
    else:
        opts.extend(('--port', ctx.pg_port))

    cmd = [
        str(c) for c in (
            ['dotnet', 'run', '-c', 'Release', '--']
            + opts
        )
    ]

    print("Running benchmark...")
    print(' '.join(cmd))
    try:
        proc = subprocess.run(
            cmd, text=True, capture_output=True, check=True,
            cwd=proj_dir,
        )
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        raise

    output = proc.stdout

    data = json.loads(output)

    avg_latency = np.average(
        np.arange(len(data['latency_stats'])),
        weights=data['latency_stats'])

    return Result(
        benchmark=benchmark,
        queryname=queryname,
        nqueries=data['nqueries'],
        duration=data['duration'],
        min_latency=data['min_latency'],
        avg_latency=avg_latency,
        max_latency=data['max_latency'],
        latency_stats=data['latency_stats'],
        samples=data['samples'],
    )


def print_result(ctx, result: Result):
    print(f'== {result.benchmark} : {result.queryname} ==')
    print(f'queries:\t{result.nqueries}')
    print(f'qps:\t\t{result.nqueries // ctx.duration} q/s')
    print(f'min latency:\t{result.min_latency / 100:.2f}ms')
    print(f'avg latency:\t{result.avg_latency / 100:.2f}ms')
    print(f'max latency:\t{result.max_latency / 100:.2f}ms')
    print()


def run_bench(ctx, benchmark):
    results = []

    for queryname in ctx.queries:
        res = run_query(ctx, benchmark, queryname)
        results.append(res)
        print_result(ctx, res)

    return results


def main():
    ctx, _ = _shared.parse_args(
        prog_desc='EdgeDB Databases Benchmark (Dotnet drivers)',
        out_to_json=True)

    print('============ .NET ============')
    print(f'queries:\t{", ".join(q for q in ctx.queries)}')
    print(f'benchmarks:\t{", ".join(b for b in ctx.benchmarks)}')
    print()
    print("Running benchmarks...")

    data = []
    for benchmark in ctx.benchmarks:
        bench_desc = _shared.IMPLEMENTATIONS[benchmark]
        if bench_desc.language != 'dotnet':
            continue

        res = run_bench(ctx, benchmark)
        data.append(res)

    if ctx.json:
        json_data = []
        for results in data:
            json_results = []
            for r in results:
                json_results.append({
                    'queryname': r.queryname,
                    'nqueries': r.nqueries,
                    'min_latency': r.min_latency,
                    'max_latency': r.max_latency,
                    'latency_stats': [int(i) for i in r.latency_stats],
                    'samples': r.samples,
                })
            json_data.append({
                'benchmark': results[0].benchmark,
                'duration': results[0].duration,
                'queries': json_results,
            })

        data = json.dumps({
            'language': 'dotnet',
            'concurrency': ctx.concurrency,
            'warmup_time': ctx.warmup_time,
            'duration': ctx.duration,
            'data': json_data,
        })
        with open(ctx.json, 'wt') as f:
            f.write(data)


if __name__ == '__main__':
    main()
