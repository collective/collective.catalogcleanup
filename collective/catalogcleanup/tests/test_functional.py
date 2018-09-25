# -*- coding: utf-8 -*-
from collective.catalogcleanup.testing import CATALOG_CLEANUP_FUNCTIONAL_TESTING  # noqa: E501
from collective.catalogcleanup.testing import cleanup
from collective.catalogcleanup.testing import make_test_doc
from collective.noindexing import patches
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from Products.CMFCore.utils import getToolByName

import transaction
import unittest


class TestCatalogCleanup(unittest.TestCase):

    layer = CATALOG_CLEANUP_FUNCTIONAL_TESTING

    def _makeOne(self):
        return make_test_doc(self.layer['portal'])

    def _delete_object_only(self, doc):
        # Delete object without removing it from the catalog.
        portal = self.layer['portal']
        patches.apply()
        portal._delObject(doc.getId())
        patches.unapply()
        transaction.commit()

    def testNormalDeletedDocument(self):
        # No tricks here, just testing some assumptions.
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ('Manager',))
        catalog = getToolByName(portal, 'portal_catalog')
        base_count = len(catalog.searchResults({}))
        doc = self._makeOne()
        self.assertEqual(len(catalog.searchResults({})), base_count + 1)
        portal._delObject(doc.getId())
        transaction.commit()
        self.assertEqual(len(catalog.searchResults({})), base_count)
        cleanup(portal)
        self.assertEqual(len(catalog.searchResults({})), base_count)

    def testDeletedDocumentWithDryRun(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ('Manager',))
        catalog = getToolByName(portal, 'portal_catalog')
        base_count = len(catalog.searchResults({}))
        doc = self._makeOne()
        self.assertEqual(len(catalog.searchResults({})), base_count + 1)
        # This call makes sure the item remains in the catalog after
        # it is removed:
        self._delete_object_only(doc)
        self.assertEqual(len(catalog.searchResults({})), base_count + 1)
        # By default dry_run is selected, so nothing is changed.
        cleanup(portal)
        self.assertEqual(len(catalog.searchResults({})), base_count + 1)
        # None of these variants should have any lasting effect.
        cleanup(portal, dry_run=True)
        self.assertEqual(len(catalog.searchResults({})), base_count + 1)
        cleanup(portal, dry_run=0)
        self.assertEqual(len(catalog.searchResults({})), base_count + 1)
        cleanup(portal, dry_run=None)
        self.assertEqual(len(catalog.searchResults({})), base_count + 1)

    def testDeletedDocumentForReal(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ('Manager',))
        catalog = getToolByName(portal, 'portal_catalog')
        base_count = len(catalog.searchResults({}))
        doc = self._makeOne()
        self.assertEqual(len(catalog.searchResults({})), base_count + 1)
        # This call makes sure the item remains in the catalog after
        # it is removed:
        self._delete_object_only(doc)
        self.assertEqual(len(catalog.searchResults({})), base_count + 1)
        cleanup(portal, dry_run='false')
        self.assertEqual(len(catalog.searchResults({})), base_count)
