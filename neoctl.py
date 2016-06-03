#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright (c) 2002-2016 "Neo Technology,"
# Network Engine for Objects in Lund AB [http://neotechnology.com]
#
# This file is part of Neo4j.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Usage:   neoctl.py <cmd=arg>
         --start=path/to/neo4j/home       : start neo4j
         --stop=path/to/neo4j/home        : stop neo4j
         --update-password=s3cr3tP4ssw0rd : update the neo4j password
         -h                               : show this help message

Example: neoctl.py --start=./neo4j-enterprise-3.0.0-M01
         neoctl.py -h
"""

from __future__ import print_function
from json import dumps as json_dumps
from base64 import b64encode
from sys import argv, exit
from os import name
import getopt
from subprocess import call, Popen, PIPE
try:
    from urllib.request import Request, urlopen, HTTPError
except ImportError:
    from urllib2 import Request, urlopen, HTTPError

is_windows = (name == 'nt')


def main():
    if len(argv) <= 1:
        print_help()
        exit()
    try:
        opts, args = getopt.getopt(argv[1:], "h", ["start=", "stop=", "update-password="])
    except getopt.GetoptError as err:
        print(str(err))
        print_help()
        exit_code = 2
    else:
        exit_code = 0
        for opt, arg in opts:
            if opt == '-h':
                print_help()
            elif opt == "--start":
                exit_code = neo4j_start(neo4j_home=arg) or 0
            elif opt == "--stop":
                exit_code = neo4j_stop(neo4j_home=arg) or 0
            elif opt == "--update-password":
                exit_code = neo4j_update_default_password("localhost", 7474, new_password=arg) or 0
            else:
                print("Bad option %s" % opt)
                exit_code = 1
            if exit_code != 0:
                break
    exit(exit_code)


def neo4j_start(neo4j_home):
    if is_windows:
        return powershell([neo4j_home + '/bin/neo4j.bat install-service;', neo4j_home + '/bin/neo4j.bat start'])
    else:
        return call([neo4j_home + "/bin/neo4j", "start"])


def neo4j_stop(neo4j_home):
    if is_windows:
        return powershell([neo4j_home + '/bin/neo4j.bat stop;', neo4j_home + '/bin/neo4j.bat uninstall-service'])
    else:
        return call([neo4j_home+"/bin/neo4j", "stop"])


def neo4j_update_default_password(host, http_port, new_password):
    exit_code = 0
    if new_password == 'neo4j':
        exit_code = neo4j_update_password(host, http_port, "neo4j", "neo4j", "1234") \
                or neo4j_update_password(host, http_port, "neo4j", "1234", "neo4j")
    else:
        exit_code = neo4j_update_password(host, http_port, "neo4j", "neo4j", new_password)
    return exit_code


def neo4j_update_password(host, http_port, user, password, new_password):
    print("Changing password...")
    request = Request("http://%s:%s/user/neo4j/password" % (host, http_port),
                      json_dumps({"password": new_password}, ensure_ascii=True).encode("utf-8"),
                      {"Authorization": "Basic " + b64encode((user + ":" + password).encode("utf-8")).decode("ascii"),
                       "Content-Type": "application/json"})
    try:
        f = urlopen(request)
        f.read()
        f.close()
    except HTTPError as error:
        raise RuntimeError("Cannot update password [%s]" % error)


def powershell(cmd):
    cmd = ['powershell.exe'] + cmd
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = p.communicate()
    return_code = p.wait()
    print(out)
    print(err)
    return return_code


def print_help():
    print(__doc__)

if __name__ == "__main__":
    main()
