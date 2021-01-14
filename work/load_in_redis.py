#!/usr/bin/python3

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import redis
import json


def main():
    """
    The function takes care of uploading part of the data involved by the API to the container used as a data lake. 
    The container manages a version of redis-server that allows you to save the downloaded playlists in key-value. 
    For convenience the keys are ids ranging from 1 to the maximum number of playlists found (approximately 1930).
    Structure of dictionary saved in redis:
    {
        playlist_id: "145qfqq4f4q44514qfq" 
        tracks:[
            {
                track_id: "rl3q2nf1342534t"
                available_market: "AL, IT, ...."
            },
        .
        .
        ]
    }
    """
    
    # Spotify settings
    sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
        client_id='118aa19f2b66476fbc062f0ac146d8b5',
        client_secret='7ca95a3159ab4391bee70f70d47a9271'
    ))

    # Redis settings
    REDIS_HOST = "jupyter_redis"
    REDIS_PORT = 6379
    REDIS = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

    # Load data if Redis is connected
    if(REDIS.ping()):
        print("1/5 - Connected to the redis-server at {}:{}".format(REDIS_HOST,REDIS_PORT))
        # Spotify data
        search_results = []
        playlists = sp.search(q='covid', type='playlist', limit=50,offset=0)['playlists']

        print('2/5 - Load Playlists from search query')
        # Load Playlists from search query
        while playlists:
            try:
                for i, playlist in enumerate(playlists['items']):
                    search_results.append(playlist)
                    print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'],  playlist['name']))
                if playlists['next']:
                    playlists = sp.next(playlists)['playlists']
                else:
                    playlists = None
            except Exception as e:
                playlists = None
                print('Done')

        print('3/5 - Load tracks id and available_market')
        # Load tracks id and available_market
        final_informations = []
        for i,playlist in enumerate(search_results):
            try:
                tracks = sp.playlist(playlist['uri'])['tracks']['items']
                track_information = []
                for track in tracks:
                    track_information.append({
                        "track_id": track['track']['id'],
                        "available_markets" : ','.join(track['track']['available_markets']),
                    })
                final_informations.append({
                    "playlist_id": playlist['id'],
                    "tracks": json.dumps(track_information)
                })
                print('Done {} of {}'.format(i, len(search_results)))
            except Exception as e:
                print('Problem {} \n at item {} of {}'.format(e, i, len(search_results)))

        print("4/5 - Load data from python to redis-server")
        # Load data from python to redis-server
        for i,playlist in enumerate(final_informations):
            REDIS.set(str(i),json.dumps(playlist))
        print("5/5 - Keys confirmed: {} on {}".format(len(REDIS.keys("*")), len(final_informations)

    else:
        print("Not connected to the redis-server at {}:{}".format(REDIS_HOST,REDIS_PORT))

        
if __name__ == "__main__":
    main()        
        
        
        
        
        
        
        
        
        
        
