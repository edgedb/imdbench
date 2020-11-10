package postgres

import (
	"database/sql"
	"encoding/json"
	"log"
	"time"

	"github.com/edgedb/webapp-bench/_go/bench"
	"github.com/edgedb/webapp-bench/_go/cli"
)

type User struct {
	ID            int               `json:"id"`
	Name          string            `json:"name"`
	Image         string            `json:"image"`
	LatestReviews []UserQueryReview `json:"latest_reviews"`
}

type UserQueryReview struct {
	ID     int    `json:"id"`
	Body   string `json:"body"`
	Rating int    `json:"rating"`
	Movie  struct {
		ID        int     `json:"id"`
		Image     string  `json:"image"`
		Title     string  `json:"title"`
		AvgRating float64 `json:"avg_rating"`
	} `json:"movie"`
}

func execUser(db *sql.DB, args cli.Args) bench.Exec {
	var (
		user   User
		review UserQueryReview
	)

	return func(id string) (time.Duration, string) {
		start := time.Now()

		rows, err := db.Query(args.Query, id)
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
