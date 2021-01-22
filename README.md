# Covid19 analysis on Spotify

Il progetto ha come scopo il costruire un Big Data System che permette di analizzare dati di playlist di spotify. Nello specifico viene chiesto di analizzare le canzoni facenti parte delle playlist che abbiano come oggetto il coronavirus, analizzando lo 'spirit of the song' considerando valori come l'energy e la valence tra gli attributi dati dall'api di spotify. I dati verranno analizzati nell'ottica di una time series per vedere com'é mutato il mood musicale durante i lockdown.

# Demo

La demo gira su un pc linux. Si da per certo una dimestichezza con l'ambiente docker.

Una volta scaricato il progetto é necessario inizializzare alcune variabili e cartelle.

Si scaricano le immagini che servono:

```
docker pull jupyter/all-spark-notebook:latest
docker pull postgres:12-alpine
docker pull redis:alpine
docker pull dpage/pgadmin4:latest
```

Si inizializzano le cartelle di sistema interessate:

```
mkdir -p ~/data/postgres
mkdir -p ~/data/postgres_backup
mkdir -p ~/data/postgres_dwh
mkdir -p ~/data/redis
```

Dalla main folder del progetto lanciare il comando da terminale

```
docker stack deploy -c stack.yml jupyter
```

Controllare che sia stato buildato il progetto é possibile lanciare il comando:

```
docker stack ps jupyter
```

Una volta lanciata la nostra applicazione bisogna importare le impostazioni server all'interno di pgAdmin il nostro gestore per DB. Dalla main folder lanciare i seguenti comandi per configurarlo.

```
docker cp servers.json [nomedelcontainerpgadmin]:/tmp/servers.json

docker exec -it [nomedelcontainerpgadmin] python /pgadmin4/setup.py --load-servers /tmp/servers.json --user user@domain.com
```

una volta entrati al suo interno con l'url 127.0.0.1:8180

basterá inserire username e password: 

```
EMAIL: user@domain.com
PASSWORD: 5up3rS3cr3t!
```

ed inserire per ogni server la password: postgres1234

Entrare nel docker principale (spark)

```
docker exec -it <containername> /bin/bash
```

Una volta dentro si fará il bootstrapping del docker, inizializzando tutte le librerie necessarie (vedesi il paragrafo dedicato sotto)

```
sh bootstrap_jupyter.sh
```

per avviare il progetto basta scrivere il comando

```
sh load_data_backup.sh
```

Si aspetta che finisca e saremo dentro la webapp all'indirizzo http://127.0.0.1:7777

Nel caso si volesse far girare tutto l'algoritmo di caricamento dei dati direttamente da spotify si puó scrivere il comando

```
sh loar_data_api.sh
```

al posto di quello di sopra. Il caricamento richiede all'incirca 10 ore poiché carica circa 2000 playlists e 380mila tracce.

## Docker

In accordo con Docker la loro tecnologia permette gli sviluppatori di essere liberi di costruire, gestire e rendere sicure applicazioni senza preoccuparsi della infrastruttura dove sono installate. Per questo progetto sto utilizzando una versione di Docker Desktop per linux.

La versione corrente include orchestratori kubernetes e Swarm per gestire e deployare container. Ho scelto di utilizzare Swarm per questo progetto. Secondo docker il cluster management é innestato nel Docker Engine costruito utilizzando swarmkit. Swarmkit é un progetto separato che implementa un layer che orchestra Docker ed é utilizzato direttamente all'interno dello stesso.

Per questo progetto Docker é perfetto per simulare un sistema scalabile orizzontalmente. Basta aggiungere un conteiner e collegarlo alla stessa rete per avere un elemento in piú da poter utilizzare. 

## Inizializzazione e comandi principali
Utilizzo il comando docker pull per scaricare in locale le immagini dei container che serviranno per il progetto direttamente da Docker Hub. 

```bash
docker pull jupyter/all-spark-notebook:latest
docker pull postgres:12-alpine
docker pull redis:alpine
docker pull dpage/pgadmin4:latest
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
    - "7777:7777/tcp"
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
      POSTGRES_DB: postgres
    ports:
    - "5432:5432/tcp"
    networks:
    - demo-net
    volumes:
    - $HOME/data/postgres:/var/lib/postgresql/data
    deploy:
     restart_policy:
       condition: on-failure
  postgres_backup:
    image: postgres:12-alpine
    environment:
      POSTGRES_USERNAME: postgres
      POSTGRES_PASSWORD: postgres1234
      POSTGRES_DB: postgres
    ports:
    - "5431:5431/tcp"
    networks:
    - demo-net
    volumes:
    - $HOME/data/postgres_backup:/var/lib/postgresql/data
    deploy:
     restart_policy:
       condition: on-failure
  postgres_dwh:
    image: postgres:12-alpine
    environment:
      POSTGRES_USERNAME: postgres
      POSTGRES_PASSWORD: postgres1234
      POSTGRES_DB: dati_finali
    ports:
    - "5430:5430/tcp"
    networks:
    - demo-net
    volumes:
    - $HOME/data/postgres_dwh:/var/lib/postgresql/data
    deploy:
     restart_policy:
       condition: on-failure
  redis:
    image: redis:alpine
    environment:
      - ALLOW_EMPTY_PASSWORD=yes
      - REDIS_DISABLE_COMMANDS=FLUSHDB,FLUSHALL
    ports:
      - '6379:6379'
    networks:
      - demo-net
    volumes:
      - $HOME/data/redis:/var/lib/redis
      #- $PWD/redis.conf:/usr/local/etc/redis/redis.conf
  pgadmin:
    image: dpage/pgadmin4:latest
    depends_on:
      - postgres
      - postgres_backup
      - postgres_dwh
    environment:
      PGADMIN_DEFAULT_EMAIL: user@domain.com
      PGADMIN_DEFAULT_PASSWORD: 5up3rS3cr3t!
    ports:
      - "8180:80/tcp"
    networks:
      - demo-net
    deploy:
      restart_policy:
        condition: on-failure
```



