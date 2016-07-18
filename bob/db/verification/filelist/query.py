#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Laurent El Shafey <Laurent.El-Shafey@idiap.ch>
#
# Copyright (C) 2011-2013 Idiap Research Institute, Martigny, Switzerland
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


"""This module provides the Dataset interface allowing the user to query the
verification database based on file lists in the most obvious ways.
"""

import os
import six

from .models import Client, File, ListReader
from bob.db.base import annotations


class Database(object):
    """This class provides a user-friendly interface to databases that are given as file lists.

    Keyword parameters:

    base_dir : str
      The directory that contains the filelists defining the protocol(s). If you use the protocol
      attribute when querying the database, it will be appended to the base directory, such that
      several protocols are supported by the same class instance of bob.db.verification.filelist.

    original_directory : str or ``None``
      The directory, where the original data can be found

    original_extension : str or [str] or ``None``
      The filename extension of the original data, or multiple extensions

    annotation_directory : str or ``None``
      The directory, where additional annotation files can be found

    annotation_extension : str or ``None``
      The filename extension of the annoation files

    annotation_type : str or ``None``
      The type of annotation that can be read.
      Currently, options are 'eyecenter', 'named', 'idiap'.
      See :py:func:`bob.db.base.annotations.read_annotation_file` for details.

    dev_subdir : str or ``None``
      Specify a custom subdirectory for the filelists of the development set (default is 'dev')

    eval_subdir : str or ``None``
      Specify a custom subdirectory for the filelists of the development set (default is 'eval')

    world_filename : str or ``None``
      Specify a custom filename for the training filelist (default is 'norm/train_world.lst')

    optional_world_1_filename : str or ``None``
      Specify a custom filename for the (first optional) training filelist
      (default is 'norm/train_optional_world_1.lst')

    optional_world_2_filename : str or ``None``
      Specify a custom filename for the (second optional) training filelist
      (default is 'norm/train_optional_world_2.lst')

    models_filename : str or ``None``
      Specify a custom filename for the model filelists (default is 'for_models.lst')

    probes_filename : str or ``None``
      Specify a custom filename for the probes filelists (default is 'for_probes.lst')

    scores_filename : str or ``None``
      Specify a custom filename for the scores filelists (default is 'for_scores.lst')

    tnorm_filename : str or ``None``
      Specify a custom filename for the T-norm scores filelists (default is 'for_tnorm.lst')

    znorm_filename : str or ``None``
      Specify a custom filename for the Z-norm scores filelists (default is 'for_znorm.lst')

    use_dense_probe_file_list : bool or None
      Specify which list to use among 'probes_filename' (dense) or 'scores_filename'.
      If ``None`` it is tried to be estimated based on the given parameters.

    keep_read_lists_in_memory : bool
      If set to true, the lists are read only once and stored in memory
    """

    def __init__(
            self,
            base_dir,

            original_directory=None,
            original_extension=None,
            annotation_directory=None,
            annotation_extension='.pos',
            annotation_type='eyecenter',

            dev_subdir=None,
            eval_subdir=None,

            world_filename=None,
            optional_world_1_filename=None,
            optional_world_2_filename=None,
            models_filename=None,

            # For probing, use ONE of the two score file lists:
            probes_filename=None,  # File containing the probe files -> dense model/probe score matrix
            scores_filename=None,  # File containing list of model and probe files -> sparse model/probe score matrix
            # For ZT-Norm:
            tnorm_filename=None,
            znorm_filename=None,
            use_dense_probe_file_list=None,
            # if both probe_filename and scores_filename is given, what kind of list should be used?
            keep_read_lists_in_memory=True
            # if set to True (the RECOMMENDED default) lists are read only once and stored in memory.
    ):
        """Initializes the database with the file lists from the given base directory,
        and the given sub-directories and file names (which default to useful values if not given)."""

        self.original_directory = original_directory
        self.original_extension = original_extension

        self.m_annotation_directory = annotation_directory
        self.m_annotation_extension = annotation_extension
        self.m_annotation_type = annotation_type

        self.m_base_dir = os.path.abspath(base_dir)
        if not os.path.isdir(self.m_base_dir):
            raise RuntimeError('Invalid directory specified %s.' % (self.m_base_dir))

        # sub-directories for dev and eval set:
        self.m_dev_subdir = dev_subdir if dev_subdir is not None else 'dev'
        self.m_eval_subdir = eval_subdir if eval_subdir is not None else 'eval'

        # training list:     format:   filename client_id
        self.m_world_filename = world_filename if world_filename is not None else os.path.join('norm',
                                                                                               'train_world.lst')
        # optional training list 1:     format:   filename client_id
        self.m_optional_world_1_filename = optional_world_1_filename if optional_world_1_filename is not None else os.path.join(
            'norm', 'train_optional_world_1.lst')
        # optional training list 2:     format:   filename client_id
        self.m_optional_world_2_filename = optional_world_2_filename if optional_world_2_filename is not None else os.path.join(
            'norm', 'train_optional_world_2.lst')
        # model list:        format:   filename model_id client_id
        self.m_models_filename = models_filename if models_filename is not None else 'for_models.lst'
        # scores list:       format:   filename model_id claimed_client_id client_id
        self.m_scores_filename = scores_filename if scores_filename is not None else 'for_scores.lst'
        # probe list:        format:   filename client_id
        self.m_probes_filename = probes_filename if probes_filename is not None else 'for_probes.lst'
        # T-Norm models      format:   filename model_id client_id
        self.m_tnorm_filename = tnorm_filename if tnorm_filename is not None else 'for_tnorm.lst'
        # Z-Norm files       format:   filename client_id
        self.m_znorm_filename = znorm_filename if znorm_filename is not None else 'for_znorm.lst'

        # decide, which scoring type we have:
        if probes_filename is not None and scores_filename is None:
            self.m_use_dense_probes = True
        elif probes_filename is None and scores_filename is not None:
            self.m_use_dense_probes = False
        elif use_dense_probe_file_list is not None:
            self.m_use_dense_probes = use_dense_probe_file_list
        # Then direct path to a given protocol
        elif os.path.isdir(os.path.join(self.get_base_directory(), self.m_dev_subdir)) or os.path.isfile(
                os.path.join(self.get_base_directory(), self.m_world_filename)):
            if os.path.exists(self.get_list_file('dev', 'for_probes')) and not os.path.exists(
                    self.get_list_file('dev', 'for_scores')):
                self.m_use_dense_probes = True
            elif not os.path.exists(self.get_list_file('dev', 'for_probes')) and os.path.exists(
                    self.get_list_file('dev', 'for_scores')):
                self.m_use_dense_probes = False
            else:
                raise ValueError("Unable to determine, which way of probing should be used. Please specify.")
        # Then path to a directory that contains several subdirectories (one for each protocol)
        else:
            # Look at subdirectories for each protocol
            protocols = [p for p in os.listdir(self.get_base_directory()) if
                         os.path.isdir(os.path.join(self.get_base_directory(), p))]
            if len(protocols) == 0:
                raise ValueError(
                    "Unable to determine, which way of probing should be used (no protocol directories found). Please specify.")
            list_use_dense_probes = []
            for p in protocols:
                if os.path.exists(self.get_list_file('dev', 'for_probes', p)) and not os.path.exists(
                        self.get_list_file('dev', 'for_scores', p)):
                    use_dense_probes = True
                elif not os.path.exists(self.get_list_file('dev', 'for_probes', p)) and os.path.exists(
                        self.get_list_file('dev', 'for_scores', p)):
                    use_dense_probes = False
                else:
                    raise ValueError(
                        "Unable to determine, which way of probing should be used, looking at the protocol (directory) '%s'. Please specify." % p)
                list_use_dense_probes.append(use_dense_probes)
            if len(set(list_use_dense_probes)) == 1:
                self.m_use_dense_probes = list_use_dense_probes[0]
            else:
                raise ValueError(
                    "Unable to determine, which way of probing should be used, since this is not consistent accross protocols. Please specify.")

        self.m_list_reader = ListReader(keep_read_lists_in_memory)

    def groups(self, protocol=None):
        """This function returns the list of groups for this database.

        protocol : str or ``None``
          The protocol for which the groups should be retrieved.

        Returns: a list of groups
        """

        groups = []
        if protocol is not None:
            if os.path.isdir(os.path.join(self.get_base_directory(), protocol, self.m_dev_subdir)):
                groups.append('dev')
            if os.path.isdir(os.path.join(self.get_base_directory(), protocol, self.m_eval_subdir)):
                groups.append('eval')
            if os.path.isfile(os.path.join(self.get_base_directory(), protocol, self.m_world_filename)):
                groups.append('world')
            if os.path.isfile(os.path.join(self.get_base_directory(), protocol, self.m_optional_world_1_filename)):
                groups.append('optional_world_1')
            if os.path.isfile(os.path.join(self.get_base_directory(), protocol, self.m_optional_world_2_filename)):
                groups.append('optional_world_2')
        else:
            if os.path.isdir(os.path.join(self.get_base_directory(), self.m_dev_subdir)):
                groups.append('dev')
            if os.path.isdir(os.path.join(self.get_base_directory(), self.m_eval_subdir)):
                groups.append('eval')
            if os.path.isfile(os.path.join(self.get_base_directory(), self.m_world_filename)):
                groups.append('world')
            if os.path.isfile(os.path.join(self.get_base_directory(), self.m_optional_world_1_filename)):
                groups.append('optional_world_1')
            if os.path.isfile(os.path.join(self.get_base_directory(), self.m_optional_world_2_filename)):
                groups.append('optional_world_2')
        return groups

    def implements_zt(self, protocol=None, groups=None):
        """Checks if the file lists for the ZT score normalization are available.

        Keyword Parameters:

        protocol : str or ``None``
          The protocol for which the groups should be retrieved.

        groups : str or [str] or ``None``
          The groups for which the ZT score normalization file lists should be checked ("dev", "eval").

        Returns:
          ``True`` if the all file lists for ZT score normalization exist, otherwise ``False``.
        """
        groups = self.check_parameters_for_validity(groups, "group", ('dev', 'eval'))

        for group in groups:
            for t in ['for_tnorm', 'for_znorm']:
                if not os.path.exists(self.get_list_file(group, t, protocol)):
                    return False
        # all files exist
        return True

    def get_base_directory(self):
        """Returns the base directory where the filelists defining the database
           are located."""
        return self.m_base_dir

    def set_base_directory(self, base_dir):
        """Resets the base directory where the filelists defining the database
          are located."""
        self.m_base_dir = base_dir
        if not os.path.isdir(self.base_dir):
            raise RuntimeError('Invalid directory specified %s.' % (self.base_dir))

    def get_list_file(self, group, type=None, protocol=None):
        if protocol:
            base_directory = os.path.join(self.get_base_directory(), protocol)
        else:
            base_directory = self.get_base_directory()
        if group == 'world':
            return os.path.join(base_directory, self.m_world_filename)
        elif group == 'optional_world_1':
            return os.path.join(base_directory, self.m_optional_world_1_filename)
        elif group == 'optional_world_2':
            return os.path.join(base_directory, self.m_optional_world_2_filename)
        else:
            group_dir = self.m_dev_subdir if group == 'dev' else self.m_eval_subdir
            list_name = {'for_models': self.m_models_filename,
                         'for_probes': self.m_probes_filename,
                         'for_scores': self.m_scores_filename,
                         'for_tnorm': self.m_tnorm_filename,
                         'for_znorm': self.m_znorm_filename
                         }[type]
            return os.path.join(base_directory, group_dir, list_name)

    def get_client_id_from_model_id(self, model_id, groups=None, protocol=None):
        """Returns the client id that is connected to the given model id.

        Keyword parameters:

        model_id : str or ``None``
          The model id for which the client id should be returned.

        groups : str or [str] or ``None``
          (optional) the groups, the client belongs to.
          Might be one or more of ('dev', 'eval', 'world', 'optional_world_1', 'optional_world_2').
          If groups are given, only these groups are considered.

        protocol : str or ``None``
          The protocol to consider

        Returns: The client id for the given model id, if found.
        """
        groups = self.check_parameters_for_validity(groups, "group",
                                                    ('dev', 'eval', 'world', 'optional_world_1', 'optional_world_2'),
                                                    default_parameters=('dev', 'eval', 'world'))

        for group in groups:
            model_dict = self.m_list_reader.read_models(self.get_list_file(group, 'for_models', protocol), group,
                                                        'for_models')
            if model_id in model_dict:
                return model_dict[model_id]

        raise ValueError("The given model id '%s' cannot be found in one of the groups '%s'" % (model_id, groups))

    def get_client_id_from_tmodel_id(self, model_id, groups=None, protocol=None):
        """Returns the client id that is connected to the given T-Norm model id.

        Keyword parameters:

        model_id : str or ``None``
          The model id for which the client id should be returned.

        groups : str or [str] or ``None``
          (optional) the groups, the client belongs to.
          Might be one or more of ('dev', 'eval').
          If groups are given, only these groups are considered.

        protocol : str or ``None``
          The protocol to consider

        Returns: The client id for the given model id of a T-Norm model, if found.
        """
        groups = self.check_parameters_for_validity(groups, "group", ('dev', 'eval'))

        for group in groups:
            model_dict = self.m_list_reader.read_models(self.get_list_file(group, 'for_tnorm', protocol), group,
                                                        'for_tnorm')
            if model_id in model_dict:
                return model_dict[model_id]

        raise ValueError(
            "The given T-norm model id '%s' cannot be found in one of the groups '%s'" % (model_id, groups))

    def clients(self, protocol=None, groups=None):
        """Returns a list of :py:class:`Client` objects for the specific query by the user.

        Keyword Parameters:

        protocol : str or ``None``
          The protocol to consider

        groups : str or [str] or ``None``
          The groups to which the clients belong ("dev", "eval", "world", "optional_world_1", "optional_world_2").

        Returns: A list containing all the :py:class:`Client` objects which have the given properties.
        """

        client_ids = self.client_ids(protocol, groups)
        return [Client(id) for id in client_ids]

    def tclients(self, protocol=None, groups=None):
        """Returns a list of T-Norm :py:class:`Client` objects for the specific query by the user.

        Keyword Parameters:

        protocol : str or ``None``
          The protocol to consider

        groups : str or [str] or ``None``
          The groups to which the clients belong ("dev", "eval").

        Returns: A list containing all the T-Norm :py:class:`Client` objects which have the given properties.
        """
        tclient_ids = self.tclient_ids(protocol, groups)
        return [Client(id) for id in tclient_ids]

    def zclients(self, protocol=None, groups=None):
        """Returns a list of Z-Norm Client objects for the specific query by the user.

        Keyword Parameters:

        protocol : str or ``None``
          The protocol to consider

        groups : str or [str] or ``None``
          The groups to which the models belong ("dev", "eval").

        Returns: A list containing all the Z-Norm Client objects which have the given properties.
        """
        zclient_ids = self.zclient_ids(protocol, groups)
        return [Client(id) for id in zclient_ids]

    def __client_id_list__(self, groups, type, protocol=None):
        ids = set()
        # read all lists for all groups and extract the model ids
        for group in groups:
            files = self.m_list_reader.read_list(self.get_list_file(group, type, protocol), group, type)
            for file in files:
                ids.add(file.client_id)
        return ids

    def client_ids(self, protocol=None, groups=None):
        """Returns a list of client ids for the specific query by the user.

        Keyword Parameters:

        protocol : str or ``None``
          The protocol to consider

        groups : str or [str] or ``None``
          The groups to which the clients belong ("dev", "eval", "world", "optional_world_1", "optional_world_2").

        Returns: A list containing all the client ids which have the given properties.
        """

        groups = self.check_parameters_for_validity(groups, "group",
                                                    ('dev', 'eval', 'world', 'optional_world_1', 'optional_world_2'),
                                                    default_parameters=('dev', 'eval', 'world'))

        return self.__client_id_list__(groups, 'for_models', protocol)

    def tclient_ids(self, protocol=None, groups=None):
        """Returns a list of T-Norm client ids for the specific query by the user.

        Keyword Parameters:

        protocol : str or ``None``
          The protocol to consider

        groups : str or [str] or ``None``
          The groups to which the clients belong ("dev", "eval").

        Returns: A list containing all the T-Norm client ids which have the given properties.
        """

        groups = self.check_parameters_for_validity(groups, "group", ('dev', 'eval'))

        return self.__client_id_list__(groups, 'for_tnorm', protocol)

    def zclient_ids(self, protocol=None, groups=None):
        """Returns a list of Z-Norm client ids for the specific query by the user.

        Keyword Parameters:

        protocol : str or ``None``
          The protocol to consider

        groups : str or [str] or ``None``
          The groups to which the clients belong ("dev", "eval").

        Returns: A list containing all the Z-Norm client ids which have the given properties.
        """

        groups = self.check_parameters_for_validity(groups, "group", ('dev', 'eval'))

        return self.__client_id_list__(groups, 'for_znorm', protocol)

    def __model_id_list__(self, groups, type, protocol=None):
        ids = set()
        # read all lists for all groups and extract the model ids
        for group in groups:
            dict = self.m_list_reader.read_models(self.get_list_file(group, type, protocol), group, type)
            ids.update(dict.keys())
        return list(ids)

    def model_ids(self, protocol=None, groups=None):
        """Returns a list of model ids for the specific query by the user.

        Keyword Parameters:

        protocol : str or ``None``
          The protocol to consider

        groups : str or [str] or ``None``
          The groups to which the models belong ("dev", "eval", "world", "optional_world_1", "optional_world_2").

        Returns: A list containing all the model ids which have the given properties.
        """

        groups = self.check_parameters_for_validity(groups, "group",
                                                    ('dev', 'eval', 'world', 'optional_world_1', 'optional_world_2'),
                                                    default_parameters=('dev', 'eval', 'world'))

        return self.__model_id_list__(groups, 'for_models', protocol)

    def tmodel_ids(self, protocol=None, groups=None):
        """Returns a list of T-Norm model ids for the specific query by the user.

        Keyword Parameters:

        protocol : str or ``None``
          The protocol to consider

        groups : str or [str] or ``None``
          The groups to which the models belong ("dev", "eval").

        Returns: A list containing all the T-Norm model ids belonging to the given group.
        """

        groups = self.check_parameters_for_validity(groups, "group", ('dev', 'eval'))

        return self.__model_id_list__(groups, 'for_tnorm', protocol)

    def objects(self, protocol=None, purposes=None, model_ids=None, groups=None, classes=None):
        """Returns a set of :py:class:`File` objects for the specific query by the user.

        Keyword Parameters:

        protocol : str or ``None``
          The protocol to consider

        purposes : str or [str] or ``None``
          The purposes required to be retrieved ("enroll", "probe") or a tuple
          with several of them. If 'None' is given (this is the default), it is
          considered the same as a tuple with all possible values. This field is
          ignored for the data from the "world", "optional_world_1", "optional_world_2" groups.

        model_ids : str or [str] or ``None``
          Only retrieves the files for the provided list of model ids (claimed
          client id). If 'None' is given (this is the default), no filter over
          the model_ids is performed.

        groups : str or [str] or ``None``
          One of the groups ("dev", "eval", "world", "optional_world_1", "optional_world_2") or a tuple with several of them.
          If 'None' is given (this is the default), it is considered the same as a
          tuple with all possible values.

        classes : str or [str] or ``None``
          The classes (types of accesses) to be retrieved ('client', 'impostor')
          or a tuple with several of them. If 'None' is given (this is the
          default), it is considered the same as a tuple with all possible values.
          Note: classes are not allowed to be specified when the 'probes_filename' is used.

        Returns: A list of :py:class:`File` objects considering all the filtering criteria.
        """

        if self.m_use_dense_probes and classes is not None:
            raise ValueError("To be able to use the 'classes' keyword, please use the 'for_scores.lst' list file.")

        purposes = self.check_parameters_for_validity(purposes, "purpose", ('enroll', 'probe'))
        groups = self.check_parameters_for_validity(groups, "group",
                                                    ('dev', 'eval', 'world', 'optional_world_1', 'optional_world_2'),
                                                    default_parameters=('dev', 'eval', 'world'))
        classes = self.check_parameters_for_validity(classes, "class", ('client', 'impostor'))

        if isinstance(model_ids, six.string_types): model_ids = (model_ids,)

        # first, collect all the lists that we want to process
        lists = []
        probe_lists = []
        if 'world' in groups:
            lists.append(self.m_list_reader.read_list(self.get_list_file('world', protocol=protocol), 'world'))
        if 'optional_world_1' in groups:
            lists.append(self.m_list_reader.read_list(self.get_list_file('optional_world_1', protocol=protocol),
                                                      'optional_world_1'))
        if 'optional_world_2' in groups:
            lists.append(self.m_list_reader.read_list(self.get_list_file('optional_world_2', protocol=protocol),
                                                      'optional_world_2'))

        for group in ('dev', 'eval'):
            if group in groups:
                if 'enroll' in purposes:
                    lists.append(
                        self.m_list_reader.read_list(self.get_list_file(group, 'for_models', protocol=protocol), group,
                                                     'for_models'))
                if 'probe' in purposes:
                    if self.m_use_dense_probes:
                        probe_lists.append(
                            self.m_list_reader.read_list(self.get_list_file(group, 'for_probes', protocol=protocol),
                                                         group, 'for_probes'))
                    else:
                        probe_lists.append(
                            self.m_list_reader.read_list(self.get_list_file(group, 'for_scores', protocol=protocol),
                                                         group, 'for_scores'))

        # now, go through the lists and filter the elements

        # remember the file ids that are already in the list
        file_ids = set()
        retval = []

        # non-probe files; just filter by model id
        for list in lists:
            for file in list:
                # check if we already have this file
                if file.id not in file_ids:
                    if model_ids is None or file._model_id in model_ids:
                        file_ids.add(file.id)
                        retval.append(file)

        # probe files; filter by model id and by class
        for list in probe_lists:
            if self.m_use_dense_probes:
                # dense probing is used; do not filter over the model ids and not over the classes
                # -> just add all probe files
                for file in list:
                    if file.id not in file_ids:
                        file_ids.add(file.id)
                        retval.append(file)

            else:
                # sparse probing is used; filter over model ids and over the classes
                for file in list:
                    # filter by model id
                    if model_ids is None or file._model_id in model_ids:
                        # filter by class
                        if ('client' in classes and file.client_id == file.claimed_id) or \
                                ('impostor' in classes and file.client_id != file.claimed_id):
                            # check if we already have this file
                            if file.id not in file_ids:
                                file_ids.add(file.id)
                                retval.append(file)

        return retval

    def tobjects(self, protocol=None, model_ids=None, groups=None):
        """Returns a list of :py:class:`File` objects for enrolling T-norm models for score normalization.

        Keyword Parameters:

        protocol : str or ``None``
          The protocol to consider

        model_ids : str or [str] or ``None``
          Only retrieves the files for the provided list of model ids (claimed
          client id). If 'None' is given (this is the default), no filter over
          the model_ids is performed.

        groups : str or [str] or ``None``
          The groups to which the models belong ("dev", "eval").

        Returns: A list of :py:class:`File` objects considering all the filtering criteria.
        """

        groups = self.check_parameters_for_validity(groups, "group", ('dev', 'eval'))

        if (isinstance(model_ids, six.string_types)):
            model_ids = (model_ids,)

        # iterate over the lists and extract the files
        # we assume that there is no duplicate file here...
        retval = []
        for group in groups:
            for file in self.m_list_reader.read_list(self.get_list_file(group, 'for_tnorm', protocol), group,
                                                     'for_tnorm'):
                if model_ids is None or file._model_id in model_ids:
                    retval.append(file)

        return retval

    def zobjects(self, protocol=None, groups=None):
        """Returns a list of :py:class:`File` objects to perform Z-norm score normalization.

        Keyword Parameters:

        protocol : str or ``None``
          The protocol to consider

        groups : str or [str] or ``None``
          The groups to which the clients belong ("dev", "eval").

        Returns: A list of File objects considering all the filtering criteria.
        """

        groups = self.check_parameters_for_validity(groups, "group", ('dev', 'eval'))

        # iterate over the lists and extract the files
        # we assume that there is no duplicate file here...
        retval = []
        for group in groups:
            retval.extend([file for file in
                           self.m_list_reader.read_list(self.get_list_file(group, 'for_znorm', protocol), group,
                                                        'for_znorm')])

        return retval

    def annotations(self, file):
        """Reads the annotations for the given file id from file and returns them in a dictionary.

        If you don't have a copy of the annotation files, you can download them under http://www.idiap.ch/resource/biometric.

        Keyword parameters:

        file : :py:class:`bob.db.verification.filelist.File`
          The :py:class:`File` object for which the annotations should be read.

        Return value
          The annotations as a dictionary: {'reye':(re_y,re_x), 'leye':(le_y,le_x)}
        """
        if self.m_annotation_directory is None:
            return None

        # since the file id is equal to the file name, we can simply use it
        annotation_file = os.path.join(self.m_annotation_directory, file.id + self.m_annotation_extension)

        # return the annotations as read from file
        return annotations.read_annotation_file(annotation_file, self.m_annotation_type)

    def original_file_name(self, file, check_existence=True):
        """Returns the original file name of the given file.

        This interface supports several original extensions, so that file lists can contain images of different data types.

        When multiple original extensions are specified, this function will check the existence of any of these file names, and return the first one that actually exists.
        In this case, the ``check_existence`` flag is ignored.

        **Keyword parameters**

        file : :py:class:`bob.db.verification.filelist.File`
          The py:class:`File` object for which the file name should be returned.

        check_existence : bool
          Should the existence of the original file be checked?
          (Ignored when multiple original extensions were specified in the contructor.)

        **Returns**
        str : The full path of the original data file.
        """

        if isinstance(self.original_extension, str):
            # extract file name
            file_name = file.make_path(self.original_directory, self.original_extension)
            if check_existence and os.path.exists(file_name):
                return file_name


        # check all registered extensions
        for extension in self.original_extension:
            file_name = file.make_path(self.original_directory, extension)
            if check_existence and os.path.exists(file_name):
                return file_name

        # None of the extensions matched
        raise IOError("File '%s' does not exist with any of the extensions '%s'" % (
        file.make_path(self.original_directory, None), self.original_extension))

    def check_parameters_for_validity(self, parameters, parameter_description, valid_parameters, default_parameters = None):
        """Checks the given parameters for validity, i.e., if they are contained in the set of valid parameters.
        It also assures that the parameters form a tuple or a list.
        If parameters is 'None' or empty, the default_parameters will be returned (if default_parameters is omitted, all valid_parameters are returned).
        This function will return a tuple or list of parameters, or raise a ValueError.

        This method was imported from the former `bob.db.verification.utils`

        Keyword parameters:
        parameters : str, [str] or None
          The parameters to be checked.
          Might be a string, a list/tuple of strings, or None.
        parameter_description : str
          A short description of the parameter.
          This will be used to raise an exception in case the parameter is not valid.
        valid_parameters : [str]
          A list/tuple of valid values for the parameters.
        default_parameters : [str] or None
          The list/tuple of default parameters that will be returned in case parameters is None or empty.
          If omitted, all valid_parameters are used.
        """
        if parameters is None:
          # parameters are not specified, i.e., 'None' or empty lists
          parameters = default_parameters if default_parameters is not None else valid_parameters

        if not isinstance(parameters, (list, tuple, set)):
          # parameter is just a single element, not a tuple or list -> transform it into a tuple
          parameters = (parameters,)

        # perform the checks
        for parameter in parameters:
          if parameter not in valid_parameters:
            raise ValueError("Invalid %s '%s'. Valid values are %s, or lists/tuples of those" % (parameter_description, parameter, valid_parameters))

        # check passed, now return the list/tuple of parameters
        return parameters
