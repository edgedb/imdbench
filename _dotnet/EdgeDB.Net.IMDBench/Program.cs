using CommandLine;
using EdgeDB;
using EdgeDB.Net.IMDBench;
using EdgeDB.Net.IMDBench.Benchmarks;
using Newtonsoft.Json;

var parser = new Parser(x =>
{
    x.HelpWriter = null;
});

await parser.ParseArguments<BenchmarkConfig>(args)
    .WithNotParsed(x =>
    {
        foreach(var err in x)
        {
            Console.Error.WriteLine($"{err.Tag}: {JsonConvert.SerializeObject(err, Formatting.Indented)}");
        }
    })
    .WithParsedAsync(async x =>
    {
        try
        {
            var benchmarkRunner = new BenchmarkRunner(x);

            await benchmarkRunner.SetupAsync();

            await benchmarkRunner.WarmupAsync();

            await benchmarkRunner.RunAsync();
        }
        catch(Exception err)
        {
            Console.Error.WriteLine($"FATAL: {err}");
            Environment.Exit(2);
        }
    });