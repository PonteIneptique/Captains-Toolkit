#!/usr/bin/python
# -*- coding: utf-8 -*-

from .files import File


class Credential(object):
    """ Credential for a user """
    def __init__(self, name="admin", password=None):
        """ Represents credentials used to access Database

        :param name: The username
        :type name: str or unicode
        :param password: The password
        :type password: str or unicode or None
        """
        self.name = name
        self.password = password

    def from_dic(self, data):
        """ Set name and password variables using a dictionary

        :param data: A dictionary containing potentially a name and a password key
        :param type: dict
        :returns: Tuple corresponding to name/password
        :rtype: tuple
        """
        if "name" in data and isinstance(data["name"], (str, unicode)):
            self.name = data["name"]
        if "password" in data and isinstance(data["password"], (str, unicode)):
            self.password = data["password"]
            if len(data["password"]) == 0:
                self.password = None
        return (self.name, self.password)

    def __str__(self):
        return "{0}:{1}".format(self.name, self.password)


class DB(object):
    """Abstraction of a DB class"""
    def __init__(self, software, version, method, path, data_dir=None, target="./", user=None, port=8080):
        """ Initiate the object

        :param software: Name of the software
        :type software: unicode or str
        :param version: Version of the software
        :type version: unicode or str
        :param method: Source type, should be git or url or local
        :type method: unicode or str
        :param data_dir: Path to data directory for the database
        :type data_dir: unicode or str
        :param path: Path to which source-downloader needs to query
        :type path: unicode or str
        :param target: Path where file needs to be deployed
        :type target: unicode or str

        """
        self.port = port
        self.software = software
        self.version = self._version_tuple(version)
        self.method = method
        self.path = path
        if user:
            self.user = user
        self.file = self._feed_file_instance(method=method, path=path, target=target)
        self.set_directory()

        self.data_dir = self.directory + "/data"
        if data_dir is not None:
            self.data_dir = data_dir

    def _version_tuple(self, version):
        """ Return a tuple representing the version for further tests

        :param version: String representation of the version
        :type  version: unicode or str
        :returns: numeric representation using tuple
        :rtype: tuple

        """
        return tuple([int(version_part) for version_part in version.split(".") if version_part.isdigit()])

    def _feed_file_instance(self, method, path, target):
        """ Returns a File() object corresponding to Git, Local or URL resource

        :param method: Source type, should be git or url or local
        :type method: unicode or str
        :param path: Path to which source-downloader needs to query
        :type path: unicode or str
        :param target: Path where file needs to be deployed
        :type target: unicode or str
        :returns: numeric representation using tuple
        :rtype: cts.files.File

        """
        instance = File(source=path, target=target, method=method)
        return instance

    def retrieve(self):
        """ Get the file used for running the DB

        :returns: Boolean indicating if the file exists
        :rtype: boolean

        """
        return self.file.get()

    def dump(self, fn, cts=5, output="./output.zip"):
        """ Dump the database

        :param fn: Function to run commands
        :type fn: function
        :param cts: Version of CTS used
        :type cts: int
        :param output: Path of the backup to be saved
        :type output: str or unicode
        :returns: List of tuple (dumped files' path , collection name)
        :rtype: list(str|unicode,str|unicode)
        """
        raise NotImplemented("This function is not implemented in this class")

    def put(self, texts):
        """ Push XML file(s) into the XML database

        :param texts: Document representing a XML file with its metadata
        :type texts: cts.xml.texts.Texts or list(cts.xml.texts.Texts) or tuple(str or unicode, str or unicode)
        :rtype: boolean


        """
        raise NotImplemented("This function is not implemented in this class")

    def set_directory(self, directory=None):
        """ Sets the binary directory for the database

        :param directory: The directory of binaries for database
        :type directory: str or unicode
        :returns: Directory path
        :rtype: str or unicode
        """
        self.directory = directory
        if directory is None:
            self.directory = self.file.directory
        return self.directory

    def set_port(self, port=8080):
        """ Sets the running port for the database

        :param port: The port for the database
        :type port: int
        :returns: port
        :rtype: int
        """
        self.port = port
        return self.port

    def feedXQuery(self, path=None):
        """ Feed an XQuery collection

        :returns: List of ShellObjects
        :rtype: List(ShellObject)

        """
        raise NotImplemented("This function is not implemented in this class")
