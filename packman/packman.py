#!/usr/bin/env python
# #
# ###### Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

# TODO: (FEAT) add http://megastep.org/makeself/ support
# TODO: (FEAT) add http://semver.org/ support
# TODO: (FEAT) add support to download and run from github repos so that "components" repos can be created  # NOQA

import logger
import utils

import python
import yum
import retrieve
import apt
import ruby
import templater
import fpm
import codes

import definitions as defs

import os
import yaml
import fabric.api as fab
import sys
import platform

# __all__ = ['list']

SUPPORTED_DISTROS = ('Ubuntu', 'debian', 'centos')
DEFAULT_PACKAGES_FILE = 'packages.yaml'
PACKAGE_TYPES = {"centos": "rpm", "debian": "deb"}


lgr = logger.init()


def get_distro():
    """returns the machine's distro
    """
    return platform.dist()[0]


def check_distro(supported=SUPPORTED_DISTROS, verbose=False):
    """checks that the machine's distro is supported

    :param tuple supported: tuple of supported distros
    :param bool verbose: verbosity level
    """
    utils.set_global_verbosity_level(verbose)
    distro = get_distro()
    lgr.debug('Distribution Identified: {0}'.format(distro))
    if distro not in supported:
        lgr.error('Your distribution is not supported.'
                  'Supported Disributions are:')
        for distro in supported:
            lgr.error('    {0}'.format(distro))
        sys.exit(codes.mapping['distro not supported'])


def _import_packages_dict(config_file=None):
    """returns a configuration object

    :param string config_file: path to config file
    """
    if config_file is None:
        try:
            with open(DEFAULT_PACKAGES_FILE, 'r') as c:
                return yaml.safe_load(c.read())['packages']
        except:
            lgr.error('No config file defines and could not find '
                      'packages.yaml in currect directory.')
            sys.exit(codes.mapping['packages_file_not_found'])
    # get config file path
    lgr.debug('Config file is: {}'.format(config_file))
    # append to path for importing
    try:
        lgr.info('importing config...')
        with open(config_file, 'r') as c:
            return yaml.safe_load(c.read())['packages']
    except IOError as ex:
        lgr.error(ex.message)
        lgr.error('Cannot access config file')
        sys.exit(codes.mapping['cannot_access_config_file'])
    except (yaml.parser.ParserError, yaml.scanner.ScannerError) as ex:
        lgr.error(ex.message)
        lgr.error('Invalid yaml file')
        sys.exit(codes.mapping['invalid_yaml_file'])


def get_package_config(package_name, packages_dict=None,
                       packages_file=None):
    """returns a package's configuration

    if `packages_dict` is not supplied, a packages.yaml file in the cwd will be
    assumed unless `packages_file` is explicitly given.
    after a `packages_dict` is defined, a `package_config` will be returned
    for the specified package_name.

    :param string package: package name to retrieve config for.
    :param dict packages_dict: dict containing packages configuration
    :param string packages_file: packages file to search in
    :rtype: `dict` representing package configuration
    """
    if packages_dict is None:
        packages_dict = {}
    lgr.debug('Retrieving configuration for {0}'.format(package_name))
    try:
        if not packages_dict:
            packages_dict = _import_packages_dict(packages_file)
        lgr.debug('{0} config retrieved successfully'.format(package_name))
        return packages_dict[package_name]
    except KeyError:
        lgr.error('Package configuration for'
                  ' {0} was not found, terminating...'.format(package_name))
        sys.exit(codes.mapping['no_config_found_for_package'])


