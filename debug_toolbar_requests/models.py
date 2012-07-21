from debug_toolbar_requests.utils import timedelta_with_milliseconds


class ResponseTimer(object):
    def __init__(self, start_time=None, end_time=None, response=None):
        self.start_time = start_time
        self.end_time = end_time
        self.response = response

    @property
    def duration(self):
        seconds = self.end_time - self.start_time
        return timedelta_with_milliseconds(seconds=seconds)

    @property
    def request(self):
        return self.response.request