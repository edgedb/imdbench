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
  inArray,
} from "drizzle-orm";
import { Pool } from "pg";
import {actors} from "./db/schema";

export class App {
  private client;
  private db;
  private concurrency: number;
  private INSERT_PREFIX: string;

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
    this.db = drizzle(this.client, { schema });
    this.concurrency = options.max;
    this.INSERT_PREFIX = "insert_test__";
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

  async movieDetails(id: number): Promise<any> {
    // XXX: `extras` doesn't support aggregations yet
    const { avgRating } = (
      await this.db
        .select({ avgRating: avg(schema.reviews.rating).mapWith(Number) })
        .from(schema.reviews)
        .where(eq(schema.reviews.movieId, id))
        .limit(1)
    )[0];
    const fullName = sql<string>`
      CASE WHEN ${schema.persons.middleName} != '' THEN
      ${schema.persons.firstName} || ' ' || ${schema.persons.middleName} || ' ' || ${schema.persons.lastName}
      ELSE
      ${schema.persons.firstName} || ' ' || ${schema.persons.lastName}
      END`;
    return await this.db.query.movies.findFirst({
      columns: {
        id: true,
        image: true,
        title: true,
        year: true,
        description: true,
      },
      extras: {
        avg_rating: sql`${avgRating}`.as("avg_rating"),
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
      where: eq(schema.movies.id, id),
    });
  }

  async userDetails(id: number): Promise<any> {
    const rv = await this.db.query.users.findFirst({
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
      where: eq(schema.users.id, id),
    });
    if (rv === undefined) {
      return;
    }
    const ratings: { [key: number]: number } = (
      await this.db
        .select({
          id: schema.reviews.movieId,
          avgRating: avg(schema.reviews.rating).mapWith(Number),
        })
        .from(schema.reviews)
        .groupBy(schema.reviews.movieId)
        .where(
          inArray(
            schema.reviews.movieId,
            rv?.reviews.map((r) => r.movie.id),
          ),
        )
    ).reduce((acc, r) => ({ ...acc, [r.id]: r.avgRating }), {});
    return {
      ...rv,
      reviews: rv.reviews.map((review) => ({
        ...review,
        movie: { ...review.movie, avg_rating: ratings[review.movie.id] },
      })),
    };
  }

  async insertMovie(val: { prefix: string; people: number[] }) {
    // XXX: insert CTE https://github.com/drizzle-team/drizzle-orm/issues/2078
    const num = Math.floor(Math.random() * 1000000);
    const movie = (
      await this.db
        .insert(schema.movies)
        .values({
          title: val.prefix + num,
          image: "img" + num + ".jpeg",
          description: val.prefix + "description" + num,
          year: num,
        })
        .returning()
    )[0];
    const fullName = sql<string>`
      CASE WHEN ${schema.persons.middleName} != '' THEN
      ${schema.persons.firstName} || ' ' || ${schema.persons.middleName} || ' ' || ${schema.persons.lastName}
      ELSE
      ${schema.persons.firstName} || ' ' || ${schema.persons.lastName}
      END`;
    const people = await this.db.query.persons.findMany({
      columns: {
        id: true,
        image: true,
      },
      extras: {
        full_name: fullName.as("full_name"),
      },
      where: inArray(schema.users.id, val.people),
    });
    const directors = people.slice(0, 1);
    const cast = people.slice(1, 4);
    await this.db
      .insert(schema.directors)
      .values(
        directors.map((director) => ({
          personId: director.id,
          movieId: movie.id,
        })),
      );
    await this.db
      .insert(schema.actors)
      .values(
        cast.map((actor) => ({
          personId: actor.id,
          movieId: movie.id,
        }))
      );
    return {...movie, directors, cast};
  }

  async cleanup(query: string) {
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
