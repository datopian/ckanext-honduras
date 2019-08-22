#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import os
import argparse

import ckanapi


def _get_script_root():

    return os.path.dirname(os.path.abspath(__file__))


def process_resources(list_file_path, url, api_key, dry_run):

    ckan = ckanapi.RemoteCKAN(url, api_key)

    counter = 0
    data_path = os.path.join(_get_script_root(), 'data')

    with open(list_file_path, 'rb') as list_file:

        for path in list_file.readlines():
            _, resource_id, file_name = path.strip().split('/')

            file_path = os.path.join(data_path, file_name)

            if not os.path.exists(file_path):
                print('\n\t##### Error: could not find file to upload for this resource ({})\n'.format(file_name))
                continue

            resource = {
                'id': resource_id,
                'upload': open(file_path, 'rb'),
            }

            try:
                if not dry_run:
                    result = ckan.action.resource_patch(**resource)
            except ckanapi.errors.NotFound as e:
                print(
                    '\n#####  Error: Resource "{}" not found\n'.format(resource_id))

            except ckanapi.errors.ValidationError as e:
                print(
                    '\n#####  Errors found uploading file {}: {}\n'.format(file_name, e))
            else:
                print('Uploaded file {} to resource {}'.format(
                    file_name, resource['id']))
                counter = counter + 1



    print('\nDone, {} files uploaded'.format(counter))
    if dry_run:
        print('Dry run, no changes were made')



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Restore missing uploads, assuming a list of missing files')
    parser.add_argument('list', help='List of missing files in the form resources/<id>/<file_name>, one per line')
    parser.add_argument('url', help='CKAN site to update')
    parser.add_argument('api_key', help='Sysadmin API key on that site')
    parser.add_argument('--dry-run', dest='dry_run', action='store_true', default=False,
        help='Don\'t perform any actual changes')


    args = parser.parse_args()
    process_resources(args.list, args.url, args.api_key, args.dry_run)
