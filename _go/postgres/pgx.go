package postgres

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/edgedb/webapp-bench/_go/bench"
	"github.com/edgedb/webapp-bench/_go/cli"
	"github.com/jackc/pgx/v4/pgxpool"
)

func PGXWorker(args cli.Args) (bench.Exec, bench.Close) {
	url := fmt.Sprintf(
		"postgresql://postgres_bench:edgedbbenchmark@%v:%v/postgres_bench",
		args.Host,
		args.Port,
	)

	pool, err := pgxpool.Connect(context.TODO(), url)
	if err != nil {
		log.Fatal(err)
	}

	regex := regexp.MustCompile(`users|movie|person`)
	queryType := regex.FindString(args.Query)

	var exec bench.Exec
	switch queryType {
	case "movie":
		exec = pgxExecMovie(pool, args)
	case "person":
		exec = pgxExecPerson(pool, args)
	case "users":
		exec = pgxExecUser(pool, args)
	default:
		log.Fatalf("unknown query type: %q", queryType)
	}

	return exec, pool.Close
}

func pgxExecMovie(pool *pgxpool.Pool, args cli.Args) bench.Exec {
	var (
		movie Movie
		wg    sync.WaitGroup
	)

	queries := strings.Split(args.Query, ";")
	m := pgxGetMovie(pool, queries[0], &movie)
	d := pgxGetDirectors(pool, queries[1], &movie)
	c := pgxGetCast(pool, queries[2], &movie)
	r := pgxGetReviews(pool, queries[3], &movie)

	return func(id string) (time.Duration, string) {
		wg.Add(4)
		start := time.Now()
		go m(id, &wg)
		go d(id, &wg)
		go c(id, &wg)
		go r(id, &wg)
		wg.Wait()

		serial, err := json.Marshal(movie)
		if err != nil {
			log.Fatal(err)
		}

		duration := time.Since(start)
		return duration, string(serial)
	}
}

func pgxGetMovie(
	pool *pgxpool.Pool,
	query string,
	movie *Movie,
) func(string, *sync.WaitGroup) {
	ctx := context.TODO()

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		row := pool.QueryRow(ctx, query, id)
		err := row.Scan(
			&movie.ID,
			&movie.Image,
			&movie.Title,
			&movie.Year,
			&movie.Description,
			&movie.AvgRating,
		)
		if err != nil {
			log.Fatal(err)
		}
	}
}

func pgxGetDirectors(
	pool *pgxpool.Pool,
	query string,
	movie *Movie,
) func(string, *sync.WaitGroup) {
	ctx := context.TODO()
	var person MovieQueryPerson

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		movie.Directors = movie.Directors[:0]
		rows, err := pool.Query(ctx, query, id)
		if err != nil {
			log.Fatal(err)
		}

		for rows.Next() {
			rows.Scan(
				&person.ID,
				&person.FullName,
				&person.Image,
			)
			movie.Directors = append(movie.Directors, person)
		}

		err = rows.Err()
		if err != nil {
			log.Fatal(err)
		}
	}
}

func pgxGetCast(
	pool *pgxpool.Pool,
	query string,
	movie *Movie,
) func(string, *sync.WaitGroup) {
	ctx := context.TODO()
	var person MovieQueryPerson

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		movie.Cast = movie.Cast[:0]
		rows, err := pool.Query(ctx, query, id)
		if err != nil {
			log.Fatal(err)
		}

		for rows.Next() {
			rows.Scan(
				&person.ID,
				&person.FullName,
				&person.Image,
			)
			movie.Cast = append(movie.Cast, person)
		}

		err = rows.Err()
		if err != nil {
			log.Fatal(err)
		}
	}
}