## Struttura cartelle

Ora la cartella a cui si ha accesso é quella specificata nel file stack.yml, la cartella /work che fará da ponte tra il container e i file in locale. Questa cartella sará permanente ed ogni modifica fatta ai file verrá salvata anche in locale, anche al riavvio dello stack.

All'interno della cartella /work abbiamo la cartella /data e /sql.

La prima contiene due file necessari a far avviare l'applicazione senza riscaricare le playlist dall'inizio. La seconda contiene i comandi sql che servono agli script per creare le tabelle da database. 

```
mkdir -p ~/data/postgres
mkdir -p ~/data/postgres_backup
mkdir -p ~/data/postgres_dwh
mkdir -p ~/data/redis
```

##  Running

Direttamente dal main folder run from the terminal

```
docker stack deploy -c stack.yml jupyter
```

Dove jupyter é il nome dello stack che abbiamo creato dal file stack.yml

Qursto crea un network di container che interagiscono tra loro.

Per controllare che sia andato a buon fine  é necessario fare un check dei container con il comando 

```
docker stack ps jupyter
```

Per poter accedere all'interfaccia di jupyter notebook é necessario controllare i log del container a cui vogliamo accedere, nel nostro caso il nome del container é jupyter_spark (nome stack + _ + nome container) con il comando log

```
docker logs $(docker ps | grep jupyter_spark | awk '{print $NF}')
```

Se é andato tutto bene ed il container é online allora é possibile avere un tocken di accesso simile al seguente: 

```
http://127.0.0.1:8888/?token=f78cbe...
```

Fare questo ultimo passaggio peró non é necessario ai fini della demo 

Fatto é possibile entrare all'interno del container principale (spark) per poter interagire con l'app.

Il comando per entrare nella shell del container é:

```
docker exec -it <containername> /bin/bash
```

Una volta entrati basterá runnare i seguenti comandi:

1. Inizializzare l'ambiente

```
sh bootstrap_jupyter.sh
```

2. Avviare l'applicazione che permetterá di avere la dashboard all'indirizzo 127.0.0.1:7777

   il file load_data_backup permette di caricare in db playlist giá scaricate ed aggiornarle con un cronjob che viene avviato da bootstrap_jupyter. Questo per evitare il caricamento dei dati che, essendo tanti, arriva ad un tempo di caricamento che puó arrivare alle 10h. 

   ```
   sh load_data_backup.sh
   ```

Sul terminale si potranno seguire le varie fasi del processo.

Se invece si vuole scaricare da api la pipeline da eseguire é 

```
sh load_data_api.sh
```



##  Bootstrap e update

Nel progetto é incluso un bootstrap script. Lo script ha lo scopo di:  

* aggiornare l'ambiente
* installare htop per la verifica delle performance (non utilissimo)
* installare tutti i pacchetti elencati in requirements.txt attraverso pip
* scaricare l'ultimo driver di postgres (o in caso utilizzare quello inserito nella cartella work)
* impostare a worning il livello dei log di spark submit all'interno del container
* lanciare un cronjob ogni ora per l'aggiornamento del db.

Il cronjob ogni ora lancia il file update.py.

Questo file scarica la lista delle playlist aggiornata ogni ora. Interroga Redis che é stato inizializzato con i dati presenti nei file csv. Se la playlist é giá presente in Redis allora viene ignorata, se é nuova si fa un update al db. Aggiornando i dati che vengono visualizzati all'interno della webapp.

questo script si fa partire all'interno del container. 

## Interagire con il DB

I database all'interno di questa applicazione sono 4. 

* Postgres
* Postgres_backup
* Postgres_dwh
* Redis

Il primo *Postgres* ci serve come primo db, al suo interno vengono salvati i dati originali presi direttamente da Spotify. 

Il secondo *Postgres_backup* é il db di backup, questo viene preso in considerazione quando cade o fallisce il primo database.

Il terzo *Postgres_dwh* é il datawarehouse che contiene i dati dopo aver attuato le operazioni di ETL con spark.

L'ultimo, *Redis*  é utilizzato per l'aggiornamento del database iniziale. Al suo interno sono salvati gli id delle playlist che abbiamo nel nostro db. Uno dei file che utilizzeremo sará un demon che andrá a fare richieste all'api una volta ogni ora. Se gli id sono presenti in Redis allora non c'é bisogno di aggiornare niente. Se la playlist é nuova allora aggiorna il db originale, ricalcola le ETL, aggiorna il DWH.



# Pipelines

File lanciati all'interno dei file load_data.sh:

* create_tables.py  -> questa permette di creare le tabelle nei database (se stiamo provando la prima volta)
* load_data_api.py / load_data_backup.py -> carica sul database principale tutte le ricerche 
* backup.py -> dalla tabella di postgres copia i dati in un file csv e poi li copia sul db di backup.
* etl.py (load data in dwh)
* visualization.py


