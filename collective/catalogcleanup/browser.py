import logging

from Acquisition import aq_inner
from OFS.Uninstalled import BrokenClass
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from ZODB.POSException import ConflictError
from zExceptions import NotFound

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
            self.remove_without_object(catalog_id)
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

    def remove_without_object(self, catalog_id):
        """Remove all brains without object.
        """
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        removed_error = 0
        removed_none = 0
        standard_filter = {'path': '/'}
        brains = list(catalog(**standard_filter))
        for brain in brains:
            try:
                obj = brain.getObject()
            except (ConflictError, KeyboardInterrupt):
                raise
            except (NotFound, AttributeError):
                catalog.uncatalog_object(brain.getPath())
                removed_error += 1
                continue
            except:
                logger.exception("Cannot handle brain at %s." %
                                 brain.getPath())
                raise
            if obj is None:
                catalog.uncatalog_object(brain.getPath())
                removed_none += 1
                continue
            elif isinstance(obj, BrokenClass):
                logger.warn("Broken: %s" % brain.getPath())
                catalog.uncatalog_object(brain.getPath())
                continue

        self.msg("Removed %d brains from %s where object is not found." % (
            removed_error, catalog_id))
        self.msg("Removed %d brains from %s where object is None." % (
            removed_none, catalog_id))
