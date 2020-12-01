"""
Templates file for FeatureService seed generation
"""

deletion = """.then(() => {
        return knex('$table').del();
    })
    """

insertion = """.then(() => {
        return knex('$table').insert(
            $inserts
        );
    })
    """

del_insert = """.then(() => {
        return knex('$table').del();
    })
    .then(() => {
        return knex('$table').insert(
            $inserts
        );
    })
    """

single_raw_sql = 'knex.raw("$sql")'

raw_sql = """
    .then(() => {
        return """ + single_raw_sql + """;
    })
    """

initjs = """'use strict';

exports.seed = function(knex, Promise) {
    return Promise.all([
        $init
    ])
    $promises.then(() => {
        return Promise.all([
            $finish
        ]);
    });
};
"""
