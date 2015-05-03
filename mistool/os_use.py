#!/usr/bin/env python3

"""
Directory : mistool
Name      : os_use
Version   : 2015.05
Author    : Christophe BAL
Mail      : projetmbc@gmail.com

This module contains an enhanced version of the classes in ``pathlib`` to
manipulate easily files, directories and so on, and there are also functions
which give informations about the system.
"""

import os
import pathlib
import shutil
import platform
from subprocess import check_call
import re


# ------------------ #
# -- WALK AND SEE -- #
# ------------------ #

_ALL_QUERIES      = set(["visible", "dir", "file"])
_SHORT_QUERIES    = {x[0]: x for x in _ALL_QUERIES}
_FILE_DIR_QUERIES = _ALL_QUERIES - set(["visible"])

def build_meta_pattern(regpattern, regexit = True):
    """
This function is used by the method ``walk`` and ``clean`` of the class ``PPath``
and also by the class ``DirView`` so as to parse the regex like pattern they use.
    """
    i = regpattern.find("::")

    if i > -1:
        queries, pattern = regpattern[:i], regpattern[i+2:]
        queries = set(_SHORT_QUERIES.get(x, x) for x in queries.split("-"))

        if not queries <= _ALL_QUERIES:
            raise ValueError("illegal filter in the regpattern.")

    else:
        queries, pattern = _FILE_DIR_QUERIES, regpattern

# The regex
    if regexit:
        for old, new in {
            '*': ".*",
            '.': "\.",
        }.items():
            pattern = pattern.replace(old, new)

    return queries, pattern


# ------------------------------------- #
# -- SPECIAL FUNCTIONS FOR OUR CLASS -- #
# ------------------------------------- #

# << Warning ! >>
#
# Sublcassing ``pathlib.Path`` is not easy ! We have to dirty a little
# our hands. Hints are hidden in the source and especially in the source
# of ``pathlib.PurePath``.
#
# Sources:
#     * http://stackoverflow.com/a/29851079/4589608
#     * https://hg.python.org/cpython/file/151cab576cab/Lib/pathlib.py
#
# Extra methods added to ``PPath`` must be defined using function. We choose to
# use names which all start with ``_ppath_somename`` where ``somename`` will be
# the name in the class ``PPath``.


# --------------- #
# -- EXTENSION -- #
# --------------- #

@property
def _ppath_ext(cls):
    """
This attribut like method returns the extension of a path, that is the value of
the attribut ``suffix`` of ``pathlib.Path`` without the leading point.
    """
# An extension is a suffix without the leading point.
    if cls.suffix:
        return cls.suffix[1:]

    raise ValueError("no extension")


def _ppath_with_ext(cls, ext):
    """
This method changes the extension of a path to the one given in the variable
``ext``. It is similar to the method ``with_suffix`` of ``pathlib.Path`` but
without the leading point.
    """
    if ext:
        ext = "." + ext

    return cls.with_suffix(ext)


# ------------------------------- #
# -- STRING VERSIONS OF A PATH -- #
# ------------------------------- #

@property
def _ppath_normpath(cls):
    """
This attribut like method changes the leading shortcut path::``~`` corresponding
to the complete name of the default user's directory, and it also reduces the
path::``/../`` used to go higher in the tree structure of a directory.


For example, on a Mac the following code will print the normed path
path::``/Users/login/dir_1/file.txt`` where ``login`` is the real os login of
the user.

python::
    from mistool import os_use

    onepath = os_use.PPath("~/dir_1/dir_2/dir_3/../../file.txt")

    print(onepath.normpath)
    """
    return os.path.normpath(os.path.expanduser(str(cls)))


@property
def _ppath_shortpath(cls):
    """
This attribut like method returns the shorstest version of a path by using the
leading shortcut path::``~`` corresponding to the complete name of the default
user's directory, if it is possible, and by reducing all path::``/../`` used to
go higher in the tree structure of a directory.
    """
    path = os.path.normpath(os.path.expanduser(str(cls)))
    userpath = os.path.expanduser("~") + cls._flavour.sep

    if path.startswith(userpath):
        path = "~" + cls._flavour.sep + path[len(userpath):]

    return path


