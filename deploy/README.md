# Deployment

To deploy the bot, use the provided [`docker-compose.yml`](docker-compose.yml) and [`.env`](.env) files.

## Environment variables

The `.env` file requires some modifications specific to your access configuration:

- change the `DB_PASSWORD` value to the password you would like to have for the database,
- change the `LDB_TOKEN` to the LDB access token (register for the token [here](http://realtime.nationalrail.co.uk/OpenLDBWSRegistration/)),
- change the `TELEGRAM_TOKEN` to the Telegram authentication token (see how to set up a bot and obtain a token [here](https://core.telegram.org/bots)).

Other environment variables can be left as is:

- `DB_USER` is the default username for the database storing the subscription information,
- `DB_NAME` is the name of the database,
- `DB_PORT` the port exposed to the host machine by which the database can be accessed.

## Starting and stopping the application stack

On the host machine, run

```sh
$ docker-compose up -d
```

from the directory containing both deployment files.

To stop the stack, run

```sh
$ docker-compose down
```

from the same directory.

## Automatic restarts

All services in the `docker-compose.yml` file will restart automatically (`restart: always`).
In case your host server is restarted, the application will restart automatically by `docker`.

## Developer tips

To verify that all containers are running fine, do:

```sh
$ docker-compose ps
AME                    COMMAND                  SERVICE             STATUS              PORTS
rail_bot-train-bot-1    "python3 rail_bot"       train-bot           running
rail_bot-watchtower-1   "/watchtower --inter…"   watchtower          running             8080/tcp
train-bot-db            "docker-entrypoint.s…"   db                  running             0.0.0.0:5432->5432/tcp, :::5432->5432/tcp
```

To peek into the database, start an interactive session with the Postgres database:

```sh
$ docker exec -it -u postgres train-bot-db psql
```

to connect to the database, and interact with the data:

```sh
postgres=# \c train-bot-db
postgres=# \l
postgres=# SELECT * FROM travel;
```