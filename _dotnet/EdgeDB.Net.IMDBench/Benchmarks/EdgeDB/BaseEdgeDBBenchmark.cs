using EdgeDB.State;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EdgeDB
{
    public abstract class BaseEdgeDBBenchmark : BaseBenchmark
    {
        private static (Guid[], Guid[], Guid[])? _ids;

        public override string Category => "edgedb_dotnet";
        public EdgeDBClient Client { get; private set; } = null!;

        public Guid UserId { get; private set; }
        public Guid MovieId { get; private set; }
        public Guid PersonId { get; private set; }


        public Guid[] UserIds { get; private set; } = Array.Empty<Guid>();
        public Guid[] MovieIds { get; private set; } = Array.Empty<Guid>();
        public Guid[] PeopleIds { get; private set; } = Array.Empty<Guid>();

        public override string GetInUseIdsState()
        {
            return $"Movie ID: {MovieId}\nUser Id: {UserId}\nPerson Id: {PersonId}";
        }

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
#if DEBUG
            var connection = new EdgeDBConnection()
            {
                Port = config.Port,
                TLSCertificateAuthority = "-----BEGIN CERTIFICATE-----\r\nMIIC0zCCAbugAwIBAgIRAOmkEvJqWEHSvrRnqLLPtsAwDQYJKoZIhvcNAQELBQAw\r\nGDEWMBQGA1UEAwwNRWRnZURCIFNlcnZlcjAeFw0yMjEwMzEyMjM3NTZaFw00MTEy\r\nMzEyMjM3NTZaMBgxFjAUBgNVBAMMDUVkZ2VEQiBTZXJ2ZXIwggEiMA0GCSqGSIb3\r\nDQEBAQUAA4IBDwAwggEKAoIBAQCtxZAVRpqpFWxycORcNCLorB6yZHhUsNBs08tC\r\nWY6oICt3h2QpIWtH4uB5XJHJBOTdRsk8sdiVIDeH8top/QecXaI67U2HNCKPovUh\r\nCOsKCkJJhrGDC4vRIXlBLqQAvr+RpvIjy9gQCZcFyKgBXKpvSzChJA7AFX+Ajcvz\r\nR6ypfxBqYMwv4G5inseha0I3LmGjW0EIJ7LIJP40E2/ZtmsSlx06rzfE91jYSQ85\r\n6sulwsYfVCe1PEK4yixnWwJyoh/X59GIXmNvW+2X3Bw1k1pv3ZfX3BvhRw9LdmQN\r\nWyfzkKzo+njLLgiDa/LWUVJ/Muns4UxMrRtEcBRCBqPpe6qHAgMBAAGjGDAWMBQG\r\nA1UdEQQNMAuCCTEyNy4wLjAuMTANBgkqhkiG9w0BAQsFAAOCAQEAhXNavQqBvTml\r\nvqR5P/0iDlitjbwwyv6J8O83mrYErY0PitLyZmsI1LygXuChMlOmmXk3cpjDO55A\r\n7yq2hMYspqyCVWAtgvsfEL1ftda66BFW6rUwKndNrYGCBoRRvwPIzk10Q/pFtwde\r\nsGkC989PYIzLjKyuttVjss71b7qcs21lFxGLZ9Sg8CCZl+b4nUQYXIEZhJTsUBms\r\nB9hOGrIPUYt2dmUfFA+DiR6xd2fkDDMr/7PxqLBMgC37RRVM6CGYtEsNov+Qbi4g\r\naJeYiGjdo/v7FpS8e1E+L8/356bIQWJZcvmveJggbS/78sj1OsRzmP3MhkOTZbky\r\nuiBuQUZ7kA==\r\n-----END CERTIFICATE-----\r\n"
            };
#else
            var connection = EdgeDBConnection.ResolveEdgeDBTOML();
#endif


            Client = new EdgeDBClient(connection, new EdgeDBClientPoolConfig
            {
                SchemaNamingStrategy = INamingStrategy.SnakeCaseNamingStrategy,
            });

            // get the ids
            var ids = await GetIdsAsync(Client, config.NumIds);

            UserIds = ids.Item1;
            MovieIds = ids.Item2;
            PeopleIds = ids.Item3;
        }

        private static async ValueTask<(Guid[], Guid[], Guid[])> GetIdsAsync(EdgeDBClient client, long numIds)
            => _ids ??= await client.QueryRequiredSingleAsync<(Guid[], Guid[], Guid[])>(Queries.GET_IDS, new Dictionary<string, object?>()
            {
                { "num_ids", numIds }
            });
    }
}
