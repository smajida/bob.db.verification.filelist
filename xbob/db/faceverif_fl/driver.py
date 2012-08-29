#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Laurent El Shafey <laurent.el-shafey@idiap.ch>

"""Commands the Face Verification File Lists database can respond to.
"""

import os
import sys
from bob.db.driver import Interface as BaseInterface

class Interface(BaseInterface):
   
  def name(self):
    return 'faceverif_fl'
  
  def version(self):
    import pkg_resources  # part of setuptools
    return pkg_resources.require('xbob.db.%s' % self.name())[0].version
  
  def files(self):

    from pkg_resources import resource_filename
    raw_files = ( 
        'raw_real.txt',
        'raw_attack.txt',
        'normalized_face_real.txt',
        'normalized_face_attack.txt',
        'detected_face_real.txt',
        'detected_face_attack.txt',
        'cross_valid.txt',
        os.path.join('raw', 'imposter_train_raw.txt'),
        os.path.join('raw', 'imposter_test_raw.txt'),
        os.path.join('raw', 'client_train_raw.txt'),
        os.path.join('raw', 'client_test_raw.txt'),
        os.path.join('NormalizedFace', 'imposter_train_normalized.txt'),
        os.path.join('NormalizedFace', 'imposter_test_normalized.txt'),
        os.path.join('NormalizedFace', 'client_train_normalized.txt'),
        os.path.join('NormalizedFace', 'client_test_normalized.txt'),
        os.path.join('Detectedface', 'imposter_train_face.txt'),
        os.path.join('Detectedface', 'imposter_test_face.txt'),
        os.path.join('Detectedface', 'client_train_face.txt'),
        os.path.join('Detectedface', 'client_test_face.txt'),
        )  
    return [resource_filename(__name__, k) for k in raw_files]

  def type(self):
    return 'text'

  def add_commands(self, parser):

    from . import __doc__ as docs
    
    subparsers = self.setup_parser(parser,
        "Face Verification File Lists database", docs)

    # example: get the "dumplist" action from a submodule
    from .dumplist import add_command as dumplist_command
    dumplist_command(subparsers)

    # example: get the "checkfiles" action from a submodule
    from .checkfiles import add_command as checkfiles_command
    checkfiles_command(subparsers)

