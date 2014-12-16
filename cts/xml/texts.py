#!/usr/bin/python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ElementTree
from codecs import *
from ..shell import Error, Warning
import os
import re

shortcut_namespace = re.compile("([a-zA-Z0-9]+\:)")


def replace_all(haystack, needles):
    """ Replace all element in a the keys of needles dict by their value

    :param haystack: The text to be search and modified
    :type haystack: str or unicode
    :param needles: The dictionary where keys are search values, and values are replace values
    :type needles: dict(str->str)
    :returns: The modified haystack
    :rtype: str or unicode
    """
    for i in needles:
        haystack = haystack.replace(i, needles[i])
    return haystack


class Citation(object):
    """ Represents a <citation /> tag """
    def __init__(self, xml, namespaces={}, strict=False):
        """ Initiate the object

        :param xml: XML markup or object, starting at the online tag
        :type xml: str or unicode or ElementTree.Element
        :param namespaces: a dictionary where key are shortcut for namespaces and value their full value
        :type namespaces: dict(str->str)
        :param strict: Indicate wether we should raise Exceptions on CTS compliancy failure
        :type strict: boolean
        """

        if isinstance(xml, ElementTree.Element):
            self.xml = xml
        else:
            self.xml = ElementTree.parse(xml).getroot()

        """label="Chapter" xpath="/tei:div[@n='?']" scope="/tei:TEI/tei:text/tei:body"""

        self.label = self.xml.get("label")
        self.xpath = self.xml.get("xpath")
        self.scope = self.xml.get("scope")

        self.namespaces = namespaces
        self.strict = strict
        self.children = self._retrieveChildren()

    def _retrieveChildren(self):
        """ Returns a Citation object if children are found in xml

        :returns: A citation object
        :rtype: Citation
        """
        children = self.xml.find("{http://chs.harvard.edu/xmlns/cts3/ti}citation")
        if children is not None:
            return Citation(
                xml=children,
                namespaces=self.namespaces,
                strict=self.strict
            )
        return None

    def full_xpath(self, removeRoot=False, string=None):
        """ Returns the xpath corresponding to this citation

        :param removeRoot: Indicates wether we should remove the root from the xquery
        :type removeRoot: boolean
        :param string: A string to overrided default self.scope + self.xpath
        :type string: str or unicode
        :returns: XPath String
        :rtype: str or unicode
        """
        if string is not None:
            xpath = string
        else:
            xpath = self.scope + self.xpath
        xpath = xpath.replace("@n='?'", "@n")

        if removeRoot is True:
            xpath = "/".join(["."] + xpath.split("/")[2:])
        xpath = replace_all(xpath, self.namespaces)

        return xpath

    def _testNamespace(self, name, string, original_string, level=1, failure_condition="equal"):
        """ Test string and return an error for attributes called name
        """
        match = len(shortcut_namespace.findall(string))
        if failure_condition == "equal" and match == 0:
            return [Error("{0}'s attribute for Citation Level {2} has no namespaces shortcuts like 'tei:' ({1})".format(name, original_string, level))]
        elif failure_condition == "greater" and match > 0:
            return [Error("{0}'s attribute for Citation Level {2} has namespaces shortcuts with no bindings ({1})".format(name, original_string, level))]
        return []

    def testNamespace(self, level=1):
        """ Test scope as a string and see if there are issues

        :returns: List of Errors
        :rtype: list(Error)
        """
        errors = []

        errors = errors + self._testNamespace("scope", self.scope, self.scope, level=level)
        errors = errors + self._testNamespace("scope", self.full_xpath(string=self.scope), self.scope, level=level, failure_condition="greater")
        errors = errors + self._testNamespace("xpath", self.xpath, self.xpath, level=level)
        errors = errors + self._testNamespace("xpath", self.full_xpath(string=self.xpath), self.xpath, level=level, failure_condition="greater")
        return errors

    def test(self, target, level=1):
        """ Test the citation attributes against an open file

        :param target: path to the file to be opened
        :type target: str or unicode
        :returns: Indicator of success and list of warnings
        :rtype: tuple(list(boolean), list(string))
        """
        status = []
        warnings = []
        xml = None

        if target:
            try:
                xml = ElementTree.parse(target)
            except:
                if self.strict is False:
                    status.append(False)
                    warnings.append(Error("Impossible to parse given element"))
                    return status, warnings
                else:
                    raise ValueError("The target parameter value is neither a file, a str nor a unicode")

        if xml:
            xpath = self.full_xpath(removeRoot=True)
            try:
                found = xml.findall(xpath)
            except:
                found = []
                warnings.append(Error("Unable to run xpath {0}".format(xpath)))

            if len(found) > 0:
                status.append(True)
            else:
                status.append(False)
                warnings = self.testNamespace(level=level)
            if self.children:
                s, w = self.children.test(target=target, level=level+1)
                status, warnings = status + s, warnings + w

        if len(status) == 0:
            status = [False]
        return status, warnings


