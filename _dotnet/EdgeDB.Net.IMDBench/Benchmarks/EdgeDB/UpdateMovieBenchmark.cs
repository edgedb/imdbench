using EdgeDB.Net.IMDBench.Benchmarks.EdgeDB.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EdgeDB
{
    internal sealed class UpdateMovieBenchmark : BaseEdgeDBBenchmark
    {
        public override string Name => "update_movie";

        public override Task<Movie> BenchmarkAsync()
            => Client.QueryRequiredSingleAsync<Movie>(Queries.UPDATE_MOVIE, new Dictionary<string, object?>
            {
                { "id", MovieId },
                { "suffix", MovieId.ToString() }
            });
    }
}
