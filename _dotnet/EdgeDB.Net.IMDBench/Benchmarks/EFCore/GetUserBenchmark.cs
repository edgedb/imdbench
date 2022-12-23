using EdgeDB.Net.IMDBench.Benchmarks.EFCore.Models;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore
{
    internal sealed class GetUserBenchmark : BaseEFCoreBenchmark
    {
        public override string Name => "get_user";

        public override async Task<User> BenchmarkAsync()
        {
            using var ctx = CreateContext();

            var user = await ctx.Users
                .Include(x => x.Reviews)
                .ThenInclude(x => x.Movie)
                .ThenInclude(x => x.Reviews)
                .FirstAsync(x => x.Id == UserId);

            // apply avg. rating
            user.Reviews.Select(x => x.Movie).ApplyAverageRating();

            return user;
        }
    }
}