class Document(object):
    """ Represents the object inside <online /> tag for Editions, Translations """
    def __init__(self, xml, rewriting_rules={}, strict=False):
        """ Initiate the object

        :param xml: XML markup or object, starting at the online tag
        :type xml: str or unicode or ElementTree.Element
        :param rewriting_rules: A dictionary where key are string to be replaced by their value
        :type rewriting_rules: dict
        :param strict: Indicate wether we should raise Exceptions on CTS compliancy failure
        :type strict: boolean
        """

        if isinstance(xml, ElementTree.Element):
            self.xml = xml
        else:
            self.xml = ElementTree.parse(xml).getroot()

        self.rewriting_rules = rewriting_rules
        self.strict = strict

        self.db = self.xml.get("docname")
        self.path = self._getFilePath()
        self.filename = os.path.basename(self.path)

        self.validate = self.xml.find("{http://chs.harvard.edu/xmlns/cts3/ti}validate").get("schema")

        self.namespaces = self._retrieveNamespace()

        self.citation = Citation(
            xml=self.xml.find("{http://chs.harvard.edu/xmlns/cts3/ti}citationMapping").find("{http://chs.harvard.edu/xmlns/cts3/ti}citation"),
            namespaces=self.namespaces,
            strict=self.strict
        )

    def _retrieveNamespace(self):
        """ Retrieve namespaces

        :returns:
        :rtype:
        """
        namespaces = {}
        for namespace in self.xml.findall("{http://chs.harvard.edu/xmlns/cts3/ti}namespaceMapping"):
            namespaces[namespace.get("abbreviation") + ":"] = "{" + namespace.get("nsURI") + "}"
        return namespaces

    def _getFilePath(self):
        """ Returns the filepath of the Document

        :returns: String representing the path to the file
        :rtype: str or unicode
        """
        return replace_all(self.db, self.rewriting_rules)

    def getFile(self):
        """ Returns the content of the file

        :returns: The file's content for this document
        :rtype: str or unicode
        """
        try:
            with open(self.path, "r") as f:
                return f.read()
        except Exception as E:
            if self.strict:
                raise E
            else:
                print(Error("The file {0} does not exist or can't be opened".format(self.path)))
        return None

    def testCitation(self):
        """ Test the citation schema against the opened file

        :returns: Indicator of success and list of warnings
        :rtype: tuple(boolean, list)
        """
        status, warnings = self.citation.test(self.path)
        return status, warnings


class Text(object):
    """ Represents an opus/a Work inside a WorkGroup inside a CTS Inventory """
    def __init__(self, xml, rewriting_rules={}, strict=False):
        """ Initiate the object

        :param xml: A string representing the TextGroup in XML or a ElementTree object
        :type xml: str or unicode or ElementTree.Element
        :param rewriting_rules: A dictionary where key are string to be replaced by their value
        :type rewriting_rules: dict
        :param strict: Indicate wether we should raise Exceptions on CTS compliancy failure
        :type strict: boolean
        """

        if isinstance(xml, ElementTree.Element):
            self.xml = xml
        else:
            self.xml = ElementTree.parse(xml).getroot()

        self.rewriting_rules = rewriting_rules
        self.strict = strict

        self.id = xml.get("projid")
        self.titles = {}
        self._retrieveTitles()

        self.document = Document(
            xml=self.xml.find("{http://chs.harvard.edu/xmlns/cts3/ti}online"),
            rewriting_rules=self.rewriting_rules
        )

    def _retrieveTitles(self):
        """ Retrieve titles from the xml """
        for title in self.xml.findall("{http://chs.harvard.edu/xmlns/cts3/ti}label"):
            self._title_lang = title.get("{http://www.w3.org/XML/1998/namespace}lang")
            self.titles[self._title_lang] = title.text

        if self.strict is True and len(self.titles) == 0:
            raise NoTitleException("Work ID {0} has no title".format(self.id))

    def getTitle(self, lang=None):
        """ Returns the title in given lang if available

        :param lang: The lang to be returned
        :type lang: str or unicode
        :returns: Title of the Work
        :rtype: str or unicode
        """
        try:
            defaulttitle = list(self.titles.keys())[0]
            return self.titles.get(lang, self.titles[defaulttitle])
        except:
            raise NoTitleException()


class Edition(Text):
    def __init__(self, xml, rewriting_rules={}, strict=False):
        """ Initiate the object

        :param xml: A string representing the TextGroup in XML or a ElementTree object
        :type xml: str or unicode or ElementTree.Element
        :param rewriting_rules: A dictionary where key are string to be replaced by their value
        :type rewriting_rules: dict
        :param strict: Indicate wether we should raise Exceptions on CTS compliancy failure
        :type strict: boolean
        """
        super(Edition, self).__init__(xml=xml, rewriting_rules=rewriting_rules, strict=strict)


class Translation(Text):
    def __init__(self, xml, rewriting_rules={}, strict=False):
        """ Initiate the object

        :param xml: A string representing the TextGroup in XML or a ElementTree object
        :type xml: str or unicode or ElementTree.Element
        :param rewriting_rules: A dictionary where key are string to be replaced by their value
        :type rewriting_rules: dict
        :param strict: Indicate wether we should raise Exceptions on CTS compliancy failure
        :type strict: boolean
        """
        super(Translation, self).__init__(xml=xml, rewriting_rules=rewriting_rules, strict=strict)
