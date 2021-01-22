# Covid19 analysis on Spotify

The project aims to build a Big Data System that allows you to analyze Spotify playlist data. Specifically, it is asked to analyze the songs that are part of the playlists that have the coronavirus as their object, analyzing the 'spirit of the song' considering values such as energy and valence among the attributes given by the spotify api. The data will be analyzed in the perspective of a time series to see how the musical mood has changed during the lockdowns.

# Demo

The demo runs on a Linux pc. You are certainly familiar with the Docker environment.

Once the project has been downloaded it is necessary to initialize some variables and folders.

You download the images that you need:

```
docker pull jupyter/all-spark-notebook:latest
docker pull postgres:12-alpine
docker pull redis:alpine
docker pull dpage/pgadmin4:latest
```

The affected system folders are initialized

```
mkdir -p ~/data/postgres
mkdir -p ~/data/postgres_backup
mkdir -p ~/data/postgres_dwh
mkdir -p ~/data/redis
```

From the main folder of the project, launch the command from the terminal

```
docker stack deploy -c stack.yml jupyter
```

Check that the project has been built, you can run the command:

```
docker stack ps jupyter
```

Once our application is launched, the server settings must be imported into pgAdmin, our DB manager. From the main folder run the following commands to configure it.

```
docker cp servers.json [nomedelcontainerpgadmin]:/tmp/servers.json

docker exec -it [nomedelcontainerpgadmin] python /pgadmin4/setup.py --load-servers /tmp/servers.json --user user@domain.com
```

once inside it with the url 127.0.0.1:8180

just enter your username and password:

```
EMAIL: user@domain.com
PASSWORD: 5up3rS3cr3t!
```

and enter the password for each server: postgres1234

Enter the main docker (spark)

```
docker exec -it <containername> /bin/bash
```

Once inside the docker will be bootstrapped, initializing all the necessary libraries (see the dedicated paragraph below)

```
sh bootstrap_jupyter.sh
```

to start the project just write the command

```
sh load_data_backup.sh
```

Expect it to finish and we will be inside the webapp at http://127.0.0.1:7777

If you want to run the whole data loading algorithm directly from spotify you can write the command

```
sh loar_data_api.sh
```

instead of the one above. Uploading takes around 10 hours as it loads around 2000 playlists and 380,000 tracks.

## Docker

According to Docker, their technology allows developers to be free to build, manage and secure applications without worrying about the infrastructure where they are installed. For this project we are using a version of Docker Desktop for linux.

The current version includes kubernetes and Swarm orchestrators to manage and deploy containers. I have chosen to use Swarm for this project. According to Docker, cluster management is grafted into the Docker Engine built using Swarmkit. Swarmkit is a separate project that implements a layer that orchestrates Docker and is used directly within it.

For this project Docker is perfect for simulating a horizontally scalable system. Just add a container and connect it to the same network to have one more element to use.


## Initialization and main commands
Use the Docker pull command to locally download the container images that will be needed for the project directly from Docker Hub. 

```bash
docker pull jupyter/all-spark-notebook:latest
docker pull postgres:12-alpine
docker pull redis:alpine
docker pull dpage/pgadmin4:latest
```

These are the images that will make up the container cluster through Docker Swarm.

The file that contains all the configurations and that allows you to build the entire cluster is the stack.yml file composed as follows:

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



## Folder structure

The folder you have access to is the one specified in the stack.yml file, the work/ folder that will bridge between the container and the local files. This folder will be permanent and any changes made to the files will also be saved locally, even when the stack is restarted.
All'interno della cartella /work abbiamo la cartella /data e /sql.

The first contains two files needed to start the application without re-downloading the playlists from the beginning. The second contains the sql commands used by the scripts to create the tables from the database 

```
mkdir -p ~/data/postgres
mkdir -p ~/data/postgres_backup
mkdir -p ~/data/postgres_dwh
mkdir -p ~/data/redis
```

##  Running

Directly from the main folder run from the terminal

```
docker stack deploy -c stack.yml jupyter
```

Where jupyter is the name of the stack we created from the stack.yml file

To check that it was successful it is necessary to check the containers with the command



```
docker stack ps jupyter
```

In order to access the jupyter notebook interface it is necessary to check the logs of the container we want to access, in our case the container name is jupyter_spark (stack name + _ + container name) with the log command

```
docker logs $(docker ps | grep jupyter_spark | awk '{print $NF}')
```

If everything went well and the container is online then it is possible to have an access tocken similar to the following:

```
http://127.0.0.1:8888/?token=f78cbe...
```

However, doing this last step is not necessary for the demo

Done, it is possible to enter the main container (spark) in order to interact with the app.


The command to enter the container shell is:

```
docker exec -it <containername> /bin/bash
```

Once entered, just run the following commands:

1. Initialize the environment

```
sh bootstrap_jupyter.sh
```

2. Start the application that will allow you to have the dashboard at 127.0.0.1:7777

   the load_data_backup file allows you to load already downloaded playlists in db and update them with a cronjob that is started by bootstrap_jupyter. This is to avoid the loading of the data which, being many, reaches a loading time that can reach 10h.

   ```
   sh load_data_backup.sh
   ```

The various stages of the process can be followed on the terminal.

If, on the other hand, you want to download from api the pipeline to run is

```
sh load_data_api.sh
```



##  Bootstrap and update

A bootstrap script is included in the project. The script aims to:  

* update the environment
* install htop for performance verification (not very useful)
* install all packages listed in requirements.txt through pip
* download the latest postgres driver (or, if necessary, use the one inserted in the work folder)
* iset to worning the level of spark submit logs inside the container
* launch a cronjob every hour to update the db.

The cronjob every hour launches the update.py file.
This file downloads the playlist list updated every hour. Query Redis which has been initialized with the data present in the csv files. If the playlist is already present in Redis then it is ignored, if it is new, the db is updated. By updating the data that is displayed within the webapp.

This script runs inside the container.

## Interact with the DB

There are 4 databases within this application. 

* Postgres
* Postgres_backup
* Postgres_dwh
* Redis

The first Postgres serves as the first db, the original data taken directly from Spotify are saved inside.

The second Postgres_backup is the backup db, this is taken into account when the first database fails or fails.

The third Postgres_dwh is the data warehouse that contains the data after carrying out the ETL operations with spark.


The last one, Redis is used for the initial database update. Inside are saved the id of the playlists we have in our db. One of the files we will use will be a demon that will make requests to the API once an hour. If the ids are present in Redis then there is no need to update anything. If the playlist is new then update the original db, recalculate the ETLs, update the DWH.



# Pipelines


Files launched inside load_data.sh files:


* create_tables.py -> this allows you to create tables in databases (if we are trying for the first time)
* load_data_api.py / load_data_backup.py -> loads all searches to the main database
* backup.py -> the postgres table copy the data to a csv file and then copy them to the backup db.
* etl.py (load data in dwh)
* visualization.py


