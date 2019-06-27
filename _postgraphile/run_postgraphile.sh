#!/bin/sh
set -ex

if [ "$(docker ps -q -f name=postgraphile-bench)" ]; then
    docker stop postgraphile-bench
fi

if [ "$(docker ps -aq -f status=exited -f name=postgraphile-bench)" ]; then
    docker rm postgraphile-bench
fi

PGDSL='postgres://postgres_bench:edgedbbenchmark@localhost:5432/postgres_bench'
docker run -d --net=host --rm --name postgraphile-bench postgraphile_bench \
    -p 8890 --graphql '/' --max-pool-size 1 --cluster-workers 10 \
    -c $PGDSL \
    --append-plugins @graphile-contrib/pg-many-to-many
