"""
VObject: module for reading vCard and vCalendar files

Description
-----------

Parses iCalendar and vCard files into Python data structures, decoding the
relevant encodings. Also serializes vobject data structures to iCalendar, vCard,
or (experimentally) hCalendar unicode strings.

Requirements
------------

Requires python 3.9 or later, dateutil 2.7.0 or later and pytz.

Recent changes
--------------
    - Revert too-strict serialization of timestamp values - broke too many other
       implementations

For older changes, see
   - http://py-vobject.github.io/vobject/#release-history or
   - http://vobject.skyhouseconsulting.com/history.html
"""

from setuptools import find_packages, setup

doclines = (__doc__ or "").splitlines()

setup(
    name="vobject",
    version="0.9.7",
    author="Jeffrey Harris",
    author_email="jeffrey@osafoundation.org",
    maintainer="David Arnold",
    maintainer_email="davida@pobox.com",
    license="Apache",
    zip_safe=True,
    url="http://py-vobject.github.io/vobject/",
    download_url="https://github.com/py-vobject/vobject/tarball/0.9.7",
    bugtrack_url="https://github.com/py-vobject/vobject/issues",
    entry_points={"console_scripts": ["ics_diff = vobject.ics_diff:main", "change_tz = vobject.change_tz:main"]},
    include_package_data=True,
    install_requires=["python-dateutil >= 2.7.0", "pytz"],
    platforms=["any"],
    packages=find_packages(),
    description="A full-featured Python package for parsing and creating " "iCalendar and vCard files",
    long_description="\n".join(doclines[2:]),
    keywords=["vobject", "icalendar", "vcard", "ics", "vcs", "hcalendar"],
    test_suite="tests",
    classifiers="""
      Development Status :: 5 - Production/Stable
      Environment :: Console
      Intended Audience :: Developers
      License :: OSI Approved :: Apache Software License
      Natural Language :: English
      Operating System :: OS Independent
      Programming Language :: Python
      Programming Language :: Python :: 2.7
      Programming Language :: Python :: 3
      Topic :: Text Processing""".strip().splitlines(),
)
