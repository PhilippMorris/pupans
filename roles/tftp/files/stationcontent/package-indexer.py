#!/usr/bin/python

import argparse
import os
import fnmatch
import json
import sys
import xml.etree.ElementTree as ET


class PackageIndexEntry:
    def load_file(self, apmFile):
        apmXml = ET.parse(apmFile)
        self.load_xml(apmXml)

    def load(self, apm):
        apmXml = ET.fromstring(apm)
        self.load_xml(apmXml)

    def load_xml(self, apmXml):
        self.sku = self.from_single_child(apmXml, 'SKU')
        self.manufacturer = self.from_single_child(apmXml, 'Manufacturer')
        self.model = self.from_single_child(apmXml, 'Model')
        self.guide_name = self.from_single_child(apmXml, 'GuideName')
        self.package_id = self.from_single_child(apmXml, 'Id')
        self.description = self.from_single_child(apmXml, 'Description')
        self.path = ''
        self.files = []

        for fileElement in apmXml.findall('./Files/File'):
            file = dict(path=self.from_single_child(fileElement, 'Name').replace('\\', '/'),
                        fileHash=self.from_single_child(fileElement, 'Hash'))
            self.files.append(file)

    def from_single_child(self, element, name):
        child_value = None
        for child in element.iter(name):
            if not child_value is None:
                raise IOError('Invalid APM content: there must be only one element named {name}'.format(**locals()))

            child_value = child.text

        return child_value


class Indexer:
    def __init__(self):
        self.packageIndex = {}
        self.packagesRootDir = 'packages'
        self.guidesRootDir = 'guides'
        self.defaultGuide = None

    def index(self):
        packageIndex = {}

        # Iterate over all package folders
        for packageFolder in os.listdir(self.packagesRootDir):
            packageFolderPath = os.path.join(self.packagesRootDir, packageFolder)
            if os.path.isdir(packageFolderPath):
                package = None

                # Scan for APM files
                for apmFile in os.listdir(packageFolderPath):
                    if not fnmatch.fnmatch(apmFile, "*.apm"): continue

                    apmFilePath = os.path.join(packageFolderPath, apmFile)
                    package = PackageIndexEntry()

                    try:
                        package.load_file(apmFilePath)
                    except ET.ParseError:
                        sys.stderr.write("Failed to parse APM file '{apmFilePath}'.\n".format(**locals()))
                        continue

                    package.path = packageFolder

                    self.add(package)

    def dump(self):

        sorted_index = sorted(self.packageIndex.values(), key=lambda i: i.sku)

        print(json.dumps([{'SKU': x.sku,
                           'Model': x.model,
                           'Manufacturer': x.manufacturer,
                           'Description': x.description,
                           'GuideName': x.guide_name,
                           'PackageId': x.package_id,
                           'Path': x.path,
                           'IsRefereshSupported': True} for x in sorted_index]))

    def add(self, package):
        if self.packageIndex.has_key(package.sku):
            existingPackage = self.packageIndex[package.sku]
            sys.stderr.write("Ignoring package {package.package_id}; there already is a package with " \
                             "SKU '{existingPackage.sku}' and its ID is {existingPackage.package_id}. " \
                             "Maybe a duplicate APM file?\n".format(**locals()))
            return False

        self.packageIndex[package.sku] = package
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indexes all packages and guides for better search by the SKU app.")
    parser.add_argument('--packagesdir', type=str, default='/srv/packages')
    parser.add_argument('--guidesdir', type=str, default='/usr/share/nginx/www/app/guides')
    parser.add_argument('--defaultguide', type=str, default='default')

    args = parser.parse_args()

    indexer = Indexer()
    indexer.packagesRootDir = args.packagesdir
    indexer.guidesRootDir = args.guidesdir
    indexer.defaultGuide = args.defaultguide

    indexer.index()
    indexer.dump()