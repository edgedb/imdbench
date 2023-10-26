Run locally
###########


#. Install Python 3.8+, then create and activate a virtual environment.

   .. code-block::

      $ python -m venv my_venv
      $ source my_venv/bin/activate

   The steps below assume your virtual environment is activated. To deactivate 
   the venv, just run ``deactivate`` at any time. Read the full `Virtual 
   Environment <https://docs.python.org/3/tutorial/venv.html>`_ docs 
   for details.

#. Install Python dependencies

   .. code-block::

      pip install -r requirements.txt

#. Install the following toolchains:

   - `EdgeDB <https://www.edgedb.com/install>`_
   - `PostgreSQL Client <https://www.postgresql.org/docs/current/installation.html>`_

#. Install `Synth <https://www.getsynth.com>`_

#. Generate the dataset.

   .. code-block::

      $ make new-dataset

#. Create an EdgeDB instance:

   .. code-block::

      $ edgedb cloud login
      $ edgedb instance create your-org/instance-name
      $ export EDGEDB_INSTANCE=your-org/instance-name

#. Create a Supabase project:

   Create a new project on supabase.com, and retrieve the following information
   from Settings - Database:

   .. code-block::

      $ export SUPABASE_HOST=db.xxxxxxxx.supabase.co
      $ export SUPABASE_PASSWORD=your_password

#. Create a PlanetScale database and branch:

   Create a new project on planetscale.com. Always create a new branch and
   password from the empty project, for each `make load-*` call:

   .. code-block::

      $ export PLANETSCALE_USER=generated_user
      $ export PLANETSCALE_PASSWORD=generated_password
      $ export PLANETSCALE_HOST=aws.connect.psdb.cloud  # or use direct
      $ export PLANETSCALE_DATABASE=your_database

#. Load the data into the test databases via ``$ make load-cloud``.
   Alternatively, you can run only the loaders you care about:

   .. code-block::

      $ make load-edgedb-cloud

#. Run the Cloud benchmarks

   .. code-block::
      
      $ make run-cloud
   
   The results will be generated into ``docs/cloud.html``.
