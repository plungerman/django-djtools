# -*- coding: utf-8 -*-

import datetime
import requests
from django.conf import settings
from django.core.cache import cache
from djtools.utils.date import calculate_age


HEADERS = {'Authorization': 'Token {0}'.format(settings.REST_FRAMEWORK_TOKEN)}


def department_detail(did):
    """Fetch a department from the API based on department ID."""
    dept = []
    response = requests.get(
        '{0}department/{1}/?format=json'.format(
            settings.DIRECTORY_API_URL,
            did,
        ),
        headers=HEADERS,
    )
    if response.json():
        dept = response.json()[0]
    return dept


def department_all(choices=False):
    """Obtain all departments and return a choices structure for forms."""
    if choices:
        depts = [('','---select---')]
    else:
        depts = []
    response = requests.get(
        '{0}department/?format=json'.format(
            settings.DIRECTORY_API_URL,
        ),
        headers=HEADERS,
    )
    if response.json():
        for dept in response.json():
            if choices:
                depts.append((str(dept['id']), dept['name']))
            else:
                depts.append(dept)
    return depts


def department_person(cid, choices=False):
    """Returns all departments to which a person belongs."""
    if choices:
        depts = [('','---select---')]
    else:
        depts = []
    response = requests.get(
        '{0}profile/{1}/detail/?format=json'.format(
            settings.DIRECTORY_API_URL,
            cid,
        ),
        headers=HEADERS,
    )
    if response.json():
        for dept in response.json()[0]['departments']:
            did = dept.split('/')[-2]
            department = department_detail(did)
            if department:
                if choices:
                    depts.append((department['id'], department['name']))
                else:
                    depts.append(department)
    return depts


def get_managers(manager, cid=False):
    """Obtain all managers."""
    peeps = []
    response = requests.get(
        '{0}profile/{1}/?format=json'.format(
            settings.DIRECTORY_API_URL,
            manager,
        ),
        headers=HEADERS,
    )
    if response.json():
        for person in response.json():
            if cid:
                if cid == person['id']:
                    return person
                else:
                    peeps = []
            else:
                peeps.append(person)
    return peeps


def get_peep(cid, profile=None):
    """Obtain the profile based on ID."""
    key = 'workday_{0}_api'.format(cid)
    peep = cache.get(key)
    if not profile:
        profile = 'profile'
    if not peep:
        earl = '{0}{1}/{2}/detail/?format=json'.format(
            settings.DIRECTORY_API_URL,
            profile,
            cid,
        )
        response = requests.get(earl, headers=HEADERS)
        if response.json():
            peep = response.json()
            cache.set(key, peep, timeout=86400)
    return peep


def get_student(peep):
    """Construct a student's profile object from API data."""
    student = None
    if peep:
        cid = peep['Student_ID']
        adult = False
        privacy = False
        incoming = False
        birth_date = peep.get('Date_of_Birth')
        residency = peep.get('housingType')
        is_incoming = peep.get('Is_Incoming')
        privacy_block = peep.get('Privacy_Block')
        if privacy_block == '1':
            privacy = True
        if is_incoming == 'T':
            incoming = True
        if residency:
            residency = residency[0]
        if birth_date:
            birth_date = datetime.datetime.strptime(birth_date, '%Y-%m-%d')
            age = calculate_age(birth_date)
            if age >= settings.ADULT_AGE:
                adult = True
        # obtain preferred name from Student attribute
        alt_name = ''
        full_name = peep.get('Student')
        first_name = peep.get('firstName')
        if full_name:
            preferred_name = full_name.split(' ')[0]
            if preferred_name != first_name:
                alt_name = preferred_name
        email =  peep.get('LRV_Student_Primary_Institutional_Email_Text')
        if email:
            student = {
                'id': cid,
                'username': email.split('@')[0],
                'first_name': first_name,
                'last_name': peep.get('lastName'),
                'alt_name': alt_name,
                'email': email,
                'second_name': peep.get('Middle_Name'),
                'suffix': peep.get('Suffix'),
                'birth_date': birth_date,
                'address1': peep.get('LRV_Student_Primary_Address_Line_1'),
                'city': peep.get('Primary_Home_Address_-_City'),
                'state': peep.get('Primary_Home_Address_-_State'),
                'postal_code': peep.get('LRV_Student_Primary_Address_Zip'),
                'country': peep.get('LRV_Student_Primary_Address_Country'),
                'gender': peep.get('Legal_Sex'),
                'class_year': peep.get('Latest_Class_Standing'),
                'residency': residency,
                'adult': adult,
                'incoming': incoming,
                'privacy':  privacy,
                'Primary_Major': peep.get('Primary_Major'),
                'Second_Major': peep.get('Second_Major'),
                'Third_Major': peep.get('Third_Major'),
                'Minor_One': peep.get('Minor_One'),
                'Minor_Two': peep.get('Minor_Two'),
                'Minor_Three': peep.get('Minor_Three'),
            }
        else:
            print('no email for student: {0}'.format(cid))

    return student


def get_students(choices=False):
    """Fetch all students."""
    students = []
    earl = '{0}student/?format=json'.format(
        settings.DIRECTORY_API_URL,
    )
    response = requests.get(earl, headers=HEADERS)
    if response.json():
        students = response.json()
    return students


def get_peeps(who=None, choices=False):
    """Obtain the folks based on who parameter."""
    key = 'workday_{0}{1}_api'.format(who, choices)
    peeps = cache.get(key)
    if not peeps:
        peeps = []
        if choices:
            peeps.append(('','---select---'))
        if who:
            earl = '{0}profile/{1}/who/?format=json'.format(
                settings.DIRECTORY_API_URL,
                who,
            )
        else:
            earl = '{0}profile/?format=json'.format(
                settings.DIRECTORY_API_URL,
            )
        response = requests.get(earl, headers=HEADERS)
        if response.json():
            for peep in response.json():
                name = '{0}, {1}'.format(peep['last_name'], peep['first_name'])
                if choices:
                    peeps.append((peep['id'], name))
                else:
                    peeps.append(peep)
            cache.set(key, peeps, timeout=86400)

    return peeps
