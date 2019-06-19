"use strict";

module.exports = function(Person) {
  Person.afterInitialize = function() {
    this.full_name = this.middle_name
      ? this.first_name + " " + this.middle_name + " " + this.last_name
      : this.first_name + " " + this.last_name;
  };

  Person.personDetails = async function(id) {
    let instance = await Person.findById(id, {
      // unfortunately when 'scope' and 'fields' is used, nested
      // include stops working
      include: [
        {
          acted_in: { relation: "reviews", scope: { fields: ["rating"] } }
        },
        {
          directed: { relation: "reviews", scope: { fields: ["rating"] } }
        }
      ]
    });
    let response = instance.toJSON();

    response = {
      id: response.id,
      full_name: response.full_name,
      image: response.image,
      bio: response.bio,
      acted_in: response.acted_in,
      directed: response.directed
    };

    // repack the data into the desired shape, etc.
    for (let fname of ["acted_in", "directed"]) {
      let base = response[fname];
      base.sort((a, b) => a.year - b.year);

      response[fname] = base.map(movie => {
        return {
          id: movie.id,
          image: movie.image,
          title: movie.title,
          year: movie.year,
          avg_rating:
            movie.reviews.reduce((total, r) => total + r.rating, 0) /
            movie.reviews.length
        };
      });
    }

    return JSON.stringify(response);
  };
};
