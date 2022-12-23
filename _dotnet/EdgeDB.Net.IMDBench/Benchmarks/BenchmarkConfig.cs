using CommandLine;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks
{
    public class BenchmarkConfig
    {
        [Option("concurrency")]
        public int Concurrency { get; set; } = 1;

        [Option("duration")]
        public int Duration { get; set; } = 2;

        [Option("timeout")]
        public int Timeout { get; set; } = 5000;

        [Option("warmup-time")]
        public int Warmup { get; set; } = 6;
        
        [Option("output-format")]
        public string? OutputFormat { get; set; }

        [Option("host")]
        public string Host { get; set; } = "localhost";
        
        public int Port
            => int.Parse(RawPort);

        [Option("nsamples")]
        public int NumSamples { get; set; } = 0;

        [Option("number-of-ids")]
        public int NumIds { get; set; } = 10;

        [Option("query")]
        public IEnumerable<string>? Queries { get; set; }

        [Option("target")]
        public IEnumerable<string>? Targets { get; set; }

        [Option("port")]
        public string RawPort { get; set; } = "15432";
    }
}
