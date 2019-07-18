#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import os
import sys
import csv
import json
import argparse
from pprint import pprint

import ckanapi
from slugify import slugify
from dateutil.parser import parse as parse_date


def _get_script_root():

    return os.path.dirname(os.path.abspath(__file__))


def _get_schema():
    file_path = os.path.join(_get_script_root(), '..', 'ckanext', 'honduras',
        'dataset.json')
    with open(file_path, 'r') as f:
        schema = json.load(f)
    return schema


def _get_choice_value(name, label, is_resource=False):
    schema = _get_schema()
    fields = schema['resource_fields'] if is_resource else schema['dataset_fields']
    for field in fields:
        if field['field_name'] == name:
            for choice in field.get('choices', []):
                if choice.get('label').encode('utf8') == label:
                        return choice.get('value')
    return label


def _iso_date(date_str):
    return parse_date(date_str).isoformat()


def _get_dataset_dict(row):

    dataset_dict = {
        'resources': []
    }
    fields = [
        'title',
        'issued',
        'modified',
        'temporal',
        'spatial',
        'describedBy',
        'references',
        'contactPoint',
    ]
    if row.get('identifier'):
        dataset_dict['name'] = slugify(row['identifier'])
    else:
        dataset_dict['name'] = slugify(row['title'])

    for field in fields:
        if row.get(field):
            dataset_dict[field] = row[field].strip()

    for field in ('issued', 'modified'):
        if row.get(field):
            dataset_dict[field] = _iso_date(row[field].strip())

    if row.get('description'):
        dataset_dict['notes'] = row['description']

    if row.get('keyword'):
        dataset_dict['tag_string'] = row['keyword']

    if row['license'] == 'https://creativecommons.org/licenses/by/4.0/deed.es':
        dataset_dict['license_id'] = 'CC-BY-4.0'
    elif row['license'] == 'https://creativecommons.org/licenses/by-sa/4.0/deed.es_ES':
        dataset_dict['license_id'] = 'CC-BY-SA-4.0'

    if row.get('theme'):
        dataset_dict['groups'] = [
            {'name': slugify(row['theme'])}
        ]

    if row.get('accrualPeriodicity'):
        dataset_dict['frequency'] = _get_choice_value('frequency', row['accrualPeriodicity'])

    return dataset_dict

def _get_resource_dict(row):

    resource_dict = {}
    resource_dict['name'] = row['title-resource']

    if not resource_dict['name']:
        return {}

    resource_dict['description'] = row['description-resource']
    resource_dict['describedBy'] = row['describedBy-resource']

    if row['byteSize-resource']:
        resource_dict['size'] = row['byteSize-resource']
    if row['mediaType-resource']:
        _format = row['mediaType-resource']
        resource_dict['format'] =  _format if not _format.startswith('ZIP') else 'ZIP'

    resource_dict['identifier'] = '{}_{}'.format(
        row['identifier-resource'], resource_dict['format'].lower())
    if row['accessURL-resource']:
        resource_dict['url'] = row['accessURL-resource']
        resource_dict['access_url'] = row['accessURL-resource']
    elif row['downloadURL-resource']:
        resource_dict['download_url'] = row['downloadURL-resource']
        if row['downloadURL-resource'].startswith('https://drive.google.com'):
            resource_dict['url'] = '_placeholder'
        else:
            resource_dict['url'] = row['downloadURL-resource']

    return resource_dict

def _create_or_update_dataset(dataset_dict, ckan):

    try:
        ckan.action.package_show(id=dataset_dict['name'])
        action = ckan.action.package_update
        action_name = 'update'
    except ckanapi.errors.NotFound:
        action = ckan.action.package_create
        action_name = 'create'

    try:
        result = action(**dataset_dict)
    except ckanapi.errors.ValidationError as e:
        print(
            '\n#####  Errors found for dataset "{}": {}\n'.format(dataset_dict['title'], e))
        return
    else:
        print('{} dataset "{}"'.format(action_name.title(), dataset_dict['title']))

    # Check if there are files to upload
    for resource in result['resources']:
        if resource.get('download_url') and resource['download_url'].startswith('https://drive.google.com'):

            # Try to find the corresponding file
            i = resource['identifier'].rfind('_')

            file_name = '{}.{}'.format(resource['identifier'][:i], resource['format'].lower())

            file_path = os.path.join(_get_script_root(), 'data', file_name)

            if not os.path.exists(file_path):
                print('\n##### Error: could not find file to upload for this resource ({})\n'.format(file_name))
            resource['upload'] = open(file_path, 'rb')
            try:

                result = ckan.action.resource_update(**resource)
            except ckanapi.errors.ValidationError as e:
                print(
                    '\n#####  Errors found uploading file {}: {}\n'.format(file_name, e))
            else:
                print('Uploaded file {} to resource {} from dataset {}'.format(
                    file_name, resource['id'], dataset_dict['title']))


def process_datasets(org, csv_file_path, url, api_key, start_index, dry_run):

    ckan = ckanapi.RemoteCKAN(url, api_key)

    with open(csv_file_path, 'rb') as csv_file:
        reader = csv.DictReader(csv_file)

        dataset_dict = None
        counter = 0
        skip = False

        for row in reader:
            if 'Dataset' in row['@type']:
                if int(row['#']) < int(start_index):
                    print('Skipping {}'.format(row['title']))
                    skip = True
                    continue
                else:
                    skip = False


                if dataset_dict:
                    # All distributions finished, we can create/updated the previous
                    # dataset
                    if not dry_run or counter != 14:
                        _create_or_update_dataset(dataset_dict, ckan)
                    counter = counter + 1
                    if counter > 15:
                        return


                # Start the new dataset
                print('{} - Dataset found: {}'.format(row['#'], row['title']))
                dataset_dict = _get_dataset_dict(row)
                dataset_dict['owner_org'] = org


            if 'Distribution' in row['@type-resource'] and not skip:
                # Add first resource (can be in the same row)
                resource_dict = _get_resource_dict(row)
                if resource_dict.get('name'):
                    dataset_dict['resources'].append(resource_dict)

        # Save last dataset_dict or we'll miss it
        if not dry_run:
            _create_or_update_dataset(dataset_dict, ckan)
        counter = counter + 1


    print('\nDone, {} datasets processed for organization "{}"'.format(counter, org))
    if dry_run:
        print('Dry run, no changes were made')


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Import datasets into the Honduras CKAN instance from a CSV')
    parser.add_argument('org', help='Organization on which to create the datasets')
    parser.add_argument('csv', help='CSV file with the datasets')
    parser.add_argument('url', help='CKAN site to update')
    parser.add_argument('api_key', help='Sysadmin API key on that site')
    parser.add_argument('--start', action='store', default=False,
        help='Start processing from this index')
    parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False,
        help='Don\'t perform any actual changes')


    args = parser.parse_args()
    process_datasets(args.org, args.csv, args.url, args.api_key, args.start, args.dry_run)
