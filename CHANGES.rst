Changelog
=========


2.0.0 (2023-11-30)
------------------

- No longer accept non-unique inherited UIDs.
  This was needed for Discussion Items, but not anymore.
  [maurits]

- Fixed setting new uuids for Dexterity content and Discussion Items.
  This part of version 1.x seems to only have worked for Archetypes.
  [maurits]

- Removed support for checking the ``reference_catalog`` and ``uid_catalog``.
  These are Archetypes-only.
  [maurits]

- Drop support for Python 2, Plone 5.1 and earlier.
  Only Plone 5.2 and 6 are supported, on Python 3.
  [maurits]


1.11.2 (2021-08-24)
-------------------

- Do not complain about paths being different when the brain path is relative.
  Happens in old uid_catalog and reference_catalog.
  [maurits]


1.11.1 (2021-08-13)
-------------------

- Again fixed error sorting UIDs when one of them is None.  [maurits]


1.11.0 (2021-07-29)
-------------------

- Report and remove brains that have a wrong path.
  These are brains where an object is found at the given path,
  but the actual path of this object is different.
  This can be caused by acquisition:
  /Plone/folder/folder has gotten in the catalog,
  but really only /Plone/folder exists.
  [maurits]

- Fixed error sorting UIDs when one of them is None.  [maurits]


1.10.0 (2020-02-08)
-------------------

- To get all brains, use ``catalog.getAllBrains`` when available.
  This is available in ``Products.ZCatalog`` 2.13.30+ or 4.1+.
  We fall back to ``unrestrictedSearchResults`` and otherwise just call the catalog.
  Fixes `issue 16 <https://github.com/collective/collective.catalogcleanup/issues/16>`_.
  [maurits]

- `Bug 22 <https://github.com/collective/collective.catalogcleanup/issues/22>`_:
  Fix startup error when Archetypes is missing.
  Fix other Plone 5.2 and Python 3 errors.
  Should be compatible with Plone 4.3, 5.1 and 5.2 now.  [maurits]


1.9.0 (2018-09-25)
------------------

- Catch TypeError when getting object for brain.
  Can happen when an object that used to be referenceable is no longer referenceable.
  Fixes `issue #19 <https://github.com/collective/collective.catalogcleanup/issues/19>`_.
  [maurits]

- Disable CSRF protection.
  Fixes `issue #17 <https://github.com/collective/collective.catalogcleanup/issues/17>`_.
  [maurits]

- Abort any transaction changes in dry run mode.
  There should not be any changes here anyway, but this makes sure.
  [maurits]


1.8.0 (2018-04-30)
------------------

- No longer test on Plone 4.1 and 4.2 and on Python 2.6.  [maurits]

- Catch ``KeyError`` and ``AttributeError`` for ``getPath`` in more cases.
  Fixes `issue #14 <https://github.com/collective/collective.catalogcleanup/issues/14>`_.
  [maurits]


1.7.2 (2017-09-18)
------------------

- Added traceback info to help in case of problems.  [maurits]


1.7.1 (2017-03-07)
------------------

- Tested for compatibility on Plone 4.0 through 5.1.  [hvelarde]

- Ignore non existing catalogs.  Plone 5 does not always have
  a ``uid_catalog`` or ``reference_catalog``.
  Fixes `issue #5 <https://github.com/collective/collective.catalogcleanup/issues/5>`_.
  [maurits]


1.7 (2017-03-03)
----------------

- Don't look for non unique ids in the ``reference_catalog``.
  It looks like it is normal there.  At least, on one Plone 4.3 site
  the code keeps creating several new uids every time I run it.
  [maurits]

- Don't complain about brains in ``reference_catalog`` where ``getObject`` returns None.
  This happens for content without apparent problems.  [maurits]


1.6 (2016-08-23)
----------------

- Do not complain about brains in uid_catalog that are references.
  When their path points to ``...at_references/<uid of brain>`` then
  this is normal.  I started wondering about a site that had more than
  20 thousand problems reported this way.  [maurits]


1.5 (2015-07-31)
----------------

- Remove all items that have the ``portal_factory`` folder in their
  path.
  [maurits]


1.4 (2014-05-12)
----------------

- Catch KeyErrors when getting the path of a brain.
  [maurits]


1.3 (2013-09-02)
----------------

- Give less confusing message for comments that inherit the UID of
  their parent.  It sounded too much like an error.
  [maurits]


1.2 (2012-06-04)
----------------

- Improved the cleanup of non unique uids.
  [maurits]


1.1 (2012-05-14)
----------------

- When doing an reindexObject, only reindex the UID.
  [maurits]


1.0 (2012-04-27)
----------------

- Initial release
  [maurits]
