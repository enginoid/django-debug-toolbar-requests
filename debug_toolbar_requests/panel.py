from django.utils.translation import ugettext_lazy as _

from debug_toolbar.panels import DebugPanel

# TODO: monkey patch `requests` and collect all requests made to thread locals (will it work?)

class RequestsDebugPanel(DebugPanel):
    """
    A panel to display HTTP requests made by the `requests` library.
    """

    name = 'Requests'
    template = 'debug_toolbar/panels/requests.html'
    has_content = True

    def nav_title(self):
        return _('HTTP Requests')

    def title(self):
        return _('HTTP Requests')

    def url(self):
        return ''