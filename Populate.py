#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import logging
import naomi
import os
import yaml

logging.basicConfig(level=logging.CRITICAL)

configfile = naomi.paths.config('profile.yml')

if os.path.exists(configfile):
    with open(configfile, "r") as f:
        config = yaml.safe_load(f)
else:
    config = {}

naomi.populate.run(config)
