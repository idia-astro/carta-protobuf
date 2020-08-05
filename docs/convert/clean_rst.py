#!/usr/bin/env python3

import re
import sys
import os
from collections import defaultdict

inputname, destdir = sys.argv[1:3]

with open(inputname) as icdfile:
    icd = icdfile.read()

# Fix references
# TODO add alternate anchors to all the protobuf messages, to simplify these.

def reference(m):
    target = re.sub('%%20', ' ', m.group(2))
    return f':ref:`{m.group(1)} <{target}>`'

icd = re.sub('`([^ <]+) <#([^>]+)>`__', reference, icd)

# inline the inexplicably substituted images

icd = re.sub(r'#\. (.*?)\\ (\|image\d+\|)', r'\1\n\n\2\n', icd)

images = re.findall('(\.\. )(\|image\d+\|) (image:: images/.*.png)', icd)

icd = re.sub('\.\. \|image\d+\| image:: images/.*.png\n', "", icd)

for begin, placeholder, end in images:
    icd = re.sub(re.escape(placeholder), f"{begin}{end}", icd)

# TODO eventually replace the images with embedded plantuml code?

# We need a nested toctree -- toctrees in the files for section 3 and 4

sections = re.findall("\n(.*?)\n={4,}", icd)
subsections = re.findall("\n(.*?)\n-{4,}", icd)

# Destination filenames

filenames = {s: f'{s.lower().replace(" ", "_")}.rst' for s in sections + subsections}
filenames["index"] = "index.rst"
filenames["changelog"] = "changelog.rst.txt"

# special includes for the protoc files

protoc = {
    "Control messages": "control.rst.txt",
    "Request messages": "request.rst.txt",
    "Data stream messages": "stream.rst.txt",
    "Sub-messages": "defs.rst.txt",
    "Enums": "enums.rst.txt",
}

toctree = """
.. toctree::
   :maxdepth: 2
   :caption: Contents:
"""

file_contents = defaultdict(list)
    
lines = iter(icd.split("\n"))
indexfile = filenames["index"]
sectionfile = None
currentfile = indexfile

has_toctree = {}

for line in lines:
    if line in filenames:
        currentfile = filenames[line]
        if line in sections:
            sectionfile = currentfile
            if not has_toctree.get(indexfile, False):
                file_contents[indexfile].append(toctree)
                has_toctree[indexfile] = True
            file_contents[indexfile].append(f'   {filenames[line].replace(".rst", "")}')
        elif line in subsections:
            if not has_toctree.get(sectionfile, False):
                file_contents[sectionfile].append(toctree)
                has_toctree[sectionfile] = True
            file_contents[sectionfile].append(f'   {filenames[line].replace(".rst", "")}')
    elif line == "**Changelog**":
        file_contents[currentfile].append(f".. include:: {filenames['changelog']}")
        currentfile = filenames["changelog"]
    
    file_contents[currentfile].append(line)
    
    # protoc includes
    
    if line in protoc:
        file_contents[currentfile].append(next(lines)) # underline
        file_contents[currentfile].append("")
        file_contents[currentfile].append(f".. include:: {protoc[line]}")
    
for filename, contents in file_contents.items():
    with open(os.path.join(destdir, filename), "w") as f:
        for line in contents:
            print(line, file=f)