packman
=======

* Master [![Circle CI](https://circleci.com/gh/cloudify-cosmo/packman/tree/master.svg?style=shield)](https://circleci.com/gh/cloudify-cosmo/packman/tree/master)

[![Build Status](https://travis-ci.org/cloudify-cosmo/packman.svg?branch=master)](https://travis-ci.org/cloudify-cosmo/packman)

[![Gitter chat](https://badges.gitter.im/cloudify-cosmo/packman.png)](https://gitter.im/cloudify-cosmo/packman)

[![PyPI](http://img.shields.io/pypi/dm/packman.svg)](http://img.shields.io/pypi/dm/packman.svg)

[![PypI](http://img.shields.io/pypi/v/packman.svg)](http://img.shields.io/pypi/v/packman.svg)

`packman` creates packages.

You can write a `packages file` containing your packages' configuration and packman will retrieve the resources and create the packages accordingly.

The project was initally invented to create Cloudify (http://getcloudify.org/) packages and is now progressing towards being a simple open-source solution to creating different types of packages.

### Quick Start
[Quick Start](http://packman.readthedocs.org/en/latest/quick_start.html)

### Documentation
[packman documentation](https://packman.readthedocs.org/en/latest/)

### Installation
see [packman requirements](http://packman.readthedocs.org/en/latest/installation.html#pre-requirements) before installing packman
```shell
 pip install packman
 # or, for dev:
 pip install https://github.com/cloudify-cosmo/cloudify-packager/archive/master.tar.gz
```

### Usage Examples
see [Packages Configuration](http://packman.readthedocs.org/en/latest/component_config.html) to configure your `packages file`
```shell
 # `pkm get` retrieves package sources
 pkm get --packages my_package --packages_file /my_packages_file.yaml
 # `pkm pack` packages sources, scripts and configs.
 pkm pack -c my_package,my_other_package
 # `pkm make` ... does both one after the other
 pkm make -x excluded_package,excluded_package2
```

### Additional Information
- [packman's cli](http://packman.readthedocs.org/en/latest/pkm.html)
- [Alternative Implementations](http://packman.readthedocs.org/en/latest/alternative_methods.html)
- [Template Handling](http://packman.readthedocs.org/en/latest/template_handling.html)
- [packman API](http://packman.readthedocs.org/en/latest/api.html)
