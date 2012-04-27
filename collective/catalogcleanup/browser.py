from itertools import groupby
from operator import attrgetter
import logging

from Acquisition import aq_inner, aq_base
from OFS.Uninstalled import BrokenClass
from Products.Archetypes.config import UUID_ATTR
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
            self.msg("Handling catalog %s.", catalog_id)
            self.report(catalog_id)
            self.remove_without_uids(catalog_id)
            self.remove_without_object(catalog_id)
            if catalog_id == 'reference_catalog':
                self.check_references()
            self.non_unique_uids(catalog_id)
        self.msg("Done with catalog cleanup.")
        return '\n'.join(self.messages)

    def msg(self, msg, *args, **kwargs):
        msg = msg % args
        level = kwargs.get('level', logging.INFO)
        logger.log(level, msg)
        self.messages.append(msg)

    def report(self, catalog_id):
        """Report about this catalog.
        """
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        size = len(catalog)
        self.msg("Brains in %s: %d", catalog_id, size)
        # Getting all brains from the catalog may give a different
        # result for some reason.  Using an empty filter to query the
        # catalog will give a DeprecationWarning and may not work on
        # Zope 2.14 anymore.  We try to avoid this.  Also, we want
        # brains in all languages in case of LinguaPlone.
        standard_filter = {'Language': 'all'}
        # Actually, the uid_catalog usually has no path index, so
        # we get the DeprecationWarning anyway.  So be it.
        alternative_size = len(catalog(**standard_filter))
        if alternative_size != size:
            self.msg("Brains in %s using standard filter is different: %d",
                     catalog_id, alternative_size, level=logging.WARN)

    def remove_without_uids(self, catalog_id):
        """Remove all brains without UID.
        """
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        uncatalog = 0
        uid_filter = {'UID': None, 'Language': 'all'}
        # We need to get the complete list instead of a lazy
        # mapping, otherwise iterating misses half of the brains
        # and we would need to try again.
        brains = list(catalog(**uid_filter))
        for brain in brains:
            catalog.uncatalog_object(brain.getPath())
            uncatalog += 1
        self.msg("%s: removed %d brains without UID.",
            catalog_id, uncatalog)

    def remove_without_object(self, catalog_id):
        """Remove all brains without object.
        """
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        status = {}
        standard_filter = {'Language': 'all'}
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
            self.msg("%s: removed %d brains with status %s.", catalog_id,
                     value, error)
        if not status:
            self.msg("%s: removed no brains in object check.", catalog_id)

    def check_references(self, catalog_id='reference_catalog'):
        """Remove all brains without proper references.
        """
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        status = {}
        standard_filter = {'Language': 'all'}
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
            self.msg("%s: removed %d brains with status %s for source or "
                     "target object.", catalog_id, value, error)
        if not status:
            self.msg("%s: removed no brains in reference check.", catalog_id)

    def non_unique_uids(self, catalog_id):
        """Report and fix non unique uids.

        A UID that is not unique is wrong.  And the UUIDIndex
        migration that is done when migrating from Plone 3 to Plone 4
        breaks in that case.  A UID might be inherited from a parent
        object; in that case the migration will not break, so we won't
        try to fix it.
        """
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        if 'UID' not in catalog.indexes():
            self.msg("%s: no UID index.", catalog_id)
            return
        non_unique = 0
        changed = 0
        standard_filter = {'Language': 'all'}
        brains = list(catalog(**standard_filter))
        uid_getter = attrgetter('UID')
        brains = sorted(brains, key=uid_getter)
        for uid, group in groupby(brains, uid_getter):
            items = list(group)
            if len(items) == 1:
                continue
            non_unique += 1
            logger.info("%s: uid %s: %d items.", catalog_id, uid, len(items))
            logger.info("%s: uid %s is kept for %s", catalog_id, uid,
                        items[0].getPath())
            # XXX Sort by lenghth of path
            for item in items[1:]:
                obj = item.getObject()
                old_uid = getattr(aq_base(obj), UUID_ATTR, None)
                if old_uid is None:
                    # Comments inherit the UID of their parent, at
                    # least in Plone 3.  This should be fine.
                    logger.info("%s: uid %s is inherited by %s.",
                        catalog_id, old_uid, item.getPath())
                    continue
                # Taken from Archetypes.  Might not work for
                # dexterity.  Might not be needed for dexterity.
                # Should not be needed for Archetypes either, really.
                delattr(aq_base(obj), UUID_ATTR)
                # Create a new UID.
                obj._register()
                obj._updateCatalog(context)
                logger.info("%s: new uid %s for %s (was %s)." % (
                    catalog_id, obj.UID(), item.getPath(), old_uid))
                changed += 1

        self.msg("%s: %d non unique uids found.", catalog_id, non_unique)
        self.msg("%s: %d items given new unique uids.", catalog_id, changed)

    def get_object_or_status(self, brain, getter='getObject'):
        try:
            # Usually: brain.getObject()
            obj = getattr(brain, getter)()
        except (ConflictError, KeyboardInterrupt):
            raise
        except (NotFound, AttributeError, KeyError):
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
