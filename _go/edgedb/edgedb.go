package edgedb

import (
	"context"
	"encoding/json"
	"log"
	"regexp"
	"time"

	"github.com/edgedb/edgedb-go/edgedb"
	"github.com/edgedb/edgedb-go/edgedb/types"

	"github.com/edgedb/webapp-bench/_go/bench"
	"github.com/edgedb/webapp-bench/_go/cli"
)

type User struct {
	ID            types.UUID `json:"id" edgedb:"id"`
	Name          string     `json:"name" edgedb:"name"`
	Image         string     `json:"image" edgedb:"image"`
	LatestReviews []Review   `json:"latest_reviews" edgedb:"latest_reviews"`
}

type Movie struct {
	ID          types.UUID `json:"id" edgedb:"id"`
	Image       string     `json:"image" edgedb:"image"`
	Title       string     `json:"title" edgedb:"title"`
	Year        int64      `json:"year" edgedb:"year"`
	Description string     `json:"description" edgedb:"description"`
	AvgRating   float64    `json:"avg_rating" edgedb:"avg_rating"`
	Directors   []Person   `json:"directors" edgedb:"directors"`
	Cast        []Person   `json:"cast" edgedb:"cast"`
	Reviews     []Review   `json:"reviews" edgedb:"reviews"`
}

type Person struct {
	ID       types.UUID `json:"id" edgedb:"id"`
	FullName string     `json:"full_name" edgedb:"full_name"`
	Image    string     `json:"image" edgedb:"image"`
	Bio      string     `json:"bio" edgedb:"bio"`
	ActedIn  []Movie    `json:"acted_in" edgedb:"acted_in"`
	Directed []Movie    `json:"directed" edgedb:"directed"`
}

type Review struct {
	ID     types.UUID `json:"id" edgedb:"id"`
	Body   string     `json:"body" edgedb:"body"`
	Rating int64      `json:"rating" edgedb:"rating"`
	Movie  Movie      `json:"movie" edgedb:"movie"`
	Author User       `json:"author" edgedb:"author"`
}

func RepackWorker(args cli.Args) (exec bench.Exec, close bench.Close) {
	ctx := context.TODO()
	client, err := edgedb.Connect(ctx, edgedb.Options{
		Host:     args.Host,
		Port:     args.Port,
		User:     "edgedb",
		Database: "edgedb_bench",
	})
	if err != nil {
		log.Fatal(err)
	}

	regex := regexp.MustCompile(`Person|Movie|User`)
	queryType := regex.FindString(args.Query)

	switch queryType {
	case "Person":
		exec = execPerson(client, args)
	case "Movie":
		exec = execMovie(client, args)
	case "User":
		exec = execUser(client, args)
	default:
		log.Fatalf("unknown query type %q", queryType)
	}

	close = func() {
		err := client.Close()
		if err != nil {
			log.Fatal(err)
		}
	}

	return exec, close
}

func execPerson(client *edgedb.Client, args cli.Args) bench.Exec {

	var person Person
	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	return func(id string) (time.Duration, string) {
		var err error
		params["id"], err = types.UUIDFromString(id)
		if err != nil {
			log.Fatal(err)
		}

		start := time.Now()
		err = client.QueryOne(ctx, args.Query, &person, params)
		if err != nil {
			log.Fatal(err)
		}

		bts, err := json.Marshal(person)
		if err != nil {
			log.Fatal(err)
		}
		duration := time.Since(start)

		return duration, string(bts)
	}
}

func execMovie(client *edgedb.Client, args cli.Args) bench.Exec {

	var movie Movie
	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	return func(id string) (time.Duration, string) {
		var err error
		params["id"], err = types.UUIDFromString(id)
		if err != nil {
			log.Fatal(err)
		}

		start := time.Now()
		err = client.QueryOne(ctx, args.Query, &movie, params)
		if err != nil {
			log.Fatal(err)
		}

		bts, err := json.Marshal(movie)
		if err != nil {
			log.Fatal(err)
		}
		duration := time.Since(start)

		return duration, string(bts)
	}
}

func execUser(client *edgedb.Client, args cli.Args) bench.Exec {

	var user User
	ctx := context.TODO()
	params := make(map[string]interface{}, 1)

	return func(id string) (time.Duration, string) {
		var err error
		params["id"], err = types.UUIDFromString(id)
		if err != nil {
			log.Fatal(err)
		}

		start := time.Now()
		err = client.QueryOne(ctx, args.Query, &user, params)
		if err != nil {
			log.Fatal(err)
		}

		bts, err := json.Marshal(user)
		if err != nil {
			log.Fatal(err)
		}
		duration := time.Since(start)

		return duration, string(bts)
	}
}

func JSONWorker(args cli.Args) (bench.Exec, bench.Close) {
	ctx := context.TODO()
	client, err := edgedb.Connect(ctx, edgedb.Options{
		Host:     args.Host,
		Port:     args.Port,
		User:     "edgedb",
		Database: "edgedb_bench",
	})
	if err != nil {
		log.Fatal(err)
	}

	params := make(map[string]interface{}, 1)

	exec := func(id string) (time.Duration, string) {
		params["id"], err = types.UUIDFromString(id)
		if err != nil {
			log.Fatal(err)
		}

		start := time.Now()
		rsp, err := client.QueryOneJSON(ctx, args.Query, params)
		duration := time.Since(start)

		if err != nil {
			log.Fatal(err)
		}

		return duration, string(rsp)
	}

	close := func() {
		err := client.Close()
		if err != nil {
			log.Fatal(err)
		}
	}

	return exec, close
}
