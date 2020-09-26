# ncs-yang

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache2-yellow.svg)](https://opensource.org/licenses/Apache-2.0)
[![Version: 1.1.1](https://img.shields.io/badge/Version-1.1.1-parrotgreen.svg)](https://github.com/kirankotari/ncs-yang)
[![Downloads](https://pepy.tech/badge/ncs-yang)](https://pepy.tech/project/ncs-yang)
[![Downloads](https://pepy.tech/badge/ncs-yang/week)](https://pepy.tech/project/ncs-yang/week)

**ncs-yang** is a simple tool to compile yang files using **ncsc**. By compiling only the required yang files makes the developer simplier and faster to develop yang files.

- [Introduction](#introduction)
- [Pre-requisites](#pre-requisites)
- [Installation and Downloads](#installation-and-downloads)
- [Features](#features)
- [Help](#help)
- [FAQ](#faq)
- [Bug Tracking and Support](#bug-tracking-and-support)
- [License and Copyright](#license-and-copyright)
- [Author and Thanks](#author-and-thanks)

## Introduction 
When I was working with big projects to compile a simple yang it use to take long time due to `make clean all` compiles all the yangs persent in the given package. When looked in I was able to compile a single yang file with dependencies, which boosted me to make this lib to help other NSO developers. 

It makes life simplier and easier to compiles only required yang files then all of them. in the big projectsIn the process we collect Makefile dependences and compile it for you.

## Pre-requisites

- ncsc command must be reconginsed by the terminal.
- ncs-yang supports both trains of **python** `2.7+ and 3.1+`, the OS should not matter.

## Installation and Downloads

The best way to get ncs-yang is with setuptools or pip. If you already have setuptools, you can install as usual:

`python -m pip install ncs-yang`  
`pip install ncs-yang`

Otherwise download it from PyPi, extract it and run the `setup.py` script

`python setup.py install`

If you're Interested in the source, you can always pull from the github repo:

- From github `git clone https://github.com/kirankotari/ncs-yang.git`

## Features

- running single yang file 
```bash
⋊> ~/k/i/cfs-package on sprint $ ncs-yang src/yang/cfs-mpls.yang
[ INFO ] :: [ ncs-yang ] :: compiling yang file: src/yang/cfs-mpls.yang
 /opt/ncs/ncs-5.2.1.2/bin/ncsc `ls cfs-mpls-ann.yang > /dev/null 2>&1 && echo "-a cfs-mpls-ann.yang"` --yangpath /opt/ncs/ncs-run/packages/cfs-package/src/../../common/src/yang --yangpath /opt/ncs/ncs-run/packages/cfs-package/src/../../resource-manager/src/yang -c -o /opt/ncs/ncs-run/packages/cfs-package/load-dir/cfs-mpls.fxs src/yang/cfs-mpls.yang
```
- running multiple yang files
```bash
⋊> ~/k/i/cfs-package/src/yang on sprint $ ncs-yang cfs-mpls.yang cfs-asa.yang
[ INFO ] :: [ ncs-yang ] :: compiling yang file: cfs-mpls.yang
 /opt/ncs/ncs-5.2.1.2/bin/ncsc `ls cfs-mpls-ann.yang > /dev/null 2>&1 && echo "-a cfs-mpls-ann.yang"` --yangpath /opt/ncs/ncs-run/packages/cfs-package/src/../../common/src/yang --yangpath /opt/ncs/ncs-run/packages/cfs-package/src/../../resource-manager/src/yang -c -o /opt/ncs/ncs-run/packages/cfs-package/load-dir/cfs-mpls.fxs cfs-mpls.yang
[ INFO ] :: [ ncs-yang ] :: compiling yang file: cfs-asa.yang
 /opt/ncs/ncs-5.2.1.2/bin/ncsc `ls cfs-asa-ann.yang > /dev/null 2>&1 && echo "-a cfs-asa-ann.yang"` --yangpath /opt/ncs/ncs-run/packages/cfs-package/src/../../common/src/yang --yangpath /opt/ncs/ncs-run/packages/cfs-package/src/../../resource-manager/src/yang -c -o /opt/ncs/ncs-run/packages/cfs-package/load-dir/cfs-asa.fxs cfs-asa.yang
```
## Help

```bash
⋊> ~/k/i/ncs-yang on master $ ncs-yang --help

ncs-yang
    <filename.yang>
    <path-to-filename.yang>
    -h | --help
    -v | --version
```

## FAQ

- **Question:** Do I need to install ncsc too?  
 **Answer:** Not really, ncsc tool comes along with NSO. If you are working with NSO it's won't be a problem.  

- **Question:** Is python mandatory for ncsc?  
 **Answer:** Yes, the library is written in python and we wanted not to be dependend on NSO versions.   

- **Question:** I am seeing an error?  
 **Answer:** Error might be related to yang file, we recommend to check again beforing opening a bug.
 
## Bug Tracking and Support

- Please report any suggestions, bug reports, or annoyances with ncs-yang through the [Github bug tracker](https://github.com/kirankotari/ncs-yang/issues).


## License and Copyright

- ncs-yang is licensed [Apache 2.0](https://opensource.org/licenses/Apache-2.0) *2019-2020*

   [![License: Apache 2.0](https://img.shields.io/badge/License-Apache2-yellow.svg)](https://opensource.org/licenses/Apache-2.0)

## Author and Thanks

ncs-yang was developed by [Kiran Kumar Kotari](https://github.com/kirankotari), For any suggestions or comments contact kkotari@cisco.com or kirankotari@live.com. If you find any bugs please fix them and send me a pull request.