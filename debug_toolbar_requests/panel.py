from functools import partial
from pprint import pformat
from threading import local
import time

import requests

from django.utils.translation import ugettext_lazy as _, ngettext
from django.template.defaultfilters import truncatechars

from debug_toolbar.panels import DebugPanel

# Retain, because it won't be retrievable after monkey-patching.
from debug_toolbar_requests.models import ResponseTimer

original_thread_class = requests.models.Request

class RequestsDebugPanel(DebugPanel):
    """
    A panel to display HTTP requests made by the `requests` library.
    """

    name = 'Requests'
    template = 'debug_toolbar/panels/requests.html'
    has_content = True

    def receive_response(self, index, response):
        print 'response', index
        self.thread_locals.response_timers[index].end_time = time.time()
        self.thread_locals.response_timers[index].response = response

    def receive_request(self, index, request):
        print 'request', index
        self.thread_locals.response_timers[index].start_time = time.time()

    def __init__(self, *args, **kwargs):
        super(RequestsDebugPanel, self).__init__(*args, **kwargs)

        self.thread_locals = local()
        self.thread_locals.response_timers = []
        debug_panel = self

        class TrackedRequest(original_thread_class):
            def __init__(self, *args, **kwargs):
                super(TrackedRequest, self).__init__(*args, **kwargs)

                response_timer = ResponseTimer()
                next_index = len(debug_panel.thread_locals.response_timers)
                debug_panel.thread_locals.response_timers.append(response_timer)

                self.register_hook('pre_request',
                    hook=partial(debug_panel.receive_request, next_index))
                self.register_hook('response',
                    hook=partial(debug_panel.receive_response, next_index))

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
        request_count = len(self.thread_locals.response_timers)
        return ngettext("%d request", "%d requests", request_count) % request_count

    def url(self):
        return ''

    def process_response(self, _request, _response):  # unused params
        response_timers = self.thread_locals.response_timers
        for response_timer in response_timers:
            # Tack template-specific information on to the response timer
            # objects to save some boilerplate in the template.
            response = response_timer.response
            response_timer.response.template_items = (
                (_("URL"), response.url),
                (_("Status"), u"{code} {reason}".format(
                    code=response.status_code, reason=response.reason)),
                (_("Headers"), pformat(response.headers)),
                (_("Body"), truncatechars(response.text, 1024)),
            )

            request = response_timer.request
            response_timer.request.template_items = (
                (_("URL"), request.url),
                (_("Method"), request.method),
                (_("Headers"), pformat(request.headers)),
                (_("Parameters"), request.params),

                # TODO: it would be nice to get the actual raw body
                (_("Data"), request.data),
                (_("Files"), request.files),
            )

        self.record_stats({
            'response_timers': response_timers,
        })

