# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from itertools import groupby
from OFS.Uninstalled import BrokenClass
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from zExceptions import NotFound
from ZODB.POSException import ConflictError
from zope.interface import alsoProvides

import logging
import transaction


try:
    from Products.Archetypes.config import UUID_ATTR
    from Products.Archetypes.ReferenceEngine import Reference
except ImportError:
    # Plone 5.2 on Python 3 never has Archetypes.
    UUID_ATTR = "_at_uid"
    Reference = None

try:
    from plone.protect.interfaces import IDisableCSRFProtection
except ImportError:
    IDisableCSRFProtection = None

logger = logging.getLogger('collective.catalogcleanup')

try:
    basestring
except NameError:
    # Python 3
    basestring = (str, bytes)


def safe_path(item):
    try:
        return item.getPath()
    except (KeyError, AttributeError):
        return 'notfound'


def path_len(item):
    try:
        return len(item.getPath())
    except (KeyError, AttributeError):
        # For our use case (sort by path length and keep the item
        # with the shortest path), it is best to return a high number
        # in case of problems.
        return 9999


def get_all_brains(catalog):
    # Return a full list, not a generator,
    # because we may delete brains from the catalog while iterating over them.
    try:
        # This needs Products.ZCatalog 2.13.30+ or 4.1+.
        return list(catalog.getAllBrains())
    except AttributeError:
        try:
            # Most other catalogs
            return list(catalog.unrestrictedSearchResults())
        except AttributeError:
            # uid_catalog
            return list(catalog())


def uid_getter(item):
    """Get UID from item (brain).

    operator.attrgetter('UID') should be fine,
    but this fails for sorting when there one of the UIDs is None:

    '<' not supported between instances of 'NoneType' and 'str'

    """
    return getattr(item, "UID", "") or ""


