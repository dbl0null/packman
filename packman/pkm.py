#!/usr/bin/env python
########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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

"""Script to run packman via command line

Usage:
    pkm get [--components=<list> --components_file=<path> --exclude=<list>]
    pkm pack [--components=<list> --components_file=<path> --exclude=<list>]
    pkm make [--components=<list> --components_file=<path> --exclude=<list>]
    pkm --version

Arguments:
    pack     Packs "Component" configured in packages.py
    get      Gets "Component" configured in packages.py
    make     Gets AND (yeah!) Packs.. don't ya kno!

Options:
    -h --help                   Show this screen.
    -c --components=<list>      Comma Separated list of component names
    -x --exclude=<list>         Comma Separated list of excluded components
    --components_file=<path>
    --verbose                   a LOT of output (NOT YET IMPLEMENTED)
    -v --version                Display current version of sandman and exit

"""

from __future__ import absolute_import
from docopt import docopt

from packman.packman import packman_runner


def main(test_options=None):
    """Main entry point for script."""
    import pkg_resources
    version = None
    try:
        version = pkg_resources.get_distribution('packman').version
    except Exception as e:
        print(e)
    finally:
        del pkg_resources

    # TODO: implement verbose output
    options = test_options or docopt(__doc__, version=version)
    print(options)
    if options['pack']:
        packman_runner('pack',
                       options.get('--components_file'),
                       options.get('--components'),
                       options.get('--exclude'))
    elif options['get']:
        packman_runner('get',
                       options.get('--components_file'),
                       options.get('--components'),
                       options.get('--exclude'))
    elif options['make']:
        packman_runner('get',
                       options.get('--components_file'),
                       options.get('--components'),
                       options.get('--exclude'))
        packman_runner('pack',
                       options.get('--components_file'),
                       options.get('--components'),
                       options.get('--exclude'))


if __name__ == '__main__':
    main()
