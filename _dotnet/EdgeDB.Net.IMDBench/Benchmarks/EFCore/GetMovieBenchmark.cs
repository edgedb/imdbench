using EdgeDB.Net.IMDBench.Benchmarks.EFCore.Models;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore
{
    internal sealed class GetMovieBenchmark : BaseEFCoreBenchmark
    {
        public override string Name => "get_movie";

        public override async Task<Movie> BenchmarkAsync(CancellationToken token)
        {
            using var ctx = CreateContext();

            return await ctx.Movies
                .Include(x => x.Directors
                    .OrderBy(x => x.ListOrder)
                    .OrderBy(x => x.Person.LastName))
                .Include(x => x.Actors
                    .OrderBy(x => x.ListOrder)
                    .OrderBy(x => x.Person.LastName))
                .Include(x => x.Reviews)
                    .ThenInclude(x => x.Author)
                .ApplyAverageRating()
                .FirstAsync(x => x.Id == MovieId, token);
        }
    }
}
