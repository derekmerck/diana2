# Setup the UMich SIREN Imaging Submission Stack

```
## Note -- data-path-addr should be an Internet connected interface
$ docker swarm init --advertise-addr=x.x.x.x --data-path-addr=y.y.y.y

## Export project variables so they are available in docker-compose
$ set -a && source ~/.secrets/siren.env && set +a

$ cd ${DIANA_DIR}/platform/docker-stacks
$ docker stack deploy -c admin/admin-stack.yaml admin
$ mkdir -p ${DATA_DIR}/splunk/{var,etc}

## Note -- $SPLUNK_HOST must be the swarm IP addr, not localhost
$ docker stack deploy -c admin/splunk-service.yaml admin

$ mkdir -p ${DATA_DIR}/postgres
$ docker stack deploy -c backend/postgres-service.yaml backend

## Note: Soft link subscriptions and env file into this directory for diana-transport
$ mkdir -p ${DATA_DIR}/postgres
$ cd ../examples/umich-siren
$ ln -s ~/.secrets/siren.env siren.env
$ ln -s ${DIANA_DIR}/apps/siren/notify.txt.j2 notify.txt.j2
$ ln -s ~/.secrets/subscriptions.yaml subscriptions.yaml
$ docker stack deploy -c submission-stack.yaml siren

```