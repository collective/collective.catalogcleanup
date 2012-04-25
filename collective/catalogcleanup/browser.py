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
        catalog_ids = ['portal_catalog', 'uid_catalog', 'reference_catalog']
        for catalog_id in catalog_ids:
            self.msg("Handling catalog %s." % catalog_id)
            self.report(catalog_id)
            self.remove_without_uids(catalog_id)
            self.remove_without_object(catalog_id)
        if 'reference_catalog' in catalog_ids:
            self.check_references()
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
        status = {}
        standard_filter = {'path': '/'}
        brains = list(catalog(**standard_filter))
        for brain in brains:
            obj = self.get_object_or_status(brain)
            if not isinstance(obj, basestring):
                continue
            # We have an error.
            count = status.get(obj, 0)
            status[obj] = count + 1
            catalog.uncatalog_object(brain.getPath())

        for error, value in status.items():
            self.msg("Removed %d brains from %s with status %s." % (
                value, catalog_id, error))

    def check_references(self, catalog_id='reference_catalog'):
        """Remove all brains without proper references.
        """
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        status = {}
        standard_filter = {'path': '/'}
        brains = list(catalog(**standard_filter))
        getters = ('getSourceObject', 'getTargetObject')
        for brain in brains:
            # This should always work, as cleanup should already have
            # been done:
            ref = brain.getObject()
            for getter in getters:
                obj = self.get_object_or_status(ref, getter)
                if not isinstance(obj, basestring):
                    continue
                # We have an error.  Remove the reference brain.
                count = status.get(obj, 0)
                status[obj] = count + 1
                catalog.uncatalog_object(brain.getPath())
                # No need for the second getter if the first already
                # fails.
                break

        for error, value in status.items():
            self.msg("Removed %d brains from %s with status %s for source or "
                     "target object." % (value, catalog_id, error))

    def get_object_or_status(self, brain, getter='getObject'):
        try:
            # Usually: brain.getObject()
            obj = getattr(brain, getter)()
        except (ConflictError, KeyboardInterrupt):
            raise
        except (NotFound, AttributeError):
            return 'notfound'
        except:
            logger.exception("Cannot handle brain at %s." %
                             brain.getPath())
            raise
        if obj is None:
            return 'none'
        if isinstance(obj, BrokenClass):
            logger.warn("Broken %s: %s" % (
                brain.portal_type, brain.getPath()))
            return 'broken'
        return obj
