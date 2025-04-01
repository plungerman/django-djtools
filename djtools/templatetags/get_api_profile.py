# -*- coding: utf-8 -*-

import requests

from django import template
from django.conf import settings


register = template.Library()

def get_api_data(cid, ptype):
    """Obtain content data from the directory API."""
    profile = None
    try:
        HEADERS = {'Authorization': 'Token {0}'.format(settings.REST_FRAMEWORK_TOKEN)}
    except Exception:
        HEADERS = {'Authorization': 'Token 666'}
    earl = '{0}{1}/{2}/detail/'.format(settings.DIRECTORY_API_URL, ptype, cid)
    response = requests.get(earl, headers=HEADERS)
    try:
        profile = response.json()
    except Exception:
        profile = None
    if profile:
        profile = profile[0]
        if ptype=='student':
            profile['majors'] = ', '.join(
                list(filter(None, [
                    profile.get('Primary_Major', ''),
                    profile.get('Second_Major', ''),
                    profile.get('Third_Major', ''),
                ]))
            )
            profile['minors'] = ', '.join(
                list(filter(None,[
                    profile.get('Minor_One', ''),
                    profile.get('Minor_Two', ''),
                    profile.get('Minor_Three', ''),
                ]))
            )
    return profile


class GetData(template.Node):
    """Get the data from the API and make it available at the template level."""

    def __init__(self, bits):
        """Initialise the class and set variables."""
        self.varname = bits[2]
        self.type=bits[3]
        self.cid=bits[4]

    def __repr__(self):
        """Default display name."""
        return '<DirectoryApiProfile>'

    def render(self, context):
        """Render the template tag content."""
        try:
            cid = template.Variable(self.cid).resolve(context)
        except Exception:
            cid = None

        context[self.varname] = get_api_data(cid, self.type)
        return ''


class DoGetData:
    """
    {% get_api_profile as variable_name profile_type ID %}
    """

    def __init__(self, tag_name):
        """Initialise the class and set variables."""
        self.tag_name = tag_name

    def __call__(self, parser, token):
        """Kick off the template tag work flow."""
        bits = token.contents.split()
        if len(bits) < 3:
            raise template.TemplateSyntaxError("'{0}' tag takes four arguments".format(bits[0]))
        if bits[1] != 'as':
            raise template.TemplateSyntaxError("First argument to '{0}' tag must be 'as'".format(bits[0]))
        return GetData(bits)


register.tag('get_api_profile', DoGetData('get_api_profile'))
