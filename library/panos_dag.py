#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage PaloAltoNetworks Firewall
# (c) 2016, techbizdev <techbizdev@paloaltonetworks.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: panos_dag
short_description: create a dynamic address group
description:
    - Create a dynamic address group
author: 
    - Palo Alto Networks 
    - Luigi Mori (jtschichold)
version_added: "0.0"
requirements:
    - pan-python
options:
    ip_address:
        description:
            - IP address (or hostname) of PAN-OS device
        required: true
        default: null
    password:
        description:
            - password for authentication
        required: true
        default: null
    username:
        description:
            - username for authentication
        required: false
        default: "admin"
    dag_name:
        description:
            - name of the dynamic address group
        required: true
        default: null
    dag_filter:
        description:
            - dynamic filter user by the dynamic address group
        required: true
        default: null
    commit:
        description:
            - commit if changed
        required: false
        default: true
'''

EXAMPLES = '''
- name: dag
  panos_dag:
    ip_address: "192.168.1.1"
    password: "admin"
    dag_name: "dag-1"
    dag_filter: "'aws-tag.aws:cloudformation:logical-id.ServerInstance' and 'instanceState.running'"
'''

import sys

try:
    import pan.xapi
except ImportError:
    print "failed=True msg='pan-python required for this module'"
    sys.exit(1)

_ADDRGROUP_XPATH = "/config/devices/entry[@name='localhost.localdomain']" +\
                   "/vsys/entry[@name='vsys1']/address-group/entry[@name='%s']"


def addressgroup_exists(xapi, group_name):
    xapi.get(_ADDRGROUP_XPATH % group_name)
    e = xapi.element_root.find('.//entry')
    if e is None:
        return False
    return True


def add_dag(xapi, dag_name, dag_filter):
    if addressgroup_exists(xapi, dag_name):
        return False

    # setup the non encrypted part of the monitor
    exml = []

    exml.append('<dynamic>')
    exml.append('<filter>%s</filter>' % dag_filter)
    exml.append('</dynamic>')

    exml = ''.join(exml)
    xapi.set(xpath=_ADDRGROUP_XPATH % dag_name, element=exml)

    return True


def main():
    argument_spec = dict(
        ip_address=dict(default=None),
        password=dict(default=None),
        username=dict(default='admin'),
        dag_name=dict(default=None),
        dag_filter=dict(default=None),
        commit=dict(type='bool', default=True)
    )
    module = AnsibleModule(argument_spec=argument_spec)

    ip_address = module.params["ip_address"]
    if not ip_address:
        module.fail_json(msg="ip_address should be specified")
    password = module.params["password"]
    if not password:
        module.fail_json(msg="password is required")
    username = module.params['username']

    xapi = pan.xapi.PanXapi(
        hostname=ip_address,
        api_username=username,
        api_password=password
    )

    dag_name = module.params['dag_name']
    if not dag_name:
        module.fail_json(msg="dag_name is required")
    dag_filter = module.params['dag_filter']
    if not dag_filter:
        module.fail_json(msg="dag_filter is required")
    commit = module.params['commit']

    changed = add_dag(xapi, dag_name, dag_filter)

    if changed and commit:
        xapi.commit(cmd="<commit></commit>", sync=True, interval=1)

    module.exit_json(changed=changed, msg="okey dokey")

from ansible.module_utils.basic import *  # noqa

main()