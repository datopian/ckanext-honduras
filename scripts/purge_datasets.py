#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse

import ckanapi

KEEP = ['yearly-data-for-government-spending']

def purge_datasets(url, api_key, org):

    ckan = ckanapi.RemoteCKAN(url, api_key)

    fq = 'organization:{}'.format(org) if org else ''
    datasets = ckan.action.package_search(fq=fq)['results']
    for dataset in datasets:
        name = dataset['name']
        if name not in KEEP:
            ckan.action.dataset_purge(id=name)
            print('Purged dataset "{}"'.format(name))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Delete and purge all datasets')
    parser.add_argument('url', help='CKAN site to update')
    parser.add_argument('api_key', help='Sysadmin API key on that site')
    parser.add_argument('--org', help='Only delete datasets from this org', default=False)

    args = parser.parse_args()
    purge_datasets(args.url, args.api_key, args.org)
