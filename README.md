# Covid19 analysis on Spotify

A seguire elencheró le tecnologie utilizzate per la creazione di questo Big Data System che permettono l'analisi dei dati estratti dall'api ufficiale di spotify attraverso una libreria che permette l'interazione con essa.

## Docker

In accordo con Docker la loro tecnologia permette gli sviluppatori di essere liberi di costruire, gestire e rendere sicure applicazioni senza preoccuparsi della infrastruttura dove sono installate. Per questo progetto sto utilizzando una versione di Docker Desktop per linux.

La versione corrente include orchestratori kubernetes e Swarm per gestire e deployare container. Ho scelto di utilizzare Swarm per questo progetto. Secondo docker il cluster management é innestato nel Docker Engine costruito utilizzando swarmkit. Swarmkit é un progetto separato che implementa un layer che orchestra Docker ed é utilizzato direttamente all'interno dello stesso.

Per questo progetto Docker é perfetto per simulare un sistema scalabile orizzontalmente. Basta aggiungere un conteiner e collegarlo alla stessa rete per avere un elemento in piú da poter utilizzare. 

## Inizializzazione e comandi principali
Utilizzo il comando docker pull per scaricare in locale le immagini dei container che serviranno per il progetto direttamente da Docker Hub. 

```bash
docker pull jupyter/all-spark-notebook:latest
docker pull postgres:12-alpine
docker pull adminer:latest
docker pull redis:alpine
```



Queste sono le immagini che andranno a comporre il cluster di container attraverso Docker Swarm. 

Il file che contiene tutte le configurazioni e che permette di buildare l'intero cluster é il file stack.yml composto come segue: 

```yaml
# docker stack deploy -c stack.yml jupyter
# optional pgadmin container
version: "3.7"
networks:
  demo-net:
services:
  spark:
    image: jupyter/all-spark-notebook:latest
    ports:
    - "8888:8888/tcp"
    - "4040:4040/tcp"
    networks:
    - demo-net
    working_dir: /home/$USER/work
    environment:
      CHOWN_HOME: "yes"
      GRANT_SUDO: "yes"
      NB_UID: 1000
      NB_GID: 100
      NB_USER: $USER
      NB_GROUP: staff
    user: root
    deploy:
     replicas: 1
     restart_policy:
       condition: on-failure
    volumes:
    - $PWD/work:/home/$USER/work
  postgres:
    image: postgres:12-alpine
    environment:
      POSTGRES_USERNAME: postgres
      POSTGRES_PASSWORD: postgres1234
      POSTGRES_DB: bakery
    ports:
    - "5432:5432/tcp"
    networks:
    - demo-net
    volumes:
    - $HOME/data/postgres:/var/lib/postgresql/data
    deploy:
     restart_policy:
       condition: on-failure
  adminer:
    image: adminer:latest
    ports:
    - "8080:8080/tcp"
    networks:
    - demo-net
    deploy:
     restart_policy:
       condition: on-failure
  redis:
    image: redis:alpine
    environment:
      # ALLOW_EMPTY_PASSWORD is recommended only for development.
      - ALLOW_EMPTY_PASSWORD=yes
      - REDIS_DISABLE_COMMANDS=FLUSHDB,FLUSHALL
    ports:
      - '6379:6379/tcp'
    networks:
      - demo-net
    volumes:
      - $HOME/data/redis:/var/lib/redis
      - $PWD/redis.conf:/usr/local/etc/redis/redis.conf
  # pgadmin:
  #   image: dpage/pgadmin4:latest
  #   environment:
  #     PGADMIN_DEFAULT_EMAIL: user@domain.com
  #     PGADMIN_DEFAULT_PASSWORD: 5up3rS3cr3t!
  #   ports:
  #     - "8180:80/tcp"
  #   networks:
  #     - demo-net
  #   deploy:
  #     restart_policy:
  #       condition: on-failure

```



Il comando per eseguire la build dell'infrastruttura é: 

```
docker stack deploy -c stack.yml jupyter
```

Dove jupyter é il nome dello stack che abbiamo creato dal file stack.yml

Qursto crea un network di container che interagiscono tra loro.

Per controllare che sia andato a buon fine  é necessario fare un check dei container con il comando 

```
docker stack ps jupyter
```

Per poter accedere all'interfaccia di jupyter é necessario controllare i log del container a cui vogliamo accedere, nel nostro caso il nome del container é jupyter_spark (nome stack + _ + nome container) con il comando log

```
docker logs $(docker ps | grep jupyter_spark | awk '{print $NF}')
```

Se é andato tutto bene ed il container é online allora é possibile avere un tocken di accesso simile al seguente: 

