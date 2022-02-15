import "reflect-metadata";
import { Connection, ConnectionOptions } from "typeorm";
import { User } from "./entity/User";
import { Person } from "./entity/Person";
import { Movie, MovieView } from "./entity/Movie";
import { Review } from "./entity/Review";
import { Directors } from "./entity/Directors";
import { Cast } from "./entity/Cast";

var defaultOptions: ConnectionOptions = {
  type: "postgres",
  host: "localhost",
  port: 15432,
  username: "typeorm_bench",
  password: "edgedbbenchmark",
  database: "typeorm_bench",
  synchronize: false,
  logging: false,
  entities: [User, Person, Movie, MovieView, Review, Directors, Cast]
};

export class App extends Connection {
  concurrency: number;


  constructor(options: ConnectionOptions) {
    var opts: ConnectionOptions = {
      ...defaultOptions
    };
    Object.assign(opts, options || {});

    super(opts);

    this.concurrency = options.extra.max;
  }

  async benchQuery(query: string, val) {
    var method;

    if (query == "get_user") {
      method = userDetails.bind(this);
    } else if (query == "get_person") {
      method = personDetails.bind(this);
    } else if (query == "get_movie") {
      method = movieDetails.bind(this);
    } else if (query == "update_movie") {
      method = updateMovie.bind(this);
    } else if (query == "insert_user") {
      method = insertUser.bind(this);
    } else if (query == "insert_movie") {
      method = insertMovie.bind(this);
    } else if (query == "insert_movie_plus") {
      method = insertMoviePlus.bind(this);
    }

    return await method(val);
  }

  async getIDs() {
    var ids = await Promise.all([
      this.getRepository(User).find({ select: ["id"] }),
      this.getRepository(Person).find({ select: ["id"] }),
      this.getRepository(Movie).find({ select: ["id", "title"] })
    ]);
    var people = ids[1].map(x => ({id: x.id}));

    return {
      get_user: ids[0].map(x => ({id: x.id})),
      get_person: people,
      get_movie: ids[2].map(x => ({id: x.id})),
      // re-use user IDs for update tests
      update_movie: ids[2].map(
        x => ({id: x.id, title: x.title + '---' + x.id})),
      // generate as many insert stubs as "concurrency" to
      // accommodate concurrent inserts
      insert_user: Array(this.concurrency).fill('insert_test__'),
      insert_movie: Array(this.concurrency).fill({
        prefix: 'insert_test__',
        people: people.slice(0, 4).map(x => x.id),
      }),
      insert_movie_plus: Array(this.concurrency).fill('insert_test__'),
    };
  }

  async setup(query) {
    if (query == "update_movie") {
      // don't care about using proper Sequelize machinery for this
      return await this.query(`
        UPDATE
            "movie"
        SET
            "title" = split_part("movie"."title", '---', 1)
        WHERE
            "movie"."title" LIKE '%---%';
      `);
    } else if (query == "insert_user") {
      return await this.query(`
        DELETE FROM
            "user"
        WHERE
            "user"."name" LIKE 'insert_test__%';
      `);
    } else if (query == 'insert_movie' || query == 'insert_movie_plus') {
      await this.query(`
          DELETE FROM
              "directors" as D
          USING
              "movie" as M
          WHERE
              D.movie_id = M.id AND M.image LIKE 'insert_test__%';
      `);
      await this.query(`
          DELETE FROM
              "cast" as A
          USING
              "movie" as M
          WHERE
              A.movie_id = M.id AND M.image LIKE 'insert_test__%';
      `);
      await this.query(`
          DELETE FROM
              "movie" as M
          WHERE
              M.image LIKE 'insert_test__%';
      `);
      return await this.query(`
          DELETE FROM
              "person" as P
          WHERE
              P.image LIKE 'insert_test__%';
      `);
    }
  }

  async cleanup(query) {
    if ([
      "update_movie", "insert_user", "insert_movie", "insert_movie_plus"
    ].indexOf(query) >= 0) {
      // The clean up is the same as setup for mutation benchmarks
      return await this.setup(query);
    }
  }

  getConnection(i: number) {
    return this;
  }
}

