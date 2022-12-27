using EdgeDB.Net.IMDBench.Benchmarks.EdgeDB.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EdgeDB
{
    internal sealed class GetPersonBenchmark : BaseEdgeDBBenchmark
    {
        public override string Name => "get_person";
        
        public override Task<Person> BenchmarkAsync(CancellationToken token)
            => Client.QueryRequiredSingleAsync<Person>(Queries.SELECT_PERSON, new Dictionary<string, object?>
            {
                { "id", PersonId }
            }, token: token);
    }
}
