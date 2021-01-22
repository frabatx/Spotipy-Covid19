#!/usr/bin/python3

import pandas as pd
import redis
import psycopg2

def main():
    """
    Prende i file in csv e li carica sul database principale
    """
    # Cleaning data
    print('- Preparing data for uploading into postgres db')
    df = pd.read_csv('data/entire_db.csv')
    df.name_playlist = df.name_playlist.apply(lambda x : str(x).replace(',', ';').replace('\'', ''))
    df.name_playlist = df.name_playlist.apply(lambda x : str(x).strip())
    df.name_track = df.name_track.apply(lambda x : str(x).replace(',', ';').replace('\'', ''))
    df.name_track = df.name_track.apply(lambda x : str(x).strip())
    df = df.fillna("")
    df.to_csv('data/clean_data.csv', index=False)

    # Postgres settings
    conn = psycopg2.connect(
        host = "postgres",
        port = "5432",
        dbname = "postgres",
        user = "postgres",
        password = "postgres1234"
    )

    # Redis settings
    REDIS_HOST = "jupyter_redis"
    REDIS_PORT = 6379
    REDIS = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

    conn.autocommit = True
    cursor = conn.cursor()

    print('- Importing data ...')
    # import data from csv file
    with open('data/clean_data.csv', 'r') as f:
        next(f)  # Skip the header row.
        try:
            cursor.copy_from(
                f,
                'spotify_details',
                sep=',',
                columns=('id_playlist','name_playlist','id_track','name_track','timestamp','danceability','energy','key','loudness','mode','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms','time_signature')
            )
            conn.commit()
        except Exception as e:
            print(e)

    # confirm by selecting record
    command = 'SELECT COUNT(*) FROM spotify_details;'
    cursor.execute(command)
    recs = cursor.fetchall()
    print('- Uploaded row: %d' % recs[0])

    if REDIS.ping():
        # Load data into Redis
        print('- Load data into Redis')
        for id_playlist in list(df['id_playlist']):
            REDIS.set(id_playlist, 1)
        print("- Confirmed playlist: {}".format(len(REDIS.keys("*"))))
    

if __name__ == "__main__":
    main()    