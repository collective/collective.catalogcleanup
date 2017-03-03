# -*- coding: utf-8 -*-
"""Setup testing fixtures.

For Plone 5 we need to install plone.app.contenttypes.
"""
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from zope.component import getMultiAdapter

import pkg_resources


try:
    pkg_resources.get_distribution('plone.app.contenttypes')
except pkg_resources.DistributionNotFound:
    from plone.app.testing import PLONE_FIXTURE
else:
    from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE as PLONE_FIXTURE


class CatalogCleanupLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import collective.catalogcleanup
        self.loadZCML(package=collective.catalogcleanup)


CATALOG_CLEANUP_FIXTURE = CatalogCleanupLayer()
CATALOG_CLEANUP_INTEGRATION_TESTING = IntegrationTesting(
    bases=(CATALOG_CLEANUP_FIXTURE,), name='CatalogCleanup:Integration')

# A few helper functions.


def make_test_doc(portal):
    new_id = portal.generateUniqueId('Document')
    portal.invokeFactory('Document', new_id)
    doc = portal[new_id]
    doc.reindexObject()  # Might have already happened, but let's be sure.
    return doc


def cleanup(portal, **kwargs):
    view = getMultiAdapter(
        (portal, portal.REQUEST), name='collective-catalogcleanup')
    return view(**kwargs)
