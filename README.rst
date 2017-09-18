.. contents::


Documentation
=============

.. image:: http://img.shields.io/pypi/v/collective.catalogcleanup.svg
   :target: https://pypi.python.org/pypi/collective.catalogcleanup

.. image:: https://img.shields.io/travis/collective/collective.catalogcleanup/master.svg
    :target: http://travis-ci.org/collective/collective.catalogcleanup

.. image:: https://img.shields.io/coveralls/collective/collective.catalogcleanup/master.svg
    :target: https://coveralls.io/r/collective/collective.catalogcleanup

Usage and goal
--------------

Add collective.catalogcleanup to the eggs in your buildout (and to zcml on
Plone 3.2 or earlier).  This makes a browser view available on the
Plone Site root: ``@@collective-catalogcleanup``.

This goes through the portal_catalog and removes all catalog brains
for which a ``getObject`` call does not work.  In other words, it
removes brains that no longer belong to an actual object in the site.

Similar cleanups are done for the uid_catalog and the
reference_catalog.

The goal is to get rid of outdated brains that could otherwise cause
problems, for example during an upgrade to Plone 4.

``@@collective-catalogcleanup`` by default does a dry run, so it
only reports problems.  Call it with
``@@collective-catalogcleanup?dry_run=false`` to perform the actual cleanup.


Details
-------

So what does the catalog cleanup do?

- It removes stuff!  You *must* make a backup first!

- It handles these catalogs: ``portal_catalog``, ``uid_catalog``,
  ``reference_catalog``.

- For each catalog it reports the number of catalog brains it
  contains.

- It removes brains that have a UID of ``None``.

- It removes brains of which the object is broken.  This can happen
  when the object belongs to a package that is no longer available in
  the Plone Site.

- It removes brains of which the object cannot be found.

- It looks for non unique uids.  There can be some legitimate reasons
  why some brains may have the same UID, for example when they belong
  to comments: the UID is inherited from the parent object.  Those
  items are kept.  For other items we accept one object and we give
  the other objects a new UID.

- References between objects that no longer exist or are broken, will
  be removed.

- A simple report will be printed in the browser.  For one catalog it
  may look like this::

    Handling catalog portal_catalog.
    Brains in portal_catalog: 20148
    portal_catalog: removed 25 brains without UID.
    portal_catalog: removed 100 brains with status broken.
    portal_catalog: removed 5 brains with status notfound.
    portal_catalog: 249 non unique uids found.
    portal_catalog: 249 items given new unique uids.

- The instance log may contain more info, about individual items.


Alternatives
------------

- A clear and rebuild of the portal_catalog should have partially the
  same effect, but it will likely take a lot longer and it will not
  solve some of the problems mentioned above.  But this is definitely
  the most logical thing to try before giving
  ``collective.catalogcleanup`` a go.


Compatibility
-------------

I have tried this on Plone 3.3, Plone 4 and Plone 5.

It is automatically tested by Travis on Plone 4.1, 4.2, 4.3, 5.0, and 5.1.


Authors
-------

Maurits van Rees
