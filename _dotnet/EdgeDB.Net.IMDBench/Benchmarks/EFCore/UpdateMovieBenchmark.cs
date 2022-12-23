using EdgeDB.Net.IMDBench.Benchmarks.EFCore.Models;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore
{
    internal sealed class UpdateMovieBenchmark : BaseEFCoreBenchmark
    {
        public override string Name => "update_movie";

        private readonly Random _random = new();

        private int _num;

        public override ValueTask IterationSetupAsync()
        {
            _num = _random.Next(0, 50000);

            return base.IterationSetupAsync();
        }
        
        public override async Task<Movie> BenchmarkAsync()
        {
            using var ctx = CreateContext();

            var movie = await ctx.Movies.FirstAsync(x => x.Id == MovieId);

            movie.Title = $"New Title {_num}";

            await ctx.SaveChangesAsync();

            return movie;
        }
    }
}
