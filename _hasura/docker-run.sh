#! /bin/bash
docker run -d --net=host --name hasura-bench --rm \
       -e HASURA_GRAPHQL_DATABASE_URL=postgres://hasurauser:edgedbbenchmark@localhost:5432/postgres_bench \
       -e HASURA_GRAPHQL_ENABLE_CONSOLE=true \
       -e HASURA_GRAPHQL_PG_CONNECTIONS=10 \
       hasura/graphql-engine:v1.0.0-beta.2