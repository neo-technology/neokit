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
Usage:   neorun.py <cmd=arg>
         --start=path/to/neo4j/home <cmd> [arg]
            : start the neo4j server in the folder specified by the path
                -v version      : download the version provided if no neo4j detected
                -n neo4j-version: download this specific neo4j enterprise nightly version from teamcity with basic access auth
                -l download-url : download the neo4j provided by this url if no neo4j found
                -p new-password : change the default password to this new password
         --stop=path/to/neo4j/home : stop a neo4j server
         -h                        : show this help message

Example: neorun.py -h
         neorun.py --start=path/to/neo4j/home -v 3.0.1 -p TOUFU
         neorun.py --start=path/to/neo4j/home -n 3.0 -p TOUFU
         neorun.py --start=path/to/neo4j/home -n 3.1
         neorun.py --stop=path/to/neo4j/home
"""
import getopt
from sys import argv, stdout, exit
from neoget import neo4j_default_archive, neo4j_archive, download
from neoctl import neo4j_start, neo4j_stop, neo4j_update_default_password
from os import path, rename, getenv
import socket
from time import time, sleep, strftime

KNOWN_HOST = path.join(path.expanduser("~"), ".neo4j", "known_hosts")
NEORUN_START_ARGS_NAME = "NEORUN_START_ARGS"

class Enum(set):
    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

ServerStatus = Enum(["STARTED", "STOPPED" ])

def main():

    if len(argv) <= 1:
        print_help()
        exit(2)
    try:
        opts, args = getopt.getopt(argv[1:], "hv:n:l:p:", ["start=", "stop="])
    except getopt.GetoptError as err:
        print(str(err))
        print_help()
        exit(2)
    else:
        exit_code = 0
        for opt, arg in opts:
            if opt == '-h':
                print_help()
                exit(2)

            if opt == "--start":
                neo4j_home = path.abspath(arg)
                if neo4j_status() == ServerStatus.STARTED:
                    stdout.write("Failed to start neo4j as a neo4j server is already running on this machine.\n")
                    exit(2)

                # get the opts from env
                env = getenv(NEORUN_START_ARGS_NAME)
                if env:
                    stdout.write("WARNING: using env var `NEORUN_START_ARGS=%s`\n" % env)
                    try:
                        start_opts, start_args = getopt.getopt(env.split(), "v:n:l:p:")
                    except getopt.GetoptError as err:
                        print(str(err))
                        print_help()
                        exit(2)
                else:
                    start_opts = opts

                # parse the opts under --start
                archive_url, archive_name, require_basic_auth = neo4j_default_archive()
                password = ''
                for start_opt, start_arg in start_opts:
                    if start_opt == "-p":
                        password = start_arg
                    elif start_opt in ['-v', '-n', '-l']:
                        archive_url, archive_name, require_basic_auth = neo4j_archive(start_opt, start_arg)

                exit_code = handle_start(archive_url, archive_name, neo4j_home, require_basic_auth)
                if exit_code == 0 and password:
                    exit_code = neo4j_update_default_password("localhost", 7474, new_password=password) or 0

            elif opt == "--stop":
                if neo4j_status() == ServerStatus.STOPPED:
                    stdout.write("Failed to stop server as no neo4j server is running on this machine.\n")
                    exit(2)
                exit_code = neo4j_stop(neo4j_home=arg) or test_neo4j_status(ServerStatus.STOPPED) or 0

            if exit_code != 0:
                break
        exit(exit_code)


def handle_start(archive_url, archive_name, neo4j_home, require_basic_auth):
    if not path.exists(neo4j_home):
        folder_name=download(archive_url, archive_name, path.dirname(neo4j_home), require_basic_auth)
        if not path.exists(neo4j_home):
            # the untared name is different from what the user gives
            rename(path.join(path.dirname(neo4j_home), folder_name), neo4j_home)
    if path.exists(KNOWN_HOST):
        known_host_backup_name = KNOWN_HOST + strftime("%Y%m%d-%H%M%S") + ".backup"
        stdout.write("Found an existing known_host file, renaming it to %s.\n" % (known_host_backup_name))
        rename(KNOWN_HOST, known_host_backup_name)

    exit_code = neo4j_start(neo4j_home) or 0
    if exit_code == 0:
        exit_code = test_neo4j_status()
    return exit_code


# Test if the neo4j server is started (status = STARTED)
# or if the neo4j server is stopped (status = STOPPED) within 4 mins.
# Return 0 if the test success, otherwise 1
def test_neo4j_status(status = ServerStatus.STARTED):
    success = False
    start_time = time()
    timeout = 60 * 4 # in seconds
    count = 0
    while not success:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        actual_status = s.connect_ex(("localhost", 7474))
        if status == ServerStatus.STARTED:
            success = True if actual_status == 0 else False
        else:
            success = True if actual_status != 0 else False
        s.close()

        current_time = time()
        if current_time - start_time > timeout:
            # failed to connect to server within timeout
            stdout.write("Failed to start server in 4 mins\n")
            return 1

        count += 1
        if count % 10 == 0:
            stdout.write(".") # print .... to indicate working on it

        sleep(0.1) # sleep for 100ms
    # server is started
    stdout.write("\n")
    return 0


def neo4j_status():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_status = ServerStatus.STARTED if s.connect_ex(("localhost", 7474)) == 0 else ServerStatus.STOPPED
    s.close()
    return server_status


def print_help():
    print(__doc__)


if __name__ == "__main__":
    main()
