using EdgeDB.Net.IMDBench.Benchmarks.EdgeDB.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EdgeDB
{
    internal sealed class InsertUserBenchmark : BaseEdgeDBBenchmark
    {
        public override string Name => "insert_user";
        
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

        public override Task<User> BenchmarkAsync(CancellationToken token)
            => Client.QueryRequiredSingleAsync<User>(Queries.INSERT_USER, new Dictionary<string, object?>()
            {
                { "name", "name_" + _num },
                { "image", "image_" + _num }
            }, token: token);
    }
}
