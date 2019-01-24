from .ticker import Ticker

class Station(object):
    def __init__(self, name, url, selected = False):
        self._name = name
        self._url = url
        self._selected = selected
        self._ticker = Ticker(8)                  # 8 characters is the default string length for the tickers
        self._ticker.setText(self._name)

    def get_name(self):
        return self._name

    def get_initials(self):
        initials = ''.join(tmp_name[0].upper() for tmp_name in self._name.split())
        return initials

    def set_name(self, new_name):
        self._name = new_name
        self._ticker.setText(self._name)

    def get_url(self):
        return self._url

    def set_url(self, new_url):
        self._url = new_url

    def is_selected(self):
        return self._selected

    def set_selected(self, select):
        self._selected = select

    def set_ticker_length(self, tlen):
        self._ticker.setMaximumStrLen(tlen)

    def pulse(self):
        if self.is_selected():
            self._ticker.pulse()
        else:
            self._ticker.reset()

    def get_ticker_txt(self):
        return self._ticker.getText()

