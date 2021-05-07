"use strict";

const Sequelize = require('sequelize');

class App extends Sequelize {
  constructor(options) {
    options = options || {};
    var opts = {
      dialect: 'postgres',
      host: 'localhost',
      port: 5432,
      username: 'sequelize_bench',
      password: 'edgedbbenchmark',
      database: 'sequelize_bench',
      // native: true,
      logging: null,
      benchmark: false,
      define: {
        freezeTableName: true,
        timestamps: false,
      },
      pool: {
        min: 1,
        max: 1,
      },
      ...options
    };
    super(opts);

    this.init_models();
  }

  init_models() {
    class User extends Sequelize.Model {}
    User.init({
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
    }, {
      sequelize: this, modelName: 'User'
    });

    class Person extends Sequelize.Model {}
    Person.init({
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
            `${this.first_name} ${this.middle_name} ${this.last_name}`
            :
            `${this.first_name} ${this.last_name}`
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
    }, {
      sequelize: this, modelName: 'Person'
    });

    class Movie extends Sequelize.Model {}
    Movie.init({
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
    }, {
      sequelize: this, modelName: 'Movie'
    });
    // this SQL computed attribute can be used in "attributes"
    Movie.avg_rating = function(movieAlias) {
      if (!movieAlias) {
        movieAlias = 'Movie';
      }
      return [
        App.literal(
          '(SELECT avg("mr"."rating")::float \
            FROM "Review" AS "mr" \
            WHERE "mr"."movie_id" = "' + movieAlias + '"."id")'),
        'avg_rating'
      ];
    }

    class Review extends Sequelize.Model {}
    Review.init({
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
    }, {
      sequelize: this, modelName: 'Review'
    });

    class Cast extends Sequelize.Model {}
    Cast.init({
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
      sequelize: this, modelName: 'Cast'
    });

    class Directors extends Sequelize.Model {}
    Directors.init({
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
      sequelize: this, modelName: 'Directors'
    });

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
  }
}
module.exports.App = App;
