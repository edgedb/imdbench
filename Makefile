.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -Ee -o pipefail

.PHONY: all load new-dataset compile load-postgres-helpers
.PHONY:	stop-docker reset-postgres
.PHONY: load-mongodb load-edgedb load-django load-sqlalchemy load-postgres
.PHONY: load-typeorm load-sequelize load-prisma
.PHONY: load-graphql load-hasura load-postgraphile
.PHONY: run-js run-py run-orms run-graphql run-edgedb
.PHONY: run-cloud load-cloud load-edgedb-cloud load-supabase-sqla
.PHONY: load-planetscale-sqla

CURRENT_DIR = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))

EDGEDB_VERSION ?= latest

DOCKER ?= docker
PSQL ?= psql
MYSQL ?= mysql

PSQL_CMD = $(PSQL) -h localhost -p 15432 -U postgres
PYTHON ?= python
PP = PYTHONPATH=$(CURRENT_DIR) $(PYTHON)

BUILD=$(abspath dataset/build/)

# Parameters that can be passed to 'make new-dataset'
people?=100000
users?=100000
reviews?=500000
# about 7% of people are going to be directors
directors=$(shell expr ${people} \* 7 / 100)
# there's some overlap between directors and actors
directorsonly=$(shell expr ${people} \* 6 / 100)
movies=$(shell expr ${people} / 4)

all:
	@echo "pick a target"

$(BUILD)/edbdataset.json:
	cd dataset && $(PP) cleandata.py

$(BUILD)/dataset.json:
	cd dataset && $(PP) cleandata.py

new-dataset:
	mkdir -p dataset/movies
	cat dataset/templates/user.json \
		| sed "s/%USERS%/$(users)/" > dataset/movies/user.json
	cat dataset/templates/person.json \
		| sed "s/%PEOPLE%/$(people)/" \
		| sed "s/%STARTAT%/$(directorsonly)/" > dataset/movies/person.json
	cat dataset/templates/director.json \
		| sed "s/%DIRECTORS%/$(directors)/" > dataset/movies/director.json
	cat dataset/templates/movie.json \
		| sed "s/%MOVIES%/$(movies)/" > dataset/movies/movie.json
	cat dataset/templates/review.json \
		| sed "s/%REVIEWS%/$(reviews)/" \
		| sed "s/%MOVIES%/$(movies)/" > dataset/movies/review.json
	synth generate dataset/movies > $(BUILD)/protodataset.json
	$(PP) dataset/cleandata.py

docker-network:
	$(DOCKER) network inspect webapp-bench>/dev/null 2>&1 \
		|| $(DOCKER) network create \
			--driver=bridge \
			--opt com.docker.network.bridge.name=br-webapp-bench \
			webapp-bench

docker-network-destroy:
	$(DOCKER) network inspect webapp-bench>/dev/null 2>&1 \
		&& $(DOCKER) network rm webapp-bench

docker-postgres-volume:
	$(DOCKER) volume inspect webapp-bench-postgres >/dev/null 2>&1 \
		|| $(DOCKER) volume create webapp-bench-postgres

docker-postgres-volume-destroy:
	$(DOCKER) volume inspect webapp-bench-postgres >/dev/null 2>&1 \
		&& $(DOCKER) volume rm webapp-bench-postgres

docker-postgres: docker-network docker-postgres-volume
	$(DOCKER) stop webapp-bench-postgres >/dev/null 2>&1 || :
	$(DOCKER) run --rm -d --name webapp-bench-postgres \
		-v webapp-bench-postgres:/var/lib/postgresql/data \
		-e POSTGRES_HOST_AUTH_METHOD=trust \
		--network=webapp-bench \
		-p 15432:5432 \
		postgres:14
	sleep 3
	$(DOCKER) exec webapp-bench-postgres pg_isready -t10

docker-postgres-stop:
	-$(DOCKER) stop webapp-bench-postgres

docker-edgedb-volume:
	$(DOCKER) volume inspect webapp-bench-edgedb >/dev/null 2>&1 \
		|| $(DOCKER) volume create webapp-bench-edgedb

docker-edgedb-volume-destroy:
	$(DOCKER) volume inspect webapp-bench-edgedb >/dev/null 2>&1 \
		&& $(DOCKER) volume rm webapp-bench-edgedb

