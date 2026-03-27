import psycopg

class Database:

    def __init__(self, config):
        self.config = config
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self)
        self.conn = psycopg.connect(**self.config)
        self.cursor = self.conn.cursor()

    def execute_and_fetch_all(self, query, params=None):
        if self.conn is None or self.cursor is None:
            self.connect()

        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

        return self.cursor.fetchall()


    def close(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None
