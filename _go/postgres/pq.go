package postgres

import (
	"encoding/json"
	"log"
	"regexp"
	"strings"
	"time"

	"database/sql"

	// import used by database/sql
	_ "gopkg.in/go-on/pq.v2"

	"github.com/edgedb/webapp-bench/_go/bench"
	"github.com/edgedb/webapp-bench/_go/cli"
)

func PQWorker(args cli.Args) (bench.Exec, bench.Close) {
	db, err := sql.Open("postgres", "user=postgres_bench dbname=postgres_bench password=edgedbbenchmark")
	if err != nil {
		log.Fatal(err)
	}
	db.SetMaxIdleConns(args.Concurrency)

	regex := regexp.MustCompile(`users|movie|person`)
	queryType := regex.FindString(args.Query)

	var exec bench.Exec

	switch queryType {
	case "movie":
		exec = pqExecMovie(db, args)
	case "person":
		exec = pqExecPerson(db, args)
	case "users":
		exec = pqExecUser(db, args)
	default:
		log.Fatalf("unknown query type: %q", queryType)
	}

	close := func() {
		err := db.Close()
		if err != nil {
			log.Fatal(err)
		}
	}

	return exec, close
}

func pqExecMovie(db *sql.DB, args cli.Args) bench.Exec {
	var (
		movie    Movie
		director MovieQueryPerson
		actor    MovieQueryPerson
		review   MovieQueryReview
	)

	queries := strings.Split(args.Query, ";")

	movieStmt, err := db.Prepare(queries[0])
	if err != nil {
		log.Fatal(err)
	}

	directorsStmt, err := db.Prepare(queries[1])
	if err != nil {
		log.Fatal(err)
	}

	actorStmt, err := db.Prepare(queries[2])
	if err != nil {
		log.Fatal(err)
	}

	reviewStmt, err := db.Prepare(queries[3])
	if err != nil {
		log.Fatal(err)
	}

	return func(id string) (time.Duration, string) {
		start := time.Now()

		tx, err := db.Begin()
		if err != nil {
			log.Fatal(err)
		}
		defer tx.Rollback()

		row := tx.Stmt(movieStmt).QueryRow(id)
		row.Scan(
			&movie.ID,
			&movie.Image,
			&movie.Title,
			&movie.Year,
			&movie.Description,
			&movie.AvgRating,
		)

		err = row.Err()
		if err != nil {
			log.Fatal(err)
		}

		movie.Directors = movie.Directors[:0]
		rows, err := tx.Stmt(directorsStmt).Query(id)
		if err != nil {
			log.Fatal(err)
		}

		for rows.Next() {
			rows.Scan(
				&director.ID,
				&director.FullName,
				&director.Image,
			)
			movie.Directors = append(movie.Directors, director)
		}

		err = rows.Err()
		if err != nil {
			log.Fatal(err)
		}

		movie.Cast = movie.Cast[:0]
		rows, err = tx.Stmt(actorStmt).Query(id)
		if err != nil {
			log.Fatal(err)
		}

		for rows.Next() {
			rows.Scan(
				&actor.ID,
				&actor.FullName,
				&actor.Image,
			)
			movie.Cast = append(movie.Cast, actor)
		}

		err = rows.Err()
		if err != nil {
			log.Fatal(err)
		}

		movie.Reviews = movie.Reviews[:0]
		rows, err = tx.Stmt(reviewStmt).Query(id)
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

		serial, err := json.Marshal(movie)
		if err != nil {
			log.Fatal(err)
		}

		duration := time.Since(start)
		return duration, string(serial)
	}
}

func pqExecPerson(db *sql.DB, args cli.Args) bench.Exec {
	var (
		person   Person
		movie    PersonQueryMovie
		directed PersonQueryMovie
	)

	queries := strings.Split(args.Query, ";")

	personStmt, err := db.Prepare(queries[0])
	if err != nil {
		log.Fatal(err)
	}

	movieStmt, err := db.Prepare(queries[1])
	if err != nil {
		log.Fatal(err)
	}

	directedStmt, err := db.Prepare(queries[2])
	if err != nil {
		log.Fatal(err)
	}

	return func(id string) (time.Duration, string) {
		start := time.Now()

		tx, err := db.Begin()
		if err != nil {
			log.Fatal(err)
		}
		defer tx.Rollback()

		row := tx.Stmt(personStmt).QueryRow(id)
		row.Scan(
			&person.ID,
			&person.FullName,
			&person.Image,
			&person.Bio,
		)

		err = row.Err()
		if err != nil {
			log.Fatal(err)
		}

		person.ActedIn = person.ActedIn[:0]
		rows, err := tx.Stmt(movieStmt).Query(id)
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

		person.Directed = person.Directed[:0]
		rows, err = tx.Stmt(directedStmt).Query(id)
		if err != nil {
			log.Fatal(err)
		}

		for rows.Next() {
			rows.Scan(
				&directed.ID,
				&directed.Image,
				&directed.Title,
				&directed.Year,
				&directed.AvgRating,
			)
			person.Directed = append(person.Directed, directed)
		}

		err = rows.Err()
		if err != nil {
			log.Fatal(err)
		}

		serial, err := json.Marshal(person)
		if err != nil {
			log.Fatal(err)
		}

		duration := time.Since(start)
		return duration, string(serial)
	}
}

func pqExecUser(db *sql.DB, args cli.Args) bench.Exec {
	var (
		user   User
		review UserQueryReview
	)

	stmt, err := db.Prepare(args.Query)
	if err != nil {
		log.Fatal(err)
	}

	return func(id string) (time.Duration, string) {
		start := time.Now()

		rows, err := stmt.Query(id)
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
