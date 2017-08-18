#!/usr/bin/python

import argparse
import fnmatch
import os
import re
from collections import defaultdict
import logging

if os.name != 'nt':
    import sh

__author__ = 'aluetjen'

LOGGER = logging.getLogger()


class AggregatedContent:
    def __init__(self, content_id, version, source_files):
        self.content_id = content_id
        self.version = version
        self.source_files = source_files
        self.alias_for = None

        alias_file = source_files.get("./.alias")
        if (alias_file is not None):
            with open(alias_file, 'r') as f:
                # Read only the first line
                self.alias_for = f.readline().replace("\n", "")

    @staticmethod
    def scan(root_folder):
        content_map = AggregatedContent._get_content_map(root_folder)

        aggregated_content = []
        aggregated_content_aliases = []

        for contentid, source_folders in content_map.items():
            version, aggregated_files = AggregatedContent._build_aggregated_content(source_folders)
            new_content = AggregatedContent(contentid, version, aggregated_files)
            if (new_content.alias_for is None):
                aggregated_content.append(new_content)
            else:
                aggregated_content_aliases.append(new_content)

        #Ensure that Alias Packages are processed last
        aggregated_content = aggregated_content + aggregated_content_aliases

        return aggregated_content

    @staticmethod
    def _build_aggregated_content(source_download_folders):

        source_files = {}

        previous_version = -1

        for source_folder, version in sorted(source_download_folders, cmp=lambda x, y: cmp(x[1], y[1])):

            if version - previous_version > 1:
                LOGGER.info(
                    'Missing intermediate version {0} before including {1}. Skipping any subsequent content until this version is present.'.
                    format(previous_version + 1, source_folder))
                break

            for root, dirs, files in os.walk(source_folder):
                relative_source_folder = os.path.relpath(root, source_folder)

                for file in files:
                    relative_source_file = os.path.join(relative_source_folder, file)
                    source_files[relative_source_file] = os.path.join(root, file)

            previous_version = version

        return previous_version, source_files

    @staticmethod
    def _get_content_map(root_folder):
        # Build content -> content torrents map
        content_tuples = defaultdict(list)

        # Legacy folders - Each content is placed without version which defaults to version 0
        AggregatedContent._get_legacy_content_map(root_folder, 'packages', 'package-', content_tuples)
        AggregatedContent._get_legacy_content_map(root_folder, 'guides', 'guide-', content_tuples)
        # All normal content folders with <contentid>#<version> notation
        AggregatedContent._get_content_map_from_folder(root_folder, content_tuples,
                                                       ignore_patterns=['packages', 'guides'])

        return content_tuples

    @staticmethod
    def _get_legacy_content_map(root_folder, legacy_subfolder, prefix, content_tuples):

        new_content_tuples = defaultdict(list)

        AggregatedContent._get_content_map_from_folder(os.path.join(root_folder, legacy_subfolder), new_content_tuples)

        for content_id in new_content_tuples.keys():
            migrated_content_id = prefix + content_id
            content_tuples[migrated_content_id] = new_content_tuples.pop(content_id)

    @staticmethod
    def is_valid_content_folder(absolute_folder_path, folder, ignore_patterns):
        skip_folder = False

        for pattern in ignore_patterns:
            if fnmatch.fnmatch(folder, pattern):
                LOGGER.debug("Skipping {0} since it matches the ignore pattern {1}.".format(folder, pattern))
                skip_folder = True

        if not os.path.isdir(absolute_folder_path):
            LOGGER.debug("Skipping {0}. Not a folder.".format(absolute_folder_path))
            skip_folder = True

        complete_file_path = os.path.join(absolute_folder_path, '.complete')

        if not os.path.exists(complete_file_path):
            skip_folder = True

        return not skip_folder

    @staticmethod
    def _get_content_map_from_folder(root_folder, content_tuples, ignore_patterns=[]):

        if not os.path.exists(root_folder):
            LOGGER.debug("Skipping {0} root folder does not exist.".format(root_folder))
            return

        for folder in os.listdir(root_folder):
            absolute_folder_path = os.path.join(root_folder, folder)

            if not AggregatedContent.is_valid_content_folder(absolute_folder_path, folder, ignore_patterns):
                continue

            folder_parts = re.match("^([^#]+)(?:#(\d*))?", folder)

            if folder_parts is None:
                LOGGER.debug("Skipping {0}. Not matching regex ^([^#]+)(?:#(\d*))?".format(folder))

            if folder_parts.group(2) is not None:
                version = int(folder_parts.group(2))
            else:
                version = -1

            content_tuples[folder_parts.group(1)].append((absolute_folder_path, version))