docker-edgedb: docker-network docker-edgedb-volume
	$(DOCKER) stop webapp-bench-edgedb >/dev/null 2>&1 || :
	$(DOCKER) run --rm -d --name webapp-bench-edgedb \
		-v webapp-bench-edgedb:/var/lib/edgedb/data \
		-e EDGEDB_SERVER_SECURITY=insecure_dev_mode \
		--network=webapp-bench \
		-p 15656:5656 \
		edgedb/edgedb:$(EDGEDB_VERSION)
	edgedb -H localhost -P 15656 \
		--tls-security=insecure --wait-until-available=120s \
		query "SELECT 'EdgeDB ready'"

docker-edgedb-stop:
	$(DOCKER) stop webapp-bench-edgedb

stop-docker:
	-$(DOCKER) stop hasura-bench
	-$(DOCKER) stop postgraphile-bench
	-$(DOCKER) stop webapp-bench-postgres
	-$(DOCKER) stop webapp-bench-edgedb

docker-clean: stop-docker docker-network-destroy \
              docker-postgres-volume-destroy docker-edgedb-volume-destroy

load-mongodb: $(BUILD)/edbdataset.json
	$(PP) -m _mongodb.loaddata $(BUILD)/edbdataset.json

load-edgedb-nobulk: $(BUILD)/edbdataset.json docker-edgedb
	-edgedb project unlink
	-edgedb instance destroy edgedb_bench --force
	edgedb -H localhost -P 15656 instance link \
		--non-interactive --trust-tls-cert --overwrite edgedb_bench \
	&& edgedb -H localhost -P 15656 project init --link \
		--non-interactive --no-migrations --server-instance edgedb_bench
	edgedb query 'CREATE DATABASE temp'
	edgedb -d temp query 'DROP DATABASE edgedb'
	edgedb -d temp query 'CREATE DATABASE edgedb'
	edgedb query 'DROP DATABASE temp'
	edgedb migrate
	$(PP) -m _edgedb.loaddata_nobulk $(BUILD)/edbdataset.json

load-edgedb: $(BUILD)/edbdataset.json docker-edgedb
	-edgedb project unlink --non-interactive
	-edgedb instance destroy edgedb_bench --force
	edgedb -H localhost -P 15656 instance link \
		--non-interactive --trust-tls-cert --overwrite edgedb_bench
	edgedb -H localhost -P 15656 project init --link \
		--non-interactive --no-migrations --server-instance edgedb_bench
	edgedb query 'CREATE DATABASE temp'
	edgedb -d temp query 'DROP DATABASE edgedb'
	edgedb -d temp query 'CREATE DATABASE edgedb'
	edgedb query 'DROP DATABASE temp'
	edgedb migrate
	$(PP) -m _edgedb.loaddata $(BUILD)/edbdataset.json
	cd _edgedb_js && npm i && npx @edgedb/generate edgeql-js --output-dir querybuilder --target cjs --force-overwrite

load-edgedb-cloud: $(BUILD)/edbdataset.json
	-edgedb project unlink --non-interactive
	edgedb project init --link --database edgedb \
		--non-interactive --no-migrations --server-instance $(EDGEDB_INSTANCE)
	edgedb query 'CREATE DATABASE temp'
	edgedb -d temp query 'DROP DATABASE edgedb'
	edgedb -d temp query 'CREATE DATABASE edgedb'
	edgedb query 'DROP DATABASE temp'
	edgedb migrate
	$(PP) -m _edgedb.loaddata $(BUILD)/edbdataset.json

load-edgedb-nosetup:
	$(PP) -m _edgedb.loaddata $(BUILD)/edbdataset.json


load-django: $(BUILD)/dataset.json docker-postgres
	$(PSQL_CMD) -tc \
		"DROP DATABASE IF EXISTS django_bench;"
	$(PSQL_CMD) -tc \
		"DROP ROLE IF EXISTS django_bench;"
	$(PSQL_CMD) -tc \
		"CREATE ROLE django_bench WITH \
			LOGIN ENCRYPTED PASSWORD 'edgedbbenchmark';"
	$(PSQL_CMD) -tc \
		"CREATE DATABASE django_bench WITH OWNER = django_bench;"

	$(PP) _django/manage.py flush --noinput
	$(PP) _django/manage.py migrate
	$(PP) -m _django.loaddata $(BUILD)/dataset.json

