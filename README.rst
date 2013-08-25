======================================
 Verification File Lists Database API
======================================

The Verification Filelist database API provides mechanisms to create
an API for a verifcation database and protocol, the user providing 
file lists.

You would normally not install this package unless you are maintaining it. What
you would do instead is to tie it in at the package you need to **use** it.
There are a few ways to achieve this:

1. You can add this package as a requirement at the ``setup.py`` for your own
   `satellite package
   <https://github.com/idiap/bob/wiki/Virtual-Work-Environments-with-Buildout>`_
   or to your Buildout ``.cfg`` file, if you prefer it that way. With this
   method, this package gets automatically downloaded and installed on your
   working environment, or

2. You can manually download and install this package using commands like
   ``easy_install`` or ``pip``.

The package is available in two different distribution formats:

1. You can download it from `PyPI <http://pypi.python.org/pypi>`_, or

2. You can download it in its source form from `its git repository
   <https://github.com/bioidiap/xbob.db.nuaa>`_. When you download the
   version at the git repository, you will need to run a command to recreate
   the backend SQLite file required for its operation. This means that the
   database raw files must be installed somewhere in this case. With option
   ``a`` you can run in `dummy` mode and only download the raw data files for
   the database once you are happy with your setup.

You can mix and match points 1/2 and a/b above based on your requirements. Here
are some examples:

Modify your setup.py and download from PyPI
===========================================

That is the easiest. Edit your ``setup.py`` in your satellite package and add
the following entry in the ``install_requires`` section (note: ``...`` means
`whatever extra stuff you may have in-between`, don't put that on your
script)::

    install_requires=[
      ...
      "xbob.db.verification.filelist",
    ],

Proceed normally with your ``boostrap/buildout`` steps and you should be all
set. That means you can now import the namespace ``xbob.db.verification.filelist`` into your scripts.

Modify your buildout.cfg and download from git
==============================================

You will need to add a dependence to `mr.developer
<http://pypi.python.org/pypi/mr.developer/>`_ to be able to install from our
git repositories. Your ``buildout.cfg`` file should contain the following
lines::

  [buildout]
  ...
  extensions = mr.developer
  auto-checkout = *
  eggs = bob
         ...
         xbob.db.verification.filelist

  [sources]
  xbob.db.verification.filelist = git https://github.com/bioidiap/xbob.db.verification.filelist.git
  ...
  
Creating file lists
===================

The initial step for using this package is to provide file lists specifying the world (train), development and evaluation set to be used by the biometric verification algorithm. The following files need to be created:

- **For training**:

1. world file, with default name ``train_world.lst``, and default subdirectory ``norm``. It is a 2-column file with format::
 
    filename client_id

2. two optional world files, with default names ``train_optional_world_1.lst`` and ``train_optional_world_2.lst``, and default subdirectory ``norm``. The format is the same as for the world file.

- **For enrollment**:

1. two model files for the development and evaluation set, with default name ``for_models.lst`` and default subdirectories ``dev`` and ``eval`` respectively. They are 3-column files with format::
  
    filename model_id client_id

- **For scoring**:

1. two probe files for the development and evaluation set, with default name ``for_probes.lst`` and default subdirectories ``dev`` and ``eval`` respectively. These files need to be provided only if the scoring is to be done exhaustively, meaning by creating a dense probe/model scoring matrix. They are 2-column files with format:: 
  
    filename client_id

2. two score files for the development and evaluation set, with default name ``for_scores.lst`` and default subdirectories ``dev`` and ``eval`` respectively.  These files need to be provided only if the scoring is to be done selectively, meaning by creating a sparse probe/model scoring matrix. They are 4-column files with format:: 

    filename model_id claimed_client_id client_id

3. two files for t-score normalization for the development and evaluation set, with default name ``for_tnorm.lst`` and default subdirectories ``dev`` and ``eval`` respectively. They are 3-column files with format::
  
    filename model_id client_id

4. two files for z-score normalization for the development and evaluation set, with default name ``for_znorm.lst`` and default subdirectories ``dev`` and ``eval`` respectively. They are 2-column files with format:: 

    filename client_id

Note that the verification algorithm will use either only the probe or only the score files, so only one of them is mandatory. In case both probe and score files are provided, the algorithm will use the parameter ``use_dense_probe_file_list`` when creating the object of the ``Database`` class.

