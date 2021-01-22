#!/usr/bin/python3

import pandas as pd
import redis
import psycopg2
from pyspark.sql.functions import to_timestamp, date_format
import pyspark.sql.functions as f
from pyspark.sql import Window
from pyspark.sql import SparkSession
import warnings
warnings.filterwarnings("ignore")

def main():
    """
    Lavora sui dati del database originale per fare ETL e caricare sulla
    dwh i dati che ci servono
    """

    spark = SparkSession \
        .builder \
        .appName('DBAnalysis') \
        .config('spark.driver.extraClassPath', 'postgresql-42.2.10.jar') \
        .getOrCreate()

    properties = {
        'driver': 'org.postgresql.Driver',
        'url': 'jdbc:postgresql://postgres:5432/postgres',
        'user': 'postgres',
        'password': 'postgres1234',
        'dbtable': ' spotify_details',
    }

    properties_dwh = {
        'driver': 'org.postgresql.Driver',
        'url': 'jdbc:postgresql://postgres_dwh:5432/postgres',
        'user': 'postgres',
        'password': 'postgres1234'
    }

    df2 = spark.read \
        .format('jdbc') \
        .option('driver', properties['driver']) \
        .option('url', properties['url']) \
        .option('user', properties['user']) \
        .option('password', properties['password']) \
        .option('dbtable', properties['dbtable']) \
        .load()

    count_tracks_distribution = df2.groupby('id_playlist')\
                                .count()

    # Creo la colonna year_month
    df3 = df2.withColumn('year_month', date_format(
            to_timestamp(df2.timestamp, "yyyy-MM-dd'T'HH:mm:ssXXX"), 
            "yyyy-MM"
        ).alias('year_month')) 

    # Aggrego sulla playlist e conto le ricorrenze
    df4 = df3.groupby('id_playlist', 'year_month').count()

    # Per assegnare un mese alla playlist si é deciso di scegliere il mese con maggiori "aggiunte" di canzoni
    # Per ogni playlist seleziono solo quella con ricorrenze per mese maggiore 
    w = Window.partitionBy('id_playlist')

    df5 = df4.withColumn('max', f.max('count').over(w))\
        .where(f.col('count') == f.col('max'))\
        .drop('max', 'count')

    month_distribution = df5\
        .where(f.col('year_month')>="2020-01")\
        .groupby('year_month')\
        .count()

    # Il df completo ha l'informazione sul mese di riferimento assegnata ad ogni playlist
    spotify_complete = df2.join(df5, on=['id_playlist'], how='left')

    df_complete2 =  spotify_complete.groupBy("id_playlist", 'name_playlist' , 'year_month')\
                    .agg(f.mean('danceability'),f.stddev_pop('danceability'),f.mean('energy'),f.stddev_pop('energy'),f.mean('valence'),f.stddev_pop('valence'))\
                    .sort('year_month', ascending=True)

    newColumns = ["id_playlist","name_playlist","year_month","avgdanceability","stdddanceability","avgenergy","stddenergy","avgvalence","stddvalence"]
    df_complete2 = df_complete2.toDF(*newColumns)

    df_complete3 = df_complete2.groupBy('year_month')\
    .agg(f.mean('avgdanceability'),f.mean('stdddanceability'),f.mean('avgenergy'),f.mean('stddenergy'),f.mean('avgvalence'),f.mean('stddvalence'))\
    .sort('year_month', ascending=True)

    newColumns = ["timestamp","mean_danceability","stdev_danceability","mean_energy","stdev_energy","mean_valence","stdev_valence"]
    audiofeatures_stat = df_complete3.toDF(*newColumns)

    audiofeatures_stat.write.jdbc(url=properties_dwh['url'],table='audiofeatures_stat',mode='overwrite',properties=properties_dwh)
    spotify_complete.write.jdbc(url=properties_dwh['url'],table='spotify_complete',mode='overwrite',properties=properties_dwh)
    month_distribution.write.jdbc(url=properties_dwh['url'],table='month_distribution',mode='overwrite',properties=properties_dwh)
    count_tracks_distribution.write.jdbc(url=properties_dwh['url'],table='count_tracks_distribution',mode='overwrite',properties=properties_dwh)


if __name__ == "__main__":
    main()    