```
http://127.0.0.1:8888/?token=f78cbe...
```

## Struttura cartelle

Ora la cartella a cui si ha accesso é quella specificata nel file stack.yml, la cartella /work che fará da ponte tra il container e i file in locale.

Questa cartella sará permanente ed ogni modifica fatta ai file verrá salvata anche in locale, anche al riavvio dello stack.

É importante tenerlo a mente perché i dati all'interno del container sono volatili, allo spegnimento questi vengono cancellati, tranne quelli presenti, nel nostro caso nella  cartella work.

Questa working-directory é settata alla riga 14 del file yml e ripresa alla riga 27. Nella riga 14 si fa riferimento alla working directory di jupyter, nella riga 27 si fa riferimento alla cartella utilizzata per lo storage, nel nostro caso sempre la stessa.

Un'altra cartella importante é la cartella data. Infatti prima di inizializzare il progetto sará necessario creare questa cartella in locale nella posizione indicata dal comando 

```
mkdir -p ~/data/postgres
mkdir -p ~/data/redis
```

##  Bootstrap environment

Nel progetto é incluso un bootstrap script. Lo script ha lo scopo di:  

* aggiornare l'ambiente
* installare htop per la verifica delle performance (non utilissimo)
* installare tutti i pacchetti elencati in requirements.txt attraverso pip
* scaricare l'ultimo driver di postgres (o in caso utilizzare quello inserito nella cartella work)
* impostare a worning il livello dei log di spark submit all'interno del container

questo script si fa partire all'interno del container. Per farlo ci sono due modi. Inizializzare su jupyter un terminale o entrare fisicamente nel container e sfruttare il terminale. Quest'ultimo si fa in questo modo:

```
docker exec -it <containername> /bin/bash
```

una volta all'interno si dovrá inizializzare il comando per far partire il bootstrap script

```
sh bootstrap_jupyter.sh
```

o in alternativa fare tutto dall'esterno con un solo comando che permette di lanciare un comando da eseguire all'interno di un container dall'ambiente esterno.

```
docker exec -it <containername> sh bootstrap_jupyter.sh
```

## Runnare script

Per poter runnare script all'interno dell'ambiente é necessario scrivere uno script python e da terminale interno al container lanciare il comando

```
python3 NOMEFILE.py
```

## Submit spark job

 Non siamo limitati ai notebook per interagire con spark, infatti in ambiente di produzione quasi sempre si fa riferimento a script per fare analisi o performare ETL script su grandi database.

Tipicamente piuttosto che lanciare lo script come fatto sopra si vuole interagire con esso attraverso il comando spark-submit, tipicamente utilizzato per poterlo lanciare in uno spark cluster.

```
$SPARK_HOME/bin/spark-submit 02_pyspark_job.py
```

immaginando che ci sia un file output creato per contenere il risultato dell'operazione potremmo visualizazrlo a schermo cosí

```
ls -alh output/items-sold.csv/
head -5 output/items-sold.csv/*.csv
```

## Interagire con il DB

I database all'interno di questa applicazione sono 4. 

* Postgres
* Postgres_backup
* Postgres_dwh
* Redis

Il primo *Postgres* ci serve come primo db, al suo interno vengono salvati i dati originali presi direttamente dall'app. 

Il secondo *Postgres_backup* é il db di backup, questo viene preso in considerazione quando cade o fallisce il primo database.

Il terzo *Postgres_dwh* é il datawarehouse che contiene i dati dopo aver attuato le operazioni di ETL con spark.

L'ultimo, *Redis*  é utilizzato per l'aggiornamento del database iniziale. Al suo interno sono salvati gli id delle playlist che abbiamo nel nostro db. Uno dei file che utilizzeremo sará un demon che andrá a fare richieste all'api una volta ogni ora. Se gli id sono presenti in Redis allora non c'é bisogno di aggiornare niente. Se la playlist é nuova allora aggiorna il db originale, ricalcola le ETL, aggiorna il DWH.



# Progetto

Il progetto ha come scopo il costruire un Big Data System che permette di analizzare dati di playlist di spotify. Nello specifico viene chiesto di analizzare le canzoni facenti parte delle playlist che abbiamo come oggetto il coronavirus, evidenziando differenze tra i vari paesi europei, analizzando lo 'spirit of the song' considerando valori come l'energy e la valence tra gli attributi dati dall'api di spotify. I dati verranno analizzati nell'ottica di una time series per vedere com'é mutato il mood musicale durante i lockdown.



### Workflow

