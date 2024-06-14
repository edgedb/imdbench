import {
  int,
  text,
  timestamp,
  mysqlTable,
  serial,
  index,
  unique,
} from "drizzle-orm/mysql-core";
import { relations } from "drizzle-orm";

export const movies = mysqlTable("movies", {
  id: serial("id").primaryKey(),
  image: text("image").notNull(),
  title: text("title").notNull(),
  year: int("year").notNull(),
  description: text("description").notNull(),
});

export const moviesRelations = relations(movies, ({ many }) => ({
  directors: many(directors),
  cast: many(actors),
  reviews: many(reviews),
}));

export const users = mysqlTable("users", {
  id: serial("id").primaryKey(),
  name: text("name").notNull(),
  image: text("image").notNull(),
});

export const usersRelations = relations(users, ({ many }) => ({
  reviews: many(reviews),
}));

export const persons = mysqlTable("persons", {
  id: serial("id").primaryKey(),
  firstName: text("first_name").notNull(),
  middleName: text("middle_name").notNull().default(""),
  lastName: text("last_name").notNull(),
  image: text("image").notNull(),
  bio: text("bio"),
});

export const directors = mysqlTable(
  "directors",
  {
    id: serial("id").primaryKey(),
    listOrder: int("list_order"),
    personId: int("person_id")
      .notNull()
      .references(() => persons.id),
    movieId: int("movie_id")
      .notNull()
      .references(() => movies.id),
  },
  (table) => {
    return {
      personIdx: index("directors_person_index").on(table.personId),
      movieIdx: index("directors_movie_index").on(table.movieId),
      unq: unique().on(table.movieId, table.personId),
    };
  },
);

export const directorsRelations = relations(directors, ({ one }) => ({
  person: one(persons, {
    fields: [directors.personId],
    references: [persons.id],
  }),
  movie: one(movies, {
    fields: [directors.movieId],
    references: [movies.id],
  }),
}));

export const actors = mysqlTable(
  "actors",
  {
    id: serial("id").primaryKey(),
    listOrder: int("list_order"),
    personId: int("person_id")
      .notNull()
      .references(() => persons.id),
    movieId: int("movie_id")
      .notNull()
      .references(() => movies.id),
  },
  (table) => {
    return {
      personIdx: index("directors_person_index").on(table.personId),
      movieIdx: index("directors_movie_index").on(table.movieId),
      unq: unique().on(table.movieId, table.personId),
    };
  },
);

export const actorsRelations = relations(actors, ({ one }) => ({
  person: one(persons, {
    fields: [actors.personId],
    references: [persons.id],
  }),
  movie: one(movies, {
    fields: [actors.movieId],
    references: [movies.id],
  }),
}));

export const reviews = mysqlTable(
  "reviews",
  {
    id: serial("id").primaryKey(),
    body: text("body").notNull(),
    rating: int("rating").notNull(),
    creationTime: timestamp("creation_time")
      .notNull()
      .defaultNow(),
    authorId: int("author_id")
      .notNull()
      .references(() => users.id),
    movieId: int("movie_id")
      .notNull()
      .references(() => movies.id),
  },
  (table) => {
    return {
      authorIdx: index("review_author_index").on(table.authorId),
      movieIdx: index("directors_movie_index").on(table.movieId),
      creationTimeIdx: index("creation_time_index").on(table.creationTime),
    };
  },
);

export const reviewsRelations = relations(reviews, ({ one }) => ({
  author: one(users, {
    fields: [reviews.authorId],
    references: [users.id],
  }),
  movie: one(movies, {
    fields: [reviews.movieId],
    references: [movies.id],
  }),
}));
