package postgres

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"strconv"
	"strings"
	"time"

	"github.com/edgedb/webapp-bench/_go/bench"
	"github.com/edgedb/webapp-bench/_go/cli"
	"github.com/jackc/pgx/v4"
)

var pgxTxOpts pgx.TxOptions = pgx.TxOptions{IsoLevel: pgx.RepeatableRead}

func PGXWorker(args cli.Args) (bench.Exec, bench.Close) {
	url := fmt.Sprintf(
		"postgresql://postgres_bench:edgedbbenchmark@%v:%v/postgres_bench",
		args.Host,
		args.Port,
	)

	con, err := pgx.Connect(context.TODO(), url)
	if err != nil {
		log.Fatal(err)
	}

	var exec bench.Exec
	switch args.QueryName {
	case "get_movie":
		exec = pgxExecMovie(con, args)
	case "get_person":
		exec = pgxExecPerson(con, args)
	case "get_user":
		exec = pgxExecUser(con, args)
	case "update_movie":
		exec = pgxUpdateMovie(con, args)
	case "insert_user":
		exec = pgxInsertUser(con, args)
	case "insert_movie":
		exec = pgxInsertMovie(con, args)
	case "insert_movie_plus":
		exec = pgxInsertMoviePlus(con, args)
	default:
		log.Fatalf("unknown query type: %q", args.QueryName)
	}

	close := func() {
		err := con.Close(context.TODO())
		if err != nil {
			log.Fatal(err)
		}
	}

	return exec, close
}

func pgxExecMovie(con *pgx.Conn, args cli.Args) bench.Exec {
	var (
		movie  Movie
		person MovieQueryPerson
		review MovieQueryReview
	)

	ctx := context.TODO()
	queries := strings.Split(args.Query, ";")

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		id := qargs[0]

		tx, err := con.BeginTx(ctx, pgxTxOpts)
		if err != nil {
			log.Fatal(err)
		}
		defer tx.Rollback(ctx)

		row := tx.QueryRow(ctx, queries[0], id)
		err = row.Scan(
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

		movie.Directors = movie.Directors[:0]
		rows, err := tx.Query(ctx, queries[1], id)
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

		movie.Cast = movie.Cast[:0]
		rows, err = tx.Query(ctx, queries[2], id)
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

		movie.Reviews = movie.Reviews[:0]
		rows, err = tx.Query(ctx, queries[3], id)
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

func pgxExecPerson(con *pgx.Conn, args cli.Args) bench.Exec {
	var (
		person   Person
		actedIn  PersonQueryMovie
		directed PersonQueryMovie
	)

	ctx := context.TODO()
	queries := strings.Split(args.Query, ";")

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		id := qargs[0]

		tx, err := con.BeginTx(ctx, pgxTxOpts)
		if err != nil {
			log.Fatal(err)
		}
		defer tx.Rollback(ctx)

		row := tx.QueryRow(ctx, queries[0], id)
		err = row.Scan(
			&person.ID,
			&person.FullName,
			&person.Image,
			&person.Bio,
		)
		if err != nil {
			log.Fatal(err)
		}

		person.ActedIn = person.ActedIn[:0]
		rows, err := tx.Query(ctx, queries[1], id)
		if err != nil {
			log.Fatal(err)
		}

		for rows.Next() {
			rows.Scan(
				&actedIn.ID,
				&actedIn.Image,
				&actedIn.Title,
				&actedIn.Year,
				&actedIn.AvgRating,
			)
			person.ActedIn = append(person.ActedIn, actedIn)
		}

		err = rows.Err()
		if err != nil {
			log.Fatal(err)
		}

		person.Directed = person.Directed[:0]
		rows, err = tx.Query(ctx, queries[2], id)
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

func pgxExecUser(con *pgx.Conn, args cli.Args) bench.Exec {
	var (
		user   User
		review UserQueryReview
	)

	ctx := context.TODO()

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		id := qargs[0]

		rows, err := con.Query(ctx, args.Query, id)
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

func pgxUpdateMovie(con *pgx.Conn, args cli.Args) bench.Exec {
	var (
		movie  PersonQueryMovie
	)

	ctx := context.TODO()

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		id := qargs[0]

		rows, err := con.Query(ctx, args.Query, id, "---" + id)
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

func pgxInsertUser(con *pgx.Conn, args cli.Args) bench.Exec {
	var (
		user   User
	)

	ctx := context.TODO()

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		text := qargs[0]
		num := rand.Intn(1_000_000)
		name := text + strconv.Itoa(num)
		image := text + "image" + strconv.Itoa(num)

		rows, err := con.Query(ctx, args.Query, name, image)
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

func pgxInsertMovie(con *pgx.Conn, args cli.Args) bench.Exec {
	var (
		movie    Movie
		person 	 MovieQueryPerson
	)

	ctx := context.TODO()
	queries := strings.Split(args.Query, ";")
	movieStmt := queries[0]
	peopleStmt := queries[1]
	directorsStmt := queries[2]
	actorStmt := queries[3]

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

		tx, err := con.BeginTx(ctx, pgxTxOpts)
		if err != nil {
			log.Fatal(err)
		}
		defer tx.Commit(ctx)

		// create the movie
		mrows, err := tx.Query(ctx, movieStmt, title, image, description, num)
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
		prows, err := tx.Query(ctx, peopleStmt, qargs[1], qargs[2], qargs[3], qargs[4])
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
		_, err = tx.Exec(ctx, directorsStmt, movie.Directors[0].ID, movie.ID)
		if err != nil {
			log.Fatal(err)
		}
		_, err = tx.Exec(ctx, actorStmt, movie.Cast[0].ID, movie.Cast[1].ID, movie.Cast[2].ID, movie.ID)
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

func pgxInsertMoviePlus(con *pgx.Conn, args cli.Args) bench.Exec {
	var (
		movie    Movie
		person 	 MovieQueryPerson
	)

	ctx := context.TODO()
	queries := strings.Split(args.Query, ";")
	movieStmt := queries[0]
	peopleStmt := queries[1]
	directorsStmt := queries[2]
	actorStmt := queries[3]

	return func(qargs []string) (time.Duration, string) {
		start := time.Now()
		prefix := qargs[0]
		num := rand.Intn(1_000_000)
		title := prefix + strconv.Itoa(num)
		image := prefix + "image" + strconv.Itoa(num)
        description := prefix + "description" + strconv.Itoa(num)

		tx, err := con.BeginTx(ctx, pgxTxOpts)
		if err != nil {
			log.Fatal(err)
		}
		defer tx.Commit(ctx)

		mrows, err := tx.Query(ctx, movieStmt, title, image, description, num)
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

		prows, err := tx.Query(ctx, peopleStmt, fname0, lname0, img0, fname1, lname1, img1, fname2, lname2, img2)
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
		_, err = tx.Exec(ctx, directorsStmt, movie.Directors[0].ID, movie.ID)
		if err != nil {
			log.Fatal(err)
		}
		_, err = tx.Exec(ctx, actorStmt, movie.Cast[0].ID, movie.Cast[1].ID, movie.ID)
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
