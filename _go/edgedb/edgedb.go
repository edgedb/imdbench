package edgedb

import (
	"context"
	"encoding/json"
	"log"
	"math/rand"
	"strconv"
	"time"

	"github.com/edgedb/edgedb-go"

	"github.com/edgedb/webapp-bench/_go/bench"
	"github.com/edgedb/webapp-bench/_go/cli"
)

type User struct {
	ID            edgedb.UUID `json:"id" edgedb:"id"`
	Name          string      `json:"name" edgedb:"name"`
	Image         string      `json:"image" edgedb:"image"`
	LatestReviews []UReview   `json:"latest_reviews" edgedb:"latest_reviews"`
}

type UReview struct {
	ID     edgedb.UUID `json:"id" edgedb:"id"`
	Body   string      `json:"body" edgedb:"body"`
	Rating int64       `json:"rating" edgedb:"rating"`
	Movie  RMovie      `json:"movie" edgedb:"movie"`
}

type RMovie struct {
	ID        edgedb.UUID `json:"id" edgedb:"id"`
	Image     string      `json:"image" edgedb:"image"`
	Title     string      `json:"title" edgedb:"title"`
	AvgRating float64     `json:"avg_rating" edgedb:"avg_rating"`
}

type Movie struct {
	ID          edgedb.UUID `json:"id" edgedb:"id"`
	Image       string      `json:"image" edgedb:"image"`
	Title       string      `json:"title" edgedb:"title"`
	Year        int64       `json:"year" edgedb:"year"`
	Description string      `json:"description" edgedb:"description"`
	AvgRating   float64     `json:"avg_rating" edgedb:"avg_rating"`
	Directors   []MPerson   `json:"directors" edgedb:"directors"`
	Cast        []MPerson   `json:"cast" edgedb:"cast"`
	Reviews     []MReview   `json:"reviews" edgedb:"reviews"`
}

type MPerson struct {
	ID       edgedb.UUID `json:"id" edgedb:"id"`
	FullName string      `json:"full_name" edgedb:"full_name"`
	Image    string      `json:"image" edgedb:"image"`
}

type MReview struct {
	ID     edgedb.UUID `json:"id" edgedb:"id"`
	Body   string      `json:"body" edgedb:"body"`
	Rating int64       `json:"rating" edgedb:"rating"`
	Author RUser       `json:"author" edgedb:"author"`
}

type RUser struct {
	ID    edgedb.UUID `json:"id" edgedb:"id"`
	Name  string      `json:"name" edgedb:"name"`
	Image string      `json:"image" edgedb:"image"`
}

type Person struct {
	ID       edgedb.UUID        `json:"id" edgedb:"id"`
	FullName string             `json:"full_name" edgedb:"full_name"`
	Image    string             `json:"image" edgedb:"image"`
	Bio      edgedb.OptionalStr `json:"bio" edgedb:"bio"`
	ActedIn  []PMovie           `json:"acted_in" edgedb:"acted_in"`
	Directed []PMovie           `json:"directed" edgedb:"directed"`
}

type PMovie struct {
	ID        edgedb.UUID `json:"id" edgedb:"id"`
	Image     string      `json:"image" edgedb:"image"`
	Title     string      `json:"title" edgedb:"title"`
	Year      int64       `json:"year" edgedb:"year"`
	AvgRating float64     `json:"avg_rating" edgedb:"avg_rating"`
}

func RepackWorker(args cli.Args) (exec bench.Exec, close bench.Close) {
	ctx := context.TODO()
	pool, err := edgedb.CreateClient(ctx, edgedb.Options{Concurrency: 1})
	if err != nil {
		log.Fatal(err)
	}

	switch args.QueryName {
	case "get_movie":
		exec = execMovie(pool, args)
	case "get_person":
		exec = execPerson(pool, args)
	case "get_user":
		exec = execUser(pool, args)
	case "update_movie":
		exec = updateMovie(pool, args)
	case "insert_user":
		exec = insertUser(pool, args)
	case "insert_movie":
		exec = insertMovie(pool, args)
	case "insert_movie_plus":
		exec = insertMoviePlus(pool, args)
	default:
		log.Fatalf("unknown query type: %q", args.QueryName)
	}

	close = func() {
		err := pool.Close()
		if err != nil {
			log.Fatal(err)
		}
	}

	return exec, close
}

