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

Per il momento mancano alcune cose ma il codice verrá aggiornato.

Il comando per eseguire la build dell'infrastruttura é: 

```
docker stack deploy -c stack.yml jupyter
```

IDEA POTREI CREARE UN DOCKER CON REDIS ED UNO CON POSTGRES PER POTER UTILIZZARE IL PRIMO PER DB E IL SECONDO COME DWH