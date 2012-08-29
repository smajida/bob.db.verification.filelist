#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Laurent El Shafey <laurent.el-shafey@idiap.ch>
#
# Copyright (C) 2011-2012 Idiap Research Institute, Martigny, Switzerland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""A few checks at the Face Verification File Lists database.
"""

import os, sys
import unittest
from .query import Database

class Faceverif_flDatabaseTest(unittest.TestCase):
  """Performs various tests on the Face Verification File Lists database."""

  def test01_query(self):

    db = Database('xbob/db/faceverif_fl/example_fl')
    self.assertEqual(len(db.models()), 6) # 6 model ids for world, dev and eval
    self.assertEqual(len(db.models(groups='world')), 2) # 2 model ids for world
    self.assertEqual(len(db.models(groups='dev')), 2) # 2 model ids for dev
    self.assertEqual(len(db.models(groups='eval')), 2) # 2 model ids for eval

    self.assertEqual(len(db.tmodels()), 2) # 2 model ids for T-Norm score normalisation
    self.assertEqual(len(db.zmodels()), 2) # 2 model ids for Z-Norm score normalisation

    self.assertEqual(len(db.objects(groups='world')), 8) # 8 samples in the world set

    self.assertEqual(len(db.objects(groups='dev', purposes='enrol')), 8) # 8 samples for enrolment in the dev set
    self.assertEqual(len(db.objects(groups='dev', purposes='probe', classes='client')), 8) # 8 samples as client probes in the dev set
    self.assertEqual(len(db.objects(groups='dev', purposes='probe', classes='impostor')), 4) # 4 samples as impostor probes in the dev set

    self.assertEqual(len(db.tobjects(groups='dev')), 8) # 8 samples for enroling T-norm models
    self.assertEqual(len(db.zobjects(groups='dev')), 8) # 8 samples for Z-norm impostor accesses

    self.assertEqual(len(db.objects(groups='eval', purposes='enrol')), 8) # 8 samples for enrolment in the dev set
    self.assertEqual(len(db.objects(groups='eval', purposes='probe', classes='client')), 8) # 8 samples as client probes in the dev set
    self.assertEqual(len(db.objects(groups='eval', purposes='probe', classes='impostor')), 0) # 0 samples as impostor probes in the dev set

    self.assertEqual(len(db.tobjects(groups='eval')), 8) # 8 samples for enroling T-norm models
    self.assertEqual(len(db.zobjects(groups='eval')), 8) # 8 samples for Z-norm impostor accesses

    self.assertEqual(db.get_client_id_from_model_id('1'), '1')
    self.assertEqual(db.get_client_id_from_model_id('3'), '3')
    self.assertEqual(db.get_client_id_from_model_id('6'), '6')
    self.assertEqual(db.get_client_id_from_tmodel_id('7'), '7')

  def test02_manage_dumplist_1(self):

    from bob.db.script.dbmanage import main

    self.assertEqual(main('faceverif_fl dumplist -b xbob/db/faceverif_fl/example_fl --self-test'.split()), 0)

  def test03_manage_checkfiles(self):

    from bob.db.script.dbmanage import main

    self.assertEqual(main('faceverif_fl checkfiles -b xbob/db/faceverif_fl/example_fl --self-test'.split()), 0)
