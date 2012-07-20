from datetime import timedelta

class timedelta_with_milliseconds(timedelta):
    def milliseconds(self):
        return int(round(self.microseconds / 1000.0))