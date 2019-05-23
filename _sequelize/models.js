"use strict";

const Sequelize = require('sequelize');

const sequelize = new Sequelize(
  'postgres://sequelize_bench:edgedbbenchmark@localhost:5432/sequelize_bench',
  {
    logging: false,
    benchmark: false,
    define: {
      freezeTableName: true,
      timestamps: false,
    }
  });
module.exports.sequelize = sequelize;


const User = sequelize.define('User', {
  // attributes
  id: {
    type: Sequelize.INTEGER,
    allowNull: false,
    primaryKey: true,
  },
  name: {
    type: Sequelize.TEXT,
    allowNull: false
  },
  image: {
    type: Sequelize.TEXT,
    allowNull: false
  },
});
module.exports.User = User;


const Person = sequelize.define('Person', {
  // attributes
  id: {
    type: Sequelize.INTEGER,
    allowNull: false,
    primaryKey: true,
  },
  first_name: {
    type: Sequelize.TEXT,
    allowNull: false
  },
  middle_name: {
    type: Sequelize.TEXT,
    allowNull: false
  },
  last_name: {
    type: Sequelize.TEXT,
    allowNull: false
  },
  full_name: {
    type: Sequelize.VIRTUAL(
      Sequelize.TEXT, ['first_name', 'middle_name', 'last_name']),
    get: function() {
      let val =  (
        this.middle_name ?
        this.first_name + ' ' + this.middle_name + ' ' + this.last_name
        :
        this.first_name + ' ' + this.last_name
      );

      return val;
    }
  },
  bio: {
    type: Sequelize.TEXT,
    allowNull: false
  },
  image: {
    type: Sequelize.TEXT,
    allowNull: false
  },
});
module.exports.Person = Person;


const Movie = sequelize.define('Movie', {
  // attributes
  id: {
    type: Sequelize.INTEGER,
    allowNull: false,
    primaryKey: true,
  },
  image: {
    type: Sequelize.TEXT,
    allowNull: false
  },
  title: {
    type: Sequelize.TEXT,
    allowNull: false
  },
  year: {
    type: Sequelize.INTEGER,
    allowNull: false,
  },
  description: {
    type: Sequelize.TEXT,
    allowNull: false
  },
});
module.exports.Movie = Movie;
// this SQL computed attribute can be used in "attributes"
Movie.avg_rating = function (movieAlias) {
  if (!movieAlias) {
    movieAlias = 'Movie';
  }
  return [
    sequelize.literal(
      '(SELECT avg("mr"."rating")::float \
        FROM "Review" AS "mr" \
        WHERE "mr"."movie_id" = "' + movieAlias + '"."id")'),
    'avg_rating'
  ];
}


const Review = sequelize.define('Review', {
  // attributes
  id: {
    type: Sequelize.INTEGER,
    allowNull: false,
    primaryKey: true,
  },
  body: {
    type: Sequelize.TEXT,
    allowNull: false
  },
  rating: {
    type: Sequelize.INTEGER,
    allowNull: false,
  },
  creation_time: {
    type: Sequelize.DATE,
    allowNull: false
  },
});
module.exports.Review = Review;


const Cast = sequelize.define('Cast', {
  // attributes
  id: {
    type: Sequelize.INTEGER,
    autoIncrement: true,
    primaryKey: true,
  },
  list_order: {
    type: Sequelize.INTEGER,
  },
}, {
  // options
});
module.exports.Cast = Cast;


const Directors = sequelize.define('Directors', {
  // attributes
  id: {
    type: Sequelize.INTEGER,
    autoIncrement: true,
    primaryKey: true,
  },
  list_order: {
    type: Sequelize.INTEGER,
  },
});
module.exports.Directors = Directors;


User.hasMany(Review, {foreignKey: 'author_id', as: 'reviews'});
// add another alias for user reviews - latest_reviews
User.hasMany(Review, {foreignKey: 'author_id', as: 'latest_reviews'});
Review.belongsTo(User, {foreignKey: 'author_id', as: 'author'});
Movie.hasMany(Review, {foreignKey: 'movie_id', as: 'reviews'});
Review.belongsTo(Movie, {foreignKey: 'movie_id', as: 'movie'});
Movie.belongsToMany(Person, {
  through: Directors, foreignKey: 'movie_id', otherKey: 'person_id',
  as: 'directors'
});
Person.belongsToMany(Movie, {
  through: Directors, foreignKey: 'person_id', otherKey: 'movie_id',
  as: 'directed'
});
Movie.belongsToMany(Person, {
  through: Cast, foreignKey: 'movie_id', otherKey: 'person_id',
  as: 'cast'
});
Person.belongsToMany(Movie, {
  through: Cast, foreignKey: 'person_id', otherKey: 'movie_id',
  as: 'acted_in'
});