# --------------------------- #
# -- INFORMATIONS IN PATHS -- #
# --------------------------- #

def _ppath_depth_in(cls, path):
    """
This method returns the depth of the actual class path regarding to another path.


Suppose that we have the following paths where ``main`` is the path of the main
directory and ``sub`` the one of a sub directory or a file contained in the main
directory. Here are some examples.

    1) The method will return ``1`` in the following case.

    python::
        main = "/Users/projects/source_dev"
        sub  = "/Users/projects/source_dev/misTool/os_use.py"

    This means that the file path::``os_use.py`` is contained in one simple sub
    directory of the main directory.

    2) In the following case, the method will return ``2``.

    python::
        main = "/Users/projects/source_dev"
        sub  = "/Users/projects/source_dev/misTool/os/os_use.py"

    3) For the last example just after, the value returned will be ``0``.

    python::
        main = "/Users/projects/source_dev"
        sub  = "/Users/projects/source_dev/os_use.py"
    """
    return len(cls.relative_to(path).parts) - 1



@property
def _ppath_parent(cls):
    """
This attribut like method returns the path of the direct folder "containing" the
file or the directory corresponding to the path.
    """
    return cls.parents[0]


def _ppath___sub__(cls, path):
    """
This magic method allows to use ``onepath - anotherpath`` instead of the long
version ``onepath.relative_to(anotherpath)`` given by ``pathlib.Path``.
    """
    return cls.relative_to(path)


def _ppath_common_with(cls, paths):
    """
This method returns the path of the smaller common "folder" of the current path
and at least one paths.


info::
    The variable ``paths`` can be a single path, or a list or a tuple of paths.


For example, the following code will print path::``"/Users/projects``.

python::
    from mistool import os_use

    path   = os_use.PPath("/Users/projects/source/doc")
    path_1 = os_use.PPath("/Users/projects/README")
    path_2 = os_use.PPath("/Users/projects/source/misTool/os_use.py")

    print(path.common_with((path_1, path_2)))
    """
    if not isinstance(paths, (list, tuple)):
        paths = [paths]

    commonparts = list(cls.parts)

    for onepath in paths:
        i = 0

        for common, actual in zip(commonparts, onepath.parts):
            if common == actual:
                i += 1
            else:
                break

        commonparts = commonparts[:i]

        if not commonparts:
            break

    commonpath = pathlib.Path("")

    for part in commonparts:
        commonpath /= part

    return commonpath


def _ppath___and__(cls, paths):
    """
This magic method allows to use ``onepath & paths`` instead of the long version
``onepath.common_with(paths)``.
    """
    return cls.common_with(paths)


# ------------------ #
# -- WALK AND SEE -- #
# ------------------ #

def _ppath_walk(cls, regpattern):
    """
Besoin de préciser le langage
    *  --> n'mporte quel nom sans separtauer
    ** --> n'import quel caractère donc aaussi spéarateur
    .  --> tel que



This method walks inside a directory, if the path is one. It allows to use almost
all the power of regexes in a pattern with also some additional queries.


warning::
    The special caracters ``*`` and ``.`` for regex become "anything" and "just
    a single point" in a pattern so as to be near to the Unix-glob syntax.


Let's see some examples of patterns ``regpattern``.

    1) ``"*.(py|txt)"`` asks to keep only path ending with either path::``py`` or
    path::``txt``. This is the main reason of the add of a new method.

    2) ``"**"`` will macth anything.

    3) If you want to keep only Puython files, just use ``"file::**.py"``. We
    have used a filter at the begining of the pattern ``regpattern``. Here are
    all the queries.

        a) ``file::`` asks to keep only files. You can use the shortcut ``f``.

        b) ``dir::`` asks to keep only directories, or folders. You can use the
        shortcut ``d``.

        c) ``visible::`` asks to keep only visible files or directories which
        have name begining with ``.``. If a file is inside an invisible folder,
        it is also invisible ! You can use the shortcut ``v``.

        d) ``visible-file::`` and ``visible-dir::`` ask to respectively keep
        only visible files, or only visible directories.
    """
