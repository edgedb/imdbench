// Copyright IBM Corp. 2016. All Rights Reserved.
// Node module: loopback-workspace
// This file is licensed under the MIT License.
// License text available at https://opensource.org/licenses/MIT

'use strict';

var loopback = require('loopback');
var boot = require('loopback-boot');
const fs = require('fs');
const _ = require('lodash');
const ProgressBar = require('progress');

var app = module.exports = loopback();

const BATCH_SIZE = 1000;


async function bulk_insert(app, data, modelName) {
  let dataName = modelName.toLowerCase();
  let adj = true;
  var bar = new ProgressBar(
    _.padEnd(modelName, 31, ' ') + '|:bar| :current/:total\t:elapsed sec',
    {total: data[dataName].length, width: 32}
  );
  bar.tick();

  await app.dataSources.psqlDs.automigrate(modelName);

  for (var chunk of _.chunk(data[dataName], BATCH_SIZE)) {
    await app.dataSources.psqlDs.transaction(async models => {
      models[modelName].create(chunk, function(err) {
        if (err) throw err;
      });
    });

    if (adj) {
      bar.tick(chunk.length - 1);
      adj = false;
    } else {
      bar.tick(chunk.length);
    }
  }
}


// Bootstrap the application, configure models, datasources and middleware.
// Sub-apps like REST API are mounted via boot scripts.
boot(app, __dirname, async function(err) {
  if (err) throw err;

  if (process.argv.length != 3) {
    throw new Error(
      'Correct usage: node _loopback/server/loaddata.js dataset.json');
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

  await bulk_insert(app, data, 'User');
  await bulk_insert(app, data, 'Person');
  await bulk_insert(app, data, 'Movie');
  await bulk_insert(app, data, 'Review');
  await bulk_insert(app, data, 'Directors');
  await bulk_insert(app, data, 'Cast');

  console.log('Models created.');
});
