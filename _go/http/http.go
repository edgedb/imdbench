package http

import (
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"strconv"
	"time"

	"github.com/valyala/fasthttp"

	"github.com/edgedb/webapp-bench/_go/bench"
	"github.com/edgedb/webapp-bench/_go/cli"
)

func processID(Vars *map[string]interface{}, key string, val string, isInt bool) {
	if isInt {
		var err error

		(*Vars)[key], err = strconv.Atoi(val)
		if err != nil {
			log.Fatal(err)
		}
	} else {
		(*Vars)[key] = val
	}
}

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

	exec := func(qargs []string) (time.Duration, string) {
		start := time.Now()

		if args.QueryName[:3] == "get" {
			// get queries only have one argument - ID
			id := qargs[0]
			processID(&payload.Variables, "id", id, args.IdsAreInts == "True")
		} else if args.QueryName == "update_movie" {
			id := qargs[0]
			processID(&payload.Variables, "id", id, args.IdsAreInts == "True")

			payload.Variables["title"] = qargs[1]
		} else if args.QueryName == "insert_user" {
			text := qargs[0]
			num := rand.Intn(1_000_000)
			payload.Variables["name"] = text + strconv.Itoa(num)
			payload.Variables["image"] = text + "image" + strconv.Itoa(num)
		} else if args.QueryName == "insert_movie" {
			text := qargs[0]
			num := rand.Intn(1_000_000)
	        payload.Variables["title"] = text + strconv.Itoa(num)
			payload.Variables["image"] = text + "image" + strconv.Itoa(num)
			payload.Variables["description"] = text + "description" + strconv.Itoa(num)
			payload.Variables["year"] = int64(num)

			processID(&payload.Variables, "did", qargs[1], args.IdsAreInts == "True")
			processID(&payload.Variables, "cid0", qargs[2], args.IdsAreInts == "True")
			processID(&payload.Variables, "cid1", qargs[3], args.IdsAreInts == "True")
			processID(&payload.Variables, "cid2", qargs[4], args.IdsAreInts == "True")
		} else if args.QueryName == "insert_movie_plus" {
			text := qargs[0]
			num := rand.Intn(1_000_000)
	        payload.Variables["title"] = text + strconv.Itoa(num)
			payload.Variables["image"] = text + "image" + strconv.Itoa(num)
			payload.Variables["description"] = text + "description" + strconv.Itoa(num)
			payload.Variables["year"] = int64(num)
	        payload.Variables["dfn"] = text + "Alice"
	        payload.Variables["dln"] = text + "Director"
	        payload.Variables["dimg"] = text + "image" + strconv.Itoa(num) + ".jpeg"
	        payload.Variables["cfn0"] = text + "Billie"
	        payload.Variables["cln0"] = text + "Actor"
	        payload.Variables["cimg0"] = text + "image" + strconv.Itoa(num + 1) + ".jpeg"
	        payload.Variables["cfn1"] = text + "Cameron"
	        payload.Variables["cln1"] = text + "Actor"
	        payload.Variables["cimg1"] = text + "image" + strconv.Itoa(num + 2) + ".jpeg"
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
