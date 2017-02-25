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
Usage:   neoget.py <cmd> [arg]
         -v neo4j-version: download this specific neo4j enterprise version
         -n neo4j-version: download this specific neo4j enterprise nightly version from teamcity with basic access auth
         -l download-url : download neo4j provided by this url
         -h              : show this help message

Example: neoget.py -v 2.3.1
         neoget.py -n 3.0
         neoget.py -h
"""
from __future__ import print_function
from sys import argv, stdout, exit, stderr
import getopt
from os import path, name, makedirs, getenv
from zipfile import ZipFile
from tarfile import TarFile
from re import match, sub
from base64 import b64encode

try:
    # py v3
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

DIST = "http://dist.neo4j.org"
DEFAULT_UNIX_URL = DIST + "/neo4j-enterprise-3.1.1-unix.tar.gz"
DEFAULT_WIN_URL = DIST + "/neo4j-enterprise-3.1.1-windows.zip"

is_windows = (name == 'nt')


def main():
    try:
        opts, args = getopt.getopt(argv[1:], "hv:n:l:")
    except getopt.GetoptError as err:
        print(str(err))
        print_help()
        exit()

    archive_url, archive_name, require_basic_auth = neo4j_default_archive()

    for opt, arg in opts:
        if opt == '-h':
            print_help()
            exit()
        elif opt in ('-v', '-n', '-l'):
            archive_url, archive_name, require_basic_auth = neo4j_archive(opt, arg)

    # download to the current dir
    download(archive_url, archive_name, require_basic_auth=require_basic_auth)

    ret = 0 if path.exists(archive_name) else 1
    exit(ret)


def neo4j_default_archive():
    archive_url = DEFAULT_WIN_URL if is_windows else DEFAULT_UNIX_URL
    archive_name = path.split(urlparse(archive_url).path)[-1]
    require_basic_auth = False
    return archive_url, archive_name, require_basic_auth


def neo4j_archive(opt, arg):
    archive_url, archive_name = '', ''
    require_basic_auth = False

    if opt == '-v':
        if is_windows:
            archive_name = "neo4j-enterprise-%s-windows.zip" % arg
        else:
            archive_name = "neo4j-enterprise-%s-unix.tar.gz" % arg
        archive_url = "%s/%s" % (DIST, archive_name)
    elif opt == '-n':
        if is_windows:
            archive_name = "neo4j-enterprise-%s-NIGHTLY-windows.zip" % arg
            url_env_var_name = "TEAMCITY_NEO4J_%sNIGHTLY_WIN" % sub('\.', '', arg)
        else:
            archive_name = "neo4j-enterprise-%s-NIGHTLY-unix.tar.gz" % arg
            url_env_var_name = "TEAMCITY_NEO4J_%sNIGHTLY" % sub('\.', '', arg)

        archive_url = getenv(url_env_var_name)
        require_basic_auth = True
        if not archive_url:
            stderr.write("Failed to load archive url for `%s` due to missing env variable `%s`.\n" % (archive_name, url_env_var_name))
            exit(1)

    elif opt == '-l':
        archive_url = arg
        archive_name = path.split(urlparse(archive_url).path)[-1]
    return archive_url, archive_name, require_basic_auth


def teamcityurlopen(archive_url):

    # first try to get the user and password from environment var
    user = getenv("TEAMCITY_USER")
    password = getenv("TEAMCITY_PASSWORD")

    # if not found, try to get it from url directly
    if not user or not password:
        matchResult = match("^(.*):\/\/(.*):(.*)@(.*)$", archive_url)
        if not matchResult:
            stderr.write("Please either provide `TEAMCITY_USER`, `TEAMCITY_PASSWORD` env variables, "
                         "or prepend `username:password@` to the hostname in the url to authenticate to teamcity.\n")
            exit(1)

        user = matchResult.group(2)
        password = matchResult.group(3)
        archive_url = matchResult.group(1) + "://" + matchResult.group(4)

    # Create basic access authentication token using username and password found
    headers = {"Authorization": "Basic " + b64encode((user + ":" + password).encode("utf-8")).decode("ascii")}

    request = Request(archive_url, headers=headers)
    return urlopen(request)


def download(archive_url, archive_name, extract_to_path='.', require_basic_auth=False):
    # download the file to extract_to_path
    if not path.exists(extract_to_path):
        makedirs(extract_to_path)

    archive_path = path.join(extract_to_path, archive_name)
    stdout.write("Downloading '%s' to '%s'...\n" % (archive_url, archive_path))

    source = urlopen(archive_url) if not require_basic_auth else teamcityurlopen(archive_url)

    with open(archive_path, "wb") as destination:
        more = True
        while more:
            data = source.read(8192)
            if data:
                destination.write(data)
            else:
                more = False

    if archive_name.endswith('.zip'):
        stdout.write("Unzipping '%s' to '%s'...\n" % (archive_path, extract_to_path))
        zip_ref = ZipFile(archive_path, 'r')
        zip_ref.extractall(extract_to_path)
        unzip_folder = zip_ref.namelist()[0]
        zip_ref.close()
        return unzip_folder
    elif archive_name.endswith('.tar.gz'):
        stdout.write("Unarchiving '%s' to '%s'...\n" % (archive_path, extract_to_path))
        tar_ref = TarFile.open(archive_path)
        tar_ref.extractall(extract_to_path)
        untar_folder=tar_ref.getnames()[0]
        tar_ref.close()
        return untar_folder


def print_help():
    print(__doc__)


if __name__ == "__main__":
    main()
