using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore
{
    internal abstract class BaseEFCoreBenchmark : BaseBenchmark
    {
        public override string Category => "efcore";

        public int UserId { get; private set; }
        public int PersonId { get; private set; }
        public int MovieId { get; private set; }

        public int[] MovieIds { get; private set; } = Array.Empty<int>();
        public int[] UserIds { get; private set; } = Array.Empty<int>();
        public int[] PeopleIds { get; private set; } = Array.Empty<int>();

        private string? _host;
        private int _port;

        public override ValueTask IterationSetupAsync()
        {
            var rand = new Random();

            UserId = UserIds[rand.Next(UserIds.Length)];
            MovieId = MovieIds[rand.Next(MovieIds.Length)];
            PersonId = PeopleIds[rand.Next(PeopleIds.Length)];

            return base.IterationSetupAsync();
        }

        public override async ValueTask SetupAsync(BenchmarkConfig config)
        {
            _host = config.Host;
            _port = config.Port;

            using var context = CreateContext();

            if(MovieIds.Length != config.NumIds)
            {
                MovieIds = await context.Movies.Select(x => x.Id).Take(config.NumIds).ToArrayAsync();
                UserIds = await context.Users.Select(x => x.Id).Take(config.NumIds).ToArrayAsync();
                PeopleIds = await context.Persons.Select(x => x.Id).Take(config.NumIds).ToArrayAsync();
            }
        }

        public PostgresBenchContext CreateContext()
            => new(_host!, _port);
    }
}
