.PHONY: all load new-dataset go
.PHONY: load-mongodb load-edgedb load-django load-sqlalchemy

CURRENT_DIR = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))

PSQL ?= psql
PYTHON ?= python
PP = PYTHONPATH=$(CURRENT_DIR) $(PYTHON)

BUILD=$(abspath dataset/build/)

# Parameters that can be passed to 'make new-dataset'
people?=100000
users?=100000
reviews?=500000


all:
	@echo "pick a target"

$(BUILD)/dataset.json: $(BUILD)/dataset.pickle.gz
	$(PP) -m dataset.jsonser

new-dataset:
	$(PP) -m dataset $(people) $(users) $(reviews)

load-mongodb:
	$(PP) -m _mongodb.loaddata

load-edgedb:
	$(PP) -m _edgedb.initdb
	$(PP) -m _edgedb.loaddata

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
	$(PP) _sqlalchemy/loaddata.py $(BUILD)/dataset.json

load-postgres: reset-postgres $(BUILD)/dataset.json
	$(PSQL) -U postgres_bench -d postgres_bench \
			--file=$(CURRENT_DIR)/_postgres/schema.sql

	$(PP) _postgres/loaddata.py $(BUILD)/dataset.json

reset-postgres:
	-docker stop hasura-bench
	-docker stop prisma-bench && docker rm prisma-bench
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
	sleep 5s
	cd _hasura && ./send-metadata.sh

load-prisma: load-postgres-helpers
	[ "$(docker ps -q -f name=prisma-bench)" ] && docker stop prisma-bench \
		&& docker rm prisma-bench || true
	cd _prisma && docker-compose up -d
	sleep 5s
	cd _prisma && prisma deploy

load-loopback: $(BUILD)/dataset.json
	$(PSQL) -U postgres -tc \
		"DROP DATABASE IF EXISTS lb_bench;"
	$(PSQL) -U postgres -tc \
		"DROP ROLE IF EXISTS lb_bench;"
	$(PSQL) -U postgres -tc \
		"CREATE ROLE lb_bench WITH \
			LOGIN ENCRYPTED PASSWORD 'edgedbbenchmark';"
	$(PSQL) -U postgres -tc \
		"CREATE DATABASE lb_bench WITH OWNER = lb_bench;"

	cd _loopback && npm i && node server/loaddata.js $(BUILD)/dataset.json

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
	  load-loopback load-typeorm load-sequelize \
	  load-hasura load-prisma

go:
	make -C _edgedb_go

ts:
	cd _typeorm && npm i && tsc
