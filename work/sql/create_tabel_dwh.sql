
CREATE TABLE "spotify_complete"
(
    "id_playlist"       text NOT NULL,
    "name_playlist"     text NULL,
    "id_track"          text NULL,
    "name_track"        text NULL,
    "year_month"        text NULL,
    "danceability"      text NULL,
    "energy"            text NULL,
    "key"               text NULL,
    "loudness"          text NULL,
    "mode"              text NULL,
    "speechiness"       text NULL,
    "acousticness"      text NULL,
    "instrumentalness"  text NULL,
    "liveness"          text NULL,
    "valence"           text NULL,
    "tempo"             text NULL,
    "duration_ms"       text NULL,
    "time_signature"    text NULL
);


CREATE TABLE "month_distribution"
(
    "timestamp"         text NOT NULL,
    "count"             integer NOT NULL
);

CREATE TABLE "count_tracks_distribution"
(
    "id_playlist"         text NOT NULL,
    "count"             numeric NOT NULL
);

CREATE TABLE "audiofeatures_stat"
(
    "timestamp"         text NOT NULL,
    "mean_energy"       decimal NOT NULL, 
    "mean_valence"       decimal NOT NULL, 
    "mean_danceability"       decimal NOT NULL, 
    "stdev_energy"       decimal NOT NULL, 
    "stdev_valence"       decimal NOT NULL, 
    "stdev_danceability"       decimal NOT NULL 
);