'use strict';

module.exports = function(Movie) {
  Movie.movie_details = function(id, cb) {
    Movie.findById(id, {
      // unfortunately when 'scope' and 'fields' is used, nested
      // include stops working
      include: [
        {directors_rel: 'person'},
        {cast_rel: 'person'},
        {reviews: 'author'}
      ]
    }, function (err, instance) {
      let response = instance.toJSON();

      response.avg_rating = response.reviews.reduce(
        (total, r) => (total + r.rating), 0) / response.reviews.length

      // repack the data into the desired shape, etc.
      for (let fname of ['directors', 'cast']) {
        let base = response[fname + '_rel'];
        base.sort((a, b) => {
          let lo = a.list_order - b.list_order;
          // list order may be sufficient by itself
          if (lo) {
            return lo;
          }
          // if the list order is the same, order by last_name
          if (a.last_name < b.last_name) {
            return -1;
          } else if (a.last_name > b.last_name) {
            return 1;
          }
          return 0;
        });

        response[fname] = base.map((rel) => {
          return {
            id: rel.person.id,
            full_name: rel.person.full_name,
            image: rel.person.image,
          }
        });
        delete response[fname + '_rel'];
      }

      let reviews = response.reviews.sort(
        (a, b) => b.creation_time - a.creation_time);
      // reorder the JSON
      delete response.reviews;
      response.reviews = reviews.map((rev) => {
        return {
          id: rev.id,
          body: rev.body,
          rating: rev.rating,
          author: rev.author,
        }
      });

      cb(null, response);
    });
  }
  Movie.remoteMethod(
    'movie_details', {
      http: {
        path: '/movie_details',
        verb: 'get'
      },
      accepts: {
        arg: 'id',
        type: 'number',
        required: true,
        http: { source: 'query' }
      },
      returns: {
        arg: 'status',
        type: 'Object'
      }
    }
  );
};