func execPerson(pool *edgedb.Client, args cli.Args) bench.Exec {
	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	var (
		person   Person
		start    time.Time
		duration time.Duration
		err      error
		bts      []byte
	)

	return func(qargs []string) (time.Duration, string) {
		id := qargs[0]
		params["id"], err = edgedb.ParseUUID(id)
		if err != nil {
			log.Fatal(err)
		}

		start = time.Now()
		err = pool.QuerySingle(ctx, args.Query, &person, params)
		if err != nil {
			log.Fatal(err)
		}

		bts, err = json.Marshal(person)
		if err != nil {
			log.Fatal(err)
		}
		duration = time.Since(start)

		return duration, string(bts)
	}
}

func execMovie(pool *edgedb.Client, args cli.Args) bench.Exec {
	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	var (
		movie    Movie
		start    time.Time
		duration time.Duration
		err      error
		bts      []byte
	)

	return func(qargs []string) (time.Duration, string) {
		id := qargs[0]
		params["id"], err = edgedb.ParseUUID(id)
		if err != nil {
			log.Fatal(err)
		}

		start = time.Now()
		err = pool.QuerySingle(ctx, args.Query, &movie, params)
		if err != nil {
			log.Fatal(err)
		}

		bts, err = json.Marshal(movie)
		if err != nil {
			log.Fatal(err)
		}
		duration = time.Since(start)

		return duration, string(bts)
	}
}

func execUser(pool *edgedb.Client, args cli.Args) bench.Exec {
	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	var (
		user     User
		start    time.Time
		duration time.Duration
		err      error
		bts      []byte
	)

	return func(qargs []string) (time.Duration, string) {
		id := qargs[0]
		params["id"], err = edgedb.ParseUUID(id)
		if err != nil {
			log.Fatal(err)
		}

		start = time.Now()
		err = pool.QuerySingle(ctx, args.Query, &user, params)
		if err != nil {
			log.Fatal(err)
		}

		bts, err = json.Marshal(user)
		if err != nil {
			log.Fatal(err)
		}
		duration = time.Since(start)

		return duration, string(bts)
	}
}

func updateMovie(pool *edgedb.Client, args cli.Args) bench.Exec {
	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	var (
		movie    RMovie
		start    time.Time
		duration time.Duration
		err      error
		bts      []byte
	)

	return func(qargs []string) (time.Duration, string) {
		id := qargs[0]
		params["id"], err = edgedb.ParseUUID(id)
		if err != nil {
			log.Fatal(err)
		}

		start = time.Now()
		err = pool.QuerySingle(ctx, args.Query, &movie, params)
		if err != nil {
			log.Fatal(err)
		}

		bts, err = json.Marshal(movie)
		if err != nil {
			log.Fatal(err)
		}
		duration = time.Since(start)

		return duration, string(bts)
	}
}

func insertUser(pool *edgedb.Client, args cli.Args) bench.Exec {
	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	var (
		user     RUser
		start    time.Time
		duration time.Duration
		err      error
		bts      []byte
	)

	return func(qargs []string) (time.Duration, string) {
		text := qargs[0]
		num := rand.Intn(1_000_000)
		params["name"] = text + strconv.Itoa(num)
		params["image"] = "image_" + text + strconv.Itoa(num)

		start = time.Now()
		err = pool.QuerySingle(ctx, args.Query, &user, params)
		if err != nil {
			log.Fatal(err)
		}

		bts, err = json.Marshal(user)
		if err != nil {
			log.Fatal(err)
		}
		duration = time.Since(start)

		return duration, string(bts)
	}
}

func insertMovie(pool *edgedb.Client, args cli.Args) bench.Exec {
	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	var (
		movie    Movie
		start    time.Time
		duration time.Duration
		err      error
		bts      []byte
	)

	return func(qargs []string) (time.Duration, string) {
		text := qargs[0]
		num := rand.Intn(1_000_000)
        params["title"] = text + strconv.Itoa(num)
		params["image"] = text + "image" + strconv.Itoa(num)
		params["description"] = text + "description" + strconv.Itoa(num)
		params["year"] = int64(num)

		params["did"], err = edgedb.ParseUUID(qargs[1])
		if err != nil {
			log.Fatal(err)
		}
		params["cid0"], err = edgedb.ParseUUID(qargs[2])
		if err != nil {
			log.Fatal(err)
		}
		params["cid1"], err = edgedb.ParseUUID(qargs[3])
		if err != nil {
			log.Fatal(err)
		}
		params["cid2"], err = edgedb.ParseUUID(qargs[4])
		if err != nil {
			log.Fatal(err)
		}

		start = time.Now()
		err = pool.QuerySingle(ctx, args.Query, &movie, params)
		if err != nil {
			log.Fatal(err)
		}

		bts, err = json.Marshal(movie)
		if err != nil {
			log.Fatal(err)
		}
		duration = time.Since(start)

		return duration, string(bts)
	}
}

