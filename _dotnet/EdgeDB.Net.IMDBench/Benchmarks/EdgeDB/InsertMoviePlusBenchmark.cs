using EdgeDB.Net.IMDBench.Benchmarks.EdgeDB.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EdgeDB
{
    internal sealed class InsertMoviePlusBenchmark : BaseEdgeDBBenchmark
    {
        public override string Name => "insert_movie_plus";

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

        public override Task<Movie> BenchmarkAsync(CancellationToken token)
            => Client.QueryRequiredSingleAsync<Movie>(Queries.INSERT_MOVIE_PLUS, new Dictionary<string, object?>
            {
                { "title", "Movie " + _num },
                { "image", "image_" + _num + ".jpeg"},
                { "description", "description " + _num },
                { "year", (long)_num },
                { "dfn", _num + "Alice" },
                { "dln", _num + "Director" },
                { "dimg", "image" + _num + ".jpeg" },
                { "cfn0", _num + "Billie" },
                { "cln0", _num + "Actor" },
                { "cimg0", "image" + (_num + 1) + ".jpeg" },
                { "cfn1", _num + "Cameron" },
                { "cln1", _num + "Actor" },
                { "cimg1", "image" + (_num + 2) + ".jpeg" },
            }, token: token);
    }
}
