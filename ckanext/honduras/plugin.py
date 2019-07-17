import ckan.lib.helpers as h

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation

from ckanext.honduras import helpers


def build_uri(value):
    if value.startswith('http'):
        return value
    else:
        return '{}/dataset/{}'.format(toolkit.config['ckan.site_url'].rstrip('/'), value)


class HondurasPlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IValidators)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'honduras')

    # IValidators

    def get_validators(self):
        return {
            'build_uri': build_uri
        }

    # ITemplateHelper

    def get_helpers(self):
        return {
            'build_links': helpers.build_links,
        }
