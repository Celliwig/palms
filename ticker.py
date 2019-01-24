import logging

class Ticker(object):
    TICKER_DELAY_START = 0
    TICKER_DELAY_END = 1

    def __init__(self, max_str_len = 20, max_iter = 2, action_delay = 5):
        self._maximum_string_length = max_str_len
        self._maximum_iterations = max_iter
        self._iteration_count = 0
        self._action_delay = action_delay
        self._action_count = 0
        self._string = ""
        self._string_position = 0
        self._state = Ticker.TICKER_DELAY_START

        self._logger = logging.getLogger(__name__)

    def setMaximumStrLen(self, max_str_len):
        self._maximum_string_length = max_str_len

    def setText(self, str):
        if not str == self._string:
            self._string = str
            self._string_position = 0
            self._iteration_count = 0
            self._action_count = 0
            self._state = Ticker.TICKER_DELAY_START

    def getText(self):
        if len(self._string) < self._maximum_string_length:
            return self._string
        else:
            return self._string[self._string_position: self._string_position + self._maximum_string_length]

    def pulse(self):
        if len(self._string) > self._maximum_string_length:
            if self._state == Ticker.TICKER_DELAY_START:
                if self._action_count >= self._action_delay:
                    if self._iteration_count >= self._maximum_iterations:
                        self._iteration_count = 0
                        if len(self._string[self._string_position:]) <= self._maximum_string_length:
                            self._action_count = 0
                            self._state = Ticker.TICKER_DELAY_END
                        else:
                            self._string_position += 1
                    else:
                        self._iteration_count += 1
                else:
                    self._logger.debug("Start delay: String position = " + str(self._string_position))
                    self._action_count += 1
            else:
                if self._action_count >= self._action_delay:
                    self._string_position = 0
                    self._iteration_count = 0
                    self._action_count = 0
                    self._state = Ticker.TICKER_DELAY_START
                else:
                    self._logger.debug("End delay: String position = " + str(self._string_position))
                    self._action_count += 1

    def reset(self):
        self._string_position = 0
        self._iteration_count = 0
        self._action_count == 0
        self._state = Ticker.TICKER_DELAY_START
