CREATE MIGRATION m1tdqg3z7lk27ovo42pne2jwvgw23pskunp2rjyo6kn7myu55wuvza
    ONTO initial
{
  CREATE ABSTRACT LINK default::crew {
      CREATE PROPERTY list_order -> std::int64;
  };
  CREATE ABSTRACT TYPE default::HasImage {
      CREATE REQUIRED PROPERTY image -> std::str;
      CREATE INDEX ON (.image);
  };
  CREATE TYPE default::Movie EXTENDING default::HasImage {
      CREATE REQUIRED PROPERTY description -> std::str;
      CREATE REQUIRED PROPERTY title -> std::str;
      CREATE REQUIRED PROPERTY year -> std::int64;
  };
  CREATE TYPE default::User EXTENDING default::HasImage {
      CREATE REQUIRED PROPERTY name -> std::str;
  };
  CREATE TYPE default::Review {
      CREATE REQUIRED LINK movie -> default::Movie;
      CREATE REQUIRED LINK author -> default::User;
      CREATE REQUIRED PROPERTY creation_time -> cal::local_datetime {
          SET default := (cal::to_local_datetime(std::datetime_current(), 'UTC'));
      };
      CREATE REQUIRED PROPERTY rating -> std::int64 {
          CREATE CONSTRAINT std::max_value(5);
          CREATE CONSTRAINT std::min_value(0);
      };
      CREATE REQUIRED PROPERTY body -> std::str;
  };
  CREATE ALIAS default::GraphQLMovieDetails := (
      SELECT
          default::Movie {
              reviews := (SELECT
                  default::Movie.<movie[IS default::Review]
              )
          }
  );
  CREATE TYPE default::Person EXTENDING default::HasImage {
      CREATE PROPERTY bio -> std::str;
      CREATE REQUIRED PROPERTY first_name -> std::str;
      CREATE REQUIRED PROPERTY last_name -> std::str;
      CREATE REQUIRED PROPERTY middle_name -> std::str {
          SET default := '';
      };
      CREATE PROPERTY full_name := ((((.first_name ++ ' ') ++ ((.middle_name ++ ' ') IF (.middle_name != '') ELSE '')) ++ .last_name));
  };
  ALTER TYPE default::Movie {
      CREATE MULTI LINK cast EXTENDING default::crew -> default::Person;
      CREATE MULTI LINK directors EXTENDING default::crew -> default::Person;
      CREATE PROPERTY avg_rating := (math::mean(.<movie[IS default::Review].rating));
  };
  CREATE ALIAS default::GraphQLPersonDetails := (
      SELECT
          default::Person {
              acted_in := (SELECT
                  default::Person.<cast[IS default::Movie]
              ),
              directed := (SELECT
                  default::Person.<directors[IS default::Movie]
              )
          }
  );
  CREATE ALIAS default::GraphQLUserDetails := (
      SELECT
          default::User {
              latest_reviews := (SELECT
                  default::User.<author[IS default::Review]
              ORDER BY
                  .creation_time DESC
              )
          }
  );
  CREATE EXTENSION edgeql_http VERSION '1.0';
  CREATE EXTENSION graphql VERSION '1.0';
  CREATE ABSTRACT LINK default::cast EXTENDING default::crew;
  CREATE ABSTRACT LINK default::directors EXTENDING default::crew;
};
