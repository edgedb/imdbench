module default {
  abstract type HasImage {
    required property image -> str; # a URL to the image
    index on (.image);
  }

  type User extending HasImage {
    required property name -> str;
  }

  type Review {
    required property body -> str;
    required property rating -> int64 {
      constraint min_value(0);
      constraint max_value(5);
    }

    required link author -> User;
    required link movie -> Movie;

    required property creation_time -> cal::local_datetime {
      default := cal::to_local_datetime(datetime_current(), 'UTC')
    }
  }

  type Person extending HasImage {
    required property first_name -> str;
    required property middle_name -> str {
      default := '';
    }
    required property last_name -> str;
    property full_name :=
      (
        .first_name ++ ' ' ++
        (
          (.middle_name ++ ' ')
          IF .middle_name != '' ELSE
          ''
        ) ++
        .last_name
      );
    property bio -> str;
  }


  type Movie extending HasImage {
    required property title -> str;
    required property year -> int64;
    required property description -> str;
    multi link directors  -> Person {
      property list_order -> int64;
    }
    multi link cast  -> Person {
      property list_order -> int64;
    }
    property avg_rating := math::mean(.<movie[IS Review].rating);
  }


}