def packman_runner(action, packages_file=None, packages=None,
                   excluded=None, verbose=False):
    """logic for running packman. mainly called from the cli (pkm.py)

    if no `packages_file` is supplied, we will assume a local packages.yaml
    as `packages_file`.

    if `packages` are supplied, they will be iterated over.
    if `excluded` are supplied, they will be ignored.

    if a pack.py or get.py files are present, and an action_package
    function exists in the files, those functions will be used.
    else, the base get and pack methods supplied with packman will be used.
    so for instance, if you have a package named `x`, and you want to write
    your own `get` function for it. Just write a get_x() function in get.py.

    :param string action: action to perform (get, pack)
    :param string packages_file: path to file containing package config
    :param string packages: comma delimited list of packages to perform
     `action` on.
    :param string excluded: comma delimited list of packages to exclude
    :param bool verbose: determines output verbosity level
    :rtype: `None`
    """
    def _build_excluded_packages_list(excluded_packages):
        lgr.debug('Building excluded packages list...')
        return filter(None, (excluded_packages or "").split(','))

    def _build_packages_list(packages, xcom_list, packages_dict):
        lgr.debug('Building packages list...')
        com_list = []
        if packages:
            for package in packages.split(','):
                com_list.append(package)
            # and raise if same package appears in both lists
            if set(com_list) & set(xcom_list):
                lgr.error('Your packages list and excluded packages '
                          'list contain a similar item.')
                sys.exit(codes.mapping['excluded_conflict'])
        # else iterate over all packages in packages file
        else:
            for package, values in packages_dict.items():
                com_list.append(package)
            # and rewrite the list after removing excluded packages
            for xcom in xcom_list:
                com_list = [com for com in com_list if com != xcom]
        return com_list

    def _import_overriding_methods(action):
        lgr.debug('Importing overriding methods file...')
        return __import__(os.path.basename(os.path.splitext(
            os.path.join(os.getcwd(), '{0}.py'.format(action)))[0]))

    def _rename_package(package):
        # replace hyphens with underscores and remove dots from the
        # overriding methods names
        # also, convert to lowercase to correspond with overriding
        # method names.
        package_re = package.replace('-', '_')
        package_re = package_re.replace('.', '')
        package_re = package_re.lower()
        return package_re

    utils.set_global_verbosity_level(verbose)
    # import dict of all packages
    packages_dict = _import_packages_dict(packages_file)
    # append excluded packages to list.
    xcom_list = _build_excluded_packages_list(excluded)
    lgr.debug('Excluded packages list: {0}'.format(xcom_list))
    # append packages to list if a list is supplied
    com_list = _build_packages_list(packages, xcom_list, packages_dict)
    lgr.debug('Packages list: {0}'.format(com_list))
    # if at least 1 package exists
    if com_list:
        # iterate and run action
        for package in com_list:
            # looks for the overriding methods file in the current path
            if os.path.isfile(os.path.join(
                    os.getcwd(), '{0}.py'.format(action))):
                # imports the overriding methods file
                # TODO: allow sending parameters to the overriding methods
                overr_methods = _import_overriding_methods(action)
                # rename overriding package name by convention
                package = _rename_package(package)
                # if the method was found in the overriding file, run it.
                if hasattr(overr_methods, '{0}_{1}'.format(action, package)):
                    getattr(overr_methods, '{0}_{1}'.format(action, package))()
                # else run the default action method
                else:
                    # TODO: check for bad action
                    globals()[action](get_package_config(
                        package, packages_file=packages_file))
            # else run the default action method
            else:
                globals()[action](get_package_config(
                    package, packages_file=packages_file))
    else:
        lgr.error('No packages to handle, check your packages file')
        sys.exit(codes.mapping['no_packages_defined'])


def get(package):
    """retrieves resources for packaging

    .. note:: package params are defined in packages.yaml

    .. note:: param names in packages.yaml can be overriden by editing
     definitions.py which also has an explanation on each param.

    :param dict package: dict representing package config
     as configured in packages.yaml
     will be appended to the filename and to the package
     depending on its type
    :rtype: `None`
    """

    def handle_sources_path(sources_path, overwrite):
        if sources_path is None:
            lgr.error('Sources path key is required under {0} '
                      'in packages.yaml.'.format(defs.PARAM_SOURCES_PATH))
            sys.exit(codes.mapping['sources_path_required'])
        u = utils.Handler()
        # should the source dir be removed before retrieving package contents?
        if overwrite:
            lgr.info('Overwrite enabled. removing {0} before retrieval'.format(
                sources_path))
            u.rmdir(sources_path)
        else:
            if u.is_dir(sources_path):
                lgr.error('The destination directory for this package already '
                          'exists and overwrite is disabled.')
                sys.exit(codes.mapping['path_already_exists_no_overwrite'])
        # create the directories required for package creation...
        if not u.is_dir(sources_path):
            u.mkdir(sources_path)

    # you can send the package dict directly, or retrieve it from
    # the packages.yaml file by sending its name
    c = package if isinstance(package, dict) else get_package_config(package)

    # set handlers
    repo = yum.Handler() if CENTOS else apt.Handler() if DEBIAN else None
    retr = retrieve.Handler()
    py = python.Handler()
    rb = ruby.Handler()

    # everything will be downloaded here
    sources_path = c.get(defs.PARAM_SOURCES_PATH, None)
    handle_sources_path(
        sources_path, c.get(defs.PARAM_OVERWRITE_SOURCES, True))

    # TODO: (TEST) raise on "command not supported by distro"
    # TODO: (FEAT) add support for building packages from source
    repo.install(c.get(defs.PARAM_PREREQS, []))
    repo.add_src_repos(c.get(defs.PARAM_SOURCE_REPOS, []))
    repo.add_ppa_repos(c.get(defs.PARAM_SOURCE_PPAS, []), DEBIAN, get_distro())
    retr.downloads(c.get(defs.PARAM_SOURCE_KEYS, []), sources_path)
    repo.add_keys(c.get(defs.PARAM_SOURCE_KEYS, []), sources_path)
    retr.downloads(c.get(defs.PARAM_SOURCE_URLS, []), sources_path)
    repo.download(c.get(defs.PARAM_REQS, []), sources_path)
    py.get_modules(c.get(defs.PARAM_PYTHON_MODULES, []), sources_path)
    rb.get_gems(c.get(defs.PARAM_RUBY_GEMS, []), sources_path)
    # nd.get_packages(c.get(defs.PARAM_NODE_PACKAGES, []), sources_path)
    lgr.info('Package retrieval completed successfully!')


