import psycopg

class Database:

    def __init__(self, config):
        self.config = config
        self.conn = None
        self.cursor = None


    def execute_and_fetch_all(self, query, params=None):
        self.conn = psycopg.connect(**self.config)
        self.cursor = self.conn.cursor()  

        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

        return self.cursor.fetchall()


    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
