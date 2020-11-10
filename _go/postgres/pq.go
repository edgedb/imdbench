package postgres

import (
	"log"
	"regexp"

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

	// the get movie query uses 4 at a time
	db.SetMaxIdleConns(4 * args.Concurrency)

	regex := regexp.MustCompile(`users|movie|person`)
	queryType := regex.FindString(args.Query)

	var exec bench.Exec

	switch queryType {
	case "users":
		exec = execUser(db, args)
	case "movie":
		exec = execMovie(db, args)
	case "person":
		exec = execPerson(db, args)
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
