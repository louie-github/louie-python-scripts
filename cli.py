#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from docopt import docopt

class _DocoptCLI

class StandardCLI(object):
    def __init__(self, parser = 'argparse',):
        self.parser = parser
            
    def configure(self, *args, **kwargs):
        if self.parser == 'argparse':
            argparse.ArgumentParser.__init__(self)
        elif self.parser == 'docopt':


    def _docopt_parse(args, )