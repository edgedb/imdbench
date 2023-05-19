using EdgeDB.Net.IMDBench.Benchmarks.EFCore.Models;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore
{
    internal sealed class InsertMovieBenchmark : BaseEFCoreBenchmark
    {
        public override string Name => "insert_movie";
        
        private readonly Random _random = new();

        private int _num;

        public override ValueTask IterationSetupAsync()
        {
            _num = _random.Next(0, 50000);

            return base.IterationSetupAsync();
        }

        public override async Task<Movie> BenchmarkAsync(CancellationToken token)
        {
            using var ctx = CreateContext();

            var movie = new Movie()
            {
                Title = $"Movie {_num}",
                Image = $"image_{_num}.jpeg",
                Description = $"description {_num}",
                Year = _num,
            };

            movie.Directors.Add(new Director
            {
                PersonId = PersonId
            });

            foreach(var id in PeopleIds[..4])
            {
                movie.Actors.Add(new Actor() { PersonId = id });
            }

            var entry = await ctx.Movies.AddAsync(movie, token);

            await ctx.SaveChangesAsync(token);

            return await ctx.Movies
                .Include(x => x.Directors)
                    .ThenInclude(x => x.Person)
                .Include(x => x.Actors)
                    .ThenInclude(x => x.Person)
                .FirstAsync(x => x.Id == entry.Entity.Id, token);
        }
    }
}
