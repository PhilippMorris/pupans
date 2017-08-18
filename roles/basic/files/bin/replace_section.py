#!/usr/bin/python
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument('--begin')
parser.add_argument('--end')
parser.add_argument('--section', help='File that contains the new content of the section.')
parser.add_argument('config_file', help='The config file to manipulate.')
args = parser.parse_args()

with open(args.section, 'r') as section_file:
    section = section_file.read()

with open(args.config_file, 'r') as config_file:
    content = config_file.read()

expression = r"{0}\n.*{1}(\n|$\Z)".format(args.begin, args.end)

if re.search(expression, content, flags=re.MULTILINE | re.DOTALL):
    content = re.sub(expression, section.strip() + '\n', content, flags=re.MULTILINE | re.DOTALL)
else:
    content += '\n' + section

with open(args.config_file, 'w') as config_file:
    config_file.write(content)
