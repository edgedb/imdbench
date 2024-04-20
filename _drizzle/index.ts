import * as schema from "./db/schema";
import { drizzle } from "drizzle-orm/node-postgres";
import {
  sql,
  like,
  exists,
  eq,
  and,
  asc,
  desc,
  avg,
} from "drizzle-orm";
import { Pool } from "pg";

export class App {
  private client;
  private db;
  private concurrency: number;
  private INSERT_PREFIX: string;
  private preparedAvgRating;
  private preparedMovieDetails;
  private preparedUserDetails;
  private preparedInsertMovie;
  private preparedPersons;

  constructor(options: { [key: string]: any }) {
    options = {
      user: "postgres_bench",
      host: "localhost",
      database: "postgres_bench",
      password: "edgedbbenchmark",
      port: 15432,
      ...(options || {}),
    };
    this.client = new Pool({
      host: options.host,
      port: options.port,
      user: options.user,
      password: options.password,
      database: options.database,
    });
    this.db = drizzle(this.client, { schema, logger: false });
    this.concurrency = options.max;
    this.INSERT_PREFIX = "insert_test__";
    const ids = this.db
      .select({ val: sql`val::int` })
      .from(
        sql`json_array_elements_text(${sql.placeholder("ids")}) as arr(val)`,
      );
    this.preparedAvgRating = this.db
      .select({
        id: schema.reviews.movieId,
        avgRating: avg(schema.reviews.rating).mapWith(Number),
      })
      .from(schema.reviews)
      .groupBy(schema.reviews.movieId)
      .where(eq(schema.reviews.movieId, sql`any(${ids})`))
      .prepare("avgRating");
    const fullName = sql<string>`
      CASE WHEN ${schema.persons.middleName} != '' THEN
      ${schema.persons.firstName} || ' ' || ${schema.persons.middleName} || ' ' || ${schema.persons.lastName}
      ELSE
      ${schema.persons.firstName} || ' ' || ${schema.persons.lastName}
      END`;
    this.preparedMovieDetails = this.db.query.movies
      .findFirst({
        columns: {
          id: true,
          image: true,
          title: true,
          year: true,
          description: true,
        },
        extras: {
          avg_rating: sql`${sql.placeholder("avgRating")}`.as("avg_rating"),
        },
        with: {
          directors: {
            columns: {},
            with: {
              person: {
                columns: {
                  id: true,
                  image: true,
                },
                extras: {
                  full_name: fullName.as("full_name"),
                },
              },
            },
            orderBy: [
              // XXX: unsupported Drizzle features as of writing
              asc(schema.directors.listOrder), // .nullsLast()
              // asc(schema.persons.lastName),
            ],
          },
          cast: {
            columns: {},
            with: {
              person: {
                columns: {
                  id: true,
                  image: true,
                },
                extras: {
                  full_name: fullName.as("full_name"),
                },
              },
            },
            orderBy: [
              // XXX: unsupported Drizzle features as of writing
              asc(schema.directors.listOrder), // .nullsLast()
              // asc(schema.persons.lastName),
            ],
          },
          reviews: {
            columns: {
              id: true,
              body: true,
              rating: true,
            },
            with: {
              author: {
                columns: {
                  id: true,
                  name: true,
                  image: true,
                },
              },
            },
            orderBy: [desc(schema.reviews.creationTime)],
          },
        },
        where: eq(schema.movies.id, sql.placeholder("id")),
      })
      .prepare("movieDetails");
    this.preparedUserDetails = this.db.query.users
      .findFirst({
        columns: {
          id: true,
          name: true,
          image: true,
        },
        with: {
          reviews: {
            columns: {
              id: true,
              body: true,
              rating: true,
            },
            with: {
              movie: {
                columns: {
                  id: true,
                  image: true,
                  title: true,
                },
              },
            },
          },
        },
        where: eq(schema.users.id, sql.placeholder("id")),
      })
      .prepare("userDetails");
    this.preparedInsertMovie = this.db
      .insert(schema.movies)
      .values({
        title: sql`${sql.placeholder("prefix")} || ${sql.placeholder("num")}`,
        image: sql`'img' || ${sql.placeholder("num")} || '.jpeg'`,
        description: sql`${sql.placeholder("prefix")} || 'description' || ${sql.placeholder("num")}`,
        year: sql.placeholder("num"),
      })
      .returning()
      .prepare("insertMovie");
    this.preparedPersons = this.db.query.persons
      .findMany({
        columns: {
          id: true,
          image: true,
        },
        extras: {
          full_name: fullName.as("full_name"),
        },
        where: eq(schema.users.id, sql`any(${ids})`),
      })
      .prepare("findPersons");
  }

