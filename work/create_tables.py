#!/usr/bin/python3

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import redis
import json
import psycopg2

def main():
    """
    Create table spotify_details
    """

    # Postgres settings
    conn = psycopg2.connect(
        host = "postgres",
        port = "5432",
        dbname = "postgres",
        user = "postgres",
        password = "postgres1234",
    )
    conn.autocommit = True
    cur = conn.cursor()

    # execute sql script
    sql_file = open('create_tabel_postgres.sql', 'r')
    sqlFile = sql_file.read()
    sql_file.close()
    sqlCommands = sqlFile.split(';')
    for command in sqlCommands:
        print(command)
        if command.strip() != '':
            try:
                cur.execute(command)
                conn.commit()
            except Exception as e:
                print(e)

    cur.close()
    conn.close()

    # Postgres settings
    conn2 = psycopg2.connect(
        host = "postgres_backup",
        port = "5432",
        dbname = "postgres",
        user = "postgres",
        password = "postgres1234",
    )
    conn2.autocommit = True
    cur2 = conn2.cursor()

    # execute sql script
    sql_file = open('create_tabel_postgres.sql', 'r')
    sqlFile = sql_file.read()
    sql_file.close()
    sqlCommands = sqlFile.split(';')
    for command in sqlCommands:
        print(command)
        if command.strip() != '':
            try:
                cur2.execute(command)
                conn2.commit()
            except Exception as e:
                print(e)

    cur2.close()
    conn2.close()

    # Postgres settings
    conn3 = psycopg2.connect(
        host = "postgres_dwh",
        port = "5432",
        dbname = "dati_finali",
        user = "postgres",
        password = "postgres1234",
    )
    conn3.autocommit = True
    cur3 = conn3.cursor()

    # execute sql script
    sql_file = open('create_tabel_dwh.sql', 'r')
    sqlFile = sql_file.read()
    sql_file.close()
    sqlCommands = sqlFile.split(';')
    for command in sqlCommands:
        print(command)
        if command.strip() != '':
            try:
                cur3.execute(command)
                conn3.commit()
            except Exception as e:
                print(e)

    cur3.close()
    conn3.close()

if __name__ == "__main__":
    main()    