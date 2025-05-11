ifneq ("$(wildcard .env)","")
    include .env
    export $(shell sed 's/=.*//' .env)
else
endif

WORKDIR := $(shell pwd)
.ONESHELL:
.EXPORT_ALL_VARIABLES:
DOCKER_BUILDKIT=1

DOCKER_COMPOSE_FILE = docker-compose.yml
DOCKER_IMAGES = $(shell docker images -qa)
DOCKER_CONTAINERS = $(shell docker ps -qa)
DOCKER_VOLUMES = $(shell docker volume ls)

help: ## Display help message
	@echo "Please use \`make <target>' where <target> is one of"
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

rebuild: ## Run and build whole architecture
	docker compose -f $(DOCKER_COMPOSE_FILE) down -v
	docker compose -f $(DOCKER_COMPOSE_FILE) up -d --build
	make ps

log-all: ## Views all containers logs
	docker compose -f $(DOCKER_COMPOSE_FILE) logs -f

start: ## Starts existing containers for a service
	docker compose -f $(DOCKER_COMPOSE_FILE) start

stop: ## Stops running containers without removing them
	docker compose -f $(DOCKER_COMPOSE_FILE) stop

restart: ## Restart running containers without removing them
	docker compose -f $(DOCKER_COMPOSE_FILE) restart

stats: ## Shows docker's resource-consuming statistics
	docker stats

ps: ## Lists containers for the project, with current status and exposed ports
	docker compose -f $(DOCKER_COMPOSE_FILE) ps

down: ## Stops containers and removes containers, networks, volumes, and images
	docker compose -f $(DOCKER_COMPOSE_FILE) down
	make prune

up: ## (Re)creates, starts, and attaches containers
	docker compose -f $(DOCKER_COMPOSE_FILE) up -d

prune: ## Removes all unused containers, networks, images
	docker system prune -f

prv: ## Pruning with volumes
	docker system prune -f --volumes

clc: ## Force cleans all exist docker containers
	docker rm -f ${DOCKER_CONTAINERS}

cli: ## Force cleans all exist docker images
	docker image rm -f ${DOCKER_IMAGES}

clv: ## Force cleans all exist docker volumes
	docker volume rm -f ${DOCKER_VOLUMES}

clean-all: ## Force cleans all exist docker data
	make down
	make prune
	make prv
	make clc
	make cli
	make clv
	docker compose -f $(DOCKER_COMPOSE_FILE) down -v
	docker system prune -af
	docker network ls -q | xargs docker network rm


init-migrations: ## init migrations config file and directory
	docker compose exec app /bin/bash -c "aerich init -t config.TORTOISE_ORM && \
                                                  aerich init-db"

.PHONY: migrations
migrations: ## create migration file
	docker compose exec app /bin/bash -c "aerich migrate"

migrate: ## apply migration
	docker compose exec app /bin/bash -c "aerich upgrade"

downgrade:  ## downgrade last migration
	docker compose exec app /bin/bash -c "aerich downgrade"

history:  ## show list history of migrations
	docker compose exec app /bin/bash -c "aerich history"

heads: ## show head migration
	docker compose exec app /bin/bash -c "aerich heads"

init-enums: ## create records in db by enums
	docker exec -it app python scripts/init_enums.py

create: ## build infrastructure on first run app
	make rebuild
	make clear-db
	make init-migrations
	make migrate
	make init-enums
	make ps


clear-db: ## Delete db and create new
	docker exec -it postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "DROP SCHEMA public CASCADE;"
	docker exec -it postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "CREATE SCHEMA public;"
