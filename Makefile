.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -Ee -o pipefail

.PHONY: all load new-dataset generate-and-clean go load-postgres-helpers
.PHONY:	stop-docker reset-postgres
.PHONY: load-mongodb load-edgedb load-django load-sqlalchemy load-postgres
.PHONY: load-typeorm load-sequelize load-prisma
.PHONY: load-graphql load-hasura load-postgraphile
.PHONY: js-querybuilder


CURRENT_DIR = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))

DOCKER ?= docker
PSQL ?= psql

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
moviesplus=$(shell expr ${movies})


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
		| sed "s/%MOVIES%/$(moviesplus)/" > dataset/movies/review.json
	synth generate dataset/movies > $(BUILD)/protodataset.json
	$(PP) dataset/cleandata.py

generate-and-clean: 
	synth generate movies > $(BUILD)/protodataset.json
	$(PP) dataset/cleandata.py

docker-network:
	$(DOCKER) network inspect webapp-bench>/dev/null 2>&1 \
		|| $(DOCKER) network create --driver=bridge webapp-bench

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
	$(DOCKER) stop webapp-bench-postgres

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
		edgedb/edgedb:1
	sleep 3

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
	
	-edgedb project info
	-edgedb project unlink
	-edgedb instance unlink edgedb_bench
	edgedb -H localhost -P 15656 instance link \
		--non-interactive --trust-tls-cert --overwrite edgedb_bench \
	&& edgedb -H localhost -P 15656 project init --link \
		--non-interactive --server-instance edgedb_bench
	edgedb query 'CREATE DATABASE temp'
	edgedb -d temp query 'DROP DATABASE edgedb'
	edgedb -d temp query 'CREATE DATABASE edgedb'
	edgedb query 'DROP DATABASE temp'
	edgedb migrate
	$(PP) -m _edgedb.loaddata_nobulk $(BUILD)/edbdataset.json

load-edgedb: $(BUILD)/edbdataset.json docker-edgedb
	
	-edgedb project info
	-edgedb project unlink
	-edgedb instance unlink edgedb_bench
	edgedb -H localhost -P 15656 instance link \
		--non-interactive --trust-tls-cert --overwrite edgedb_bench \
	&& edgedb -H localhost -P 15656 project init --link \
		--non-interactive --server-instance edgedb_bench
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

	cd _sqlalchemy/migrations && $(PP) -m alembic.config upgrade head
	$(PP) _sqlalchemy/loaddata.py $(BUILD)/dataset.json

load-postgres: stop-docker reset-postgres $(BUILD)/dataset.json
	$(PSQL_CMD) -U postgres_bench -d postgres_bench \
			--file=$(CURRENT_DIR)/_postgres/schema.sql

	$(PP) _postgres/loaddata.py $(BUILD)/dataset.json

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
	cd _prisma
	npm i
	echo 'DATABASE_URL="postgresql://postgres_bench:edgedbbenchmark@localhost:15432/postgres_bench?schema=public"' > .env
	npx prisma generate && npm i

load-postgraphile: docker-postgres
	cd _postgraphile
	$(PSQL_CMD) -U postgres_bench -d postgres_bench \
			--file=$(CURRENT_DIR)_postgraphile/helpers.sql
	docker build -t postgraphile_bench:latest .
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

	cd _typeorm && npm i && npm run loaddata $(BUILD)/dataset.json

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

go:
	make -C _go

ts:
	cd _typeorm && npm i && npm run build

js-querybuilder:
	cd _edgedb_js && npx edgeql-js --output-dir querybuilder
