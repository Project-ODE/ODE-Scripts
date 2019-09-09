"""
Templates file for FeatureService seed generation
"""

del_insert = """
    .then(() => {
        return knex('$table').del();
    })
    .then(() => {
        return knex('$table').insert(
            $inserts
        );
    })"""

initjs = """
'use strict';

exports.seed = function(knex, Promise) {
    return knex('users').del()
    .then(() => {
        return knex('users').insert(
            $users
        );
    })
    $promises
    .then(() => {
        // The following lines set index autoincrement counter to 1000
        // We have to do this since previous inserts don't change increment counter on PGSQL
        return Promise.all([
            knex.raw('ALTER SEQUENCE users_id_seq RESTART WITH 1000'),
            knex.raw('ALTER SEQUENCE dataset_types_id_seq RESTART WITH 1000'),
            knex.raw('ALTER SEQUENCE geo_metadata_id_seq RESTART WITH 1000'),
            knex.raw('ALTER SEQUENCE audio_metadata_id_seq RESTART WITH 1000'),
            knex.raw('ALTER SEQUENCE datasets_id_seq RESTART WITH 1000'),
            knex.raw('ALTER SEQUENCE dataset_files_id_seq RESTART WITH 1000'),
            knex.raw('ALTER SEQUENCE annotation_sets_id_seq RESTART WITH 1000'),
            knex.raw('ALTER SEQUENCE annotation_tags_id_seq RESTART WITH 1000'),
            knex.raw('ALTER SEQUENCE annotation_set_tags_id_seq RESTART WITH 1000'),
            knex.raw('ALTER SEQUENCE annotation_campaigns_id_seq RESTART WITH 1000'),
            knex.raw('ALTER SEQUENCE annotation_campaign_datasets_id_seq RESTART WITH 1000'),
            knex.raw('ALTER SEQUENCE annotation_tasks_id_seq RESTART WITH 1000')
        ]);
    });
};
"""
