from Products.Five import BrowserView


class Patch(BrowserView):

    def __call__(self):
        return u"TODO: collective.catalogcleanup not functioning yet."
