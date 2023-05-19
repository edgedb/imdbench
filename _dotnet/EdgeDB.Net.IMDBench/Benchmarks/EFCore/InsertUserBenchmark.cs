using EdgeDB.Net.IMDBench.Benchmarks.EFCore.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore
{
    internal sealed class InsertUserBenchmark : BaseEFCoreBenchmark
    {
        public override string Name => "insert_user";

        private readonly Random _random = new();

        private int _num;

        public override ValueTask IterationSetupAsync()
        {
            _num = _random.Next(0, 50000);

            return base.IterationSetupAsync();
        }
        
        public override async Task<User> BenchmarkAsync(CancellationToken token)
        {
            using var ctx = CreateContext();

            var user = new User
            {
                Name = $"User {_num}",
                Image = $"image_{_num}"
            };

            var entry = await ctx.Users.AddAsync(user, token);

            await ctx.SaveChangesAsync(token);

            return entry.Entity;
        }
    }
}
