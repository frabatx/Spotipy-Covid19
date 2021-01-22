#!/usr/bin/python3
import pandas as pd
import psycopg2
import os.path

def main():
    """
    Prende i file in csv e li carica sul database di backup.
    Se il file entire_db non esiste allora ne faccio uno dai dati della mia tabella originale
    Se il file clean_data non esiste allora ne faccio uno dai dati creati sopra
    """

    # Check file entire_db
    if(not(os.path.exists('data/entire_db.csv'))):
        print('- File entire_db not exist. Creating it from postgres db')
        # Postgres settings
        conn = psycopg2.connect(
            host = "postgres",
            port = "5432",
            dbname = "postgres",
            user = "postgres",
            password = "postgres1234"
        )
        cursor = conn.cursor()

        cursor.execute('select * from spotify_details')
        rows = cursor.fetchall()
        # Creo file csv
        columns = 'id_playlist,name_playlist,id_track,name_track,timestamp,danceability,energy,key,loudness,mode,speechiness,acousticness,instrumentalness,liveness,valence,tempo,duration_ms,time_signature'
        df = pd.DataFrame(rows, columns=columns.split(','))
        df.to_csv('data/entire_db.csv', index=False)

    # Check file clean_data
    if(not(os.path.exists('data/clean_data.csv'))):
        print('- File clean_data not exist')
        # Cleaning data
        print('- Preparing data for uploading into backup db')
        df = pd.read_csv('data/entire_db.csv')
        df.name_playlist = df.name_playlist.apply(lambda x : str(x).replace(',', ';').replace('\'', ''))
        df.name_playlist = df.name_playlist.apply(lambda x : str(x).strip())
        df.name_track = df.name_track.apply(lambda x : str(x).replace(',', ';').replace('\'', ''))
        df.name_track = df.name_track.apply(lambda x : str(x).strip())
        df = df.fillna("")
        df.to_csv('data/clean_data.csv', index=False)


    # Connetto al secondo postgres di backup
    # Postgres settings
    conn2 = psycopg2.connect(
        host = "postgres_backup",
        port = "5432",
        dbname = "postgres",
        user = "postgres",
        password = "postgres1234"
    )
    conn2.autocommit = True
    cursor2 = conn2.cursor()

    print('- Importing data ...')
    # import data from csv file
    with open('data/clean_data.csv', 'r') as f:
        next(f)  # Skip the header row.
        try:
            cursor2.copy_from(
                f,
                'spotify_details',
                sep=',',
                columns=('id_playlist','name_playlist','id_track','name_track','timestamp','danceability','energy','key','loudness','mode','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms','time_signature')
            )
            conn2.commit()
        except Exception as e:
            print(e)

    # confirm by selecting record
    command = 'SELECT COUNT(*) FROM spotify_details;'
    cursor2.execute(command)
    recs = cursor2.fetchall()
    print('- Uploaded row: %d into backup db' % recs[0])
    

if __name__ == "__main__":
    main()    