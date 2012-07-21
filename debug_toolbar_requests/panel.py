from functools import partial
from pprint import pformat
from threading import local
import time

import requests
import requests.defaults

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
        self.thread_locals.response_timers[index].end_time = time.time()
        self.thread_locals.response_timers[index].response = response

    def receive_request(self, index, request):
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

            # TODO: this desperately needs tests
            # TODO: the browser replay functionality calls for extraction
            #   into its own module.
            def check_browser_compatible_headers(request):
                # We only have access to the resulting headers.  To verify
                # that the standard `requests` headers are being sent (which
                # themselves are browser-compatible), we check that the
                # headers sent are exactly equivalent to the default headers
                # sent by `requests`.

                # As an exception, we can also support a request if it only
                # adds a `Content-Type` header to the defaults sent by
                # `requests`.  However, we only support that header if it
                # contains one of the two encodings supported by HTML4.
                browser_supported_enctypes = (
                    # automatically sent by browser for every POST form
                    'application/x-www-form-urlencoded',

                    # sent by POST forms with `enctype` set to this
                    'multipart/form-data'
                )

                headers = request.headers.copy()  # don't corrupt the original
                header_name = 'Content-Type'
                content_type_header = headers.get(header_name, '')
                for enctype in browser_supported_enctypes:
                    # `startswith` is used because we might have a trailing
                    # semicolon: multipart/form-data; boundary=foobar
                    if content_type_header.startswith(enctype):
                        # TODO: need much safer parsing for this, find header lib
                        # TODO: also matches 'multipart/form-data-foo`
                        # TODO: messy
                        del headers[header_name]

                return headers == requests.defaults.defaults['base_headers']

            # The template displays a button in-browser allowing the user to
            # repeat the call.  Because this is done through a form, we cannot
            # allow this for some more complex requests.  Multiple conditions
            # are required to determine this, and they are kept in a dict
            # instead of a serial condition for traceability (for debugging,
            # or to show why request can't be displayed in the template).
            response_timer.request.browser_repeatability_conditions = dict(
                is_get_or_post = request.method in ('GET', 'POST'),

                # The browser can't send its own headers. We must ensure
                # that the headers sent only use headers that won't make
                # the meaning of the request semantically different, or
                # headers that we can support using forms (e.g. 'enctype'
                # can emulate some values of  the'Content-Type' header.)
                has_browser_compatible_headers = check_browser_compatible_headers(request),

                # Can't repeat GET requests with anything in the body.  The
                # browser will just tack it on to the URL instead of using
                # a GET body.  (Not that GET bodies have semantic meaning in
                # HTTP, but people still do strange things.)
                is_not_get_with_body = any((
                    (request.method == 'POST'),
                    ((not request.data) and (not request.files)),
                )),

                # In POST requests, you can send multipart and non-multipart
                # data separately.  Once browser forms have an encoding of
                # `multipart/form-data`, however, every parameter will be
                # sent as multipart data.
                is_not_data_and_files = not (request.data and request.files),

                # For POST bodies, the browser only do key-value bodies and
                # not other payloads, such as strings.
                is_key_value_body = isinstance(request.data, dict),
            )

            response_timer.request.is_browser_repeatable = all(
                response_timer.request.browser_repeatability_conditions.values()
            )

        self.record_stats({
            'response_timers': response_timers,
        })

