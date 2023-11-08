from Acquisition import aq_inner
from itertools import groupby
from OFS.Uninstalled import BrokenClass
from plone.protect.interfaces import IDisableCSRFProtection
from plone.uuid.interfaces import ATTRIBUTE_NAME
from plone.uuid.interfaces import IUUID
from plone.uuid.interfaces import IUUIDGenerator
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from zExceptions import NotFound
from ZODB.POSException import ConflictError
from zope.component import queryUtility
from zope.interface import alsoProvides

import logging
import transaction


logger = logging.getLogger("collective.catalogcleanup")


def safe_path(item):
    try:
        return item.getPath()
    except (KeyError, AttributeError):
        return "notfound"


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
    return list(catalog.getAllBrains())


def uid_getter(brain):
    """Get UID from brain.

    operator.attrgetter('UID') should be fine,
    but this fails for sorting when there one of the UIDs is None:

    '<' not supported between instances of 'NoneType' and 'str'

    """
    return getattr(brain, "UID", "") or ""


class Cleanup(BrowserView):
    def __call__(self, dry_run=None):
        # Avoid csrf protection errors, as we have no form.
        alsoProvides(self.request, IDisableCSRFProtection)
        self.messages = []
        self.msg("Starting catalog cleanup.")
        # Determine whether this is a dry run or not.  We are very
        # explicit and only accept the boolean value False and the
        # string 'false' (in lower, upper or mixed case).  All other
        # values are considered True.
        if dry_run is None:
            dry_run = self.request.get("dry_run")
        if isinstance(dry_run, str):
            dry_run = dry_run.lower()
            if dry_run == "false":
                dry_run = False
        if dry_run is False:
            self.dry_run = False
            self.newline()
            self.msg("NO dry_run SELECTED. CHANGES ARE PERMANENT.")
            self.newline()
        else:
            self.dry_run = True
            self.newline()
            self.msg(
                "dry_run SELECTED, SO ONLY REPORTING. To make changes "
                'permanent, add "?dry_run=false" to the URL.'
            )
            self.newline()
        context = aq_inner(self.context)
        catalog_ids = ["portal_catalog"]
        for catalog_id in catalog_ids:
            problems = 0
            self.newline()
            if getToolByName(context, catalog_id, None) is None:
                self.msg(f"Ignored non existing catalog {catalog_id}.")
                continue
            self.msg(f"Handling catalog {catalog_id}.")
            problems += self.report(catalog_id)
            problems += self.remove_without_uids(catalog_id)
            problems += self.remove_without_object(catalog_id)
            problems += self.non_unique_uids(catalog_id)
            self.msg(f"{catalog_id}: total problems: {problems:d}")

        self.newline()
        self.msg("Done with catalog cleanup.")
        if self.dry_run:
            # We should not have made any changes, but let's back out any
            # inadvertent changes anyway.
            transaction.abort()
            self.msg("Dry run selected: aborted any transaction changes.")

        return "\n".join(self.messages)

    def msg(self, msg, **kwargs):
        level = kwargs.get("level", logging.INFO)
        logger.log(level, msg)
        self.messages.append(msg)

    def newline(self):
        self.messages.append("")

    def report(self, catalog_id):
        """Report about this catalog."""
        __traceback_info__ = catalog_id
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        # This uses a special method to get the length:
        size = len(catalog)
        self.msg(f"Brains in {catalog_id}: {size:d}")
        # Getting all brains from the catalog may give a different
        # result for various reasons: multilingual language filter,
        # publication date in future, catalog not returning any results
        # when called without a query, even with unrestrictedSearchResults.
        # So check that we can get all brains, as we will use this in all checks.
        alternative_size = len(get_all_brains(catalog))
        if alternative_size != size:
            self.msg(
                "Brains in {} using getAllBrains is different: {:d}".format(
                    catalog_id, alternative_size
                ),
                level=logging.WARN,
            )
            return 1
        return 0

    def remove_without_uids(self, catalog_id):
        """Remove all brains without UID."""
        __traceback_info__ = catalog_id
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        uncatalog = 0
        # We need to get the complete list instead of a lazy
        # mapping, otherwise iterating misses half of the brains
        # and we would need to try again.
        brains = list(catalog.unrestrictedSearchResults(UID=None))
        for brain in brains:
            if not self.dry_run:
                try:
                    path = brain.getPath()
                except (KeyError, AttributeError):
                    continue
                catalog.uncatalog_object(path)
            uncatalog += 1
        self.msg(f"{catalog_id}: removed {uncatalog:d} brains without UID.")
        return uncatalog

    def remove_without_object(self, catalog_id):
        """Remove all brains without object."""
        __traceback_info__ = catalog_id
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        status = {}
        brains = get_all_brains(catalog)
        for brain in brains:
            obj = self.get_object_or_status(brain)
            if not isinstance(obj, str):
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
                "{}: removed {:d} brains with status {}.".format(
                    catalog_id, value, error
                )
            )
        if not status:
            self.msg(f"{catalog_id}: removed no brains in object check.")
        return sum(status.values())

    def non_unique_uids(self, catalog_id):
        """Report and fix non unique uids.

        A UID that is not unique is wrong.  And the UUIDIndex
        migration that is done when migrating from Plone 3 to Plone 4
        breaks in that case.
        """
        __traceback_info__ = catalog_id
        context = aq_inner(self.context)
        catalog = getToolByName(context, catalog_id)
        if "UID" not in catalog.indexes():
            self.msg(f"{catalog_id}: no UID index.")
            return
        non_unique = 0
        changed = 0
        obj_errors = 0
        # Get a uuid generator and try it out.
        uuid_generator = queryUtility(IUUIDGenerator)
        try_uuid = uuid_generator() if uuid_generator is not None else None
        if not try_uuid:
            self.msg("Could not get a working uuid generator utility.")
            return
        brains = get_all_brains(catalog)
        brains = sorted(brains, key=uid_getter)
        for uid, group in groupby(brains, uid_getter):
            items = list(group)
            if len(items) == 1:
                continue
            non_unique += 1
            logger.info("%s: uid %s: %d items.", catalog_id, uid, len(items))
            # Sort by length of path.
            items = sorted(items, key=path_len)
            logger.info(
                "%s: uid %s is kept for %s", catalog_id, uid, safe_path(items[0])
            )
            for item in items[1:]:
                obj = self.get_object_or_status(item)
                if isinstance(obj, str):
                    # This is an error. This should fix itself when no
                    # dry_run has been selected.
                    obj_errors += 1
                    continue
                if obj is None:
                    # No error, but no object either.
                    continue
                old_uid = IUUID(obj, None)
                if old_uid is None:
                    # Comments used to inherit the UID of their parent, at
                    # least in Plone 3.  This is no longer the case in Plone 5.2/6.0.
                    # This may have already changed since 4.1 with the introduction of
                    # plone.app.discussion.  We used to accept this and do a reindex
                    # of the UID, as we may have given the parent a fresh UID a moment
                    # ago.  But now we warn, and create a new uuid.
                    logger.info(
                        "%s: %s has no uid of its own. Will give it a fresh one.",
                        catalog_id,
                        safe_path(item),
                    )
                # We need a change.
                changed += 1
                if not self.dry_run:
                    uuid = uuid_generator()
                    setattr(obj, ATTRIBUTE_NAME, uuid)
                    obj.reindexObject(idxs=["UID"])
                    logger.info(
                        "{}: new uid {} for {} (was {}).".format(
                            catalog_id, obj.UID(), safe_path(item), old_uid
                        )
                    )

        if obj_errors:
            self.msg(f"{catalog_id}: problem getting {obj_errors:d} objects.")
        self.msg(f"{catalog_id}: {non_unique:d} non unique uids found.")
        if self.dry_run:
            self.msg(f"{catalog_id}: {changed:d} items need new unique uids.")
        else:
            self.msg(f"{catalog_id}: {changed:d} items given new unique uids.")
        return obj_errors + changed

    def get_object_or_status(self, brain, getter="getObject"):
        __traceback_info__ = [brain, getter]
        try:
            brain_id = brain.getPath()
        except (AttributeError, KeyError):
            return "notfound"
        else:
            if "portal_factory" in brain_id.split("/"):
                return "factory"
        __traceback_info__.append(brain_id)
        try:
            # Usually: brain.getObject()
            obj = getattr(brain, getter)()
        except (ConflictError, KeyboardInterrupt):
            raise
        except (NotFound, AttributeError, KeyError):
            return "notfound"
        except TypeError:
            logger.warning(
                "TypeError, returning notfound for brain at %s.", brain_id, exc_info=1
            )
            return "notfound"
        except Exception:
            logger.exception("Cannot handle brain at %s.", brain_id)
            raise
        if obj is None:
            return "none"
        if isinstance(obj, BrokenClass):
            logger.warning("Broken %s: %s", brain.portal_type, brain_id)
            return "broken"
        if brain_id.startswith("/"):
            actual_path = "/".join(obj.getPhysicalPath())
            if brain_id != actual_path:
                # Likely acquisition:
                # /Plone/folder/folder has gotten in the catalog,
                # but really only /Plone/folder exists.
                logger.warning(
                    "Wrong path: getting %s leads to %s", brain_id, actual_path
                )
                return "wrong_path"
        return obj
