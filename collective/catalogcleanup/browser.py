import logging

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView

logger = logging.getLogger('collective.catalogcleanup')


class Cleanup(BrowserView):

    def __call__(self):
        self.messages = []
        self.msg("Starting catalog cleanup.")
        context = aq_inner(self.context)
        catalog_ids = ['portal_catalog', 'uid_catalog']
        for catalog_id in catalog_ids:
            self.msg("Handling catalog %s." % catalog_id)
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
            uncatalog = 0

            # Remove all brains without UID.
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

        return '\n'.join(self.messages)

    def msg(self, msg, level=logging.INFO):
        logger.log(level, msg)
        self.messages.append(msg)