# Do we have an existing directory ?
    if not cls.is_dir():
        raise OSError("the path does not point to an existing directory.")

# Metadatas and the normal regex
    queries, pattern = build_meta_pattern(regpattern)

    keepdir     = "dir" in queries
    keepfile    = "file" in queries
    keepvisible = "visible" in queries

    regex_obj = re.compile(pattern)

# Let's walk
    for root, dirs, files in os.walk(str(cls)):

# Do the actual directory must be added ?
        addthisdir = False

        if keepdir \
        and root != str(cls) \
        and regex_obj.match(root):
            root_ppath = PPath(root)

            if not keepvisible \
            or not any(
                x.startswith('.')
                for x in root_ppath.relative_to(cls).parts
            ):
                addthisdir = True

# A new file ?
        if keepfile:
            for file in files:
                if keepvisible and file.startswith('.'):
                    continue

                file = os.path.join(root, file)

                if regex_obj.match(file):
                    yield PPath(file)

# A new directory ?
        if addthisdir:
            yield root_ppath


def _ppath_see(cls):
    """
This method shows one directory or one file in the OS, if it is possible.


info::
    The files are opened within their associated applications, if they have one.
    """
# Nothing to open...
    if not cls.is_file() and not cls.is_dir():
        raise OSError("the path does not point to one existing file.")

# We need the string normalized version of the path.
    path = cls.normpath

# Each OS has its own method.
    osname = system()

# Windows
    if osname == "windows":
        if isonefile:
            os.startfile(path)
        else:
            check_call(args = ['explorer', path])

# Mac
    elif osname == "mac":
        check_call(args = ['open', path])

# Linux
#
# Source :
#     * http://forum.ubuntu-fr.org/viewtopic.php?pid=3952590#p3952590
    elif osname == "linux":
        check_call(args = ['xdg-open', path])

# Unknown method...
    else:
        raise OSError(
            "the opening of the file on the OS "
            "<< {0} >> is not supported.".format(osname)
        )


# ------------ #
# -- CREATE -- #
# ------------ #

def _ppath_make_dir(cls):
    """
This method builds the directory with the given path ``path``. This argument
must be an instance of the class ``pathlib.Path`` or ``PPath``.

If one parent directory must be build, the function will do the job.
    """
    if not cls.is_dir():
        os.makedirs(str(cls))


def _ppath_make_txt_file(
    cls,
    text     = '',
    encoding = 'utf-8'
):
    """
This method builds the file with  the text like content ``text`` and the given
path ``path``. This last argument must be an instance of the class
``pathlib.Path`` or ``PPath``.

You can also indicate the encoding of the file with the optional argument
``encoding`` whose default value is ``"utf-8"``. The available encodings are the
same as the ones for the standard ¨python function ``open``.
    """
    cls.parent.make_dir()

    with cls.open(
        mode     = "w",
        encoding = encoding
    ) as f:
        f.write(text)


# ------------ #
# -- DELETE -- #
# ------------ #

def _ppath_destroy(cls):
    """
This method removes the directory or the file given by its path ``path``. This
argument must be an instance of the class ``pathlib.Path`` or ``PPath``.
    """
    if cls.is_dir():
        shutil.rmtree(str(cls))

    elif cls.is_file():
        os.remove(str(cls))


def _ppath_clean(cls, regpattern):
    """
This method cleans a directory regarding the value of ``regpattern`` which must
be an almost regex pattern. See the documentation of the method ``walk``.
    """
# We have to play with the queries and the pattern in ``regpattern``.
    queries, pattern = build_meta_pattern(regpattern, regexit = False)

    if "visible" in queries:
        prefix = "visible-"

    else:
        prefix = ""

