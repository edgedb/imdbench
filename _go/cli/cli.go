package cli

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"time"

	"gopkg.in/alecthomas/kingpin.v2"
)

type Args struct {
	Duration    time.Duration
	Timeout     time.Duration
	Warmup      time.Duration
	Query       string
	Ids         []string
	Host        string
	Port        int
	Path        string
	IdsAreInts  string
	NSamples    int
	Concurrency int
	Benchmark   string
}

func parseOrFatal(seconds int) time.Duration {
	duration, err := time.ParseDuration(fmt.Sprintf("%vs", seconds))
	if err != nil {
		log.Fatal(err)
	}

	return duration
}

func ParseArgs() Args {
	var (
		app = kingpin.New(
			"golang-edgedb-http-bench",
			"EdgeDB HTTP benchmark runner.")

		concurrency = app.Flag(
			"concurrency", "number of concurrent connections").Default("10").Int()

		duration = app.Flag(
			"duration", "duration of test in seconds").Default("30").Int()

		timeout = app.Flag(
			"timeout", "server timeout in seconds").Default("2").Int()

		warmup = app.Flag(
			"warmup-time",
			"duration of warmup period for each benchmark in seconds",
		).Default("5").Int()

		_ = app.Flag(
			"output-format",
			"result output format",
		).Default("text").Enum("text", "json")

		host = app.Flag(
			"host", "EdgeDB server host").Default("127.0.0.1").String()

		port = app.Flag(
			"port", "EdgeDB server port").Default("8080").Int()

		path = app.Flag(
			"path", "GraphQL API path").Default("").String()

		nsamples = app.Flag(
			"nsamples", "Number of result samples to return").Default("10").Int()

		idsAreInts = app.Flag(
			"ids-are-ints",
			"Whether or not ids are integers",
		).Default("False").Enum("True", "False")

		benchmark = app.Flag(
			"benchmark",
			"application protocol to use: http or edgedb",
		).Required().String()

		queryfile = app.Arg(
			"queryfile",
			"file to read benchmark query information from",
		).Required().String()
	)

	kingpin.MustParse(app.Parse(os.Args[1:]))

	args := Args{
		Duration:    parseOrFatal(*duration),
		Timeout:     parseOrFatal(*timeout),
		Warmup:      parseOrFatal(*warmup),
		Host:        *host,
		Port:        *port,
		Path:        *path,
		IdsAreInts:  *idsAreInts,
		NSamples:    *nsamples,
		Concurrency: *concurrency,
		Benchmark:   *benchmark,
	}

	file := os.Stdin
	if *queryfile != "-" {
		var err error
		file, err = os.Open(*queryfile)
		if err != nil {
			log.Fatal(err)
		}
	}

	bts, err := ioutil.ReadAll(file)
	if err != nil {
		log.Fatal(err)
	}

	json.Unmarshal(bts, &args)
	if err != nil {
		log.Fatal(err)
	}

	return args
}