load-sqlalchemy: $(BUILD)/dataset.json docker-postgres
	$(PSQL_CMD) -tc \
		"DROP DATABASE IF EXISTS sqlalch_bench;"
	$(PSQL_CMD) -tc \
		"DROP ROLE IF EXISTS sqlalch_bench;"
	$(PSQL_CMD) -tc \
		"CREATE ROLE sqlalch_bench WITH \
			LOGIN ENCRYPTED PASSWORD 'edgedbbenchmark';"
	$(PSQL_CMD) -tc \
		"CREATE DATABASE sqlalch_bench WITH OWNER = sqlalch_bench;"

	cd _sqlalchemy/migrations && $(PP) -m alembic.config upgrade head && cd ../..
	$(PP) _sqlalchemy/loaddata.py $(BUILD)/dataset.json


load-postgres: docker-postgres-stop reset-postgres $(BUILD)/dataset.json
	$(PSQL_CMD) -U postgres_bench -d postgres_bench \
			--file=$(CURRENT_DIR)/_postgres/schema.sql

	$(PP) _postgres/loaddata.py $(BUILD)/dataset.json
	cd _postgres && npm i

load-planetscale-prisma: export MYSQL_PWD=$(PLANETSCALE_PASSWORD)
load-planetscale-prisma: $(BUILD)/dataset.json
	$(MYSQL) -h $(PLANETSCALE_HOST) -u $(PLANETSCALE_USER) \
		< $(CURRENT_DIR)/_postgres/planetscale.sql

	$(PP) _postgres/loaddata_planetscale.py $(BUILD)/dataset.json

	cd _prisma && \
	npm i && \
	echo 'DATABASE_URL="mysql://$(PLANETSCALE_USER):$(PLANETSCALE_PASSWORD)@$(PLANETSCALE_HOST):3306/$(PLANETSCALE_DATABASE)?sslaccept=strict&schema=public"' > .env && \
	npx prisma generate --schema=prisma/planetscale.prisma && npm i

reset-postgres: docker-postgres
	$(PSQL_CMD) -tc \
		"DROP DATABASE IF EXISTS postgres_bench;"
	$(PSQL_CMD) -U postgres -tc \
		"DROP ROLE IF EXISTS postgres_bench;"
	$(PSQL_CMD) -U postgres -tc \
		"CREATE ROLE postgres_bench WITH \
			LOGIN ENCRYPTED PASSWORD 'edgedbbenchmark';"
	$(PSQL_CMD) -U postgres -tc \
		"CREATE DATABASE postgres_bench WITH OWNER = postgres_bench;"

load-postgres-helpers: docker-postgres
	$(PSQL_CMD) -U postgres_bench -d postgres_bench -tc "\
		CREATE OR REPLACE VIEW movie_view AS \
		SELECT \
			movies.id, \
			movies.image, \
			movies.title, \
			movies.year, \
			movies.description, \
			movies.avg_rating AS avg_rating \
		FROM movies; \
		CREATE OR REPLACE VIEW person_view AS \
		SELECT \
			persons.id, \
			persons.first_name, \
			persons.middle_name, \
			persons.last_name, \
			persons.image, \
			persons.bio, \
			persons.full_name AS full_name \
		FROM persons; \
		"

load-hasura: load-postgres-helpers
	$(PSQL_CMD) -d postgres_bench -tc \
		"DROP SCHEMA IF EXISTS hdb_catalog CASCADE;"
	$(PSQL_CMD) -d postgres_bench -tc \
		"DROP SCHEMA IF EXISTS hdb_views CASCADE;"
	$(PSQL_CMD) -d postgres_bench -tc \
		"CREATE EXTENSION IF NOT EXISTS pgcrypto;"
	_hasura/docker-run.sh
	sleep 60s
	(cd _hasura && ./send-metadata.sh)

load-prisma: docker-postgres
	cd _prisma && \
	npm i && \
	echo 'DATABASE_URL="postgresql://postgres_bench:edgedbbenchmark@localhost:15432/postgres_bench?schema=public"' > .env && \
	npx prisma generate && npm i

load-postgraphile: docker-postgres
	cd _postgraphile && \
	$(PSQL_CMD) -U postgres_bench -d postgres_bench \
			--file=$(CURRENT_DIR)_postgraphile/helpers.sql && \
	docker build -t postgraphile_bench:latest . && \
	./run_postgraphile.sh

load-typeorm: $(BUILD)/dataset.json docker-postgres
	$(PSQL_CMD) -tc \
		"DROP DATABASE IF EXISTS typeorm_bench;"
	$(PSQL_CMD) -tc \
		"DROP ROLE IF EXISTS typeorm_bench;"
	$(PSQL_CMD) -tc \
		"CREATE ROLE typeorm_bench WITH \
			LOGIN ENCRYPTED PASSWORD 'edgedbbenchmark';"
	$(PSQL_CMD) -tc \
		"CREATE DATABASE typeorm_bench WITH OWNER = typeorm_bench;"

	cd _typeorm && \
	npm i && \
	npm run loaddata $(BUILD)/dataset.json && \
	npm run build