# We must first remove the files. This is in case of folders to destroy.
    if "file" in queries:
        filepattern = "{0}file::{1}".format(prefix, pattern)

        for path in cls.walk(filepattern):
            path.destroy()


# We can destroy folders but we can use an iterator (because of sub directories).
    if "dir" in queries:
        dirpattern = "{0}dir::{1}".format(prefix, pattern)

        sortedpaths = sorted(list(p for p in cls.walk(dirpattern)))

        for path in sortedpaths:
            path.destroy()


# ----------------- #
# -- MOVE & COPY -- #
# ----------------- #

def _ppath_copy_to(cls, path):
    """
This method copies the actual file to the destination ``path``. This last path
must be an instance of the class ``pathlib.Path`` or ``PPath``.


info::
    The actual path is not changed.


warning::
    Copy of a directory is not yet supported.
    """
    if cls.is_file():
        if not path.parent.is_dir():
            makedir(path.parent)

        shutil.copy(str(cls), str(path))

    elif cls.is_dir():
        raise ValueError("copy of directories is not yet supported.")

    else:
        raise OSError("actual path is not a real one.")


def _ppath_move_to(cls, path):
    """
This method moves the actual file to the destination ``path``. This last path
must be an instance of the class ``pathlib.Path`` or ``PPath``.

If the source and the destination have the same parent directory, then the final result will just be a renaming of the file or the directory.


info::
    The actual path is not changed.


warning::
    Moving a directory is not yet supported.
    """
    if cls.is_file():
        cls.copy_to(path)

# Let's be cautious...
        if path.is_file():
            cls.destroy()

        else:
            raise OSError("moving the file has failed.")

    elif cls.is_dir():
        raise ValueError("moving directories is not yet supported.")

    else:
        raise OSError("actual path is not a real one.")


# ------------------------ #
# -- OUR ENHANCED CLASS -- #
# ------------------------ #

_SPECIAL_FUNCS = [
    (x[len("_ppath_"):], x)
    for x in dir()
    if x.startswith("_ppath_")
]

class PPath(pathlib.Path):
    """
    hhhh
    """
    def __new__(cls, *args):
        if cls is PPath:
            cls = pathlib.WindowsPath if os.name == 'nt' else pathlib.PosixPath

# We have to add our additional methods using a short dirty way.
        for specialname, specialfunc in _SPECIAL_FUNCS:
            setattr(cls, specialname, globals()[specialfunc])

        return cls._from_parts(args)


# ----------------------- #
# -- VIEWS OF A FOLDER -- #
# ----------------------- #

