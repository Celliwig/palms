import logging

class config(object):

    def __init__(self, sqlc):
        self._sqlcon = sqlc
        self._key_store = {}

        self._logger = logging.getLogger(__name__)

        self.create_tables()
        self.load_config()

    def exists(self, key):
        if key in self._key_store:
            return True
        else:
            return False

    def get(self, key):
        return self._key_store[key]

    def set(self, key, value):
        self._key_store[key] = value

    def get_sqlcon(self):
        return self._sqlcon

#####################################################################################################
# SQL functions
    def load_config(self):
        self._logger.debug("Loading config")
        sql_csr = self._sqlcon.cursor()

        sql_strs = "select config_key, value from config_str order by config_key"
        sql_csr.execute(sql_strs)
        rows = sql_csr.fetchall()
        for tmp_config in rows:
            self._logger.debug("Loaded STR value: " + str(tmp_config[0]) + " - " + str(tmp_config[1]))
            self._key_store[tmp_config[0]] = str(tmp_config[1])

        sql_bools = "select config_key, value from config_bool order by config_key"
        sql_csr.execute(sql_bools)
        rows = sql_csr.fetchall()
        for tmp_config in rows:
            self._logger.debug("Loaded BOOL value: " + str(tmp_config[0]) + " - " + str(tmp_config[1]))
            if tmp_config[1] == "True":
                tmp_bool = True
            else:
                tmp_bool = False
            self._key_store[tmp_config[0]] = tmp_bool

        sql_ints = "select config_key, value from config_int order by config_key"
        sql_csr.execute(sql_ints)
        rows = sql_csr.fetchall()
        for tmp_config in rows:
            self._logger.debug("Loaded INT value: " + str(tmp_config[0]) + " - " + str(tmp_config[1]))
            self._key_store[tmp_config[0]] = int(tmp_config[1])

    def save_config(self):
        for tmp_key, tmp_val in self._key_store.items():
            if type(tmp_val) == str:
                self._save_str(tmp_key, tmp_val)
            if type(tmp_val) == int:
                self._save_int(tmp_key, tmp_val)
            if type(tmp_val) == bool:
                self._save_bool(tmp_key, tmp_val)

    def _save_str(self, key, value):
        sql_csr = self._sqlcon.cursor()
        sql_update = "REPLACE INTO config_str (config_key, value) VALUES (\"" + str(key) + "\", \"" + str(value) + "\")"
        sql_csr.execute(sql_update)
        self._sqlcon.commit()

    def _save_bool(self, key, value):
        sql_csr = self._sqlcon.cursor()
        sql_update = "REPLACE INTO config_bool (config_key, value) VALUES (\"" + str(key) + "\", \"" + str(value) + "\")"
        sql_csr.execute(sql_update)
        self._sqlcon.commit()

    def _save_int(self, key, value):
        sql_csr = self._sqlcon.cursor()
        sql_update = "REPLACE INTO config_int (config_key, value) VALUES (\"" + str(key) + "\", \"" + str(value) + "\")"
        sql_csr.execute(sql_update)
        self._sqlcon.commit()

    def create_tables(self):
        sql_csr = self._sqlcon.cursor()

        # Check if table exist
        sql_table_check = "SELECT name FROM sqlite_master WHERE type='table' AND name='config_str';"
        sql_csr.execute(sql_table_check)
        table_exists = sql_csr.fetchone()

        if table_exists is None:
            sql_table_create = "CREATE TABLE config_str (config_key VARCHAR UNIQUE, value VARCHAR)"
            sql_csr.execute(sql_table_create)
            self._sqlcon.commit()

        # Check if table exist
        sql_table_check = "SELECT name FROM sqlite_master WHERE type='table' AND name='config_bool';"
        sql_csr.execute(sql_table_check)
        table_exists = sql_csr.fetchone()

        if table_exists is None:
            sql_table_create = "CREATE TABLE config_bool (config_key VARCHAR UNIQUE, value BOOLEAN)"
            sql_csr.execute(sql_table_create)
            self._sqlcon.commit()

        # Check if table exist
        sql_table_check = "SELECT name FROM sqlite_master WHERE type='table' AND name='config_int';"
        sql_csr.execute(sql_table_check)
        table_exists = sql_csr.fetchone()

        if table_exists is None:
            sql_table_create = "CREATE TABLE config_int (config_key VARCHAR UNIQUE, value INTEGER)"
            sql_csr.execute(sql_table_create)
            self._sqlcon.commit()

