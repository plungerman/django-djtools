# -*- coding: utf-8 -*-

import json

import requests
from django import template
from django.core.cache import cache

register = template.Library()


class GetProf(template.Node):
    """Obtain the profile from the CMS."""

    def __init__(self, bits):
        """Initialize the template tag class with variables passed to."""
        self.varname = bits[2]
        # ldap username
        self.uname = bits[3]

    def __repr__(self):
        """Default value."""
        return '<Profile>'

    def render(self, context):
        """Render the template tag content."""
        try:
            uname = template.Variable(self.uname).resolve(context).split('@')[0].strip()
        except Exception:
            uname = None
        prof = None
        if uname:
            key = 'livewhale_get_prof_{0}'.format(uname)
            if cache.get(key):
                prof = cache.get(key)
            else:
                root = 'https://www.carthage.edu'
                earl = '{0}/live/json/profiles/search/{1}/'.format(root, uname)
                response = requests.get(earl)
                '''
                try:
                    json_data = json.loads(response.read())
                except Exception:
                    json_data = ''
                '''
                #content = response.content
                json_data = response.json()
                if json_data:
                    email = '{0}@carthage.edu'.format(uname)
                    for profile in json_data:
                        # 33 = faculty
                        # 71 = staff
                        # 90 = Admissions Representatives
                        status = (
                            profile.get('profiles_33') and
                            email in profile.get('profiles_33') or
                            (
                                profile.get('profiles_71') and
                                email in profile.get('profiles_71')
                            ) or
                            (
                                profile.get('profiles_90') and
                                email in profile.get('profiles_90')
                            )
                        )
                        if status:
                            earl = '{0}/live/profiles/{1}@JSON'.format(root, profile['id'])
                            response = requests.get(earl)
                            profile_data = response.json()
                            if profile_data.get('parent'):
                                earl = '{0}/live/profiles/{1}@JSON'.format(
                                    root, profile_data['parent'],
                                )
                                response = requests.get(earl)
                                if response:
                                    profile_data = response.json()
                            if profile_data.get('thumb'):
                                listz = profile_data['thumb'].split('/')
                                listz[8] = '145'
                                listz[0] = 'https:'
                                new_listz = listz[:9]
                                new_listz.append(listz[-1])
                                profile['thumbnail'] = '/'.join(new_listz)
                            prof = profile
                            cache.set(key, prof)

        context[self.varname] = prof
        return ''


class DoGetProf(object):
    """
    Fetch a profile from the CMS.

    {% get_prof as variable_name ldap_user %}
    """

    def __init__(self, tag_name):
        """Initialize the template tag wrapper."""
        self.tag_name = tag_name

    def __call__(self, parser, token):
        """Invoke the actual template tag class."""
        bits = token.contents.split()
        if len(bits) < 3:
            raise template.TemplateSyntaxError(
                "'{0}' tag takes two arguments".format(bits[0]),
            )
        if bits[1] != "as":
            raise template.TemplateSyntaxError(
                "First argument to '{0}' tag must be 'as'".format(bits[0]),
            )
        return GetProf(bits)


register.tag('get_prof', DoGetProf('get_prof'))
