using EdgeDB.Net.IMDBench.Benchmarks.EdgeDB.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EdgeDB
{
    internal sealed class GetUserBenchmark : BaseEdgeDBBenchmark
    {
        public override string Name => "get_user";

        public override Task<User> BenchmarkAsync()
            => Client.QueryRequiredSingleAsync<User>(Queries.SELECT_USER, new Dictionary<string, object?>()
            {
                { "id", UserId }
            });
    }
}
