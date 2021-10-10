#! /bin/bash

set -ex

if [ "$(docker ps -q -f name=hasura-bench)" ]; then
    docker stop hasura-bench
fi

if [ "$(docker ps -aq -f status=exited -f name=hasura-bench)" ]; then
    docker rm hasura-bench
fi

docker run -d --net=host --name hasura-bench --rm \
       -e HASURA_GRAPHQL_DATABASE_URL=postgres://postgres_bench:edgedbbenchmark@localhost:5432/postgres_bench \
       -e HASURA_GRAPHQL_ENABLE_CONSOLE=true \
       -e HASURA_GRAPHQL_LOG_LEVEL=error \
       hasura/graphql-engine:v2.0.9
