#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse

import ckanapi

KEEP = ['yearly-data-for-government-spending']

def purge_datasets(url, api_key):

    ckan = ckanapi.RemoteCKAN(url, api_key)

    names = ckan.action.package_list()
    for name in names:
        if name not in KEEP:
            ckan.action.dataset_purge(id=name)
            print('Purged dataset "{}"'.format(name))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Delete and purge all datasets')
    parser.add_argument('url', help='CKAN site to update')
    parser.add_argument('api_key', help='Sysadmin API key on that site')

    args = parser.parse_args()
    purge_datasets(args.url, args.api_key)
