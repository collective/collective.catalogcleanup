# -*- coding: utf-8 -*-
"""Setup testing fixtures.

For Plone 5 we need to install plone.app.contenttypes.
"""
from plone.app.testing import FunctionalTesting
from plone.app.testing import PloneSandboxLayer
from zope.component import getMultiAdapter

import pkg_resources
import random
import string
import transaction


try:
    pkg_resources.get_distribution('plone.app.contenttypes')
except pkg_resources.DistributionNotFound:
    from plone.app.testing import PLONE_FIXTURE
else:
    from plone.app.contenttypes.testing import (
        PLONE_APP_CONTENTTYPES_FIXTURE as PLONE_FIXTURE)


class CatalogCleanupLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import collective.catalogcleanup
        self.loadZCML(package=collective.catalogcleanup)


CATALOG_CLEANUP_FIXTURE = CatalogCleanupLayer()
CATALOG_CLEANUP_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(CATALOG_CLEANUP_FIXTURE,), name='CatalogCleanup:Integration')

# A few helper functions.


def make_test_doc(portal):
    # new_id = portal.generateUniqueId('Document')
    # generateUniqueId no longer exists in all Plone versions.
    # Get a sufficiently unique id.
    new_id = "doc_{0}_{1}".format(
        "".join(random.sample(string.ascii_letters, 10)),
        "".join(random.sample(string.digits, 4)),
    )
    portal.invokeFactory('Document', new_id)
    doc = portal[new_id]
    doc.reindexObject()  # Might have already happened, but let's be sure.
    transaction.commit()
    return doc


def cleanup(portal, **kwargs):
    view = getMultiAdapter(
        (portal, portal.REQUEST), name='collective-catalogcleanup')
    return view(**kwargs)
