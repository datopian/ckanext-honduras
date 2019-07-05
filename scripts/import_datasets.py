#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import sys
import csv
import json
import argparse

import ckanapi
from slugify import slugify


def _get_resource_dict(row):

    # TODO: add the rest of resource fields
    resource_dict = {}
    resource_dict['name'] = row['title-resource']
    resource_dict['identifier'] = row['identifier-resource']
    if row['accessURL-resource']:
        resource_dict['url'] = row['accessURL-resource']

        # TODO if row['downloadURL-resource'] has a value
        # it means the file needs to be uploaded
        # (not here as the dataset still does not exist)

    return resource_dict

def process_datasets(csv_file_path, url, api_key):

    ckan = ckanapi.RemoteCKAN(url, api_key)

    with open(csv_file_path, 'rb') as csv_file:
        reader = csv.DictReader(csv_file)

        dataset_dict = {'resources': []}
        for row in reader:
            if 'Dataset' in row['@type']:

                if len(dataset_dict['resources']):
                    # All distributions finished, we can create/updated the previous
                    # dataset
                    # TODO: use API to create/update

                    # try:
                    #    ckan.action.package_show(...)
                    #
                    #    ckan.action.package_update(...)
                    # except ckanapi.errors.NotFound:
                    #    ckan.action.package_create(...)

                    print dataset_dict
                    dataset_dict = {'resources': []}


                # TODO: add the rest of dataset fields
                dataset_dict['title'] = row['title']


                # Add first resource (same row)
                dataset_dict['resources'].append(_get_resource_dict(row))

            elif 'Distribution' in row['@type-resource']:

                dataset_dict['resources'].append(_get_resource_dict(row))

        # TODO: Save last dataset_dict or we'll miss it

        print dataset_dict


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Import datasets into the Honduras CKAN instance from a CSV')
    parser.add_argument('csv', help='CSV file with the datasets')
    parser.add_argument('url', help='CKAN site to update')
    parser.add_argument('api_key', help='Sysadmin API key on that site')

    args = parser.parse_args()
    process_datasets(args.csv, args.url, args.api_key)