export async function userDetails(
    this,
    val: {id: number; title?: string}
): Promise<string> {
  var user = await this.createQueryBuilder(User, "user")
    .select(["user", "review.id", "review.body", "review.rating"])
    .leftJoin("user.reviews", "review")
    .leftJoinAndMapOne(
      "review.movie",
      MovieView,
      "movie",
      "movie.id = review.movie_id"
    )
    .where("user.id = :id", { id: val.id })
    .orderBy("review.creation_time", "DESC")
    .getOne();

  user.latest_reviews = user.reviews.slice(0, 10).map(rev => {
    rev.movie = {
      id: rev.movie.id,
      image: rev.movie.image,
      title: rev.movie.title,
      // PostgreSQL floats are returned as strings
      avg_rating: parseFloat(rev.movie.avg_rating)
    };
    return rev;
  });
  delete user.reviews;
  var result = user;

  return JSON.stringify(result);
}

export async function personDetails(
    this,
    val: {id: number; title?: string}
): Promise<string> {
  var person = await this.createQueryBuilder(Person, "person")
    .leftJoinAndSelect("person.directed", "directors")
    .leftJoinAndMapOne(
      "directors.movie",
      MovieView,
      "dmovie",
      "dmovie.id = directors.movie_id"
    )
    .leftJoinAndSelect("person.acted_in", "cast")
    .leftJoinAndMapOne(
      "cast.movie",
      MovieView,
      "cmovie",
      "cmovie.id = cast.movie_id"
    )
    .where("person.id = :id", { id: val.id })
    .orderBy("dmovie.year", "ASC")
    .addOrderBy("cmovie.year", "ASC")
    .getOne();

  for (let fname of ["acted_in", "directed"]) {
    person[fname] = person[fname].map(rel => {
      return {
        id: rel.movie.id,
        image: rel.movie.image,
        title: rel.movie.title,
        year: rel.movie.year,
        // PostgreSQL floats are returned as strings
        avg_rating: parseFloat(rel.movie.avg_rating)
      };
    });
  }
  var result = {
    id: person.id,
    full_name: person.get_full_name(),
    image: person.image,
    bio: person.bio,
    acted_in: person.acted_in,
    directed: person.directed
  };

  return JSON.stringify(result);
}

export async function movieDetails(
    this,
    val: {id: number; title?: string}
): Promise<string> {
  var movie = await this.createQueryBuilder(Movie, "movie")
    .select([
      "movie.id",
      "movie.image",
      "movie.title",
      "movie.year",
      "movie.description",
      "directors.list_order",
      "cast.list_order",
      "dperson.id",
      "dperson.first_name",
      "dperson.middle_name",
      "dperson.last_name",
      "dperson.image",
      "cperson.id",
      "cperson.first_name",
      "cperson.middle_name",
      "cperson.last_name",
      "cperson.image",
      "review.id",
      "review.body",
      "review.rating",
      "user.id",
      "user.name",
      "user.image"
    ])
    .leftJoinAndSelect("movie.directors", "directors")
    .leftJoinAndSelect("directors.person", "dperson")
    .leftJoinAndSelect("movie.cast", "cast")
    .leftJoinAndSelect("cast.person", "cperson")
    .leftJoinAndSelect("movie.reviews", "review")
    .leftJoinAndSelect("review.author", "user")
    .where("movie.id = :id", { id: val.id })
    .orderBy("directors.list_order", "ASC")
    .addOrderBy("dperson.last_name", "ASC")
    .addOrderBy("cast.list_order", "ASC")
    .addOrderBy("cperson.last_name", "ASC")
    .addOrderBy("review.creation_time", "DESC")
    .getOne();

  movie.avg_rating =
    movie.reviews.reduce((total, r) => total + r.rating, 0) /
    movie.reviews.length;

  for (let fname of ["directors", "cast"]) {
    movie[fname] = movie[fname].map(rel => {
      return {
        id: rel.person.id,
        full_name: rel.person.get_full_name(),
        image: rel.person.image
      };
    });
  }
  movie.reviews = movie.reviews.map(rev => {
    delete rev.creation_time;
    return rev;
  });
  var result = movie;

  return JSON.stringify(result);
}

export async function updateMovie(
    this,
    val: {id: number; title?: string}
): Promise<string> {
  var result = await this.createQueryBuilder(Movie, "movie")
    .update()
    .set({title: val.title})
    .where("movie.id = :id", { id: val.id })
    .returning(["id", "title"])
    .execute();

  return JSON.stringify(result.raw[0]);
}

export async function insertUser(
    this,
    val: string
): Promise<string> {
  var num = Math.floor(Math.random() * 1000000);
  var result = await this.createQueryBuilder()
    .insert()
    .into(User)
    .values([{
      // using the automatic id sequence from cast as a matter of convenience
      id: () => "nextval('cast_id_seq')",
      name: val + num,
      image: val + 'image' + num,
    }])
    .returning(["id", "name", "image"])
    .execute();

  return JSON.stringify(result.raw[0]);
}

