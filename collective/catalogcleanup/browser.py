import logging

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView

logger = logging.getLogger('collective.catalogcleanup')


class Cleanup(BrowserView):

    def __call__(self):
        self.messages = []
        context = aq_inner(self.context)
        pc = getToolByName(context, 'portal_catalog')
        uid_cat = getToolByName(context, 'uid_catalog')
        self.msg("Starting catalog cleanup.")
        # Using an empty filter to query the catalog will give a
        # DeprecationWarning and may not work on Zope 2.14 anymore.
        # We try to avoid this.
        standard_filter = {'path': '/'}
        self.msg("portal_catalog brains: %d" % len(pc(**standard_filter)))
        # Actually, the uid_catalog usually has no path index, so we
        # get the DeprecationWarning anyway.  So be it.
        self.msg("uid_catalog brains: %d" % len(uid_cat(**standard_filter)))
        uncatalog = 0
        # Remove all brains without UID.
        for catalog in pc, uid_cat:
            # For some reason we need several tries, because not all
            # are removed the first time around.
            tries = 0
            uid_filter = {'UID': None}
            while len(catalog(**uid_filter)) > 0:
                tries += 1
                self.msg("Try %d, total uncatalogs: %d" % (tries, uncatalog))
                for brain in catalog(**uid_filter):
                    catalog.uncatalog_object(brain.getPath())
                    uncatalog += 1
        self.msg("Removed %d catalog brains without UID." % uncatalog)
        return '\n'.join(self.messages)

    def msg(self, msg, level=logging.INFO):
        logger.log(level, msg)
        self.messages.append(msg)
