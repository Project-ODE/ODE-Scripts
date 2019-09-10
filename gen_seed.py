#!/bin/python3

import argparse
import csv
from pathlib import Path
from string import Template

import initjs_templates

PARSER = argparse.ArgumentParser(description='Script that generates a png spectrogram from an audio wav file')
PARSER.add_argument('seed_folder', help='Path to the folder containing wav files and the three required CSVs')
USERS = [
    'admin@test.ode',
    'dc@test.ode',
    'ek@test.ode',
    'ja@test.ode',
    'pnhd@test.ode',
    'ad@test.ode',
    'rv@test.ode',
]
USER_MDP = '$2a$10$RTELpt2ltJpjDEYRhU1NR.uK8hw4pdVCWZNl5FCRYx.ejUI7LMzb.'
REQUIRED_FILES = ['datasets.csv', 'dataset_files.csv', 'annotation_campaigns.csv']

# TODO add header checking for CSV

def main(seed_folder):
    # Generating users
    users = []
    for i, user in enumerate(USERS):
        users.append({
            'id': i + 1,
            'email': user,
            'password': USER_MDP
        })


    # Loading CSV files data in a dict
    data = {}
    for file in REQUIRED_FILES:
        with open(seed_folder / file, 'r') as csvfile:
            data[file] = list(csv.DictReader(csvfile, skipinitialspace=True))

    inserts = ""

    # Generating dataset_types
    dataset_types = {
        ds['dataset_type_name']:{
            'name': ds['dataset_type_name'],
            'desc': ds['dataset_type_description']
        } for ds in data['datasets.csv']
    }
    for i, key in enumerate(dataset_types.keys()):
        dataset_types[key]['id'] = i + 1
    inserts += Template(initjs_templates.del_insert).substitute({
        'table': 'dataset_types',
        'inserts': list(dataset_types.values())
    })

    # Generating geo_metadata
    geo_metadata = {
        ds['location_name']:{
            'name': ds['location_name'],
            'desc': ds['location_desc'],
            'location': ds['location_lat'] + ', ' + ds['location_lon']
        } for ds in data['datasets.csv']
    }
    sql_locations = []
    for i, key in enumerate(geo_metadata.keys()):
        geo_metadata[key]['id'] = i + 1
        # Location needs to be given in sql
        latlon = geo_metadata[key].pop('location')
        if latlon.strip(' ,') != '':
            location = f"POINT({latlon})"
            sql_locations.append(Template(initjs_templates.raw_sql).substitute({
                'sql': f"UPDATE geo_metadata SET location = {location} WHERE id = {i + 1}"
            }))
    inserts += Template(initjs_templates.del_insert).substitute({
        'table': 'geo_metadata',
        'inserts': list(geo_metadata.values())
    })
    for sql_location in sql_locations:
        inserts += sql_location

    # Generating audio_metadata
    dataset_audio_metadata = {
        ds['name']:{
            key[6:]:val for key, val in ds.items() if key.startswith('audio_') and val != ''
        } for ds in data['datasets.csv']
    }
    dataset_files_audio_metadata = {
        dsf['filename']:{
            key[6:]:val for key, val in dsf.items() if key.startswith('audio_') and val != ''
        } for dsf in data['dataset_files.csv']
    }
    audio_metadata = { **dataset_audio_metadata, **dataset_files_audio_metadata }
    for i, key in enumerate(audio_metadata.keys()):
        audio_metadata[key]['id'] = i + 1
    inserts += Template(initjs_templates.del_insert).substitute({
        'table': 'audio_metadata',
        'inserts': list(audio_metadata.values())
    })

    # Generating datasets
    datasets = {
        ds['name']:{
            'name': ds['name'],
            'start_date': ds['start_date'],
            'end_date': ds['end_date'],
            'files_type': ds['files_type'],
            'status': 1,
            'dataset_type_id': dataset_types[ds['dataset_type_name']]['id'],
            'geo_metadata_id': geo_metadata[ds['location_name']]['id'],
            'audio_metadata_id': audio_metadata[ds['name']]['id'],
            'owner_id': 1
        } for ds in data['datasets.csv']
    }
    for i, key in enumerate(datasets.keys()):
        datasets[key]['id'] = i + 1
    inserts += Template(initjs_templates.del_insert).substitute({
        'table': 'datasets',
        'inserts': list(datasets.values())
    })

    # Generating dataset_files
    dataset_files = {
        dsf['filename']:{
            'filename': dsf['filename'],
            'size': (seed_folder / dsf['filename']).stat().st_size,
            'dataset_id': datasets[dsf['dataset_name']]['id'],
            'audio_metadata_id': audio_metadata[dsf['filename']]['id']
        } for dsf in data['dataset_files.csv']
    }
    for i, key in enumerate(dataset_files.keys()):
        dataset_files[key]['id'] = i + 1
    inserts += Template(initjs_templates.del_insert).substitute({
        'table': 'dataset_files',
        'inserts': list(dataset_files.values())
    })

    # Generating annotation_sets
    annotation_sets = {
        ac['annotation_set'].replace(' ', ''):{
            'name': ac['name'],
            'desc': 'Annotation set made for ' + ac['name'],
            'owner_id': 1
        } for ac in data['annotation_campaigns.csv']
    }
    for i, key in enumerate(annotation_sets.keys()):
        annotation_sets[key]['id'] = i + 1
    inserts += Template(initjs_templates.del_insert).substitute({
        'table': 'annotation_sets',
        'inserts': list(annotation_sets.values())
    })

    # Generating annotation_tags
    annotation_tags = {
        tag:{
            'id': i + 1,
            'name': tag
        } for i, tag in enumerate(','.join(annotation_sets.keys()).split(','))
    }
    inserts += Template(initjs_templates.del_insert).substitute({
        'table': 'annotation_tags',
        'inserts': list(annotation_tags.values())
    })

    # Generating annotation_set_tags_id
    annotation_set_tags = []
    k_id = 0
    for annotation_set in annotation_sets.keys():
        for tag in annotation_set.split(','):
            k_id += 1
            annotation_set_tags.append({
                'id': k_id,
                'annotation_set_id': annotation_sets[annotation_set]['id'],
                'annotation_tag_id': annotation_tags[tag]['id']
            })
    inserts += Template(initjs_templates.del_insert).substitute({
        'table': 'annotation_set_tags',
        'inserts': annotation_set_tags
    })

    # Generating annotation_campaigns
    annotation_campaigns = {
        ac['name']:{
            'name': ac['name'],
            'desc': ac['desc'],
            'start': ac['start'],
            'end': ac['end'],
            'annotation_set_id': annotation_sets[ac['annotation_set'].replace(' ', '')]['id'],
            'owner_id': 1
        } for ac in data['annotation_campaigns.csv']
    }
    for i, key in enumerate(annotation_campaigns.keys()):
        annotation_campaigns[key]['id'] = i + 1
    inserts += Template(initjs_templates.del_insert).substitute({
        'table': 'annotation_campaigns',
        'inserts': list(annotation_campaigns.values())
    })

    # Generating annotation_campaign_datasets
    annotation_campaign_datasets = []
    for i, line in enumerate(data['annotation_campaigns.csv']):
        annotation_campaign_datasets.append({
            'id': i + 1,
            'annotation_campaign_id': annotation_campaigns[line['name']]['id'],
            'dataset_id': datasets[line['dataset_name']]['id']
        })
    inserts += Template(initjs_templates.del_insert).substitute({
        'table': 'annotation_campaign_datasets',
        'inserts': annotation_campaign_datasets
    })


    # Generating annotation_tasks
    user_count = initjs_templates.initjs.count('@test.ode')
    annotation_tasks = []
    annotation_files = { dataset['id']:[] for dataset in datasets.values() }
    for dataset_file in dataset_files.values():
        annotation_files[dataset_file['dataset_id']].append(dataset_file['id'])
    k_id = 0
    for campaign in annotation_campaign_datasets:
        for file_id in annotation_files[campaign['dataset_id']]:
            for user_id in range(1, len(USERS) + 1):
                k_id += 1
                annotation_tasks.append({
                    'id': k_id,
                    'annotation_campaign_id': campaign['annotation_campaign_id'],
                    'dataset_file_id': file_id,
                    'status': 0,
                    'annotator_id': user_id
                })
    inserts += Template(initjs_templates.del_insert).substitute({
        'table': 'annotation_tasks',
        'inserts': annotation_tasks
    })

    template_data = { 'users': users, 'promises': inserts }
    with open(seed_folder / 'init.js', 'w') as res_f:
        res_f.write(Template(initjs_templates.initjs).substitute(template_data))

if __name__ == '__main__':

    ARGS = PARSER.parse_args()

    main(Path(ARGS.seed_folder))
