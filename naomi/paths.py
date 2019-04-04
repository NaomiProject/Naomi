# -*- coding: utf-8 -*-
import os

# Naomi main directory
PKG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(PKG_PATH, "data")
PLUGIN_PATH = os.path.normpath(os.path.join(PKG_PATH, os.pardir, "plugins"))

SUB_PATH = os.path.expanduser(os.getenv(‘NAOMI_SUB’,os.getenv(‘JASPER_CONFIG’,”~/.naomi”)))
CONFIG_PATH = os.path.join(SUB_PATH, 'configs')


def config(*fname):
    return os.path.join(CONFIG_PATH, *fname)

def sub(*fname):
    return os.path.join(SUB_PATH, *fname)

def data(*fname):
    return os.path.join(DATA_PATH, *fname)
