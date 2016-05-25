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
         -n neo4j-version: download this neo4j enterprise nightly version
         -l download-url : download neo4j provided by this url
         -h              : show this help message

Example: neoget.py -v 2.3.1
         neoget.py -h
         neoget.py -n 3.0
"""
from __future__ import print_function
from sys import argv, stdout, exit
import getopt
from os import path, name, makedirs
from zipfile import ZipFile
from tarfile import TarFile
try:
    # For Python 3.0 and later
    from urllib.request import urlretrieve
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib import urlretrieve

try:
    # py v3
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

DIST = "http://dist.neo4j.org"
NIGHTLY_DIST = "http://alpha.neohq.net/dist"
NIGHTLY30_UNIX_URL = "http://alpha.neohq.net/dist/neo4j-enterprise-3.0-NIGHTLY-unix.tar.gz"
NIGHTLY30_WIN_URL = "http://alpha.neohq.net/dist/neo4j-enterprise-3.0-NIGHTLY-windows.zip"

is_windows = (name == 'nt')


def main():
    try:
        opts, args = getopt.getopt(argv[1:], "hv:s:l:")
    except getopt.GetoptError as err:
        print(str(err))
        print_help()
        exit()

    archive_url, archive_name = neo4j_default_archive()

    for opt, arg in opts:
        if opt == '-h':
            print_help()
            exit()
        elif opt in ('-v', '-n', '-l'):
            archive_url, archive_name = neo4j_archive(opt, arg)
    try:
        download(archive_url, archive_name)
    finally:
        ret = 0 if path.exists(archive_name) else 1
        exit(ret)


def neo4j_default_archive():
    archive_url = NIGHTLY30_WIN_URL if is_windows else NIGHTLY30_UNIX_URL
    archive_name = path.split(urlparse(archive_url).path)[-1]
    return archive_url, archive_name


def neo4j_archive(opt, arg):
    archive_url, archive_name = '', ''

    if opt == '-v':
        if is_windows:
            archive_name = "neo4j-enterprise-%s-windows.zip" % arg
        else:
            archive_name = "neo4j-enterprise-%s-unix.tar.gz" % arg
        archive_url = "%s/%s" % (DIST, archive_name)
    elif opt == '-n':
        if is_windows:
            archive_name = "neo4j-enterprise-%s-NIGHTLY-windows.zip" % arg
        else:
            archive_name = "neo4j-enterprise-%s-NIGHTLY-unix.tar.gz" % arg
        archive_url = "%s/%s" % (NIGHTLY_DIST, archive_name)
    elif opt == '-l':
        archive_url = arg
        archive_name = path.split(urlparse(archive_url).path)[-1]
    return archive_url, archive_name


def download(archive_url, archive_name, extract_to_path='.'):
    # download the file to extract_to_path
    if not path.exists(extract_to_path):
        makedirs(extract_to_path)

    archive_path = path.join(extract_to_path, archive_name)
    stdout.write("Downloading '%s' to '%s'...\n" % (archive_url, archive_path))
    urlretrieve(archive_url, archive_path)

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
