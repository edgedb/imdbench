package postgres

import (
	"encoding/json"
	"log"
	"math/rand"
	"strconv"
	"strings"
	"time"

	"database/sql"

	// import used by database/sql
	_ "gopkg.in/go-on/pq.v2"

	"github.com/edgedb/webapp-bench/_go/bench"
	"github.com/edgedb/webapp-bench/_go/cli"
)

func PQWorker(args cli.Args) (bench.Exec, bench.Close) {
	db, err := sql.Open("postgres", "user=postgres_bench dbname=postgres_bench password=edgedbbenchmark sslmode=disable")
	if err != nil {
		log.Fatal(err)
	}
	db.SetMaxIdleConns(args.Concurrency)

	var exec bench.Exec

	switch args.QueryName {
	case "get_movie":
		exec = pqExecMovie(db, args)
	case "get_person":
		exec = pqExecPerson(db, args)
	case "get_user":
		exec = pqExecUser(db, args)
	case "update_movie":
		exec = pqUpdateMovie(db, args)
	case "insert_user":
		exec = pqInsertUser(db, args)
	case "insert_movie":
		exec = pqInsertMovie(db, args)
	case "insert_movie_plus":
		exec = pqInsertMoviePlus(db, args)
	default:
		log.Fatalf("unknown query type: %q", args.QueryName)
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

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		id := qargs[0]

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

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		id := qargs[0]

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

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		id := qargs[0]

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

func pqUpdateMovie(db *sql.DB, args cli.Args) bench.Exec {
	var (
		movie    PersonQueryMovie
	)

	stmt, err := db.Prepare(args.Query)
	if err != nil {
		log.Fatal(err)
	}

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		id := qargs[0]

		rows, err := stmt.Query(id, "---" + id)
		if err != nil {
			log.Fatal(err)
		}

		for rows.Next() {
			rows.Scan(
				&movie.ID,
				&movie.Title,
			)
		}

		serial, err := json.Marshal(movie)
		if err != nil {
			log.Fatal(err)
		}

		duration := time.Since(start)
		return duration, string(serial)
	}
}

func pqInsertUser(db *sql.DB, args cli.Args) bench.Exec {
	var (
		user   User
	)

	stmt, err := db.Prepare(args.Query)
	if err != nil {
		log.Fatal(err)
	}

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		text := qargs[0]
		num := rand.Intn(1_000_000)
		name := text + strconv.Itoa(num)
		image := text + "image" + strconv.Itoa(num)

		rows, err := stmt.Query(name, image)
		if err != nil {
			log.Fatal(err)
		}

		for rows.Next() {
			rows.Scan(
				&user.ID,
				&user.Name,
				&user.Image,
			)
		}

		serial, err := json.Marshal(user)
		if err != nil {
			log.Fatal(err)
		}

		duration := time.Since(start)
		return duration, string(serial)
	}
}

