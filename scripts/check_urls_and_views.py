#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse
from urlparse import urlunsplit
import json
import csv

import requests
import ckanapi

def _get_datapusher_error_message(status):

    error = status.get('task_info', {}).get('error')

    if not error:
        return

    if isinstance(error, basestring):
        return error

    if error.get('HTTP status code'):
        if error['HTTP status code'] != 409:
            return 'HTTP Error: {}'.format(error['HTTP status code'])
        else:
            datastore_error = None
            url = status['task_info']['metadata']['original_url']
            try:
                datastore_response = json.loads(error['Response'])
            except ValueError as e:
                datastore_error = 'Invalid column name (check headers are present)'

            if not datastore_error:
                datastore_error = datastore_response['error']['field'][0]

            return 'DataStore Error: {}'.format(datastore_error)

    if error.get('message'):
        return error['message']


def check_datasets(url, api_key, org, datapusher, force_datapusher, start):

    url = url.rstrip('/')

    ckan = ckanapi.RemoteCKAN(url, api_key)

    fq = 'organization:{}'.format(org) if org else ''
    datasets = ckan.action.package_search(fq=fq, rows=1000)['results']

    report = []
    for counter, dataset in enumerate(datasets):

        if counter + 1 < int(start):

            print('{}: Skipping "{}"'.format(counter + 1, dataset['name']))
            continue

        print('{}: "{}"'.format(counter + 1, dataset['name']))
        for resource in dataset.get('resources', []):

            if 'placeholder' in resource['url']:
                print('##### Error: placeholder in resource {}'.format(resource['id']))


            if resource['format'].lower() in ['csv', 'xlsx', 'xls']:

                # Check resource page
                page_url = url + '/dataset/' + dataset['id'] + '/resource/' + resource['id']
                r = requests.get(page_url)
                if r.status_code != 200:
                    print('##### Error in resource page, dataset {}, resource {} (code {})'.format(dataset['name'], resource['id'], r.status_code))

                views = ckan.action.resource_view_list(id=resource['id'])

                if len(views) == 0:
                    ckan.action.resource_view_create(
                        resource_id=resource['id'],
                        title='Data Explorer',
                        view_type='recline_view')
                    print('\t\tCreated recline view for resource {}'.format(resource['id']))


                #recline_view_exists = ('recline_view' in [v['view_type'] for v in views])
                #for view in views:
                #    if view['view_type'] == 'recline_grid_view':
                #        ckan.action.resource_view_delete(id=view['id'])
                #        if not recline_view_exists:
                #            ckan.action.resource_view_create(
                #                resource_id=resource['id'],
                #                title='Data Explorer',
                #                view_type='recline_view')
                #            print('\t\tUpdated view for resource {}'.format(resource['id']))


                if not resource.get('datastore_active') or len(views) == 0:
                    print('\tResource {}: datastore_active: {}, Views: {}'.format(
                        resource['id'], resource.get('datastore_active'), len(views)))
                    error_message = None
                    try:
                        status = ckan.action.datapusher_status(resource_id=resource['id'])
                        if status['status'] == 'error':
                            error_message = _get_datapusher_error_message(status)
                            if error_message:
                                print('\t\tDatapusher reported an error: {} '.format(error_message))
                            else:
                                print('\t\t##### Error, could not get DataPusher error')

                            report.append({
                                'dataset': dataset['title'].encode('utf8'),
                                'resource': resource['name'].encode('utf8'),
                                'error': error_message.encode('utf8'),
                                'url': resource['url'],
                                'resource_url': url + '/dataset/' + dataset['name'] + '/resource/' + resource['id'],
                            })
                    except ckanapi.errors.CKANAPIError as e:
                        print('\t\tError getting DataPusher status: {}'.format(e))




                if (not resource.get('datastore_active') and datapusher) or force_datapusher:
                    try:
                        ckan.action.datapusher_submit(resource_id=resource['id'])
                        print('\tSubmitted resource {} to the DataPusher'.format(resource['id']))
                    except ckanapi.errors.CKANAPIError as e:
                        print('\t\tError submitting data to the DataPusher: {}'.format(e))
    if report:
        with open('honduras_datastore_errors.csv', 'w') as f:
            field_names = ['dataset', 'resource', 'error', 'url', 'resource_url']
            writer = csv.DictWriter(f, fieldnames=field_names)
            writer.writeheader()
            writer.writerows(report)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Check resource urls and views')
    parser.add_argument('url', help='CKAN site to update')
    parser.add_argument('api_key', help='Sysadmin API key on that site')
    parser.add_argument('--org', help='Only check datasets from this org', default=False)
    parser.add_argument('--datapusher', action='store_true', help='Submit data not in DataStore', default=False)
    parser.add_argument('--force-datapusher', action='store_true', help='Submit to DataStore in all cases', default=False)
    parser.add_argument('--start', action='store', default=False,
        help='Start processing from this index')

    args = parser.parse_args()
    check_datasets(args.url, args.api_key, args.org, args.datapusher, args.force_datapusher, args.start)