class Cleanup(BrowserView):

    def __call__(self, dry_run=None):
        self.messages = []
        self.msg('Starting catalog cleanup.')
        # Determine whether this is a dry run or not.  We are very
        # explicit and only accept the boolean value False and the
        # string 'false' (in lower, upper or mixed case).  All other
        # values are considered True.
        if dry_run is None:
            dry_run = self.request.get('dry_run')
        if isinstance(dry_run, basestring):
            dry_run = dry_run.lower()
            if dry_run == 'false':
                dry_run = False
        if dry_run is False:
            self.dry_run = False
            self.newline()
            self.msg('NO dry_run SELECTED. CHANGES ARE PERMANENT.')
            self.newline()
        else:
            self.dry_run = True
            self.newline()
            self.msg('dry_run SELECTED, SO ONLY REPORTING. To make changes '
                     'permanent, add "?dry_run=false" to the URL.')
            self.newline()
        context = aq_inner(self.context)
        catalog_ids = ['portal_catalog', 'uid_catalog', 'reference_catalog']
        for catalog_id in catalog_ids:
            problems = 0
            self.newline()
            if getToolByName(context, catalog_id, None) is None:
                self.msg(
                    'Ignored non existing catalog {0}.'.format(catalog_id))
                continue
            self.msg('Handling catalog {0}.'.format(catalog_id))
            problems += self.report(catalog_id)
            problems += self.remove_without_uids(catalog_id)
            problems += self.remove_without_object(catalog_id)
            if catalog_id == 'reference_catalog':
                problems += self.check_references()
            else:
                # Non unique ids seem persistent in the reference catalog.
                # Running the code several times keeps creating new uids.
                problems += self.non_unique_uids(catalog_id)
            self.msg('{0}: total problems: {1:d}'.format(catalog_id, problems))

        self.newline()
        self.msg('Done with catalog cleanup.')
        if self.dry_run:
            # We should not have made any changes, but let's back out any
            # inadvertent changes anyway.
            transaction.abort()
            self.msg('Dry run selected: aborted any transaction changes.')
        elif IDisableCSRFProtection is not None:
            # Avoid csrf protection errors, as we have no form.
            alsoProvides(self.request, IDisableCSRFProtection)

        return '\n'.join(self.messages)

    def msg(self, msg, **kwargs):
        level = kwargs.get('level', logging.INFO)
        logger.log(level, msg)
        self.messages.append(msg)

    def newline(self):
        self.messages.append('')

    def report(self, catalog_id):
        """Report about this catalog.
        """
        __traceback_info__ = catalog_id
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        # This uses a special method to get the length:
        size = len(catalog)
        self.msg('Brains in {0}: {1:d}'.format(catalog_id, size))
        # Getting all brains from the catalog may give a different
        # result for various reasons: multilingual language filter,
        # publication date in future, catalog not returning any results
        # when called without a query, even with unrestrictedSearchResults.
        # So check that we can get all brains, as we will use this in all checks.
        alternative_size = len(get_all_brains(catalog))
        if alternative_size != size:
            self.msg(
                'Brains in {0} using getAllBrains is different: {1:d}'
                .format(catalog_id, alternative_size), level=logging.WARN)
            return 1
        return 0

    def remove_without_uids(self, catalog_id):
        """Remove all brains without UID.
        """
        __traceback_info__ = catalog_id
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        uncatalog = 0
        # We need to get the complete list instead of a lazy
        # mapping, otherwise iterating misses half of the brains
        # and we would need to try again.
        try:
            brains = list(catalog.unrestrictedSearchResults(UID=None))
        except AttributeError:
            # uid_catalog
            brains = list(catalog(UID=None))
        for brain in brains:
            if not self.dry_run:
                try:
                    path = brain.getPath()
                except (KeyError, AttributeError):
                    continue
                catalog.uncatalog_object(path)
            uncatalog += 1
        self.msg(
            '{0}: removed {1:d} brains without UID.'
            .format(catalog_id, uncatalog))
        return uncatalog

    def remove_without_object(self, catalog_id):
        """Remove all brains without object.
        """
        __traceback_info__ = catalog_id
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        status = {}
        brains = get_all_brains(catalog)
        for brain in brains:
            obj = self.get_object_or_status(brain)
            if not isinstance(obj, basestring):
                continue
            if not self.dry_run:
                try:
                    path = brain.getPath()
                except (KeyError, AttributeError):
                    continue
                catalog.uncatalog_object(path)
            # We have an error.
            count = status.get(obj, 0)
            status[obj] = count + 1

        for error, value in status.items():
            self.msg(
                '{0}: removed {1:d} brains with status {2}.'
                .format(catalog_id, value, error))
        if not status:
            self.msg(
                '{0}: removed no brains in object check.'.format(catalog_id))
        return sum(status.values())

    def check_references(self, catalog_id='reference_catalog'):
        """Remove all brains without proper references.
        """
        __traceback_info__ = catalog_id
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        status = {}
        ref_errors = 0
        brains = get_all_brains(catalog)
        getters = ('getSourceObject', 'getTargetObject')
        for brain in brains:
            ref = self.get_object_or_status(brain)
            if isinstance(ref, basestring):
                # We have an error. This means a dry_run is being
                # done, as otherwise this brain should have been
                # cleaned up by one of the other methods already.
                ref_errors += 1
                continue
            if ref is None:
                # No error, but no object either.  This can happen
                # for references.  Let's accept it.
                continue
            for getter in getters:
                obj = self.get_object_or_status(ref, getter)
                if not isinstance(obj, basestring):
                    continue
                # We have an error.  Remove the reference brain.
                count = status.get(obj, 0)
                status[obj] = count + 1
                if not self.dry_run:
                    try:
                        path = brain.getPath()
                    except (KeyError, AttributeError):
                        continue
                    catalog.uncatalog_object(path)
                # No need for the second getter if the first already
                # fails.
                break

        if ref_errors:
            self.msg(
                '{0}: problem getting {1:d} references.'
                .format(catalog_id, ref_errors))
        for error, value in status.items():
            self.msg(
                '{0}: removed {1:d} brains with status {2} for source or '
                'target object.'.format(catalog_id, value, error))
        if not status:
            self.msg(
                '{0}: removed no brains in reference check.'
                .format(catalog_id))
        return sum(status.values()) + ref_errors

    def non_unique_uids(self, catalog_id):
        """Report and fix non unique uids.

        A UID that is not unique is wrong.  And the UUIDIndex
        migration that is done when migrating from Plone 3 to Plone 4
        breaks in that case.  A UID might be inherited from a parent
        object; in that case the migration will not break, so we won't
        try to fix it.
        """
        __traceback_info__ = catalog_id
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        if 'UID' not in catalog.indexes():
            self.msg('{0}: no UID index.'.format(catalog_id))
            return
        non_unique = 0
        changed = 0
        obj_errors = 0
        brains = get_all_brains(catalog)
        brains = sorted(brains, key=uid_getter)
        for uid, group in groupby(brains, uid_getter):
            items = list(group)
            if len(items) == 1:
                continue
            non_unique += 1
            logger.info('%s: uid %s: %d items.', catalog_id, uid, len(items))
            # Sort by length of path.
            items = sorted(items, key=path_len)
            logger.info('%s: uid %s is kept for %s', catalog_id, uid,
                        safe_path(items[0]))
            for item in items[1:]:
                obj = self.get_object_or_status(item)
                if isinstance(obj, basestring):
                    # This is an error. This should fix itself when no
                    # dry_run has been selected.
                    obj_errors += 1
                    continue
                if obj is None:
                    # No error, but no object either.  This happens in the
                    # uid_catalog for references.
                    continue
                old_uid = getattr(aq_base(obj), UUID_ATTR, None)
                if old_uid is None:
                    # Comments inherit the UID of their parent, at
                    # least in Plone 3.  This should be fine.
                    # But a reindex is good, as we may have given the
                    # parent a fresh UID a moment ago.
                    if not self.dry_run:
                        obj.reindexObject(idxs=['UID'])
                        new_uid = obj.UID()
                        logger.info('%s: uid %s is inherited by %s.',
                                    catalog_id, new_uid, safe_path(item))
                    continue
                # We need a change.
                changed += 1
                # Taken from Archetypes.  Might not work for
                # dexterity.  Might not be needed for dexterity.
                # Should not be needed for Archetypes either, really.
                if not self.dry_run:
                    delattr(aq_base(obj), UUID_ATTR)
                    # Create a new UID.
                    try:
                        obj._register()
                    except AttributeError:
                        # Might happen for a Reference.
                        if Reference is not None and isinstance(obj, Reference):
                            logger.warn('%s: removing reference %s with '
                                        'duplicate uid %s.', catalog_id,
                                        safe_path(item), old_uid)
                            del aq_parent(obj)[obj.getId()]
                            continue
                    obj._updateCatalog(context)
                    obj.reindexObject(idxs=['UID'])
                    logger.info('{0}: new uid {1} for {2} (was {3}).'.format(
                        catalog_id, obj.UID(), safe_path(item), old_uid))

        if obj_errors:
            self.msg(
                '{0}: problem getting {1:d} objects.'
                .format(catalog_id, obj_errors))
        self.msg(
            '{0}: {1:d} non unique uids found.'.format(catalog_id, non_unique))
        if self.dry_run:
            self.msg(
                '{0}: {1:d} items need new unique uids.'
                .format(catalog_id, changed))
        else:
            self.msg(
                '{0}: {1:d} items given new unique uids.'
                .format(catalog_id, changed))
        return obj_errors + changed

    def get_object_or_status(self, brain, getter='getObject'):
        __traceback_info__ = [brain, getter]
        try:
            brain_id = brain.getPath()
        except KeyError:
            return 'notfound'
        except AttributeError:
            # Probably not a real brain, but a reference.
            brain_id = brain.getId()
        else:
            if 'portal_factory' in brain_id.split('/'):
                return 'factory'
        __traceback_info__.append(brain_id)
        try:
            # Usually: brain.getObject()
            obj = getattr(brain, getter)()
        except (ConflictError, KeyboardInterrupt):
            raise
        except (NotFound, AttributeError, KeyError):
            return 'notfound'
        except TypeError:
            logger.warning(
                'TypeError, returning notfound for brain at %s.',
                brain_id, exc_info=1)
            return 'notfound'
        except:  # noqa: B901
            logger.exception('Cannot handle brain at %s.', brain_id)
            raise
        if obj is None:
            # This might be a problem, but it also happens when the brain is
            # for a reference.
            if ('at_references' in brain_id and
                    brain_id.endswith('at_references/' + brain.UID)):
                return
            return 'none'
        if isinstance(obj, BrokenClass):
            logger.warning('Broken %s: %s', brain.portal_type, brain_id)
            return 'broken'
        actual_path = "/".join(obj.getPhysicalPath())
        if brain_id != actual_path:
            # Likely acquisition:
            # /Plone/folder/folder has gotten in the catalog,
            # but really only /Plone/folder exists.
            logger.warning('Wrong path: getting %s leads to %s', brain_id, actual_path)
            return 'wrong_path'
        return obj