func pqInsertMovie(db *sql.DB, args cli.Args) bench.Exec {
	var (
		movie    Movie
		person 	 MovieQueryPerson
	)

	queries := strings.Split(args.Query, ";")

	movieStmt, err := db.Prepare(queries[0])
	if err != nil {
		log.Fatal(err)
	}

	peopleStmt, err := db.Prepare(queries[1])
	if err != nil {
		log.Fatal(err)
	}

	directorsStmt, err := db.Prepare(queries[2])
	if err != nil {
		log.Fatal(err)
	}

	actorStmt, err := db.Prepare(queries[3])
	if err != nil {
		log.Fatal(err)
	}

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		prefix := qargs[0]
		num := rand.Intn(1_000_000)
		title := prefix + strconv.Itoa(num)
		image := prefix + "image" + strconv.Itoa(num)
        description := prefix + "description" + strconv.Itoa(num)
		dirID, err := strconv.Atoi(qargs[1])
	    if err != nil {
			log.Fatal(err)
	    }

		tx, err := db.Begin()
		if err != nil {
			log.Fatal(err)
		}
		defer tx.Commit()

		// create the movie
		mrows, err := tx.Stmt(movieStmt).Query(title, image, description, num)
		if err != nil {
			log.Fatal(err)
		}

		for mrows.Next() {
			mrows.Scan(
				&movie.ID,
				&movie.Image,
				&movie.Title,
				&movie.Year,
				&movie.Description,
			)
		}
		movie.Directors = movie.Directors[:0]
		movie.Cast = movie.Cast[:0]

		// get the people to be used as directors and cast
		prows, err := tx.Stmt(peopleStmt).Query(qargs[1], qargs[2], qargs[3], qargs[4])
		err = prows.Err()
		if err != nil {
			log.Fatal(err)
		}

		// add the people as directors or cast
		for prows.Next() {
			prows.Scan(
				&person.ID,
				&person.FullName,
				&person.Image,
			)
			if person.ID == dirID {
				movie.Directors = append(movie.Directors, person)
			} else {
				movie.Cast = append(movie.Cast, person)
			}
		}

		// create actual directors and actors entries
		_, err = tx.Stmt(directorsStmt).Exec(movie.Directors[0].ID, movie.ID)
		if err != nil {
			log.Fatal(err)
		}
		_, err = tx.Stmt(actorStmt).Exec(movie.Cast[0].ID, movie.Cast[1].ID, movie.Cast[2].ID, movie.ID)
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

func pqInsertMoviePlus(db *sql.DB, args cli.Args) bench.Exec {
	var (
		movie    Movie
		person 	 MovieQueryPerson
	)

	queries := strings.Split(args.Query, ";")

	movieStmt, err := db.Prepare(queries[0])
	if err != nil {
		log.Fatal(err)
	}

	peopleStmt, err := db.Prepare(queries[1])
	if err != nil {
		log.Fatal(err)
	}

	directorsStmt, err := db.Prepare(queries[2])
	if err != nil {
		log.Fatal(err)
	}

	actorStmt, err := db.Prepare(queries[3])
	if err != nil {
		log.Fatal(err)
	}

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		prefix := qargs[0]
		num := rand.Intn(1_000_000)
		title := prefix + strconv.Itoa(num)
		image := prefix + "image" + strconv.Itoa(num)
        description := prefix + "description" + strconv.Itoa(num)

		tx, err := db.Begin()
		if err != nil {
			log.Fatal(err)
		}
		defer tx.Commit()

		mrows, err := tx.Stmt(movieStmt).Query(title, image, description, num)
		if err != nil {
			log.Fatal(err)
		}

		for mrows.Next() {
			mrows.Scan(
				&movie.ID,
				&movie.Image,
				&movie.Title,
				&movie.Year,
				&movie.Description,
			)
		}
		movie.Directors = movie.Directors[:0]
		movie.Cast = movie.Cast[:0]

		// get the people to be used as directors and cast
        fname0 := prefix + "Alice"
        lname0 := prefix + "Director"
        img0 := prefix + "image" + strconv.Itoa(num) + ".jpeg"
        fname1 := prefix + "Billie"
        lname1 := prefix + "Actor"
        img1 := prefix + "image" + strconv.Itoa(num + 1) + ".jpeg"
        fname2 := prefix + "Cameron"
        lname2 := prefix + "Actor"
        img2 := prefix + "image" + strconv.Itoa(num + 2) + ".jpeg"

		prows, err := tx.Stmt(peopleStmt).Query(fname0, lname0, img0, fname1, lname1, img1, fname2, lname2, img2)
		err = prows.Err()
		if err != nil {
			log.Fatal(err)
		}

		// add the people as directors or cast
		for prows.Next() {
			prows.Scan(
				&person.ID,
				&person.FullName,
				&person.Image,
			)
			if person.FullName[len(person.FullName) - 8:] == "Director" {
				movie.Directors = append(movie.Directors, person)
			} else {
				movie.Cast = append(movie.Cast, person)
			}
		}

		// create actual directors and actors entries
		_, err = tx.Stmt(directorsStmt).Exec(movie.Directors[0].ID, movie.ID)
		if err != nil {
			log.Fatal(err)
		}
		_, err = tx.Stmt(actorStmt).Exec(movie.Cast[0].ID, movie.Cast[1].ID, movie.ID)
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
