import unittest2 as unittest

from Products.CMFCore.utils import getToolByName
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles

from collective.catalogcleanup.testing import (
    CATALOG_CLEANUP_INTEGRATION_TESTING,
    make_test_doc,
    )


class TestCatalogCleanup(unittest.TestCase):

    layer = CATALOG_CLEANUP_INTEGRATION_TESTING

    def _makeOne(self):
        return make_test_doc(self.layer['portal'])

    def testDeletedDocument(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ('Manager',))
        catalog = getToolByName(portal, 'portal_catalog')
        base_count = len(catalog.searchResults({}))
        doc = self._makeOne()
        self.assertEqual(len(catalog.searchResults({})), base_count + 1)
        # TODO: do some tricks so the item remains in the catalog
        # after it is removed.
