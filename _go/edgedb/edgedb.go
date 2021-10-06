package edgedb

import (
	"context"
	"encoding/json"
	"log"
	"regexp"
	"time"

	"github.com/edgedb/edgedb-go"

	"github.com/edgedb/webapp-bench/_go/bench"
	"github.com/edgedb/webapp-bench/_go/cli"
)

type User struct {
	ID            edgedb.UUID `json:"id" edgedb:"id"`
	Name          string     `json:"name" edgedb:"name"`
	Image         string     `json:"image" edgedb:"image"`
	LatestReviews []UReview   `json:"latest_reviews" edgedb:"latest_reviews"`
}

type UReview struct {
	ID     edgedb.UUID `json:"id" edgedb:"id"`
	Body   string     `json:"body" edgedb:"body"`
	Rating int64      `json:"rating" edgedb:"rating"`
	Movie  RMovie      `json:"movie" edgedb:"movie"`
}

type RMovie struct {
	ID          edgedb.UUID `json:"id" edgedb:"id"`
	Image       string     `json:"image" edgedb:"image"`
	Title       string     `json:"title" edgedb:"title"`
	AvgRating   float64    `json:"avg_rating" edgedb:"avg_rating"`
}

type Movie struct {
	ID          edgedb.UUID `json:"id" edgedb:"id"`
	Image       string     `json:"image" edgedb:"image"`
	Title       string     `json:"title" edgedb:"title"`
	Year        int64      `json:"year" edgedb:"year"`
	Description string     `json:"description" edgedb:"description"`
	AvgRating   float64    `json:"avg_rating" edgedb:"avg_rating"`
	Directors   []MPerson   `json:"directors" edgedb:"directors"`
	Cast        []MPerson   `json:"cast" edgedb:"cast"`
	Reviews     []MReview   `json:"reviews" edgedb:"reviews"`
}

type MPerson struct {
	ID       edgedb.UUID `json:"id" edgedb:"id"`
	FullName string     `json:"full_name" edgedb:"full_name"`
	Image    string     `json:"image" edgedb:"image"`
}

type MReview struct {
	ID     edgedb.UUID `json:"id" edgedb:"id"`
	Body   string     `json:"body" edgedb:"body"`
	Rating int64      `json:"rating" edgedb:"rating"`
	Author RUser       `json:"author" edgedb:"author"`
}

type RUser struct {
	ID            edgedb.UUID `json:"id" edgedb:"id"`
	Name          string     `json:"name" edgedb:"name"`
	Image         string     `json:"image" edgedb:"image"`
}

type Person struct {
	ID       edgedb.UUID `json:"id" edgedb:"id"`
	FullName string     `json:"full_name" edgedb:"full_name"`
	Image    string     `json:"image" edgedb:"image"`
	Bio      edgedb.OptionalStr     `json:"bio" edgedb:"bio"`
	ActedIn  []PMovie    `json:"acted_in" edgedb:"acted_in"`
	Directed []PMovie    `json:"directed" edgedb:"directed"`
}

type PMovie struct {
	ID          edgedb.UUID `json:"id" edgedb:"id"`
	Image       string     `json:"image" edgedb:"image"`
	Title       string     `json:"title" edgedb:"title"`
	Year        int64      `json:"year" edgedb:"year"`
	AvgRating   float64    `json:"avg_rating" edgedb:"avg_rating"`
}

func RepackWorker(args cli.Args) (exec bench.Exec, close bench.Close) {
	ctx := context.TODO()
	pool, err := edgedb.ConnectDSN(ctx, "edgedb_bench", edgedb.Options{})
	if err != nil {
		log.Fatal(err)
	}

	regex := regexp.MustCompile(`Person|Movie|User`)
	queryType := regex.FindString(args.Query)

	switch queryType {
	case "Person":
		exec = execPerson(pool, args)
	case "Movie":
		exec = execMovie(pool, args)
	case "User":
		exec = execUser(pool, args)
	default:
		log.Fatalf("unknown query type %q", queryType)
	}

	close = func() {
		err := pool.Close()
		if err != nil {
			log.Fatal(err)
		}
	}

	return exec, close
}

func execPerson(pool *edgedb.Pool, args cli.Args) bench.Exec {
	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	var (
		person   Person
		start    time.Time
		duration time.Duration
		err      error
		bts      []byte
	)

	return func(id string) (time.Duration, string) {
		params["id"], err = edgedb.ParseUUID(id)
		if err != nil {
			log.Fatal(err)
		}

		start = time.Now()
		err = pool.QueryOne(ctx, args.Query, &person, params)
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

func execMovie(pool *edgedb.Pool, args cli.Args) bench.Exec {
	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	var (
		movie    Movie
		start    time.Time
		duration time.Duration
		err      error
		bts      []byte
	)

	return func(id string) (time.Duration, string) {
		params["id"], err = edgedb.ParseUUID(id)
		if err != nil {
			log.Fatal(err)
		}

		start = time.Now()
		err = pool.QueryOne(ctx, args.Query, &movie, params)
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

func execUser(pool *edgedb.Pool, args cli.Args) bench.Exec {

	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	var (
		user     User
		start    time.Time
		duration time.Duration
		err      error
		bts      []byte
	)

	return func(id string) (time.Duration, string) {
		params["id"], err = edgedb.ParseUUID(id)
		if err != nil {
			log.Fatal(err)
		}

		start = time.Now()
		err = pool.QueryOne(ctx, args.Query, &user, params)
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

func JSONWorker(args cli.Args) (bench.Exec, bench.Close) {
	ctx := context.TODO()
	pool, err := edgedb.ConnectDSN(ctx, "edgedb_bench", edgedb.Options{})
	if err != nil {
		log.Fatal(err)
	}

	params := make(map[string]interface{}, 1)

	var (
		rsp      []byte
		start    time.Time
		duration time.Duration
	)

	exec := func(id string) (time.Duration, string) {
		params["id"], err = edgedb.ParseUUID(id)
		if err != nil {
			log.Fatal(err)
		}

		start = time.Now()
		err = pool.QueryOneJSON(ctx, args.Query, &rsp, params)
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