func insertMoviePlus(pool *edgedb.Client, args cli.Args) bench.Exec {
	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	var (
		movie    Movie
		start    time.Time
		duration time.Duration
		err      error
		bts      []byte
	)

	return func(qargs []string) (time.Duration, string) {
		text := qargs[0]
		num := rand.Intn(1_000_000)
        params["title"] = text + strconv.Itoa(num)
		params["image"] = text + "image" + strconv.Itoa(num)
		params["description"] = text + "description" + strconv.Itoa(num)
		params["year"] = int64(num)
        params["dfn"] = text + "Alice"
        params["dln"] = text + "Director"
        params["dimg"] = text + "image" + strconv.Itoa(num) + ".jpeg"
        params["cfn0"] = text + "Billie"
        params["cln0"] = text + "Actor"
        params["cimg0"] = text + "image" + strconv.Itoa(num + 1) + ".jpeg"
        params["cfn1"] = text + "Cameron"
        params["cln1"] = text + "Actor"
        params["cimg1"] = text + "image" + strconv.Itoa(num + 2) + ".jpeg"

		start = time.Now()
		err = pool.QuerySingle(ctx, args.Query, &movie, params)
		if err != nil {
			log.Fatal(err)
		}

		bts, err = json.Marshal(movie)
		if err != nil {
			log.Fatal(err)
		}
		duration = time.Since(start)

		return duration, string(bts)
	}
}

func JSONWorker(args cli.Args) (bench.Exec, bench.Close) {
	ctx := context.TODO()
	pool, err := edgedb.CreateClient(ctx, edgedb.Options{Concurrency: 1})
	if err != nil {
		log.Fatal(err)
	}

	params := make(map[string]interface{}, 1)

	var (
		rsp      []byte
		start    time.Time
		duration time.Duration
	)

	exec := func(qargs []string) (time.Duration, string) {
		if args.QueryName[:3] == "get" {
			// get queries only have one argument - ID
			params["id"], err = edgedb.ParseUUID(qargs[0])
			if err != nil {
				log.Fatal(err)
			}
		} else if args.QueryName == "update_movie" {
			params["id"], err = edgedb.ParseUUID(qargs[0])
			if err != nil {
				log.Fatal(err)
			}
		} else if args.QueryName == "insert_user" {
			// need to add more variables for the query
			text := qargs[0]
			num := rand.Intn(1_000_000)
			params["name"] = text + strconv.Itoa(num)
			params["image"] = "image_" + text + strconv.Itoa(num)
		} else if args.QueryName == "insert_movie" {
			text := qargs[0]
			num := rand.Intn(1_000_000)
	        params["title"] = text + strconv.Itoa(num)
			params["image"] = text + "image" + strconv.Itoa(num)
			params["description"] = text + "description" + strconv.Itoa(num)
			params["year"] = int64(num)

			params["did"], err = edgedb.ParseUUID(qargs[1])
			if err != nil {
				log.Fatal(err)
			}
			params["cid0"], err = edgedb.ParseUUID(qargs[2])
			if err != nil {
				log.Fatal(err)
			}
			params["cid1"], err = edgedb.ParseUUID(qargs[3])
			if err != nil {
				log.Fatal(err)
			}
			params["cid2"], err = edgedb.ParseUUID(qargs[4])
			if err != nil {
				log.Fatal(err)
			}
		} else if args.QueryName == "insert_movie_plus" {
			text := qargs[0]
			num := rand.Intn(1_000_000)
	        params["title"] = text + strconv.Itoa(num)
			params["image"] = text + "image" + strconv.Itoa(num)
			params["description"] = text + "description" + strconv.Itoa(num)
			params["year"] = int64(num)
	        params["dfn"] = text + "Alice"
	        params["dln"] = text + "Director"
	        params["dimg"] = text + "image" + strconv.Itoa(num) + ".jpeg"
	        params["cfn0"] = text + "Billie"
	        params["cln0"] = text + "Actor"
	        params["cimg0"] = text + "image" + strconv.Itoa(num + 1) + ".jpeg"
	        params["cfn1"] = text + "Cameron"
	        params["cln1"] = text + "Actor"
	        params["cimg1"] = text + "image" + strconv.Itoa(num + 2) + ".jpeg"
		}

		start = time.Now()
		err = pool.QuerySingleJSON(ctx, args.Query, &rsp, params)
		duration = time.Since(start)

		if err != nil {
			log.Fatal(err)
		}

		return duration, string(rsp)
	}

	close := func() {
		err := pool.Close()
		if err != nil {
			log.Fatal(err)
		}
	}

	return exec, close
}
