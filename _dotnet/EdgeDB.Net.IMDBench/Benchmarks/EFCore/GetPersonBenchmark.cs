using EdgeDB.Net.IMDBench.Benchmarks.EFCore.Models;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore
{
    internal class GetPersonBenchmark : BaseEFCoreBenchmark
    {
        public override string Name => "get_person";

        public override async Task<Person> BenchmarkAsync(CancellationToken token)
        {
            using var ctx = CreateContext();

            var person =  await ctx.Persons
                .Include(x => x.Actors
                    .OrderBy(y => y.Movie.Year)
                    .OrderBy(y => y.Movie.Title)
                ).ThenInclude(x => x.Movie)
                .ThenInclude(x => x.Reviews)
                .Include(x => x.Directors
                    .OrderBy(x => x.Movie.Year)
                    .OrderBy(x => x.Movie.Title)
                ).ThenInclude(x => x.Movie)
                .ThenInclude(x => x.Reviews)
                .FirstAsync(x => x.Id == PersonId, token);

            // include avg. rating
            person.Actors
                .Select(x => x.Movie)
                .Concat(
                    person.Directors
                    .Select(x => x.Movie))
                .ApplyAverageRating();

            return person;
        }
    }
}
