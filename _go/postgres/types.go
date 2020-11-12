package postgres

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
