package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math"
	"math/rand"
	"time"

	"github.com/edgedb/webapp-bench/_go/bench"
	"github.com/edgedb/webapp-bench/_go/cli"
	"github.com/edgedb/webapp-bench/_go/edgedb"
	"github.com/edgedb/webapp-bench/_go/http"
	"github.com/edgedb/webapp-bench/_go/postgres"
)

type Slice struct {
	Start 	int
	End 	int
}

type Stats struct {
	Queries       int64    `json:"nqueries"`
	MinLatency    int64    `json:"min_latency"`
	MaxLatency    int64    `json:"max_latency"`
	LatencyCounts []int64  `json:"latency_stats"`
	Duration      float64  `json:"duration"`
	Samples       []string `json:"samples"`
}

func safeSlice(
	array 	[]string,
	slice 	Slice,
) []string {
	l := len(array)

	if l < slice.Start {
		return array[l:l];
	} else if l < slice.End {
		return array[slice.Start:l];
	} else {
		return array[slice.Start:slice.End];
	}
}

func doWork(
	work bench.Worker,
	duration time.Duration,
	args cli.Args,
	slice Slice,
	statsChan chan Stats,
) {
	exec, close := work(args)
	defer close()

	stats := Stats{
		Queries:       0,
		MinLatency:    math.MaxInt64,
		MaxLatency:    0,
		LatencyCounts: make([]int64, 1+args.Timeout.Nanoseconds()/10_000),
		Samples:       make([]string, 0, args.NSamples),
	}

	var (
		id 		string
		text 	string
		lenArgs	int
	)

	// To avoid concurrent modification of the same objects separate
	// the inputs into non-overlapping chunks.
	Ids := safeSlice(args.Ids, slice)
	Text := safeSlice(args.Text, slice)

	if len(Text) < len(Ids) {
		lenArgs = len(Ids)
	} else {
		lenArgs = len(Text)
	}

	for i := 0; i < args.NSamples; i++ {
		index := rand.Intn(lenArgs)

		if len(Ids) > 0 {
			id = Ids[index]
		}
		if len(Text) > 0 {
			text = Text[index]
		}

		_, sample := exec(id, text)
		stats.Samples = append(stats.Samples, sample)
	}

	roundedTimeout := args.Timeout.Nanoseconds() / 10_000
	start := time.Now()
	for time.Since(start) < duration {
		index := rand.Intn(lenArgs)

		if len(Ids) > 0 {
			id = Ids[index]
		}
		if len(Text) > 0 {
			text = Text[index]
		}

		reqTime, _ := exec(id, text)

		rounded := reqTime.Nanoseconds() / 10_000
		if rounded > stats.MaxLatency {
			stats.MaxLatency = rounded
		}

		if rounded < stats.MinLatency {
			stats.MinLatency = rounded
		}

		if rounded > roundedTimeout {
			rounded = roundedTimeout
		}

		stats.LatencyCounts[rounded]++
		stats.Queries++
	}

	statsChan <- stats
}

func doConcurrentWork(
	work bench.Worker,
	duration time.Duration,
	args cli.Args,
) Stats {
	statsChan := make(chan Stats, args.Concurrency)
    // We want to split the input ids into separate chunks, so that we
    // avoid concurrent mutations of the same object.
    var chunk_len int
	if len(args.Ids) > 0 {
	    chunk_len = (len(args.Ids) + args.Concurrency - 1) / args.Concurrency
	} else if len(args.Text) > 0 {
	    chunk_len = (len(args.Text) + args.Concurrency - 1) / args.Concurrency
	}

	for i := 0; i < args.Concurrency; i++ {
		slice := Slice{Start: chunk_len*i, End: chunk_len*(i+1)}
		go doWork(work, duration, args, slice, statsChan)
	}

	samples := make([]string, 0, args.NSamples*args.Concurrency)
	stats := Stats{
		Queries:       0,
		MinLatency:    math.MaxInt64,
		MaxLatency:    0,
		LatencyCounts: make([]int64, 1+args.Timeout.Nanoseconds()/10_000),
		Samples:       make([]string, 0, args.NSamples),
		Duration:      duration.Seconds(),
	}

	for i := 0; i < args.Concurrency; i++ {
		tStats := <-statsChan
		stats.Queries += tStats.Queries
		samples = append(samples, tStats.Samples...)

		for i := 0; i < len(stats.LatencyCounts); i++ {
			stats.LatencyCounts[i] += tStats.LatencyCounts[i]
		}

		if tStats.MaxLatency > stats.MaxLatency {
			stats.MaxLatency = tStats.MaxLatency
		}

		if tStats.MinLatency < stats.MinLatency {
			stats.MinLatency = tStats.MinLatency
		}
	}

	for i := 0; i < args.NSamples; i++ {
		sample := samples[rand.Intn(args.NSamples)]
		stats.Samples = append(stats.Samples, sample)
	}

	return stats

}

func main() {
	args := cli.ParseArgs()
	var worker bench.Worker

	switch args.Benchmark {
	case "edgedb_repack_go":
		worker = edgedb.RepackWorker
	case "edgedb_json_go":
		worker = edgedb.JSONWorker
	case "postgres_pq":
		worker = postgres.PQWorker
	case "postgres_pgx":
		worker = postgres.PGXWorker
	default:
		worker = http.Worker
	}

	doConcurrentWork(worker, args.Warmup, args)

	stats := doConcurrentWork(worker, args.Duration, args)

	data, err := json.Marshal(stats)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(string(data))
}
