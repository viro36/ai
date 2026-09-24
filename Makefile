venv:
	python3 -m venv .venv

# source .venv/bin/activate

freeze:
	pip3 freeze > requirements.txt

req:
	pip3 install -r requirements.txt


# ----------------------------------------

# SELECT setval(pg_get_serial_sequence('users', 'id'), coalesce(max(id)+1, 1), false) FROM users;

# docker-compose exec ai python3 manage.py startapp

build-d:
	docker-compose -f docker-compose.yml up --build -d --remove-orphans

build-p:
	docker-compose -f docker-compose.prod.yml up --build -d --remove-orphans

build-timeout:
	COMPOSE_HTTP_TIMEOUT=400 docker-compose up --build -d --remove-orphans

build-no:
	docker-compose build --no-cache

up-d:
	docker-compose -f docker-compose.yml up -d

up-p:
	docker-compose -f docker-compose.prod.yml up -d

up-timeout:
	COMPOSE_HTTP_TIMEOUT=400 docker-compose up -d

down-d:
	docker-compose -f docker-compose.yml down

down-p:
	docker-compose -f docker-compose.prod.yml down

re_celery:
	docker-compose restart ai celery_worker

logs:
	docker-compose logs

shell-d:
	docker-compose exec ai python manage.py shell

dbshell:
	docker-compose exec ai python manage.py dbshell

migrate-d:
	docker-compose exec ai python manage.py migrate --noinput

makemigrations:
	docker-compose exec ai python manage.py makemigrations

flush:
	docker-compose exec ai python manage.py flush

reset_db:
	docker-compose exec ai python manage.py reset_db

showmigrations:
	docker-compose exec ai python manage.py showmigrations

superuser:
	docker-compose exec ai python manage.py createsuperuser

collectstatic:
	docker-compose exec ai python manage.py collectstatic --no-input --clear

findstatic:
	docker-compose exec ai python manage.py findstatic css/style.css --verbosity 2

sessioninfo:
	docker-compose exec ai python manage.py sessioninfo

pytest:
	docker-compose exec ai python -m pytest -v

pytest-orgs:
	docker-compose exec ai python -m pytest -v apps/organizations/tests/

pytest-accounts:
	docker-compose exec ai python -m pytest -v apps/accounts/tests/

pytest-questions:
	docker-compose exec ai python -m pytest -v apps/questions/tests/

pytest-surveys:
	docker-compose exec ai python -m pytest -v apps/surveys/tests/

pytest-courses:
	docker-compose exec ai python -m pytest -v apps/courses/tests/

pytest-recommendations:
	docker-compose exec ai python -m pytest -v apps/recommendations/tests/

pytest-goal:
	docker-compose exec ai python -m pytest -v apps/goal_setting/tests/

pytest-tech:
	docker-compose exec ai python -m pytest -v apps/technical_requirements/tests/

pytest-cov:
	docker-compose exec ai python -m pytest -v apps/coverage_analysis/tests/

pytest-all:
	docker-compose exec ai python -m pytest apps/ -v --cov=apps --cov-report=term-missing

db-connect:
	docker-compose exec ai psql -h postgres-db -U admin -d ai

inspectdb:
	docker-compose exec ai python manage.py inspectdb > models.py

cache:
	docker-compose exec ai python manage.py createcachetable

show_urls:
	docker-compose exec ai python manage.py show_urls

dump-all-db:
	docker exec -t --user postgres ai_postgres-db_1 pg_dumpall -c -U postgres > dump.sql

bash:
	docker-compose exec ai bash

load_districts:
	docker-compose exec ai python manage.py load_districts

load_orgs:
	docker-compose exec ai python manage.py import_orgs apps/organizations/fixtures/orgs.csv

load_init:
	docker-compose exec ai python apps/surveys/scripts/init_survey_data.py

load_goal:
	docker-compose exec ai python manage.py seed_goal_setting_questions

load_technical_requirements:
	docker-compose exec ai python manage.py create_initial_questions

load_tech_statuses:
	docker-compose exec ai python manage.py create_initial_statuses

load_riasec_codes:
	docker-compose exec ai python manage.py load_riasec_codes

load_standards_otf:
	docker-compose exec ai python manage.py load_standards_otf

load_coverage_analysis:
	docker-compose exec ai python manage.py load_coverage_analysis

load_coverage_analysis_r:
	docker-compose exec ai python manage.py load_coverage_analysis --scenario REALISTIC

load_coverage_analysis_o:
	docker-compose exec ai python manage.py load_coverage_analysis --scenario OPTIMISTIC

load_coverage_methodology:
	docker-compose exec ai python manage.py load_coverage_methodology