* Caricamento dati. O si caricano da api o si caricano da backup
* Sui dati dal db si applicano le operazioni di ETL e si copiano i dati in DWH
* Dashboard prende i dati da DWH e li presenta



File da lanciare:

* create_tables.py  -> questa permette di creare le tabelle nei database (se stiamo provando la prima volta)
* load_data_api.py / load_data_backup.py -> carica sul database principale tutte le ricerche 
* backup.py -> dalla tabella di postgres copia i dati in un file csv e poi li copia sul db di backup.
* etl_processing.py (load data in dwh)
* visualization.py

Pipeline

* create_tables |load_data_api/load_data_backup(redis inizializzato) | backup | cronjob_update(lancia update) | etl_processing | visualization

#TODO gestire redis e gli aggiornamenti. Lanciare un file che runna in backup che aggiorna la lista nel caso di aggiornamenti.

#TODO gestire i database in pgAdmin, cercare di automatizzare la creazione dei server tramite json.



Detto questo abbiamo due database a cui dobbiamo connetterci ed interagire. La prima cosa da fare é scaricare le informazioni che ci servono sul data lake. Un esempio di output che ricaviamo dall'api é il seguente:

```json
{
   "playlists":{
      "href":"https://api.spotify.com/v1/search 						query=covid&type=playlist&offset=0&limit=50",
      "items":[],
      "limit":50,
      "next":"https://api.spotify.com/v1/search?query=covid&type=playlist&offset=50&limit=50",
      "offset":0,
      "previous":"None",
      "total":73180
   }
}
```

l'oggetto items contiene la lista di playlist ed é formato come seguech

```json
{
            "collaborative":false,
            "description":"",
            "external_urls":{
               "spotify":"https://open.spotify.com/playlist/7I5p2wl30OGnqmgrA5J0Bj"
            },
            "href":"https://api.spotify.com/v1/playlists/7I5p2wl30OGnqmgrA5J0Bj",
            "id":"7I5p2wl30OGnqmgrA5J0Bj",
            "images":[],
            "name":"COVID Sessions",
            "owner":{
               "display_name":"v2G,GXQKAYZRhDEsyk",
               "external_urls":{
                  "spotify":"https://open.spotify.com/user/2dw54lriqjf1buje476wje1ks"
               },
               "href":"https://api.spotify.com/v1/users/2dw54lriqjf1buje476wje1ks",
               "id":"2dw54lriqjf1buje476wje1ks",
               "type":"user",
               "uri":"spotify:user:2dw54lriqjf1buje476wje1ks"
            },
            "primary_color":"None",
            "public":"None",
            "snapshot_id":"Niw2OWY2M2JjNDk2ODQzNDNkODEzYjc0NTVmODUzY2UwZTNjMzYyYTgy",
            "tracks":{
               "href":"https://api.spotify.com/v1/playlists/7I5p2wl30OGnqmgrA5J0Bj/tracks",
               "total":5
            },
            "type":"playlist",
            "uri":"spotify:playlist:7I5p2wl30OGnqmgrA5J0Bj"
         }
```

Da qui é possibile ricavare il playlist_id che ci servirá per ricavare l'oggetto playlist e le sue sottocategorie. 

con il comando python spotipy.playlist(playlist_id) ricaviamo l'oggetto:

```json
{
   "collaborative":false,
   "description":"",
   "external_urls":{},
   "href":"https://api.spotify.com/v1/playlists/7I5p2wl30OGnqmgrA5J0Bj?additional_types=track",
   "id":"7I5p2wl30OGnqmgrA5J0Bj",
   "images":[],
   "name":"COVID Sessions",
   "owner":{},
   "primary_color":"None",
   "public":true,
   "snapshot_id":"Niw2OWY2M2JjNDk2ODQzNDNkODEzYjc0NTVmODUzY2UwZTNjMzYyYTgy",
   "tracks":{
      "href":"https://api.spotify.com/v1/playlists/7I5p2wl30OGnqmgrA5J0Bj/tracks?offset=0&limit=100&additional_types=track",
      "items":[],
      "limit":100,
      "next":"None",
      "offset":0,
      "previous":"None",
      "total":5
   },
   "type":"playlist",
   "uri":"spotify:playlist:7I5p2wl30OGnqmgrA5J0Bj"
}
```

L'oggetto che ricaviamo ha al suo interno l'oggetto tracks che contiene una proprietá items che contiene una lista di oggetti. Questi oggetti sono le tracce, qui sotto rappresentate come esempio:

