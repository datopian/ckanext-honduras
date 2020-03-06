import json
import os

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation

from ckanext.dcat.interfaces import IDCATRDFHarvester
from ckanext.dcat.profiles import RDFProfile, DCT, DCAT, VCARD

from ckanext.scheming.helpers import scheming_get_dataset_schema
from ckanext.honduras import helpers


class HondurasPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(IDCATRDFHarvester, inherit=True)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'honduras')

    # ITemplateHelper

    def get_helpers(self):
        return {
            'build_links': helpers.build_links,
        }

    # IDCATRDFHarvester

    def before_update(self, harvest_object, dataset_dict, temp_dict):
        return _normalize_dataset_dict(dataset_dict)

    def before_create(self, harvest_object, dataset_dict, temp_dict):
        return _normalize_dataset_dict(dataset_dict)


def _normalize_dataset_dict(dataset_dict):
    '''
    Adapt the dataset dict returned by the RDF harvester to the one expected by
    the custom Honduras schema
    '''

    dataset_schema = scheming_get_dataset_schema('dataset')

    field_names = [f['field_name'] for f in dataset_schema['dataset_fields']]

    # Promote extras to root fields
    for name in field_names:
        val = _remove_dataset_dict_extra(dataset_dict, name)
        if val:
            dataset_dict[name] = val

    return dataset_dict


def _remove_dataset_dict_extra(dataset_dict, key):
    '''Remove the dataset extra with the provided key, and return its
    value.
    '''
    extras = dataset_dict['extras'] if 'extras' in dataset_dict else []
    for extra in extras:
        if extra['key'] == key:
            val = extra['value']
            dataset_dict['extras'] = \
                [e for e in extras if not e['key'] == key]
            return val
    return None


def _get_available_licenses():
    path = os.path.join(os.path.dirname(__file__), 'public', 'licenses.json')
    with open(path, 'r') as f:
        return json.load(f)


class HondurasDCATAPProfile(RDFProfile):

    def parse_dataset(self, dataset_dict, dataset_ref):

        available_licenses = _get_available_licenses()

        # Try to match the license to the internal list
        license = self._object(dataset_ref, DCT.license)
        if license:
            license = str(license)

            for l in available_licenses:
                if ((
                        license.startswith('http') and l['url'].startswith(license)
                    ) or (
                        license.lower() == l['title'].lower()
                        )):
                    dataset_dict['license_id'] = l['id']

        # Fallback to the default one
        if not dataset_dict.get('license_id'):
            dataset_dict['license_id'] = available_licenses[0]['id']


        # Contact email (POC defines VCARD.email, ckanext-rdf uses VCARD.hasEmail)
        contact = self._object(dataset_ref, DCAT.contactPoint)
        if contact:
            email = self._without_mailto(self._get_vcard_property_value(contact, VCARD.email))
            if email:
                dataset_dict['contactPoint'] = email

        return dataset_dict
