#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import naomi
import sys

class SystemError(Exception):
    def __init__(self,message):
        self.message = message

if(sys.version_info.major < 3):
    raise SystemError("This version of Naomi requires Python 3.5 or greater")

naomi.main()
