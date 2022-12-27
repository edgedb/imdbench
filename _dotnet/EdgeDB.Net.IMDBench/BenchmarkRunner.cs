using EdgeDB.Net.IMDBench.Benchmarks;
using EdgeDB.Net.IMDBench.Benchmarks.EdgeDB.Models;
using Humanizer;
using Newtonsoft.Json;
using Newtonsoft.Json.Serialization;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench
{
    internal class BenchmarkRunner
    {
        public static Dictionary<string, Dictionary<string, BaseBenchmark>> AllBenchmarks { get; }

        private readonly BenchmarkConfig _config;
        private readonly DefaultContractResolver _contractResolver;

        static BenchmarkRunner()
        {
            // discover all benchmarks
            var benchmarks = Assembly.GetExecutingAssembly().DefinedTypes.Where(x =>
            {
                return !x.IsAbstract && x.IsAssignableTo(typeof(BaseBenchmark));
            });

            AllBenchmarks = new();

            // create instances and store them 
            
            foreach(var benchmark in benchmarks)
            {
                var inst = (BaseBenchmark)Activator.CreateInstance(benchmark)!;

                AllBenchmarks.TryAdd(inst.Category, new());

                AllBenchmarks[inst.Category] ??= new();

                AllBenchmarks[inst.Category][inst.Name] = inst;
            }
        }

        public BenchmarkRunner(BenchmarkConfig config)
        {
            _config = config;
            _contractResolver = new()
            {
                NamingStrategy = new SnakeCaseNamingStrategy()
            };
        }

        public async Task SetupAsync()
        {
            var benchmarks = GetActiveBenchmarks();

#if DEBUG
            Console.WriteLine($"Setting up {benchmarks.Length} benchmarks...");
#endif

            for(int i = 0; i != benchmarks.Length; i++)
            {
                var benchmark = benchmarks[i];
#if DEBUG
                Console.WriteLine("Setting up benchmark {0}/{1}: {2}", i + 1, benchmarks.Length, benchmark);
#endif
                await benchmark.SetupAsync(_config);
            }

#if DEBUG
            Console.WriteLine("Setup complete");
#endif
        }

        public async Task WarmupAsync()
        {
            var benchmarks = GetActiveBenchmarks();

#if DEBUG
            Console.WriteLine($"Starting warmup with {benchmarks.Count()} benchmarks with a duration of {_config.Warmup}s");
#endif
            for (int i = 0; i < benchmarks.Length; i++)
            {
                var benchmark = benchmarks[i];
                try
                {
#if DEBUG
                    Console.WriteLine("Warming up benchmark {0}/{1}: {2}", i + 1, benchmarks.Length, benchmark);

                    var results = await RunManyAsync(_config.Concurrency, () => BenchAsync(benchmark, _config.Warmup, _config.NumSamples));
                    var stats = new BenchStats(_config.Timeout, results);

                    Console.WriteLine("{0}: Avg: {1}μs Min: {2}μs Max: {3}μs", benchmark, stats.Average, stats.Min, stats.Max);
#else
                    await RunManyAsync(_config.Concurrency, () => BenchAsync(benchmark, _config.Warmup));
#endif
                }
                catch (Exception x)
                {
                    Console.Error.WriteLine($"Exception in {benchmark.Category}.{benchmark.Name}: {x}");

#if RELEASE
                    Environment.Exit(1);
#endif
                }
            }

#if DEBUG
            Console.WriteLine("Cleaning up...");

            GC.Collect();
#endif

#if DEBUG
            Console.WriteLine("Warmup complete");
#endif
        }

        public async Task RunAsync()
        {
            var benchmarks = GetActiveBenchmarks();

#if DEBUG
            Console.WriteLine($"Starting benchmarks with {benchmarks.Count()} benchmarks with a duration of {_config.Duration}s");
#endif
            for (int i = 0; i < benchmarks.Length; i++)
            {
                var benchmark = benchmarks[i];
                
                BenchResult[] result;

#if DEBUG
                Console.WriteLine("Running benchmark {0}/{1}: {2}", i + 1, benchmarks.Length, benchmark);
#endif
                try
                {
                    result = await RunManyAsync(_config.Concurrency, () => BenchAsync(benchmark, _config.Duration, _config.NumSamples));
                }
                catch (Exception x)
                {
                    Console.Error.WriteLine($"Exception in {benchmark}: {x}");

#if RELEASE
                    Environment.Exit(1);
#endif

                    continue;
                }

                var stats = new BenchStats(_config.Timeout, result);
#if RELEASE
                // report results of this run
                Console.WriteLine(JsonConvert.SerializeObject(stats, new JsonSerializerSettings 
                {
                    ReferenceLoopHandling = Newtonsoft.Json.ReferenceLoopHandling.Ignore,
                    ContractResolver = _contractResolver
                }));
#else

                Console.WriteLine($"{benchmark.Category}.{benchmark.Name}: Avg: {stats.Average}μs. Min: {stats.Min}μs. Max: {stats.Max}μs.");
#endif
            }
        }

        private Task<TResult[]> RunManyAsync<TResult>(int count, Func<Task<TResult>> func)
        {
            List<Task<TResult>> tasks = new();

            for(int i = 0; i != count; i++)
            {
                tasks.Add(func());
            }

            return Task.WhenAll(tasks);
        }

        private async Task<BenchResult> BenchAsync(BaseBenchmark benchmark, long duration, int sampleCount = 0)
        {
            var startTime = DateTimeOffset.UtcNow;
            var sw = new Stopwatch();

            List<object?> samples = new();
            List<TimeSpan> times = new();

            do
            {
                var cts = new CancellationTokenSource(TimeSpan.FromSeconds(_config.Timeout));
                await benchmark.IterationSetupAsync();

                sw.Start();
                var task = benchmark.BenchmarkAsync(cts.Token);
                await task;
                sw.Stop();

                cts.Dispose();

                // record the sample
                if (samples.Count < sampleCount && TryGetTaskResult(task, out var result))
                {
                    samples.Add(result);
                }

                // add the time
                times.Add(sw.Elapsed);

                // reset and go again
                sw.Reset();
            }
            while ((DateTimeOffset.UtcNow - startTime).TotalSeconds <= duration);

            return new BenchResult(benchmark.Category, benchmark.Name, samples, times, duration);
        }

        private BaseBenchmark[] GetActiveBenchmarks()
        {
            return AllBenchmarks
                .Where(x => _config.Targets!.Contains(x.Key))
                .SelectMany(x => x.Value.Where(y => _config.Queries!.Contains(y.Key)))
                .Select(x => x.Value)
                .ToArray();
        }

        private bool TryGetTaskResult(Task task, out object? result)
        {
            result = null;

            var resultProp = task.GetType().GetProperty("Result", BindingFlags.Public | BindingFlags.Instance);

            if (resultProp is null)
                return false;

            result = resultProp.GetValue(task);
            return true;
        }

        private record BenchResult(string Category, string Name, List<object?> Samples, List<TimeSpan> Times, long Duration);

        private class BenchStats
        {
            [JsonProperty("min_latency")]
            public double Min { get; }

            [JsonProperty("max_latency")]
            public double Max { get; }

            [JsonProperty("nqueries")]
            public long NumQueries { get; }

            [JsonProperty("samples")]
            public object? Samples { get; }

            [JsonProperty("latency_stats")]
            public double[] LatencyStats { get; }

            [JsonProperty("duration")]
            public double Duration { get; }

            [JsonProperty("avg_latency")]
            public double Average { get; }

            public BenchStats(int timeout, BenchResult result)
            {
                Min = result.Times.Min(x => x.TotalMicroseconds) / 10;
                Max = result.Times.Max(x => x.TotalMicroseconds) / 10;
                NumQueries = result.Times.Count;
                Samples = result.Samples;
                LatencyStats = CalculateLatency(timeout, result.Times);
                Duration = TimeSpan.FromMicroseconds(result.Times.Sum(x => x.TotalMicroseconds)).TotalSeconds;

                Average = result.Times.Average(x => x.TotalMilliseconds);
            }

            public BenchStats(int timeout, BenchResult[] results)
            {
                Min = results.Min(result => result.Times.Min(x => x.TotalMicroseconds)) / 10;
                Max = results.Min(result => result.Times.Max(x => x.TotalMicroseconds)) / 10;
                NumQueries = results.Sum(result => result.Times.Count);
                Samples = results.SelectMany(result => result.Samples).ToArray();
                LatencyStats = CalculateLatency(timeout, results.SelectMany(x => x.Times));
                Duration = TimeSpan.FromMicroseconds(results.Average(result => result.Times.Sum(x => x.TotalMicroseconds))).TotalSeconds;
                Average = results.Average(result => result.Times.Average(x => x.TotalMilliseconds));
            }

            private static double[] CalculateLatency(int timeout, IEnumerable<TimeSpan> times)
            {
                var mc = times.Select(x => (long)Math.Round(x.TotalMicroseconds / 10));

                var arr = new double[(long)Math.Round(TimeSpan.FromSeconds(timeout).TotalMicroseconds / 10)];

                foreach (var x in mc)
                {
                    arr[x]++;
                }

                return arr;
            }
        }
    }
}
