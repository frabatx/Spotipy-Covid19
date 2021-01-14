#!/usr/bin/python3

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import redis
import json
import psycopg2

#TODO imparare ad utilizzare la libreria psycopg2

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

    # Redis settings
    REDIS_HOST = "jupyter_redis"
    REDIS_PORT = 6379
    REDIS = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

    if(REDIS.ping()):
        # Itero su tutte le key di redis

        # Mi prendo la lista tracce di ogni playlist
        
        # Ricavo i dati delle canzoni

        # Mi connetto con postgres 

        # Inserisco i dati

        # Chiudo la connessione

if __name__ == "__main__":
    main()       