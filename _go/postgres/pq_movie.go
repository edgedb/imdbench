package postgres

import (
	"database/sql"
	"encoding/json"
	"log"
	"strings"
	"sync"
	"time"

	"github.com/edgedb/webapp-bench/_go/bench"
	"github.com/edgedb/webapp-bench/_go/cli"
)

type Movie struct {
	ID          int
	Image       string
	Title       string
	Year        int
	Description string
	AvgRating   float64
	Directors   []MovieQueryPerson
	Cast        []MovieQueryPerson
	Reviews     []MovieQueryReview
}

type MovieQueryPerson struct {
	ID       int
	FullName string
	Image    string
}

type MovieQueryReview struct {
	ID     int
	Body   string
	Rating int
	Author struct {
		ID    int
		Name  string
		Image string
	}
}

func execMovie(db *sql.DB, args cli.Args) bench.Exec {
	var (
		movie Movie
		wg    sync.WaitGroup
	)

	queries := strings.Split(args.Query, ";")
	m := getMovie(db, queries[0], &movie)
	d := getDirectors(db, queries[1], &movie)
	c := getCast(db, queries[2], &movie)
	r := getReviews(db, queries[3], &movie)

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

func getMovie(
	db *sql.DB,
	query string,
	movie *Movie,
) func(string, *sync.WaitGroup) {
	stmt, err := db.Prepare(query)
	if err != nil {
		log.Fatal(err)
	}

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		row := stmt.QueryRow(id)
		row.Scan(
			&movie.ID,
			&movie.Image,
			&movie.Title,
			&movie.Year,
			&movie.Description,
			&movie.AvgRating,
		)

		err := row.Err()
		if err != nil {
			log.Fatal(err)
		}
	}
}

func getDirectors(
	db *sql.DB,
	query string,
	movie *Movie,
) func(string, *sync.WaitGroup) {
	stmt, err := db.Prepare(query)
	if err != nil {
		log.Fatal(err)
	}

	var person MovieQueryPerson

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		movie.Directors = movie.Directors[:0]
		rows, err := stmt.Query(id)
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

func getCast(
	db *sql.DB,
	query string,
	movie *Movie,
) func(string, *sync.WaitGroup) {
	stmt, err := db.Prepare(query)
	if err != nil {
		log.Fatal(err)
	}

	var person MovieQueryPerson

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		movie.Cast = movie.Cast[:0]
		rows, err := stmt.Query(id)
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

func getReviews(
	db *sql.DB,
	query string,
	movie *Movie,
) func(string, *sync.WaitGroup) {
	stmt, err := db.Prepare(query)
	if err != nil {
		log.Fatal(err)
	}

	var review MovieQueryReview

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		movie.Reviews = movie.Reviews[:0]
		rows, err := stmt.Query(id)
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