```json
{
    "added_at":"2020-09-16T21:46:15Z",
    "added_by":{},
    "is_local":false,
    "primary_color":"None",
    "track":{
        "album":{},
        "artists":[],
        "available_markets":["AD","AE",..],
        "disc_number":1,
        "duration_ms":205547,
        "episode":false,
        "explicit":false,
        "external_ids":{},
        "external_urls":{},
        "href":"https://api.spotify.com/v1/tracks/5sXPAGXZEnl7dMReMWwFTg",
        "id":"5sXPAGXZEnl7dMReMWwFTg",
        "is_local":false,
        "name":"Cloud Trippin'",
        "popularity":32,
        "preview_url":"https://p.scdn.co/mp3-preview/b346fd424c5bfabec42926010537c5899453cb08?cid=118aa19f2b66476fbc062f0ac146d8b5",
        "track":true,
        "track_number":1,
        "type":"track",
        "uri":"spotify:track:5sXPAGXZEnl7dMReMWwFTg"
    },
    "video_thumbnail":{
        "url":"None"
    }
}
```

In questo elemento é possibile trovare i mercati disponibili per la traccia e in piú l'id. In questo caso basta per avere abbastanza informazioni aggiungendo un altro comando che accetta una lista di track_id che restituisce tanti oggetti audiofeatures quanti sono gli id.

L'oggetto restituito é una lista di oggetti con le seguenti informazioni 

```json
{'danceability': 0.796,
  'energy': 0.419,
  'key': 2,
  'loudness': -9.686,
  'mode': 1,
  'speechiness': 0.0704,
  'acousticness': 0.114,
  'instrumentalness': 0.938,
  'liveness': 0.105,
  'valence': 0.165,
  'tempo': 94.958,
  'type': 'audio_features',
  'id': '5sXPAGXZEnl7dMReMWwFTg',
  'uri': 'spotify:track:5sXPAGXZEnl7dMReMWwFTg',
  'track_href': 'https://api.spotify.com/v1/tracks/5sXPAGXZEnl7dMReMWwFTg',
  'analysis_url': 'https://api.spotify.com/v1/audio-analysis/5sXPAGXZEnl7dMReMWwFTg',
  'duration_ms': 205547,
  'time_signature': 4}
```



### Load_in_redis.py

Questo file fa quello spiegato sopra. Carica i file dall'API al container redis. I file non sono ancora completi e mancano delle audio features. Il programma viene runnato con il comando: 

```bash
python3 load_in_redis.py
```

Fatto questo Redis avrá all'incirca 1900 chiavi con l'oggetto sopra indicato come valore.  Il codice commentato é quello che segue:

```python
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

```



### Load_in_postgres

Prossimo file prende i dati da redis, li aggiorna e li carica su postgres. File che permette di completare il lavoro con le api e di salvare tutti i dati in postgres. I dati rappresentano le qualitá di una sola canzone.

```
python3 load_in_postgres.py
```

Postgres ha una libreria per python che permette di gestire le connessioni. L'oggetto principale é il cursor. Il cursor altro sarebbe che un puntatore che permette di interagire con la tabella. Ne esistono di due tipi. Il client-side cursor carica l'intera tabella sul client e poi inizia a processarlo. Il lerver-side cursor non carica tutto sul client, a meno che non gli sia richiesto. Questo permette di gestire meglio la pesantezza dei dati anche se chiede al db un ingente numero di connessioni in piú.

# databases

Una volta lanciata la nostra applicazione bisogna importare le impostazioni server all'interno di pgAdmin il nostro gestore per DB. Dalla folder dove si trova il file stack lanciare i seguenti comandi per configurarlo.

```
docker cp servers.json [nomedelcontainerpgadmin]:/tmp/servers.json
docker exec -it [nomedelcontainerpgadmin] python /pgadmin4/setup.py --load-servers /tmp/servers.json --user user@domain.com
```

per esportare i config relativi a i database invece basta runnare il seguente

```
docker exec -it [nomedelcontainerpgadmin] python /pgadmin4/setup.py --dump-servers /tmp/servers.json
docker cp [nomedelcontainerpgadmin]:/tmp/servers.json .
```

una volta entrati al suo interno con l'url 127.0.0.1:8180

basterá inserire username e password: 

```
PGADMIN_DEFAULT_EMAIL: user@domain.com
PGADMIN_DEFAULT_PASSWORD: 5up3rS3cr3t!
```

ed inserire per ogni server la password: postgres1234

# Per runnare la dash

```
docker service inspect --format="{{json .Endpoint.Spec.Ports}}" jupyter_spark
```

una volta lanciato il file visualization ci si connette al link di riferimento

http://127.0.0.1:7777/



## References

* https://spotipy.readthedocs.io/en/2.16.1/#features