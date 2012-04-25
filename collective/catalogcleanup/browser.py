import logging

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView

logger = logging.getLogger('collective.catalogcleanup')


class Cleanup(BrowserView):

    def __call__(self):
        self.messages = []
        self.msg("Starting catalog cleanup.")
        catalog_ids = ['portal_catalog', 'uid_catalog']
        for catalog_id in catalog_ids:
            self.msg("Handling catalog %s." % catalog_id)
            self.report(catalog_id)
            self.remove_without_uids(catalog_id)
        self.msg("Done with catalog cleanup.")
        return '\n'.join(self.messages)

    def msg(self, msg, level=logging.INFO):
        logger.log(level, msg)
        self.messages.append(msg)

    def report(self, catalog_id):
        """Report about this catalog.
        """
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        size = len(catalog)
        self.msg("Brains in %s: %d" % (catalog_id, size))
        # Getting all brains from the catalog may give a different
        # result for some reason.  Using an empty filter to query
        # the catalog will give a DeprecationWarning and may not
        # work on Zope 2.14 anymore.  We try to avoid this.
        standard_filter = {'path': '/'}
        # Actually, the uid_catalog usually has no path index, so
        # we get the DeprecationWarning anyway.  So be it.
        alternative_size = len(catalog(**standard_filter))
        if alternative_size != size:
            self.msg("Brains in %s using standard filter is different: %d"
                     % (catalog_id, alternative_size), level=logging.WARN)

    def remove_without_uids(self, catalog_id):
        """Remove all brains without UID.
        """
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        uncatalog = 0
        uid_filter = {'UID': None}
        # We need to get the complete list instead of a lazy
        # mapping, otherwise iterating misses half of the brains
        # and we would need to try again.
        brains = list(catalog(**uid_filter))
        for brain in brains:
            catalog.uncatalog_object(brain.getPath())
            uncatalog += 1
        self.msg("Removed %d brains without UID from %s." % (
            uncatalog, catalog_id))
