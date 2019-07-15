#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import argparse

import ckanapi
from slugify import slugify


GROUPS = [
    'Ciencia y Tecnología',
    'Comercio',
    'Cultura y Ocio',
    'Demografía',
    'Deporte',
    'Economía',
    'Educación',
    'Empleo',
    'Energía',
    'Hacienda',
    'Industria',
    'Legislación y Justicia',
    'Medio Ambiente',
    'Medio Rural',
    'Salud',
    'Sector Público',
    'Seguridad',
    'Sociedad y Bienestar',
    'Transporte',
    'Turismo',
    'Urbanismo e Infraestructuras',
    'Vivienda',
]

def create_groups(url, api_key):

    ckan = ckanapi.RemoteCKAN(url, api_key)

    for group in GROUPS:
        try:
    	    ckan.action.group_create(name=slugify(group), title=group)
        except ckanapi.errors.ValidationError as e:

            print('##### Error creating group "{}": {}'.format(group, e))
        else:
	    print('Created group "{}"'.format(group))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Create initial groups on the site')
    parser.add_argument('url', help='CKAN site to update')
    parser.add_argument('api_key', help='Sysadmin API key on that site')

    args = parser.parse_args()
    create_groups(args.url, args.api_key)
