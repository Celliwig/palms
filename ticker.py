class Ticker(object):
    def __init__(self, max_str_len = 20, max_iter = 7):
        self._iteration_count = 0
        self._maximum_iterations = max_iter
        self._maximum_string_length = max_str_len
        self._string = ""
        self._string_position = 0

    def setMaximumStrLen(self, max_str_len):
        self._maximum_string_length = max_str_len

    def setText(self, str):
        if not str == self._string:
            self._string = str
            self._string_position = 0
            self._iteration_count = 0

    def getText(self):
        if len(self._string) < self._maximum_string_length:
            return self._string
        else:
            return self._string[self._string_position: self._string_position + self._maximum_string_length]

    def pulse(self):
        if len(self._string) > self._maximum_string_length:
            if self._iteration_count >= self._maximum_iterations:
                self._string_position += 1
                self._iteration_count = 0
                if len(self._string[self._string_position:]) < self._maximum_string_length:
                    self._string_position = 0

            self._iteration_count += 1

    def reset(self):
        self._string_position = 0
        self._iteration_count = 0
