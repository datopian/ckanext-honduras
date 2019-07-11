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


def _get_schema():
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), '..', 'ckanext', 'honduras',
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
                try:
                    if choice.get('label').encode('utf8') == label:
                        return choice.get('value')
                except UnicodeDecodeError:
                    import ipdb; ipdb.set_trace()
    return label


def _iso_date(date_str):
    return parse_date(date_str).isoformat()


def _get_dataset_dict(row):

    dataset_dict = {
        'resources': []
    }
    fields = [
        'title',
        'identifier',
        'issued',
        'modified',
        'temporal',
        'spatial',
        'describedBy',
        'references',
        'contactPoint',
    ]
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

    if row.get('theme'):
        dataset_dict['theme'] = _get_choice_value('theme', row['theme'])

    if row.get('accrualPeriodicity'):
        dataset_dict['frequency'] = _get_choice_value('frequency', row['accrualPeriodicity'])

    return dataset_dict

def _get_resource_dict(row):

    resource_dict = {}
    resource_dict['name'] = row['title-resource']
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
        resource_dict['url'] = '_placeholder'

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
            '#####  Errors found for dataset "{}": {}'.format(dataset_dict['title'], e))
    else:
        print('{} dataset "{}"'.format(action_name.title(), dataset_dict['title']))


def process_datasets(org, csv_file_path, url, api_key):

    ckan = ckanapi.RemoteCKAN(url, api_key)

    with open(csv_file_path, 'rb') as csv_file:
        reader = csv.DictReader(csv_file)

        dataset_dict = None
        counter = 0

        for row in reader:
            if 'Dataset' in row['@type']:

                if dataset_dict:
                    # All distributions finished, we can create/updated the previous
                    # dataset
                    # TODO: use API to create/update

                    _create_or_update_dataset(dataset_dict, ckan)
                    counter = counter + 1

                # Start the new dataset
                dataset_dict = _get_dataset_dict(row)
                dataset_dict['owner_org'] = org

                # Add first resource (same row)
                dataset_dict['resources'].append(_get_resource_dict(row))

            elif 'Distribution' in row['@type-resource']:

                dataset_dict['resources'].append(_get_resource_dict(row))
        # Save last dataset_dict or we'll miss it
        _create_or_update_dataset(dataset_dict, ckan)
        counter = counter + 1


    print('\nDone, {} datasets processed'.format(counter))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Import datasets into the Honduras CKAN instance from a CSV')
    parser.add_argument('org', help='Organization on which to create the datasets')
    parser.add_argument('csv', help='CSV file with the datasets')
    parser.add_argument('url', help='CKAN site to update')
    parser.add_argument('api_key', help='Sysadmin API key on that site')

    args = parser.parse_args()
    process_datasets(args.org, args.csv, args.url, args.api_key)