class Symlink:
    def __init__(self, link_path, target):

        self.link_path = link_path
        self.target = target

    def link(self):

        if os.name == 'nt':
            print("rm {0}".format(self.link_path))
            print("ln -s {0} {1}".format(self.target, self.link_path))
        else:
            if os.path.lexists(self.link_path):
                if not(os.path.islink(self.link_path)) or  os.readlink(self.link_path) != self.target:
                    LOGGER.info("Update symlink source='{0}' target='{1}'.".format(self.link_path, target))
                    sh.rm(self.link_path)
                    sh.ln("-s", self.target, self.link_path)
            else:
                LOGGER.info("Create symlink source='{0}' target='{1}'.".format(self.link_path, target))
                sh.ln("-s", self.target, self.link_path)


class TargetContentRootFolder:
    def __init__(self, target_path):
        self.target_path = target_path

    def _populate_content_folder(self, content, content_folder_path):
        for link_file, target in content.source_files.items():

            link_file_subfolder = os.path.dirname(link_file)
            link_file_folder_path = os.path.join(content_folder_path, link_file_subfolder)
            link_file_path = os.path.join(content_folder_path, link_file)

            if not os.path.exists(link_file_folder_path):
                os.makedirs(link_file_folder_path)

            link = Symlink(link_file_path, target)
            link.link()

    def populate(self, contents, folder_filter=None):
        for content in contents:
            if folder_filter is not None and not fnmatch.fnmatch(content.content_id, folder_filter):
                continue

            # Backwards compatibility: remove package- and guide- prefix from target folders.
            id_match = re.match('^([^-]+)-(.+)', content.content_id)
            if id_match is not None:
                content.content_id = id_match.group(2)

            content_folder_path = os.path.join(self.target_path, content.content_id)

            if not os.path.exists(content_folder_path):
                os.makedirs(content_folder_path)

            with open(os.path.join(content_folder_path, ".version"), "w") as version_file:
                version_file.write(str(content.version))

            # Symlink Alias Packages to their original name
            if (content.alias_for is not None):
                print("{0} is an alias for {1}.".format(content.content_id, content.alias_for))
                source_path = content_folder_path.replace(content.content_id, content.alias_for)
                if os.path.exists(source_path):
                    source_path += "/."
                    destination_path = content_folder_path + "/."
                    print("copying {0} to {1}.".format(source_path, destination_path))
                    sh.cp("-av", source_path, destination_path)
                    self._populate_content_folder(content, content_folder_path)
                else:
                    print("Skipping {0}, aliased package {1} does not exist.".format(content.content_id, content.alias_for))
            else:
                self._populate_content_folder(content, content_folder_path)


def configure_logging():
    FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)


if __name__ == "__main__":
    configure_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("--targetdir", type=str, required=True)
    parser.add_argument("--downloaddir", type=str, default='/usr/share/p2pclient/download')
    parser.add_argument("--contentfilter", type=str, required=True)

    args = parser.parse_args()

    if os.name == 'nt':
        print("You are running on Windows, so this will only show you a 'what if?'.")

    if not os.path.exists(args.downloaddir):
        raise IOError("Download directory does not exist.\n")

    contents = AggregatedContent.scan(args.downloaddir)

    target = TargetContentRootFolder(args.targetdir)
    target.populate(contents, args.contentfilter)
