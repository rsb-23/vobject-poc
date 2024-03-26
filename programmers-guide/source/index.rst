.. vobject programmers guide
   Copyright (C) 2024, David Arnold

.. Introduction
   Quick Start
   Calendars and Cards
   Installing
   Importing
   Parsing
   Creating
   Common Problems
   Getting Help
   Index

vObject
=======

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Introduction
============

Quick Start
===========

Calendars and Cards
===================

.. index:: Apple, AT&T, IBM, IETF, Internet Mail Consortium, Lucent, Siemens, Versit Consortium
.. index:: vCard, vCalendar, iCalendar

The *vCard* and *vCalendar* specifications were originally developed by the
Versit Consortium, with contributions from Apple, IBM, AT&T/Lucent, and
Siemens.  Their stewardship subsequently passed to the Internet Mail
Consortium, before later being adopted by the IETF.

Within the IETF, vCard versions 3.0 and 4.0, and a revised and expanded
calendar specification renamed to *iCalendar* 2.0 have been published,
together with numerous extensions, clarifications, and related standards.

The two main standards (vCard and iCalendar) form a way to store and
communicate information about contacts (names, addresses, phone numbers,
etc), and scheduling (events, todos, etc).  They have been widely
adopted for both storage and sharing of contact and calendar data.

vCard
-----

.. index:: RFC-2426, RFC-6350

vCard 2.1 was the final version published by Versit, and is still widely
used.  vCard 3.0, published as IETF RFC-2426, is also widely used, however
both versions are frequently extended by vendors or have implementation
quirks in part due to unclear specification.  vCard 4.0 (IETF RFC-6350)
attempted to resolve the issues of earlier versions, but in doing so
necessarily broke some backward compatibility, and as a result, it has
not been universally adopted.

iCalendar
---------

.. index:: CalDAV, RFC-2445

vCalendar 1.0 was published by Versit, however it was not until the
renamed iCalendar 2.0 (IETF RFC-2445) was published that wide-spread
interoperability was possible.  Together with various extensions, and in
particular the CalDAV specification for sharing calendars, iCalendar is
now almost universally used for communication of calendaring data.

Related Standards
-----------------

.. index:: JSON, microformat, XML

Alongside vCard and iCalendar several different formats have been
developed that reuse most (or all) of their semantic model, while
adopting a different syntax.  XML and JSON variants of both standards
exist, as well as HTML microformats.

More recent work in the IETF is looking to revise the semantic models
of vCard and iCalendar, proposing new standards that can be translated
to and from vCard and iCalendar, but add additional functionality.

vObject
-------

The Python ``vobject`` module supports parsing vCard and iCalendar objects
from strings (email attachments, files, etc) and generating those
formatted strings from Python card and calendar objects.  It maintains
compatibility with older versions of the specifications, and supports
various quirks of widely-used implementations, simplifying real-life
usage.

.. index:: Open Source Applications Foundation, OSAF, Chandler, Eventable, GitHub, Apache
.. index:: single: Harris, Jeffrey
.. index:: single: Karim, Sameen

``vobject`` was originally developed by Jeffrey Harris, working at the Open
Source Applications Foundation (OSAF) on their Chandler project.  It was
subsequently adopted by Sameen Karim at Eventable, before passing to
community maintenance.  The source code is freely available under the
Apache 2.0 license, and developed in a public repository at GitHub.

Installing
==========

``vobject`` has a few dependencies.  Firstly, it is known to run on
Python_ 2.7, and 3.7 through to 3.12.  It is not supported on
Python 3.0 through to 3.6, nor Python 2.6 or earlier.

You can install it using pip_::

    $ pip install vobject


It's usually a good idea to install ``vobject`` into a virtual
environment, to avoid issues with incompatible versions and system-wide
packaging schemes.

Getting the code
----------------

You can also get the source code from PyPI_ or GitHub_. You can either clone the
public repository::

    $ git clone git://github.com/py-vobject/vobject.git

Download the tarball::

    $ curl -OL https://github.com/py-vobject/vobject/tarball/master

Or, download the zipball::

    $ curl -OL https://github.com/py-vobject/vobject/zipball/master

Once you have a copy of the source you can install it into your virtual
environment's site-packages easily::

    $ python setup.py install

Importing
=========

You can import the ``vobject`` module maintaining its internal structure,
or you can import some or all bindings directly.

.. index:: vobject, vCard
.. code-block:: python
    :linenos:

    import vobject

    card = vobject.vCard()


Or

.. code-block:: python
    :linenos:

    from vobject import *

    card = vCard()


.. index:: import, namespace

Note that the ``import \*`` form is explicitly supported, with the exposed
namespace explicitly managed to contain only the public features of the
package.

All the example code in this document will use the first form, which is
strongly recommended.

Parsing
=======

To parse one top level component from an existing iCalendar stream or
string, use the readOne function:

.. code-block:: python
    :linenos:

    >>> parsedCal = vobject.readOne(icalstream)
    >>> parsedCal.vevent.dtstart.value
    datetime.datetime(2006, 2, 16, 0, 0, tzinfo=tzutc())

Similarly, readComponents is a generator yielding one top level component at a time from a stream or string.

.. code-block:: python
    :linenos:

    >>> vobject.readComponents(icalstream).next().vevent.dtstart.value
    datetime.datetime(2006, 2, 16, 0, 0, tzinfo=tzutc())

Parsing vCards is very similar.

.. code-block:: python
    :linenos:

    >>> s = """
    ... BEGIN:VCARD
    ... VERSION:3.0
    ... EMAIL;TYPE=INTERNET:jeffrey@osafoundation.org
    ... EMAIL;TYPE=INTERNET:jeffery@example.org
    ... ORG:Open Source Applications Foundation
    ... FN:Jeffrey Harris
    ... N:Harris;Jeffrey;;;
    ... END:VCARD
    ... """
    >>> v = vobject.readOne( s )
    >>> v.prettyPrint()
     VCARD
        ORG: Open Source Applications Foundation
        VERSION: 3.0
        EMAIL: jeffrey@osafoundation.org
        params for  EMAIL:
           TYPE [u'INTERNET']
        FN: Jeffrey Harris
        N:  Jeffrey  Harris
    >>> v.n.value.family
    u'Harris'
    >>> v.email_list
    [<EMAIL{'TYPE': ['INTERNET']}jeffrey@osafoundation.org>,
     <EMAIL{'TYPE': ['INTERNET']}jeffery@example.org>]

Just like with iCalendar example above readComponents will yield a
generator from a stream or string containing multiple vCards objects.

.. code-block:: python
    :linenos:

    >>> vobject.readComponents(vCardStream).next().email.value
    'jeffrey@osafoundation.org'

Creating Objects
================

Model
-----

Both iCalendar and vCard share a syntax and basic semantic model that is
worth explaining up front because it's a little unusual.

.. index:: component, content line, object, parameter, value

The major components of the model are:

* Object
* Component
* Content Line
* Parameter
* Value

An *Object* represents a complete entity: a person, an event, a journal
entry, etc.  Objects are comprised of one or more *Components*.

A Component has a name, written in ALL CAPS style.  It may also have
zero or more *Parameters*, and finally a *Value*.  Parameters have a
name, and optional value.

A *Content Line* is used to hold the *Value* of a *Component*.  When
generating an encoded object, the content line is formatted in a particular
way, and handle the quoting of reserved characters, line wrapping, data
encoding, etc.

While the iCalendar, vCard, and their various extension specifications
define the standard components of the calendar and contact objects, the
model is extensible, and vendors may add additional components and
parameters, and do so often in practice.

iCalendar
---------

vObject has a basic datastructure for working with iCalendar-like
syntax.  Additionally, it defines specialized behaviors for many of
the standard iCalendar components.

The iCalendar standard defines six object types:

* VEVENT
* VTODO
* VJOURNAL
* VTIMEZONE
* VFREEBUSY
* VALARM

plus the containing VCALENDAR object (note the name, a hold-over from
the v1.0 Versit standard).

An iCalendar stream (eg. an .ics file) is comprised of a sequence of
these objects.

Within vObject, each standard object has a defined *behavior* class,
that specifies its allowed cardinality, base data type, ability to
convert to/from native Python data types, etc.  These behaviors are
maintained in a registry within the vobject module, and identified by
name.

To create an object that already has a behavior defined, run:

.. index:: newFromBehavior
.. code-block:: python
    :linenos:

    >>> import vobject
    >>> cal = vobject.newFromBehavior('vcalendar')
    >>> cal.behavior
    <class 'vobject.icalendar.VCalendar2_0'>

Convenience functions exist to create iCalendar and vCard objects:

.. code-block:: python
    :linenos:

    >>> cal = vobject.iCalendar()
    >>> cal.behavior
    <class 'vobject.icalendar.VCalendar2_0'>
    >>> card = vobject.vCard()
    >>> card.behavior
    <class 'vobject.vcard.VCard3_0'>

Once you have an object, you can use the add method to create
children:

.. index:: add, prettyPrint
.. code-block:: python
    :linenos:

    >>> cal.add('vevent')
    <VEVENT| []>
    >>> cal.vevent.add('summary').value = "This is a note"
    >>> cal.prettyPrint()
     VCALENDAR
        VEVENT
           SUMMARY: This is a note

Note that summary is a little different from vevent, it's a
ContentLine, not a Component.  It can't have children, and it has a
special value attribute.

ContentLines can also have parameters.  They can be accessed with
regular attribute names with _param appended:

.. code-block:: python
    :linenos:

    >>> cal.vevent.summary.x_random_param = 'Random parameter'
    >>> cal.prettyPrint()
     VCALENDAR
        VEVENT
           SUMMARY: This is a note
           params for  SUMMARY:
              X-RANDOM ['Random parameter']