func pgxGetReviews(
	pool *pgxpool.Pool,
	query string,
	movie *Movie,
) func(string, *sync.WaitGroup) {
	ctx := context.TODO()
	var review MovieQueryReview

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		movie.Reviews = movie.Reviews[:0]
		rows, err := pool.Query(ctx, query, id)
		if err != nil {
			log.Fatal(err)
		}

		for rows.Next() {
			rows.Scan(
				&review.ID,
				&review.Body,
				&review.Rating,
				&review.Author.ID,
				&review.Author.Name,
				&review.Author.Image,
			)
			movie.Reviews = append(movie.Reviews, review)
		}

		err = rows.Err()
		if err != nil {
			log.Fatal(err)
		}
	}
}

func pgxExecPerson(pool *pgxpool.Pool, args cli.Args) bench.Exec {
	var (
		person Person
		wg     sync.WaitGroup
	)

	queries := strings.Split(args.Query, ";")
	p := pgxGetPerson(pool, queries[0], &person)
	a := pgxGetActedIn(pool, queries[1], &person)
	d := pgxGetDirected(pool, queries[2], &person)

	return func(id string) (time.Duration, string) {
		wg.Add(3)
		start := time.Now()
		go p(id, &wg)
		go a(id, &wg)
		go d(id, &wg)
		wg.Wait()

		serial, err := json.Marshal(person)
		if err != nil {
			log.Fatal(err)
		}

		duration := time.Since(start)
		return duration, string(serial)
	}
}

func pgxGetPerson(
	pool *pgxpool.Pool,
	query string,
	person *Person,
) func(string, *sync.WaitGroup) {
	ctx := context.TODO()

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		row := pool.QueryRow(ctx, query, id)
		err := row.Scan(
			&person.ID,
			&person.FullName,
			&person.Image,
			&person.Bio,
		)
		if err != nil {
			log.Fatal(err)
		}
	}
}

func pgxGetActedIn(
	pool *pgxpool.Pool,
	query string,
	person *Person,
) func(string, *sync.WaitGroup) {
	ctx := context.TODO()
	var movie PersonQueryMovie

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		person.ActedIn = person.ActedIn[:0]
		rows, err := pool.Query(ctx, query, id)
		if err != nil {
			log.Fatal(err)
		}

		for rows.Next() {
			rows.Scan(
				&movie.ID,
				&movie.Image,
				&movie.Title,
				&movie.Year,
				&movie.AvgRating,
			)
			person.ActedIn = append(person.ActedIn, movie)
		}

		err = rows.Err()
		if err != nil {
			log.Fatal(err)
		}
	}
}

func pgxGetDirected(
	pool *pgxpool.Pool,
	query string,
	person *Person,
) func(string, *sync.WaitGroup) {
	ctx := context.TODO()
	var movie PersonQueryMovie

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		person.Directed = person.Directed[:0]
		rows, err := pool.Query(ctx, query, id)
		if err != nil {
			log.Fatal(err)
		}

		for rows.Next() {
			rows.Scan(
				&movie.ID,
				&movie.Image,
				&movie.Title,
				&movie.Year,
				&movie.AvgRating,
			)
			person.Directed = append(person.Directed, movie)
		}

		err = rows.Err()
		if err != nil {
			log.Fatal(err)
		}
	}
}

func pgxExecUser(pool *pgxpool.Pool, args cli.Args) bench.Exec {
	var (
		user   User
		review UserQueryReview
		ctx    context.Context = context.TODO()
	)

	return func(id string) (time.Duration, string) {
		start := time.Now()

		rows, err := pool.Query(ctx, args.Query, id)
		if err != nil {
			log.Fatal(err)
		}

		user.LatestReviews = user.LatestReviews[:0]
		for rows.Next() {
			rows.Scan(
				&user.ID,
				&user.Name,
				&user.Image,
				&review.ID,
				&review.Body,
				&review.Rating,
				&review.Movie.ID,
				&review.Movie.Image,
				&review.Movie.Title,
				&review.Movie.AvgRating,
			)

			user.LatestReviews = append(user.LatestReviews, review)
		}

		serial, err := json.Marshal(user)
		if err != nil {
			log.Fatal(err)
		}

		duration := time.Since(start)
		return duration, string(serial)
	}
}
