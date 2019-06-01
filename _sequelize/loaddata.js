"use strict";

const Sequelize = require('sequelize');
const {App} = require("./models.js");

const fs = require('fs');
const _ = require('lodash');
const ProgressBar = require('progress');

const BATCH_SIZE = 1000;


async function bulk_insert(app, data, modelName) {
  let dataName = modelName.toLowerCase();
  let adj = true;
  var bar = new ProgressBar(
    _.padEnd(modelName, 31, ' ') + '|:bar| :current/:total\t:elapsed sec',
    {total: data[dataName].length, width: 32}
  );
  bar.tick();

  for (var chunk of _.chunk(data[dataName], BATCH_SIZE)) {
    await app.transaction(async function (Model, chunk, t) {
      await Model.bulkCreate(chunk);
    }.bind(null, app.models[modelName], chunk));

    if (adj) {
      bar.tick(chunk.length - 1);
      adj = false;
    } else {
      bar.tick(chunk.length);
    }
  }
}


async function main() {
  if (process.argv.length != 3) {
    throw new Error(
      'Correct usage: node _sequelize/loaddata.js dataset.json');
  }

  const dataset_path = process.argv[2];
  var dataset = JSON.parse(fs.readFileSync(dataset_path, 'utf8'));
  var data = {};

  for (let rec of dataset) {
    let rtype = rec.model.split('.')[1];
    let datum = rec.fields;
    if (rec.pk !== undefined) {
      datum.id = rec.pk;
    }
    // convert datetime
    if (rtype == 'review') {
      datum.creation_time = new Date(datum.creation_time);
    }

    if (!(rtype in data)) {
      data[rtype] = [];
    }
    data[rtype].push(datum);
  }

  var sequelize = new App({
    pool: {
      max: 10
    }
  });
  await sequelize.sync({force: true});

  await bulk_insert(sequelize, data, 'User');
  await bulk_insert(sequelize, data, 'Person');
  await bulk_insert(sequelize, data, 'Movie');
  await bulk_insert(sequelize, data, 'Review');
  await bulk_insert(sequelize, data, 'Directors');
  await bulk_insert(sequelize, data, 'Cast');

  // creating these particular indexes is awkward in the model description
  await sequelize.getQueryInterface().addIndex('Review', {
    using: 'btree',
    fields: ['author_id'],
  });
  await sequelize.getQueryInterface().addIndex('Review', {
    using: 'btree',
    fields: ['movie_id'],
  });

  console.log('Models created.');
}

main();
