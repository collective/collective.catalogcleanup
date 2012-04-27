from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from zope.component import getMultiAdapter
from zope.configuration import xmlconfig


class CatalogCleanupLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import collective.catalogcleanup
        xmlconfig.file('configure.zcml', collective.catalogcleanup,
                      context=configurationContext)

CATALOG_CLEANUP_FIXTURE = CatalogCleanupLayer()
CATALOG_CLEANUP_INTEGRATION_TESTING = IntegrationTesting(
    bases=(CATALOG_CLEANUP_FIXTURE,), name="CatalogCleanup:Integration")

# A few helper functions.


def make_test_doc(portal):
    new_id = portal.generateUniqueId('Document')
    portal.invokeFactory('Document', new_id)
    doc = portal[new_id]
    doc.reindexObject()  # Might have already happened, but let's be sure.
    return doc


def cleanup(portal, **kwargs):
    view = getMultiAdapter((portal, portal.REQUEST),
                            name='collective-catalogcleanup')
    return view(**kwargs)