There are a few things to note about this example

  * The underscore in x_random is converted to a dash (dashes are
    legal in iCalendar, underscores legal in Python)
  * X-RANDOM's value is a list.

If you want to access the full list of parameters, not just the first,
use &lt;paramname&gt;_paramlist:

.. code-block:: python
    :linenos:

    >>> cal.vevent.summary.x_random_paramlist
    ['Random parameter']
    >>> cal.vevent.summary.x_random_paramlist.append('Other param')
    >>> cal.vevent.summary
    <SUMMARY{'X-RANDOM': ['Random parameter', 'Other param']}This is a note>

Similar to parameters, If you want to access more than just the first
child of a Component, you can access the full list of children of a
given name by appending `_list` to the attribute name:

.. code-block:: python
    :linenos:

    >>> cal.add('vevent').add('summary').value = "Second VEVENT"
    >>> for ev in cal.vevent_list:
    ...     print ev.summary.value
    This is a note
    Second VEVENT

The interaction between the del operator and the hiding of the
underlying list is a little tricky, del cal.vevent and del
cal.vevent_list both delete all vevent children:

.. code-block:: python
    :linenos:

    >>> first_ev = cal.vevent
    >>> del cal.vevent
    >>> cal
    <VCALENDAR| []>
    >>> cal.vevent = first_ev

VObject understands Python's datetime module and tzinfo classes.

.. code-block:: python
    :linenos:

    >>> import datetime
    >>> utc = vobject.icalendar.utc
    >>> start = cal.vevent.add('dtstart')
    >>> start.value = datetime.datetime(2006, 2, 16, tzinfo = utc)
    >>> first_ev.prettyPrint()
         VEVENT
            DTSTART: 2006-02-16 00:00:00+00:00
            SUMMARY: This is a note
            params for  SUMMARY:
               X-RANDOM ['Random parameter', 'Other param']

Components and ContentLines have serialize methods:

.. code-block:: python
    :linenos:

    >>> cal.vevent.add('uid').value = 'Sample UID'
    >>> icalstream = cal.serialize()
    >>> print icalstream
    BEGIN:VCALENDAR
    VERSION:2.0
    PRODID:-//PYVOBJECT//NONSGML Version 1//EN
    BEGIN:VEVENT
    UID:Sample UID
    DTSTART:20060216T000000Z
    SUMMARY;X-RANDOM=Random parameter,Other param:This is a note
    END:VEVENT
    END:VCALENDAR

Observe that serializing adds missing required lines like version and
prodid.  A random UID would be generated, too, if one didn't exist.

If dtstart's tzinfo had been something other than UTC, an appropriate
vtimezone would be created for it.

vCard
-----

Making vCards proceeds in much the same way. Note that the 'N' and 'FN'
attributes are required.

.. code-block:: python
    :linenos:

    >>> j = vobject.vCard()
    >>> j.add('n')
     <N{}    >
    >>> j.n.value = vobject.vcard.Name( family='Harris', given='Jeffrey' )
    >>> j.add('fn')
     <FN{}>
    >>> j.fn.value ='Jeffrey Harris'
    >>> j.add('email')
     <EMAIL{}>
    >>> j.email.value = 'jeffrey@osafoundation.org'
    >>> j.email.type_param = 'INTERNET'
    >>> j.add('org')
     <ORG{}>
    >>> j.org.value = ['Open Source Applications Foundation']
    >>> j.prettyPrint()
     VCARD
        ORG: ['Open Source Applications Foundation']
        EMAIL: jeffrey@osafoundation.org
        params for  EMAIL:
           TYPE ['INTERNET']
        FN: Jeffrey Harris
        N:  Jeffrey  Harris

serializing will add any required computable attributes (like 'VERSION')

.. code-block:: python
    :linenos:

    >>> j.serialize()
    'BEGIN:VCARD\r\nVERSION:3.0\r\nEMAIL;TYPE=INTERNET:jeffrey@osafoundation.org\r\nFN:Jeffrey Harris\r\nN:Harris;Jeffrey;;;\r\nORG:Open Source Applications Foundation\r\nEND:VCARD\r\n'
    >>> j.prettyPrint()
     VCARD
        ORG: Open Source Applications Foundation
        VERSION: 3.0
        EMAIL: jeffrey@osafoundation.org
        params for  EMAIL:
           TYPE ['INTERNET']
        FN: Jeffrey Harris
        N:  Jeffrey  Harris



Common Problems
===============

Getting Help
============

.. epigraph::

    95=17|96=RAW DATA \\x00\\x01 VALUE|


.. _GitHub: https://github.com/py-vobject/vobject
.. _Python: http://www.python.org/
.. _PyPI: https://pypi.org/project/vobject/
.. _pip: http://www.pip-installer.org/


