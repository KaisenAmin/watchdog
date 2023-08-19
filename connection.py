import psycopg2
import os

def reader_sql(sql_file_address):
    connection = psycopg2.connect(database="postgres", user="postgres", password="", host="127.0.0.1", port="5432")
    cursor = connection.cursor()
    rows = []
    with cursor as cur:
        cur.execute(open(sql_file_address, "r").read())
        cur.execute("select relname from pg_class where relkind='r' and relname !~ '^(pg_|sql_)';")
        tables = cur.fetchall()
        print(tables)

        for table in tables:
            cur.execute("SELECT * FROM " + table[0])
            rows.append(cur.fetchall() + [table[0]])
            sql = "COPY (SELECT * FROM user_details) TO STDOUT WITH CSV DELIMITER ';'"

            with open(os.path.dirname(__file__) + "\\table.csv", "a") as file:
                cur.copy_expert(sql, file)
        

    cursor.close()

    return rows

def sql_command_operation(command, sql_file_address, table_name):
    connection = psycopg2.connect(database="postgres", user="postgres", password="", host="127.0.0.1", port="5432")
    cursor = connection.cursor()
    with cursor as cur:
        cur.execute(open(sql_file_address, "r").read())
        cur.execute(command)
        cur.execute("SELECT * FROM " + table_name)
        rows = cur.fetchall()

    cur.close()

    return rows 

