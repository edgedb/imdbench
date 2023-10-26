from __future__ import with_statement

import os

from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
import logging

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
import _sqlalchemy.models
target_metadata = _sqlalchemy.models.Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

dsn = "".join([
    "postgresql+asyncpg://",
    os.environ.get("PGUSER", "sqlalch_bench"),
    ":",
    os.environ.get("PGPASSWORD", "edgedbbenchmark"),
    "@",
    os.environ.get("PGHOST", "localhost"),
    ":",
    os.environ.get("PGPORT", "15432"),
    "/",
    os.environ.get("PGDATABASE", os.environ.get("PGUSER", "sqlalch_bench")),
    "?async_fallback=true",
])


def run_migrations_offline():
    """Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    context.configure(
        url=dsn, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    conf = config.get_section(config.config_ini_section)
    conf["sqlalchemy.url"] = dsn
    connectable = engine_from_config(
        conf,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
