.ONESHELL:
SHELL = /bin/bash
.SHELLFLAGS += -Ee -o pipefail

.PHONY: all load new-dataset go load-postgres-helpers
.PHONY:	stop-docker reset-postgres
.PHONY: load-mongodb load-edgedb load-django load-sqlalchemy load-postgres
.PHONY: load-typeorm load-sequelize load-prisma
.PHONY: load-graphql load-hasura load-postgraphile
.PHONY: js-querybuilder

CURRENT_DIR = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))

PSQL ?= psql -h localhost
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
moviesplus=$(shell expr ${movies} + 1)


all:
	@echo "pick a target"

$(BUILD)/edbdataset.json:
	cd dataset && $(PP) cleandata.py

$(BUILD)/dataset.json:
	cd dataset && $(PP) cleandata.py

new-dataset:
	cd dataset
	mkdir -p movies
	cat templates/user.json \
		| sed "s/%USERS%/$(users)/" > movies/user.json
	cat templates/person.json \
		| sed "s/%PEOPLE%/$(people)/" \
		| sed "s/%STARTAT%/$(directorsonly)/" > movies/person.json
	cat templates/director.json \
		| sed "s/%DIRECTORS%/$(directors)/" > movies/director.json
	cat templates/movie.json \
		| sed "s/%MOVIES%/$(movies)/" > movies/movie.json
	cat templates/review.json \
		| sed "s/%REVIEWS%/$(reviews)/" \
		| sed "s/%MOVIES%/$(moviesplus)/" > movies/review.json
	synth generate movies > $(BUILD)/protodataset.json
	$(PP) cleandata.py

load-mongodb: $(BUILD)/edbdataset.json
	$(PP) -m _mongodb.loaddata $(BUILD)/edbdataset.json

load-edgedb: $(BUILD)/edbdataset.json
	edgedb project info || edgedb project init --server-instance edgedb_bench
	edgedb query 'CREATE DATABASE temp'
	edgedb -d temp query 'DROP DATABASE edgedb'
	edgedb -d temp query 'CREATE DATABASE edgedb'
	edgedb query 'DROP DATABASE temp'
	edgedb migrate
	$(PP) -m _edgedb.loaddata $(BUILD)/edbdataset.json

load-django: $(BUILD)/dataset.json
	$(PSQL) -U postgres -tc \
		"DROP DATABASE IF EXISTS django_bench;"
	$(PSQL) -U postgres -tc \
		"DROP ROLE IF EXISTS django_bench;"
	$(PSQL) -U postgres -tc \
		"CREATE ROLE django_bench WITH \
			LOGIN ENCRYPTED PASSWORD 'edgedbbenchmark';"
	$(PSQL) -U postgres -tc \
		"CREATE DATABASE django_bench WITH OWNER = django_bench;"

	$(PP) _django/manage.py flush --noinput
	$(PP) _django/manage.py migrate
	$(PP) -m _django.loaddata $(BUILD)/dataset.json

load-sqlalchemy: $(BUILD)/dataset.json
	$(PSQL) -U postgres -tc \
		"DROP DATABASE IF EXISTS sqlalch_bench;"
	$(PSQL) -U postgres -tc \
		"DROP ROLE IF EXISTS sqlalch_bench;"
	$(PSQL) -U postgres -tc \
		"CREATE ROLE sqlalch_bench WITH \
			LOGIN ENCRYPTED PASSWORD 'edgedbbenchmark';"
	$(PSQL) -U postgres -tc \
		"CREATE DATABASE sqlalch_bench WITH OWNER = sqlalch_bench;"

	cd _sqlalchemy/migrations && $(PP) -m alembic.config upgrade head
	cd .. && $(PP) loaddata.py $(BUILD)/dataset.json

load-postgres: stop-docker reset-postgres $(BUILD)/dataset.json
	$(PSQL) -U postgres_bench -d postgres_bench \
			--file=$(CURRENT_DIR)/_postgres/schema.sql

	$(PP) _postgres/loaddata.py $(BUILD)/dataset.json

stop-docker:
	-docker stop hasura-bench
	-docker stop postgraphile-bench

reset-postgres:
	$(PSQL) -U postgres -tc \
		"DROP DATABASE IF EXISTS postgres_bench;"
	$(PSQL) -U postgres -tc \
		"DROP ROLE IF EXISTS postgres_bench;"
	$(PSQL) -U postgres -tc \
		"CREATE ROLE postgres_bench WITH \
			LOGIN ENCRYPTED PASSWORD 'edgedbbenchmark';"
	$(PSQL) -U postgres -tc \
		"CREATE DATABASE postgres_bench WITH OWNER = postgres_bench;"

load-postgres-helpers:
	$(PSQL) -U postgres_bench -d postgres_bench -tc "\
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
	$(PSQL) -U postgres -d postgres_bench -tc \
		"DROP SCHEMA IF EXISTS hdb_catalog CASCADE;"
	$(PSQL) -U postgres -d postgres_bench -tc \
		"DROP SCHEMA IF EXISTS hdb_views CASCADE;"
	$(PSQL) -U postgres -d postgres_bench -tc \
		"CREATE EXTENSION IF NOT EXISTS pgcrypto;"
	_hasura/docker-run.sh
	sleep 60s
	(cd _hasura && ./send-metadata.sh)

load-prisma: load-postgres-helpers
	cd _prisma
	echo 'DATABASE_URL="postgresql://postgres_bench:edgedbbenchmark@localhost:5432/postgres_bench?schema=public"' > .env
	npx prisma generate && npm i

load-postgraphile:
	cd _postgraphile
	$(PSQL) -U postgres_bench -d postgres_bench \
			--file=$(CURRENT_DIR)_postgraphile/helpers.sql
	docker build -t postgraphile_bench:latest .
	./run_postgraphile.sh

load-typeorm: $(BUILD)/dataset.json
	$(PSQL) -U postgres -tc \
		"DROP DATABASE IF EXISTS typeorm_bench;"
	$(PSQL) -U postgres -tc \
		"DROP ROLE IF EXISTS typeorm_bench;"
	$(PSQL) -U postgres -tc \
		"CREATE ROLE typeorm_bench WITH \
			LOGIN ENCRYPTED PASSWORD 'edgedbbenchmark';"
	$(PSQL) -U postgres -tc \
		"CREATE DATABASE typeorm_bench WITH OWNER = typeorm_bench;"

	cd _typeorm && npm i && npm run loaddata $(BUILD)/dataset.json

load-sequelize: $(BUILD)/dataset.json
	$(PSQL) -U postgres -tc \
		"DROP DATABASE IF EXISTS sequelize_bench;"
	$(PSQL) -U postgres -tc \
		"DROP ROLE IF EXISTS sequelize_bench;"
	$(PSQL) -U postgres -tc \
		"CREATE ROLE sequelize_bench WITH \
			LOGIN ENCRYPTED PASSWORD 'edgedbbenchmark';"
	$(PSQL) -U postgres -tc \
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
	cd _edgedb_js && npx edgedb-generate --output-dir querybuilder