class DirView:
    """
-----------------
Small description
-----------------

This class displays the tree structure of one directory with the possibility to
keep only some relevant informations like in the following example. Note that in
a given directory, the files are displayed before the directories.

code::
    + mistool_old
        * __init__.py
        * latex_use.py
        * LICENCE.txt
        * os_use.py
        * README.md
        * ...
        + change_log
            + 2012
                * 07.pdf
                * 08.pdf
                * 09.pdf
        + debug
            * debug_latex_use.py
            * debug_os_use.py
            + debug_latex_use
                * latex_test.pdf
                * latex_test.tex
                * latex_test_builder.py
                * ...
        + to_use
            + latex
                * ...


In this output no invisible directory or file has been printed, and ellipsis
indicated visible files that do not match to our pattern. All of this has been
obtained with the following code.

python::
    from mistool import os_use

    DirView = os_use.DirView(
        ppath      = "/Users/projetmbc/python/mistool",
        regpattern = "visible::*.(py|txt|tex|pdf)",
        display    = "main short"
    )

    print(DirView.ascii)


-------------
The arguments
-------------

This class uses the following variables.

    1) ``ppath`` is a path defined using the class ``PPath``.

    2) ``regpattern`` is an optional string which is an almost regex pattern.
    See the documentation of the method ``walk`` of the class ``PPath``. By
    default, ``regpattern = "**"`` which indicates to look for anything.

    3) ``display`` is an optional string which can contains the following
    options separated by spaces. By default, ``format = "main short"``.

        a) ``long`` asks to display the whole paths of the
        files and directories found. You can use the shortcut ``l``.

        b) ``relative`` asks to display relative paths comparing to the main
        directory analysed. You can use the shortcut ``r``.

        c) ``short`` asks to only display names of directories found, and
        names, with its extensions, of the files found. You can use the
        shortcut ``s``.

        d) ``main`` asks to display the main directory which is analyzed. You
        can use the shortcut ``m``.

        e) ``found`` asks to only display directories and files which path
        matches the pattern ``regpattern``. You can use the shortcut ``f``.

        e) ``alpha`` asks to display directories and files in an alphabetic
        order instead of the files before the folders for a given depth. This
        second behavior is the default one. You can use the shortcut ``a``.
    """
    ASCII_DECOS = {
        'dir' : "+",
        'file': "*",
        'tab' : " "*4
    }

    _FORMATTERS = set(["alpha", "found", "main", "long", "relative", "short"])
    _PATH_FORMATTERS = set(["long", "relative", "short"])
    _SHORT_FORMATTERS = {x[0]: x for x in _FORMATTERS}

    def __init__(
        self,
        ppath,
        regpattern = "**",
        display    = "main short"
    ):
        self.ppath      = ppath
        self.regpattern = regpattern
        self.display    = display

        self._ellipsis = PPath('...')

        self.build()


    def build(self):
        """
This method builds first one flat list ``self.listview`` of dictionaries of the
following kind that will ease the making of the tree view. This list is sorted
in alphabetic order with a depth walk.

python::
    {
        'kind'   : "dir" or "file",
        'depth'  : the depth level regarding to the main directory,
        'relpath': the relative path of one directory or file found
    }


Then, if it is asked byt the user, a second list ``self.filefirst_listview`` is
build. It is a reordering such as for a given dpeth the file appears before the
directories.
        """
# Reset all things !
        self.listview = []
        self.options  = set()
        self.output   = {}

        self.queries, _ = build_meta_pattern(
            self.regpattern,
            regexit = False
        )

# What have to be displayed ?
        for opt in self.display.split(" "):
            opt = opt.strip()
            opt = self._SHORT_FORMATTERS.get(opt, opt)

            if opt not in self._FORMATTERS:
                raise ValueError("unknown option for displaying.")

            self.options.add(opt)

        if len(self._PATH_FORMATTERS & self.options) > 1:
            raise ValueError("ambiguous option for printing the paths.")

# We must add all the folders except if the option "found" has been used.
        if "found" not in self.options:
            if "visible" in self.queries:
                prefix = "visible-"

            else:
                prefix = ""

            self.listview = [
                {
                    'kind'   : "dir",
                    'depth'  : p.depth_in(self.ppath),
                    'relpath': p.relative_to(self.ppath)
                }
                for p in self.ppath.walk(prefix + "dir::**")
            ]

# Unsorted flat version of the tree view.
        for onepath in self.ppath.walk(self.regpattern):
            kind = "file" if onepath.is_file() else "dir"

            infos = {
                'kind'   : kind,
                'depth'  : onepath.depth_in(self.ppath),
                'relpath': onepath.relative_to(self.ppath)
            }

# We do not want to see twice a folder !
            if kind == "file" or infos not in self.listview:
                self.listview.append(infos)

# If the option "found" has been used, we must add folders of files found.
        if "found" in self.options:
            self._add_parentdir()

# We build the alphabetic sorted version. This works because ``PPath`` does
# better comparisons than the ones of ``pathlib``.
        self.listview.sort(key = lambda x: x['relpath'])

# If the option "found" has not been used, we must take care of folder with no
# winning files so as to display ellipsis ``...``.
        if "found" not in self.options:
            self._add_ellipsis()

