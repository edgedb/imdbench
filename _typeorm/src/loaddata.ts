import "reflect-metadata";
import {createConnection, InsertQueryBuilder} from "typeorm";
import {User} from "./entity/User"
import {Person} from "./entity/Person"
import {Movie} from "./entity/Movie"
import {Review} from "./entity/Review"
import {Directors} from "./entity/Directors"
import {Cast} from "./entity/Cast"

import * as _ from 'lodash';
import * as fs from 'fs';
import * as ProgressBar from 'progress';

const BATCH_SIZE = 1000;


async function bulk_insert(conn, data, Model) {
    let dataName = Model.name.toLowerCase();
    let adj = true;
    var bar = new ProgressBar(
        _.padEnd(Model.name, 31, ' ') + '|:bar| :current/:total\t:elapsed sec',
        {total: data[dataName].length, width: 32}
    );
    bar.tick();

    for (var chunk of _.chunk(data[dataName], BATCH_SIZE)) {
        let models = chunk.map((raw) => {
            let model = new Model();
            _.forEach(raw, (val, key) => {
                if (_.endsWith(key, '_id')) {
                    model[key.slice(0, -3)] = {id: val};
                } else {
                    model[key] = val;
                }
            });

            return model;
        });

        await conn.manager.save(models);

        if (adj) {
            bar.tick(chunk.length - 1);
            adj = false;
        } else {
            bar.tick(chunk.length);
        }
    }
}


createConnection().then(async connection => {

    if (process.argv.length != 3) {
        throw new Error(
        'Correct usage: npm run loaddata dataset.json');
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

    await bulk_insert(connection, data, User);
    await bulk_insert(connection, data, Person);
    await bulk_insert(connection, data, Movie);
    await bulk_insert(connection, data, Review);
    await bulk_insert(connection, data, Directors);
    await bulk_insert(connection, data, Cast);

    console.log('Models created.');

}).catch(error => console.log(error));
