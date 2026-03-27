import psycopg

class Database:

    def __init__(self, config): #initializes the Database object
        self.config = config
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self) #establishes a new connection
        self.conn = psycopg.connect(**self.config)
        self.cursor = self.conn.cursor()

    def execute_and_fetch_all(self, query, params=None): #Executes the query and returns all results
        if self.conn is None or self.cursor is None:
            self.connect()

        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

        return self.cursor.fetchall()


    def close(self): #Closes the cursor and the connection
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None