# "Files first" sorting version of the flat version of the tree view.
        if "alpha" not in self.options:
            self._filefirst_sort()


    def _filefirst_sort(self):
        """
This method sorts the list view so as to first show the files and then the
directories contained in a folder.
        """
        maxdepth = 0
        depth    = 0

        while(depth <= maxdepth):
            firsts = []
            lasts  = []

            for infos in self.listview:
                if infos['depth'] < depth:
                    firsts += lasts
                    lasts = []
                    firsts.append(infos)

                elif infos['depth'] == depth:
                    if infos['kind'] == "file":
                        firsts.append(infos)

                    else:
                        lasts.append(infos)
                else:
                    if infos['depth'] > maxdepth:
                        maxdepth = infos['depth']

                    lasts.append(infos)

            self.listview = firsts + lasts

            depth += 1

    def _add_parentdir(self):
        """
When the option ``found`` is used, we only show files found but we also have to
add all their parent directories.
        """
        for x in self.listview:
            parts = x['relpath'].parts

            if len(parts) != 1:
                newdir = PPath("")
                depth  = -1

                for part in parts[:-1]:
                    newdir /= part
                    depth  += 1

                    infos = {
                        'kind'   : "dir",
                        'depth'  : depth,
                        'relpath': newdir
                    }

                    if infos not in self.listview:
                        self.listview.append(infos)

    def _add_ellipsis(self):
        """
When the option ``found`` is not used, we have to add ellipsis ``...`` so as to
materiealize unshown files.
        """
        indexes = []

        for i, infos in enumerate(self.listview):
            if infos['kind'] == "dir":
                for p in (self.ppath / infos['relpath']).iterdir():
                    if p.is_file() \
                    and (
                        "visible" not in self.queries
                        or not p.name.startswith('.')
                    ) \
                    and {
                        'kind'   : "file",
                        'depth'  : infos['depth'] + 1,
                        'relpath': p.relative_to(self.ppath)
                    } not in self.listview:
                        indexes.append((i + 1, infos['depth'] + 1))
                        break

        delay = 0

        for i, depth in indexes:
            self.listview.insert(
                i + delay,
                {
                    'kind'   : "file",
                    'depth'  : depth,
                    'relpath': self._ellipsis
                }
            )

            delay += 1


    @property
    def ascii(self):
        """
This attribut like method returns an ASCCI view of the tree structure.
        """
        if 'ascii' not in self.output:
            seemain = "main" in self.options
            text    = []

            if seemain:
                if "long" in self.options:
                    mainpath = self._pathprinted(PPath(""))

                else:
                    mainpath = self.ppath.name

                text = [
                    "{0} {1}".format(self.ASCII_DECOS["dir"], mainpath)
                ]

            for infos in self.listview:
                depth = infos["depth"]

# Does the main directory must be displayed ?
                if seemain:
                    depth += 1

                tab = self.ASCII_DECOS['tab']*depth

                decokind = self.ASCII_DECOS[infos["kind"]]

                pathtoshow = self._pathprinted(infos["relpath"])

                text.append(
                    "{0}{1} {2}".format(tab, decokind, pathtoshow)
                )

            self.output['ascii'] = '\n'.join(text)

        return self.output['ascii']


    def _pathprinted(self, path):
# The path are stored relatively by default !
        if path == self._ellipsis or  "relative" in self.options:
            return str(path)

# We have to rebuild the while path.
        if "long" in self.options:
            return str(self.ppath / path)

# "short" is the default option for printing the paths.
        return str(path.name)


# ------------------- #
# -- GENERAL INFOS -- #
# ------------------- #

def pathenv():
    """
This function simply returns the variable ``PATH`` that contains paths of some
executables known by your OS.
    """
    return os.getenv('PATH')

def system():
    """
The purpose of this function is to give the name, in lower case, of the OS used.
Possible names can be "windows", "mac", "linux" and also "java".
    """
    osname = platform.system()

    if not osname:
        raise SystemError("the operating sytem can not be found.")

    if osname == 'Darwin':
        return "mac"

    else:
        return osname.lower()
