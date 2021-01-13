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

ci sono due db all'interno di questa architettura. Uno implementato postgres, un'altro redis.

Redis verrá utilizzato come Data Lake. Questo tipo di DB utilizza kv ed é estremamente versatile. 

Si accede al server con il comando

```
docker exec -it nomecontainer redis-cli
```

In python é importante settare come redis_host il nome del container 'jupyter_host' ore 2 del mattino.



# Progetto

Il progetto ha come scopo il costruire un Big Data System che permette di analizzare dati di playlist di spotify. Nello specifico viene chiesto di analizzare le canzoni facenti parte delle playlist che abbiamo come oggetto il coronavirus, evidenziando differenze tra i vari paesi europei, analizzando lo 'spirit of the song' considerando valori come l'energy e la valence tra gli attributi dati dall'api di spotify.























IDEA POTREI CREARE UN DOCKER CON REDIS ED UNO CON POSTGRES PER POTER UTILIZZARE IL PRIMO PER DB E IL SECONDO COME DWH