using EdgeDB.Net.IMDBench.Benchmarks.EdgeDB.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EdgeDB
{
    internal sealed class InsertMovieBenchmark : BaseEdgeDBBenchmark
    {
        public override string Name => "insert_movie";

        private Random? _rand;
        private int _num;

        public override ValueTask SetupAsync(BenchmarkConfig config)
        {
            _rand = new();

            return base.SetupAsync(config);
        }

        public override ValueTask IterationSetupAsync()
        {
            _num = _rand!.Next(0, 50000);
            return base.IterationSetupAsync();
        }

        public override Task<Movie> BenchmarkAsync()
            => Client.QueryRequiredSingleAsync<Movie>(Queries.INSERT_MOVIE, new Dictionary<string, object?>()
            {
                { "title", "Movie " + _num },
                { "image", "image_" + _num + ".jpeg"},
                { "description", "description " + _num },
                { "year", (long)_num },
                { "d_id", PeopleIds[_num % PeopleIds.Length] },
                { "cast", PeopleIds[..4] }
            });
    }
}