  async getIDs(number_of_ids: number) {
    const ids = await Promise.all([
      this.db.query.users.findMany({
        columns: { id: true },
        orderBy: sql`random()`,
      }),
      this.db.query.persons.findMany({
        columns: { id: true },
        orderBy: sql`random()`,
      }),
      this.db.query.movies.findMany({
        columns: { id: true },
        orderBy: sql`random()`,
      }),
    ]);
    const people = ids[1].map((x) => x.id);
    return {
      get_user: ids[0].map((x) => x.id),
      get_person: people,
      get_movie: ids[2].map((x) => x.id),
      update_movie: ids[2].map((x) => x.id),
      insert_user: Array(this.concurrency).fill(this.INSERT_PREFIX),
      insert_movie: Array(this.concurrency).fill({
        prefix: this.INSERT_PREFIX,
        people: people.slice(0, 4),
      }),
      insert_movie_plus: Array(this.concurrency).fill(this.INSERT_PREFIX),
    };
  }

  async setup(query: string) {
    if (query == "update_movie") {
      await this.db
        .update(schema.movies)
        .set({ title: sql`split_part(title, '---', 1)` })
        .where(like(schema.movies.title, "%---%"));
    } else if (query == "insert_user") {
      await this.db
        .delete(schema.users)
        .where(like(schema.users.name, `${this.INSERT_PREFIX}%`));
    } else if (query == "insert_movie" || query == "insert_movie_plus") {
      // XXX: use `delete ... using ...` once Drizzle supports it
      await this.db.delete(schema.directors).where(
        exists(
          this.db
            .select()
            .from(schema.movies)
            .where(
              and(
                eq(schema.directors.movieId, schema.movies.id),
                like(schema.movies.image, `${this.INSERT_PREFIX}%`),
              ),
            ),
        ),
      );
      await this.db.delete(schema.actors).where(
        exists(
          this.db
            .select()
            .from(schema.movies)
            .where(
              and(
                eq(schema.actors.movieId, schema.movies.id),
                like(schema.movies.image, `${this.INSERT_PREFIX}%`),
              ),
            ),
        ),
      );
      await this.db
        .delete(schema.movies)
        .where(like(schema.movies.image, `${this.INSERT_PREFIX}%`));

      await this.db
        .delete(schema.persons)
        .where(like(schema.persons.image, `${this.INSERT_PREFIX}%`));
    }
  }

  getConnection(i: number) {
    return this;
  }

  async benchQuery(query: string, val: any) {
    if (query == "get_user") {
      return await this.userDetails(val as number);
    } else if (query == "get_person") {
      // return await this.personDetails(id);
    } else if (query == "get_movie") {
      return await this.movieDetails(val as number);
    } else if (query == "update_movie") {
      // return await this.updateMovie(id);
    } else if (query == "insert_user") {
      // return await this.insertUser(id);
    } else if (query == "insert_movie") {
      return await this.insertMovie(
        val as { prefix: string; people: number[] },
      );
    } else if (query == "insert_movie_plus") {
      // return await this.insertMoviePlus(id);
    }
  }

  async movieDetails(id: number): Promise<string> {
    // XXX: `extras` doesn't support aggregations yet
    const rs = await this.preparedAvgRating.execute({
      ids: `[${id}]`,
    });
    let avgRating: number = 0;
    if (rs.length > 0) {
      avgRating = rs[0].avgRating;
    }
    let result = await this.preparedMovieDetails.execute({ avgRating, id });
    return JSON.stringify(result);
  }

  async userDetails(id: number): Promise<any> {
    const rv = await this.preparedUserDetails.execute({ id });
    if (rv === undefined) {
      return;
    }
    const ratings = (
      await this.preparedAvgRating.execute({
        ids: JSON.stringify(rv?.reviews.map((r) => r.movie.id)),
      })
    ).reduce(
      (acc: { [key: number]: number }, r) => ({ ...acc, [r.id]: r.avgRating }),
      {},
    );
    let result = {
      ...rv,
      reviews: rv.reviews.map((review) => ({
        ...review,
        movie: { ...review.movie, avg_rating: ratings[review.movie.id] },
      })),
    };
    return JSON.stringify(result);
  }

  async insertMovie(val: { prefix: string; people: number[] }): Promise<string> {
    // XXX: insert CTE https://github.com/drizzle-team/drizzle-orm/issues/2078
    const num = Math.floor(Math.random() * 1000000);
    const movie = (
      await this.preparedInsertMovie.execute({ prefix: val.prefix, num })
    )[0];
    const people = await this.preparedPersons.execute({
      ids: JSON.stringify(val.people),
    });
    const directors = people.slice(0, 1);
    const cast = people.slice(1, 4);
    // XXX: prepared statements & batching
    await this.db.insert(schema.directors).values(
      directors.map((director) => ({
        personId: director.id,
        movieId: movie.id,
      })),
    );
    await this.db.insert(schema.actors).values(
      cast.map((actor) => ({
        personId: actor.id,
        movieId: movie.id,
      })),
    );
    return JSON.stringify({...movie, directors, cast});
  }

  async cleanup(query: string): Promise<void> {
    if (
      [
        "update_movie",
        "insert_user",
        "insert_movie",
        "insert_movie_plus",
      ].indexOf(query) >= 0
    ) {
      // The clean up is the same as setup for mutation benchmarks
      return await this.setup(query);
    }
  }
}
