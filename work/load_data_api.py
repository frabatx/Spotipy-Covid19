#!/usr/bin/python3

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import redis
import json
import psycopg2

def main():
    """
    The function takes the data collected in redis, increases it and inserts it into a postgres table. 
    The data thus obtained are complete and are available for ETL operations.
    """

    # Spotify settings
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
        client_id='118aa19f2b66476fbc062f0ac146d8b5',
        client_secret='7ca95a3159ab4391bee70f70d47a9271'
    ))
    # Postgres settings
    conn = psycopg2.connect(
        host = "postgres",
        port = "5432",
        dbname = "postgres",
        user = "postgres",
        password = "postgres1234",
    )
    # Redis settings
    REDIS_HOST = "jupyter_redis"
    REDIS_PORT = 6379
    REDIS = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

    # Spotify data
    search_results = []
    playlists = sp.search(q='covid', type='playlist', limit=50,offset=0)['playlists']

    print('- Load Playlists from search query')
    # Load Playlists from search query
    while playlists:
        try:
            for i, playlist in enumerate(playlists['items']):
                search_results.append(playlist['id'])
                print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['id'],  playlist['name']))
            if playlists['next']:
                playlists = sp.next(playlists)['playlists'] # Get next playlist given a page result
            else:
                playlists = None
        except Exception as e:
            playlists = None
            print('Done')

    print('- Load tracks into postgres')
    ## Load information into Postgres
    counter = 0
    final_informations = []
    columns = 'id_playlist,name_playlist,id_track,name_track,timestamp,danceability,energy,key,loudness,mode,speechiness,acousticness,instrumentalness,liveness,valence,tempo,duration_ms,time_signature'

    for playlist_id in search_results:
        try:
            playlist_complete = sp.playlist(playlist_id)
            tracks = playlist_complete['tracks']
            while tracks:
                for track in tracks['items']:
                    audio_features = sp.audio_features(track['track']['id'])[0]
                    # Open cursor
                    cur = conn.cursor()
                    # Insert
                    cur.execute(f'insert into spotify_details ({columns}) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                                (
                                    playlist_complete['id'],
                                    playlist_complete['name'],
                                    track['track']['id'],
                                    track['track']['name'],
                                    track['added_at'],
                                    audio_features['danceability'],
                                    audio_features['energy'],
                                    audio_features['key'],
                                    audio_features['loudness'],
                                    audio_features['mode'],
                                    audio_features['speechiness'],
                                    audio_features['acousticness'],
                                    audio_features['instrumentalness'],
                                    audio_features['liveness'],
                                    audio_features['valence'],
                                    audio_features['tempo'],
                                    audio_features['duration_ms'],
                                    audio_features['time_signature']
                                ))
                    # Commit the transition
                    conn.commit()
                    # Close cursor
                    cur.close()
                if tracks['next']:
                        tracks = sp.next(tracks) # Get next playlist given a page result
                else:
                    tracks = None
            print(f'Done playlist: {counter} of {len(search_results)}')
            counter += 1
        except Exception as e:
            print(e)
            counter += 1
    # Close connection
    conn.close()

    print('Done! All data are in your primary db!')
    print('- Load playlist id into redis')

    # Load data from python to redis-server
    for playlist_id in search_results:
        REDIS.set(playlist_id, 1)
    print("- Keys confirmed: {} on {}".format(len(REDIS.keys("*")), len(search_results)))

if __name__ == "__main__":
    main()    