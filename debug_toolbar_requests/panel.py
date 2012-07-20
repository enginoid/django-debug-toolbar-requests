from threading import local

import requests

from django.utils.translation import ugettext_lazy as _, ngettext

from debug_toolbar.panels import DebugPanel


class RequestsDebugPanel(DebugPanel):
    """
    A panel to display HTTP requests made by the `requests` library.
    """

    name = 'Requests'
    template = 'debug_toolbar/panels/requests.html'
    has_content = True

    def set_response(self, response):
        self.thread_locals.responses.append(response)

    def __init__(self, *args, **kwargs):
        super(RequestsDebugPanel, self).__init__(*args, **kwargs)

        self.thread_locals = local()
        self.thread_locals.responses = []
        debug_panel = self

        class TrackedRequest(requests.models.Request):
            def __init__(self, *args, **kwargs):
                super(TrackedRequest, self).__init__(*args, **kwargs)
                self.register_hook('response', debug_panel.set_response)

        # TODO: in the interest of forward-compatibility, can this be done
        #   more safely dynamically; e.g. by looking for use of the `Request`
        #   object in all package modules?
        requests.models.Request = TrackedRequest
        requests.Request = TrackedRequest
        requests.sessions.Request = TrackedRequest

    def nav_title(self):
        return _('HTTP Requests')

    def title(self):
        return _('HTTP Requests')

    def nav_subtitle(self):
        request_count = len(self.thread_locals.responses)
        return ngettext("%d request", "%d requests", request_count) % request_count

    def url(self):
        return ''

    def process_response(self, request, response):
        self.record_stats({
            'responses': self.thread_locals.responses,
        })