export async function _getMovieAfterInsert(
    app: App,
    id: number
): Promise<string> {
  var movie = await app.createQueryBuilder(Movie, "movie")
    .select([
      "movie.id",
      "movie.image",
      "movie.title",
      "movie.year",
      "movie.description",
      "directors.list_order",
      "cast.list_order",
      "dperson.id",
      "dperson.first_name",
      "dperson.middle_name",
      "dperson.last_name",
      "dperson.image",
      "cperson.id",
      "cperson.first_name",
      "cperson.middle_name",
      "cperson.last_name",
      "cperson.image",
    ])
    .leftJoinAndSelect("movie.directors", "directors")
    .leftJoinAndSelect("directors.person", "dperson")
    .leftJoinAndSelect("movie.cast", "cast")
    .leftJoinAndSelect("cast.person", "cperson")
    .where("movie.id = :id", { id: id })
    .getOne();

  for (let fname of ["directors", "cast"]) {
    movie[fname] = movie[fname].map(rel => {
      return {
        id: rel.person.id,
        full_name: rel.person.get_full_name(),
        image: rel.person.image
      };
    });
  }
  var result = movie;

  return JSON.stringify(result);
}

export async function insertMovie(
    this,
    val: {prefix: string, people: number[]}
): Promise<string> {
  var num = Math.floor(Math.random() * 1000000);
  var movie = await this.createQueryBuilder()
    .insert()
    .into(Movie)
    .values([{
      // using the automatic id sequence from cast as a matter of convenience
      id: () => "nextval('cast_id_seq')",
      title: val.prefix + num,
      image: val.prefix + "image" + num + ".jpeg",
      description: val.prefix + "description" + num,
      year: num,
    }])
    .returning(["id"])
    .execute();

  await this.createQueryBuilder()
    .insert()
    .into(Directors)
    .values([{
      movie_id: movie.raw[0].id,
      person_id: val.people[0],
      list_order: 0,
    }])
    .execute();
  await this.createQueryBuilder()
    .insert()
    .into(Cast)
    .values(val.people.slice(1).map(x => ({
      movie_id: movie.raw[0].id,
      person_id: x,
      list_order: 0,
    })))
    .execute();

  // returning is not sufficient to get nested results, so we fetch them
  return await _getMovieAfterInsert(this, movie.raw[0].id);
}

export async function insertMoviePlus(
    this,
    val: string
): Promise<string> {
  var num = Math.floor(Math.random() * 1000000);

  var people = await this.createQueryBuilder()
    .insert()
    .into(Person)
    .values([{
      id: () => "nextval('cast_id_seq')",
      first_name: val + "Alice",
      middle_name: "",
      last_name: val + "Director",
      image: val + "image" + num + ".jpeg",
      bio: "",
    }, {
      id: () => "nextval('cast_id_seq')",
      first_name: val + "Billie",
      middle_name: "",
      last_name: val + "Actor",
      image: val + "image" + (num + 1) + ".jpeg",
      bio: "",
    }, {
      id: () => "nextval('cast_id_seq')",
      first_name: val + "Cameron",
      middle_name: "",
      last_name: val + "Actor",
      image: val + "image" + (num + 2) + ".jpeg",
      bio: "",
    }])
    .returning(["id"])
    .execute();

  var movie = await this.createQueryBuilder()
    .insert()
    .into(Movie)
    .values([{
      // using the automatic id sequence from cast as a matter of convenience
      id: () => "nextval('cast_id_seq')",
      title: val + num,
      image: val + "image" + num + ".jpeg",
      description: val + "description" + num,
      year: num,
    }])
    .returning(["id"])
    .execute();

  // adding directors and cast only seems to be possible as a separate step
  await this.createQueryBuilder()
    .insert()
    .into(Directors)
    .values([{
      movie_id: movie.raw[0].id,
      person_id: people.raw[0].id,
      list_order: 0,
    }])
    .execute();
  await this.createQueryBuilder()
    .insert()
    .into(Cast)
    .values(people.raw.slice(1).map(x => ({
      movie_id: movie.raw[0].id,
      person_id: x.id,
      list_order: 0,
    })))
    .execute();

  // returning is not sufficient to get nested results, so we fetch them
  return await _getMovieAfterInsert(this, movie.raw[0].id);
}
