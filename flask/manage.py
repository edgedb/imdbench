#!/usr/bin/env python3

from flask_migrate import Migrate, MigrateCommand

import webapp


app = webapp.app
migrate = Migrate(app, app.db)
app.manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    app.manager.run()
