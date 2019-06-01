'use strict';

module.exports = function(User) {
  User.user_details = async function(id) {
    let instance = await User.findById(id, {
      // unfortunately when 'scope' and 'fields' is used, nested
      // include stops working
      include: {
        reviews: {
          movie: {
            relation: 'reviews', scope: {fields: ['rating']}
          }
        }
      }
    });
    let response = instance.toJSON();

    // repack the data into the desired shape, etc.
    response.reviews.sort((a, b) => b.creation_time - a.creation_time);
    response.reviews = response.reviews.slice(0, 10);
    response.latest_reviews = response.reviews.map((rev) => {
      return {
        id: rev.id,
        body: rev.body,
        rating: rev.rating,
        movie: {
          id: rev.movie.id,
          image: rev.movie.image,
          title: rev.movie.title,
          avg_rating: rev.movie.reviews.reduce(
            (total, r) => (total + r.rating), 0) / rev.movie.reviews.length
        },
      }
    });
    delete response.reviews;

    return response;
  }
};
