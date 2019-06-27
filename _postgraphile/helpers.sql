--
-- Copyright (c) 2019 MagicStack Inc.
-- All rights reserved.
--
-- See LICENSE for details.
--

CREATE OR REPLACE FUNCTION persons_full_name(p persons) RETURNS text AS $$
    SELECT
        (CASE WHEN p.middle_name != '' THEN
            p.first_name || ' ' || p.middle_name || ' ' || p.last_name
         ELSE
            p.first_name || ' ' || p.last_name
         END);
$$ LANGUAGE SQL STABLE;

CREATE OR REPLACE FUNCTION movies_avg_rating(m movies) RETURNS numeric AS $$
    SELECT avg(rating)
    FROM reviews
    WHERE movie_id = m.id;
$$ LANGUAGE SQL STABLE;
