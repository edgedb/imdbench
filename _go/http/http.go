package http

import (
	"encoding/json"
	"fmt"
	"log"
	"strconv"
	"time"

	"github.com/valyala/fasthttp"

	"github.com/edgedb/webapp-bench/_go/bench"
	"github.com/edgedb/webapp-bench/_go/cli"
)

func Worker(args cli.Args) (bench.Exec, bench.Close) {
	url := fmt.Sprintf("http://%s:%d%s", args.Host, args.Port, args.Path)

	client := &fasthttp.Client{}
	rsp := fasthttp.AcquireResponse()
	req := fasthttp.AcquireRequest()
	req.Header.SetMethod("POST")
	req.Header.SetContentType("application/json")
	req.SetRequestURI(url)

	var payload struct {
		Query     string                 `json:"query"`
		Variables map[string]interface{} `json:"variables"`
	}

	payload.Query = args.Query
	payload.Variables = make(map[string]interface{}, 0)

	exec := func(id string) (time.Duration, string) {
		start := time.Now()

		if args.IdsAreInts == "True" {
			var err error
			payload.Variables["id"], err = strconv.Atoi(id)
			if err != nil {
				log.Fatal(err)
			}
		} else {
			payload.Variables["id"] = id
		}

		bts, err := json.Marshal(payload)
		if err != nil {
			log.Fatal(err)
		}

		req.SetBody(bts)
		err = client.Do(req, rsp)
		if err != nil {
			log.Fatal(err)
		}

		sample := string(rsp.Body())
		return time.Since(start), sample
	}

	close := func() {
		fasthttp.ReleaseResponse(rsp)
		fasthttp.ReleaseRequest(req)
	}

	return exec, close
}
