package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"math"
	"math/rand"
	"os"
	"strconv"
	"sync"
	"time"

	"github.com/valyala/fasthttp"
	"gopkg.in/alecthomas/kingpin.v2"
)

type ReportFunc func(int64, int64, int64, []int64, []string)
type WorkerFunc func(time.Time, time.Duration, time.Duration,
	string, []string,
	*sync.WaitGroup, ReportFunc)

type Query struct {
	Query     string                 `json:"query"`
	Variables map[string]interface{} `json:"variables"`
}

func http_worker(
	start time.Time, duration time.Duration, timeout time.Duration,
	query string, ids []string, wg *sync.WaitGroup,
	report ReportFunc) {

	defer wg.Done()

	var samples []string
	samples_collected := int(0)
	latency_stats := make([]int64, timeout/1000/10 + 1)
	timeout_ns := timeout.Nanoseconds()
	min_latency := int64(math.MaxInt64)
	max_latency := int64(0)
	queries := int64(0)

	num_ids := len(ids)

	c := &fasthttp.Client{}
	req := fasthttp.AcquireRequest()
	resp := fasthttp.AcquireResponse()

	url := fmt.Sprintf("http://%s:%d%s", *host, *port, *path)

	req.Header.SetMethod("POST")
	req.Header.SetContentType("application/json")
	req.SetRequestURI(url)

	query_data := &Query{}
	query_data.Query = query
	query_data.Variables = make(map[string]interface{})

	for time.Since(start) < duration || duration == 0 {
		req_start := time.Now()

		if *ids_are_ints == "True" {
			rid, err := strconv.Atoi(ids[rand.Intn(num_ids)])
			if err != nil {
				log.Fatal(err)
			}
			query_data.Variables["id"] = rid
		} else {
			query_data.Variables["id"] = ids[rand.Intn(num_ids)]
		}

		json_data, err := json.Marshal(query_data)

		if err != nil {
			log.Fatal(err)
		}

		req.SetBody(json_data)

		err = c.Do(req, resp)
		if err != nil {
			log.Fatal(err)
		}

		resp_data := resp.Body()

		req_time_ns := time.Since(req_start).Nanoseconds()
		req_time := req_time_ns / 1000 / 10
		if req_time > max_latency {
			max_latency = req_time
		}
		if req_time < min_latency {
			min_latency = req_time
		}

		if req_time_ns > timeout_ns {
			req_time = timeout_ns / 1000 / 10
		}
		latency_stats[req_time] += 1

		queries += 1

		if samples_collected < *nsamples {
			samples = append(samples, string(resp_data))
			samples_collected += 1
		}

		if duration == 0 {
			break
		}
	}

	fasthttp.ReleaseResponse(resp)
	fasthttp.ReleaseRequest(req)

	if report != nil {
		report(queries, min_latency, max_latency, latency_stats, samples)
	}
}

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

	warmup_time = app.Flag(
		"warmup-time", "duration of warmup period for each benchmark in seconds").Default("5").Int()

	output_format = app.Flag(
		"output-format", "result output format").Default("text").Enum("text", "json")

	host = app.Flag(
		"host", "EdgeDB server host").Default("127.0.0.1").String()

	port = app.Flag(
		"port", "EdgeDB server port").Default("8080").Int()

	path = app.Flag(
		"path", "GraphQL API path").Default("").String()

	nsamples = app.Flag(
		"nsamples", "Number of result samples to return").Default("10").Int()

	ids_are_ints = app.Flag(
		"ids-are-ints", "Whether or not ids are integers").Default("False").Enum("True", "False")

	queryfile = app.Arg(
		"queryfile", "file to read benchmark query information from").Required().String()
)

type QueryInfo struct {
	Query string
	Ids   []string
}

func main() {
	kingpin.MustParse(app.Parse(os.Args[1:]))

	duration, err := time.ParseDuration(fmt.Sprintf("%vs", *duration))
	if err != nil {
		log.Fatal(err)
	}
	timeout, err := time.ParseDuration(fmt.Sprintf("%vs", *timeout))
	if err != nil {
		log.Fatal(err)
	}
	warmup_time, err := time.ParseDuration(fmt.Sprintf("%vs", *warmup_time))
	if err != nil {
		log.Fatal(err)
	}

	var queryf *os.File

	if *queryfile == "-" {
		queryf = os.Stdin
	} else {
		queryf, err = os.Open(*queryfile)
		if err != nil {
			log.Fatal(err)
		}
	}

	querydata_json, err := ioutil.ReadAll(queryf)
	if err != nil {
		log.Fatal(err)
	}

	var querydata QueryInfo
	json.Unmarshal(querydata_json, &querydata)

	queries := int64(0)
	min_latency := int64(math.MaxInt64)
	max_latency := int64(0)
	latency_stats := make([]int64, timeout/1000/10 + 1)
	var samples []string

	report := func(t_queries int64,
		t_min_latency int64, t_max_latency int64, t_latency_stats []int64,
		t_samples []string) {

		if t_min_latency < min_latency {
			min_latency = t_min_latency
		}

		if t_max_latency > max_latency {
			max_latency = t_max_latency
		}

		for i, elem := range t_latency_stats {
			latency_stats[i] += elem
		}

		queries += t_queries
		samples = t_samples
	}

	var worker WorkerFunc

	worker = http_worker

	do_run := func(
		worker WorkerFunc,
		query string,
		query_args []string,
		concurrency int,
		run_duration time.Duration,
		report ReportFunc) time.Duration {

		var wg sync.WaitGroup
		wg.Add(concurrency)

		start := time.Now()

		for i := 0; i < concurrency; i += 1 {
			go worker(start, run_duration, timeout, query,
				query_args, &wg, report)
		}

		wg.Wait()

		return time.Since(start)
	}

	if warmup_time > 0 {
		do_run(worker, querydata.Query, querydata.Ids, *concurrency,
			warmup_time, nil)
	}

	duration = do_run(worker, querydata.Query, querydata.Ids, *concurrency,
		duration, report)

	data := make(map[string]interface{})
	data["nqueries"] = queries
	data["min_latency"] = min_latency
	data["max_latency"] = max_latency
	data["latency_stats"] = latency_stats
	data["duration"] = duration.Seconds()
	data["samples"] = samples

	json, err := json.Marshal(data)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(string(json))
}
