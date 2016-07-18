#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# @author: Manuel Guenther <Manuel.Guenther@idiap.ch>
# @date: Wed Oct 24 10:47:43 CEST 2012
#
# Copyright (C) 2011-2013 Idiap Research Institute, Martigny, Switzerland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This file defines simple Client and File interfaces that are comparable with other bob.db databases.
"""

import os
import fileinput
import re
import bob.io.base


class Client(object):
    """
    The clients of this database contain ONLY client ids. Nothing special.
    """

    def __init__(self, client_id):
        self.id = client_id
        """The ID of the client, which is stored as a :py:class:`str` object."""


class File(object):
    """
     Initialize the File object with the minimum required data.

     If the ``model_id`` is not specified, ``model_id`` and ``client_id`` are identical.
     If the ``claimed_id`` is not specified, it is expected to be the ``client_id``.

     **Parameters**

     client_id : various type
       The id of the client, this file belongs to.
       The type of it is dependent on your implementation.
       If you use an SQL database, this should be an SQL type like Integer or String.
     path : str
       The path of this file, relative to the basic directory.
       If you use an SQL database, this should be the SQL type String.
       Please do not specify any file extensions.
     file_id : various type
       The id of the file.
       The type of it is dependent on your implementation.
       If you use an SQL database, this should be an SQL type like Integer or String.
       If you are using an automatically determined file id, you can skip selecting the file id.
    """

    def __init__(self, file_name, client_id, model_id=None, claimed_id=None):
        self.file_id = file_name  # Merged from bob.db.verification.utils
        self.id = file_name  # Merged from bob.db.verification.utils
        self.client_id = client_id
        self.path = file_name


        # Note: in case of probe files, model ids are considered to be the ids of the model for the given probe file.
        # Hence, there might be several probe files with the same file id, but different model ids.
        # Therefore, please DO NOT USE the model_id outside of this class (or the according database queries).
        # when the model id is not specified, we use the client id instead
        self._model_id = client_id if model_id is None else model_id
        # when the claimed id is not specified, we use the client id instead
        self.claimed_id = client_id if claimed_id is None else claimed_id

    def __lt__(self, other):
        """
        This function defines the order on the File objects. File objects are always ordered by their ID, in ascending
        order.
        """
        return self.id < other.id

    def __repr__(self):
        """This function describes how to convert a File object into a string.
        Overwrite it if you want more/other details of the File to be written."""
        return "<File('%s': '%s' -- '%s')>" % (str(self.id), str(self.client_id), str(self.path))

    def make_path(self, directory=None, extension=None):
        """Wraps the current path so that a complete path is formed
        Keyword parameters:
        directory : str or None
          An optional directory name that will be prefixed to the returned result.
        extension : str or None
          An optional extension that will be suffixed to the returned filename.
          The extension normally includes the leading ``.`` character as in ``.jpg`` or ``.hdf5``.
        Returns a string containing the newly generated file path.
        """
        # assure that directory and extension are actually strings
        if not directory: directory = ''
        if not extension: extension = ''
        # create the path
        return str(os.path.join(directory, self.path + extension))

    def save(self, data, directory=None, extension='.hdf5', create_directories=True):
        """Saves the input data at the specified location and using the given extension.
        Keyword parameters:
        data : various types
          The data blob to be saved (normally a :py:class:`numpy.ndarray`).
        directory : str or None
          If not empty or None, this directory is prefixed to the final file destination
        extension : str or None
          The extension of the filename.
          This extension will control the type of output and the codec for saving the input blob.
        create_directories : bool
          Should the directory structure be created (if necessary) before writing the data?
        """
        # get the path
        path = self.make_path(directory, extension)
        # use the bob API to save the data
        bob.io.base.save(data, path, create_directories=create_directories)


#############################################################################
### internal access functions for the file lists; do not export!
#############################################################################


class ListReader(object):
    def __init__(self, store_lists):
        self.m_read_lists = {}
        self.m_model_dicts = {}
        self.m_store_lists = store_lists

    def _read_multi_column_list(self, list_file):
        rows = []
        if not os.path.isfile(list_file):
            raise RuntimeError('File %s does not exist.' % (list_file,))
        try:
            for line in fileinput.input(list_file):
                parsed_line = re.findall('[\w/(-.)]+', line)
                if len(parsed_line):
                    # perform some sanity checks
                    if len(parsed_line) not in (2, 3, 4):
                        raise IOError("The read line '%s' from file '%s' could not be parsed successfully!" % (
                        line.rstrip(), list_file))
                    if len(rows) and len(rows[0]) != len(parsed_line):
                        raise IOError(
                            "The parsed line '%s' from file '%s' has a different number of elements than the first parsed line '%s'!" % (
                            parsed_line, list_file, rows[0]))
                    # append the read line
                    rows.append(parsed_line)
            fileinput.close()
        except IOError as e:
            raise RuntimeError("Error reading the file '%s' : '%s'." % (list_file, e))

        # return the read list as a vector of columns
        return rows

    def _read_column_list(self, list_file, column_count):
        # read the list
        rows = self._read_multi_column_list(list_file)
        # extract the file from the first two columns
        file_list = []
        for row in rows:
            if column_count == 2:
                assert len(row) == 2
                # we expect: filename client_id
                file_list.append(File(file_name=row[0], client_id=row[1]))
            elif column_count == 3:
                assert len(row) in (2, 3)
                # we expect: filename, model_id, client_id
                file_list.append(File(file_name=row[0], client_id=row[2] if len(row) > 2 else row[1], model_id=row[1]))
            elif column_count == 4:
                assert len(row) in (3, 4)
                # we expect: filename, model_id, claimed_id, client_id
                file_list.append(File(file_name=row[0], client_id=row[3] if len(row) > 3 else row[1], model_id=row[1],
                                      claimed_id=row[2]))
            else:
                raise ValueError(
                    "The given column count %d cannot be interpreted. This is a BUG, please report to the author." % column_count)

        return file_list

    def _create_model_dictionary(self, files):
        # remember model ids
        retval = {}
        for file in files:
            if file._model_id not in retval:
                retval[file._model_id] = file.client_id
            else:
                if retval[file._model_id] != file.client_id:
                    raise ValueError(
                        "The read model id '%s' is associated to two different client ids '%s' and '%s'!" % (
                        file._model_id, file.client_id, retval[file._model_id]))
        return retval

    def read_list(self, list_file, group, type=None):
        """Reads the list of Files from the given list file (if not done yet) and returns it."""
        if group in ('world', 'optional_world_1', 'optional_world_2'):
            if group not in self.m_read_lists:
                # read the world list into memory
                list = self._read_column_list(list_file, 2)
                if self.m_store_lists:
                    self.m_read_lists[group] = list
                return list
            # just return the previously read list
            return self.m_read_lists[group]

        else:
            if group not in self.m_read_lists:
                self.m_read_lists[group] = {}
            if type not in self.m_read_lists[group]:
                if type in ('for_models', 'for_tnorm'):
                    list = self._read_column_list(list_file, 3)
                elif type == 'for_scores':
                    list = self._read_column_list(list_file, 4)
                elif type in ('for_probes', 'for_znorm'):
                    list = self._read_column_list(list_file, 2)
                else:
                    raise ValueError("The given type must be one of %s, but not '%s'" % (
                    ('for_models', 'for_scores', 'for_probes', 'for_tnorm', 'for_znorm'), type))
                if self.m_store_lists:
                    self.m_read_lists[group][type] = list
                return list
            return self.m_read_lists[group][type]

    def read_models(self, list_file, group, type=None):
        """Generates a dictionary from model_ids to client_ids for the given list file, if not done yet, and returns it"""
        assert group in ('dev', 'eval', 'world', 'optional_world_1', 'optional_world_2')
        assert type in ('for_models', 'for_tnorm')
        if group not in self.m_model_dicts:
            self.m_model_dicts[group] = {}
        if type not in self.m_model_dicts[group]:
            dict = self._create_model_dictionary(self.read_list(list_file, group, type))
            if self.m_store_lists:
                self.m_model_dicts[group][type] = dict
            return dict
        return self.m_model_dicts[group][type]
