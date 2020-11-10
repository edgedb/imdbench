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

type Person struct {
	ID       int
	FullName string
	Image    string
	Bio      string
	ActedIn  []PersonQueryMovie
	Directed []PersonQueryMovie
}

type PersonQueryMovie struct {
	ID        int
	Image     string
	Title     string
	Year      int
	AvgRating float64
}

func execPerson(db *sql.DB, args cli.Args) bench.Exec {
	var (
		person Person
		wg     sync.WaitGroup
	)

	queries := strings.Split(args.Query, ";")
	p := getPerson(db, queries[0], &person)
	a := getActedIn(db, queries[1], &person)
	d := getDirected(db, queries[2], &person)

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

func getPerson(
	db *sql.DB,
	query string,
	person *Person,
) func(string, *sync.WaitGroup) {
	stmt, err := db.Prepare(query)
	if err != nil {
		log.Fatal(err)
	}

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		row := stmt.QueryRow(id)
		row.Scan(
			&person.ID,
			&person.FullName,
			&person.Image,
			&person.Bio,
		)

		err := row.Err()
		if err != nil {
			log.Fatal(err)
		}
	}
}

func getActedIn(
	db *sql.DB,
	query string,
	person *Person,
) func(string, *sync.WaitGroup) {
	stmt, err := db.Prepare(query)
	if err != nil {
		log.Fatal(err)
	}

	var movie PersonQueryMovie

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		person.ActedIn = person.ActedIn[:0]
		rows, err := stmt.Query(id)
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

func getDirected(
	db *sql.DB,
	query string,
	person *Person,
) func(string, *sync.WaitGroup) {
	stmt, err := db.Prepare(query)
	if err != nil {
		log.Fatal(err)
	}

	var movie PersonQueryMovie

	return func(id string, wg *sync.WaitGroup) {
		defer wg.Done()

		person.Directed = person.Directed[:0]
		rows, err := stmt.Query(id)
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
