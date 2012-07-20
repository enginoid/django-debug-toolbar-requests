from datetime import timedelta
from functools import partial
from threading import local
import time

import requests

from django.utils.translation import ugettext_lazy as _, ngettext

from debug_toolbar.panels import DebugPanel

class timedelta(timedelta):
    def milliseconds(self):
        return int(round(self.microseconds / 1000.0))

class ResponseTimer(object):
    def __init__(self, start_time=None, end_time=None, response=None):
        self.start_time = start_time
        self.end_time = end_time
        self.response = response

    @property
    def duration(self):
        seconds = self.end_time - self.start_time
        return timedelta(seconds=seconds)

# Retain, because it won't be retrievable after monkey-patching.
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

    def process_response(self, request, response):
        self.record_stats({
            'response_timers': self.thread_locals.response_timers,
        })

