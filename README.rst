.. contents::


Documentation
=============

.. image:: http://img.shields.io/pypi/v/collective.catalogcleanup.svg
   :target: https://pypi.python.org/pypi/collective.catalogcleanup


Usage and goal
--------------

Add ``collective.catalogcleanup`` to the eggs in your buildout.
This makes a browser view available on the Plone Site root: ``@@collective-catalogcleanup``.

This goes through the ``portal_catalog`` and removes all catalog brains for which a ``getObject`` call does not work.
In other words, it removes brains that no longer belong to an actual object in the site.

The goal is to get rid of outdated brains that could otherwise cause problems, for example during an upgrade to a new major Plone version.

``@@collective-catalogcleanup`` by default does a dry run, so it only reports problems.
Call it with ``@@collective-catalogcleanup?dry_run=false`` to perform the actual cleanup.


Details
-------

So what does the catalog cleanup do?

- It removes stuff!  You *must* make a backup first!

- It handles the ``portal_catalog``.
  Version 1.x also handled ``uid_catalog`` and ``reference_catalog``.

- For each catalog it reports the number of catalog brains it contains.

- It removes brains that have a UID of ``None``.

- It removes brains of which the object is broken.  This can happen
  when the object belongs to a package that is no longer available in
  the Plone Site.

- It removes brains of which the object cannot be found.

- It looks for non unique uids.
  We accept one object and we give the other objects a new UID.

- A simple report will be printed in the browser.
  It may look like this::

    Brains in portal_catalog: 20148
    portal_catalog: removed 25 brains without UID.
    portal_catalog: removed 100 brains with status broken.
    portal_catalog: removed 5 brains with status notfound.
    portal_catalog: 249 non unique uids found.
    portal_catalog: 249 items given new unique uids.

- The instance log may contain more info, about individual items.


Alternatives
------------

- A clear and rebuild of the ``portal_catalog`` should have partially the
  same effect, but it will likely take a lot longer and it will not
  solve some of the problems mentioned above.  But this is definitely
  the most logical thing to try before giving
  ``collective.catalogcleanup`` a go.


Compatibility
-------------

Version 2.x works on Plone 5.2 and 6.0, on Python 3 only.
For earlier Plone and Python versions, use version 1.x.


Authors
-------

Maurits van Rees
