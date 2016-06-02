# Neo4j Driver Toolkit

Tools for downloading, managing and testing Neo4j servers.

- `neoget` - download and unarchive Neo4j server packages
- `neoctl` - start and stop Neo4j servers and update default server password
- `neorun` - start and stop a Neo4j server with guarantee of server fully started and stopped


## Neoget
Neoget is a download script for fetching Neo4j server packages. To download the latest released version of Neo4j, simply use:
```
python neoget.py
```
If successful, the downloaded package would be unarchived immediately following the download.

To install a specific Neo4j package version, use `-v` to specify the version:
```
python neoget.py -v 3.0.1
```

Alternatively, a url could also be used with option `-l` to directly download the Neo4j specified by the url
```
python neoget.py -l http://alpha.neohq.net/dist/neo4j-enterprise-3.0-NIGHTLY-unix.tar.gz
```

To install a nightly version, use `-n` to specify the nightly version togther with env var `TEAMCITY_NEO4J_<version>[_WIN]` (such as `TEAMCITY_NEO4J_30NIGHTLY`) to provide the secret teamcity download url for the nightly archives.

Teamcity requires basic access authentication, which could either be provided via environment variable `TEAMCITY_USER` and `TEAMCITY_PASSWORD` or via the url directly with `username:password@` added in front of hostname.
```
TEAMCITY_USER=username TEAMCITY_PASSWORD=password TEAMCITY_NEO4J_30NIGHTLY=https://<teamcity_hostname>/repository/download/<build_type_id>/lastSuccessful/<artifact_path> python neoget.py -n 3.0
```
or
```
TEAMCITY_NEO4J_30NIGHTLY=https://username:password@<teamcity_hostname>/repository/download/<build_type_id>/lastSuccessful/<artifact_path> python neoget.py -n 3.0
```

witch is almost equivalent to
```
curl --user username:password -O https://<teamcity_hostname>/repository/download/<build_type_id>/lastSuccessful/<artifact_path>
```

For a full help page, use `-h`:
```
python neoget.py -h
```

## Neoctl
Neoctl is a controller for start and stop Neo4j packages. It also provides a method to update default neo4j password.

To start a server, use the `start` command:
```
python neoctl.py --start=neo4j
```

Similarly, to stop a server, use the `stop` command:
```
python neoctl.py --stop=neo4j
```

To change the default passowrd of a Neo4j server, simply use
```
python neoctrl.py --update-passowrd=s3cr3tP4ssw0rd
```


## Neorun
Neorun provides commands to start and stop a Neo4j server with the guarantee that the server is fully started and stopped when the script returns.
The start command also exposes a command to download and install a specific Neo4j server if no Neo4j found locally,
as well as an option to change the default server password after the start.

To start a Neo4j server, simply use the following command:
```
python neorun.py --start=neo4j
```
When the script returns, then the server is fully ready for any database tasks.

If no Neo4j server is found in path `./neo4j`, then the default Neo4j server version used in `neoget.py` will be downloaded and installed to `./neo4j`.
To specify other versions to download when a Neo4j is absent, use `-v`, `-t`, `-l` in a similar way as they are defined in `neoget.py`:
```
python neorun.py --start=neo4j -v 3.0.2 -p s3cr3tP4ssw0rd
```
In the example above, the `-p` option is used to change the default Neo4j password after the server is ready.

For stopping the server, simply use the `stop` command:
```
python neorun.py --stop=neo4j
```