load-sequelize: $(BUILD)/dataset.json docker-postgres
	$(PSQL_CMD) -tc \
		"DROP DATABASE IF EXISTS sequelize_bench;"
	$(PSQL_CMD) -tc \
		"DROP ROLE IF EXISTS sequelize_bench;"
	$(PSQL_CMD) -tc \
		"CREATE ROLE sequelize_bench WITH \
			LOGIN ENCRYPTED PASSWORD 'edgedbbenchmark';"
	$(PSQL_CMD) -tc \
		"CREATE DATABASE sequelize_bench WITH OWNER = sequelize_bench;"

	cd _sequelize && npm i && node loaddata.js $(BUILD)/dataset.json

load: load-mongodb load-edgedb load-django load-sqlalchemy load-postgres \
	  load-typeorm load-sequelize load-prisma load-graphql

load-graphql: load-hasura load-postgraphile

PSQL_SUPABASE = $(PSQL) -h $(SUPABASE_HOST) -U postgres

load-supabase-sqla: export PGPASSWORD=$(SUPABASE_PASSWORD)
load-supabase-sqla: export SQLA_DSN=postgresql+asyncpg://postgres:$(SUPABASE_PASSWORD)@$(SUPABASE_HOST)/sqlalch_bench?async_fallback=true
load-supabase-sqla:
	$(PSQL_SUPABASE) -tc \
		"DROP DATABASE IF EXISTS sqlalch_bench;"
	$(PSQL_SUPABASE) -tc \
		"CREATE DATABASE sqlalch_bench;"

	cd _sqlalchemy/migrations && $(PP) -m alembic.config upgrade head && cd ../..
	$(PP) _sqlalchemy/loaddata.py $(BUILD)/dataset.json

load-planetscale-sqla: export SQLA_DSN=mysql://$(PLANETSCALE_USER):$(PLANETSCALE_PASSWORD)@$(PLANETSCALE_HOST)/$(PLANETSCALE_DATABASE)
load-planetscale-sqla: export IMDBENCH_EXTRA_ENV=planetscale
load-planetscale-sqla:
	cd _sqlalchemy/migrations && $(PP) -m alembic.config upgrade head && cd ../..
	$(PP) _sqlalchemy/loaddata.py $(BUILD)/dataset.json

load-cloud: load-edgedb-cloud load-supabase-sqla load-planetscale-sqla

compile:
	make -C _go

RUNNER = python bench.py --query insert_movie --query get_movie --query get_user --concurrency 1 --duration 10 --net-latency 1
CLOUD_RUNNER = python bench.py --query insert_movie --query get_movie --query get_user --concurrency 4 --duration 60 --async-split 4

run-js:
	$(RUNNER) --html docs/js.html --json docs/js.json typeorm sequelize prisma edgedb_js_qb

run-py:
	$(RUNNER) --html docs/py.html --json docs/py.json django sqlalchemy edgedb_py_sync

run-sql:
	$(RUNNER) --html docs/sql.html --json docs/sql.json edgedb_py_sync postgres_psycopg postgres_asyncpg postgres_pg postgres_pgx postgres_dart

run-graphql:
	$(RUNNER) --html docs/py.html --json docs/py.json postgres_hasura_go postgres_postgraphile_go edgedb_go_graphql

run-orms:
	$(RUNNER) --html docs/orms.html --json docs/orms.json typeorm sequelize prisma edgedb_js_qb django django_restfw mongodb sqlalchemy

run-edgedb:
	$(RUNNER) --html docs/edgedb.html --json docs/edgedb.json edgedb_py_sync edgedb_py_json edgedb_py_json_async edgedb_go edgedb_go_json edgedb_go_graphql edgedb_go_http edgedb_js edgedb_js_json edgedb_js_qb edgedb_dart edgedb_dart_json

run-scratch:
	python bench.py --query insert_movie --concurrency 1 --warmup-time 2 --duration 5 --html docs/scratch.html edgedb_go

run-cloud:
	$(CLOUD_RUNNER) --html docs/cloud.html --json docs/cloud.json edgedb_py_sync supabase_sqla planetscale_sqla