def pack(package):
    """creates a package according to the provided package configuration
    in packages.yaml
    uses fpm (https://github.com/jordansissel/fpm/wiki) to create packages.

    .. note:: package params are defined in packages.yaml but can be passed
     directly to the pack function as a dict.

    .. note:: param names in packages.yaml can be overriden by editing
     definitions.py which also has an explanation on each param.

    :param string|dict package: string or dict representing package
     name or params (coorespondingly) as configured in packages.yaml
    :rtype: `None`
    """

    def handle_package_path(package_path, sources_path, name, overwrite):
        if not common.is_dir(package_path):
            common.mkdir(package_path)
        # can't use sources_path == package_path for the package... duh!
        if sources_path == package_path:
            lgr.error('Sources path and package paths must'
                      ' be different to avoid conflicts!')
            sys.exit(codes.mapping['sources_and_package_paths_identical'])
        if overwrite:
            lgr.info('Overwrite enabled. Removing {0}/{1}* '
                     'before packaging'.format(package_path, name))
            common.rm('{0}/{1}*'.format(package_path, name))

    def set_dst_pkg_type():
        lgr.debug('Destination package type omitted')
        if CENTOS:
            lgr.debug('Assuming default type: {0}'.format(
                PACKAGE_TYPES['centos']))
            return [PACKAGE_TYPES['centos']]
        elif DEBIAN:
            lgr.debug('Assuming default type: {0}'.format(
                PACKAGE_TYPES['debian']))
            return [PACKAGE_TYPES['debian']]

    # you can send the package dict directly, or retrieve it from
    # the packages.yaml file by sending its name
    c = package if isinstance(package, dict) else get_package_config(package)

    # define params for packaging process
    name = c.get(defs.PARAM_NAME)
    bootstrap_template = c.get(defs.PARAM_BOOTSTRAP_TEMPLATE_PATH, False)
    bootstrap_script = c.get(defs.PARAM_BOOTSTRAP_SCRIPT_PATH, False)
    src_pkg_type = c.get(defs.PARAM_SOURCE_PACKAGE_TYPE, False)
    dst_pkg_types = c.get(
        defs.PARAM_DESTINATION_PACKAGE_TYPES, set_dst_pkg_type())
    try:
        sources_path = c[defs.PARAM_SOURCES_PATH]
    except KeyError:
        lgr.error('Sources path key is required under {0} '
                  'in packages.yaml.'.format(defs.PARAM_SOURCES_PATH))
    package_path = c.get(defs.PARAM_PACKAGE_PATH, os.getcwd())

    # set handlers
    common = utils.Handler()
    templates = templater.Handler()

    handle_package_path(
        package_path, sources_path, name,
        c.get(defs.PARAM_OVERWRITE_OUTPUT, False))

    lgr.info('Generating package scripts and config files...')
    if c.get(defs.PARAM_CONFIG_TEMPLATE_CONFIG, False):
        templates.generate_configs(c)
    if bootstrap_script:
        templates.generate_from_template(
            c, bootstrap_script, bootstrap_template)
        for package in dst_pkg_types:
            if package in ('tar', 'tar.gz'):
                lgr.debug('Granting execution permissions to script.')
                utils.do('chmod +x {0}'.format(bootstrap_script))
                lgr.debug('Copying bootstrap script to package directory')
                common.cp(bootstrap_script, sources_path)

    lgr.info('Packaging: {0}'.format(name))
    # this checks if a package needs to be created. If no source package type
    # is supplied, the assumption is that packages are only being downloaded
    # so if there's a source package type...
    if src_pkg_type:
        if not os.listdir(sources_path) == []:
            # change the path to the destination path, since fpm doesn't
            # accept (for now) a dst dir, but rather creates the package in
            # the cwd.
            with fab.lcd(package_path):
                for dst_pkg_type in dst_pkg_types:
                    i = fpm.Handler(name, src_pkg_type, dst_pkg_type,
                                    os.path.abspath(sources_path), sudo=True)
                    i.execute(version=c.get(defs.PARAM_VERSION, False),
                              force=c.get(defs.PARAM_OVERWRITE_OUTPUT, True),
                              depends=c.get(defs.PARAM_DEPENDS, False),
                              after_install=bootstrap_script,
                              chdir=False, before_install=None)
                    if dst_pkg_type == "tar.gz":
                        lgr.debug('Converting tar to tar.gz...')
                        utils.do('sudo gzip {0}.tar*'.format(name))
                    # lgr.info("isolating archives...")
                    # common.mv('{0}/*.{1}'.format(
                    #     package_path, dst_pkg_type), package_path)
        else:
            lgr.error('Sources directory is empty. Nothing to package.')
            sys.exit(codes.mapping['sources_empty'])
    else:
        lgr.info("Isolating archives...")
        for dst_pkg_type in dst_pkg_types:
            common.mv('{0}/*.{1}'.format(
                package_path, dst_pkg_type), package_path)
    lgr.info('Package creation completed successfully!')
    if not c.get(defs.PARAM_KEEP_SOURCES, True):
        lgr.debug('Removing sources...')
        common.rmdir(sources_path)


def main():
    lgr.debug('Running in main...')

if __name__ == '__main__':
    main()

CENTOS = get_distro() in ('centos')
DEBIAN = get_distro() in ('Ubuntu', 'debian')
