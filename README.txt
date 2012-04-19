.. contents::


Documentation
=============


Usage and goal
--------------

Add collective.catalogcleanup to the eggs in your buildout (and to zcml on
Plone 3.2 or earlier).  This makes a browser view available on the
Plone Site root: ``@@collective-catalogcleanup``.

This goes through the portal_catalog and removes all catalog brains
for which a ``getObject`` call does not work.  In other words, it
removes brains that no longer belong to an actual object in the site.

The goal is to get rid of outdated brains that could otherwise cause
problems, for example during an upgrade to Plone 4.


Notes
-----

- No code has been written yet. :-)

- We may want to do similar cleanups for the uid_catalog and maybe the
  reference_catalog.


Alternatives
------------

- A clear and rebuild of the portal_catalog should have the same
  effect, but it will likely take a lot longer.


Authors
-------

Maurits van Rees
