using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks
{
    public abstract class BaseBenchmark
    {
        public abstract string Name { get; }
        public abstract string Category { get; }
        
        public virtual ValueTask IterationSetupAsync() { return ValueTask.CompletedTask; }

        public virtual ValueTask SetupAsync(BenchmarkConfig config) { return ValueTask.CompletedTask; }

        public abstract Task BenchmarkAsync(CancellationToken token);

        public override string ToString()
        {
            return $"{Category}.{Name}";
        }
    }
}
