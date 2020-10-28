package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math"
	"math/rand"
	"time"
)

type Exec func(string) (time.Duration, string)

type Close func()

type Worker func(args Args) (Exec, Close)

type WorkResult struct {
	Durations []time.Duration
	Samples   []string
}

type Stats struct {
	Queries       int64    `json:"nqueries"`
	MinLatency    int64    `json:"min_latency"`
	MaxLatency    int64    `json:"max_latency"`
	LatencyCounts []int64  `json:"latency_stats"`
	Duration      float64  `json:"duration"`
	Samples       []string `json:"samples"`
}

func doWork(
	work Worker,
	duration time.Duration,
	args Args,
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

	for i := 0; i < args.NSamples; i++ {
		id := args.Ids[rand.Intn(len(args.Ids))]
		_, sample := exec(id)
		stats.Samples = append(stats.Samples, sample)
	}

	roundedTimeout := args.Timeout.Nanoseconds() / 10_000
	start := time.Now()
	for time.Since(start) < duration {
		id := args.Ids[rand.Intn(len(args.Ids))]
		reqTime, _ := exec(id)

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
	work Worker,
	duration time.Duration,
	args Args,
) Stats {
	statsChan := make(chan Stats, args.Concurrency)

	for i := 0; i < args.Concurrency; i++ {
		go doWork(work, duration, args, statsChan)
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
	args := parseArgs()

	var worker Worker
	if args.Protocol == "http" {
		worker = httpWorker
	} else if args.Serialization == "json" {
		worker = edgedbJSONWorker
	} else {
		worker = edgedbRepackWorker
	}

	doConcurrentWork(worker, args.Warmup, args)
	stats := doConcurrentWork(worker, args.Duration, args)

	data, err := json.Marshal(stats)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(string(data))
}
