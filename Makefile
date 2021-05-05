.PHONY: \
	lint unit-test integration-test \
	deploy-01-dns deploy-02-resources deploy-03-api \
	undeploy-01-dns undeploy-02-resources undeploy-03-api \
	help venv run clean
.DEFAULT_GOAL := help

BUCKET_NAME := migueli.to
TABLE_NAME  := Url2
MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MKFILE_DIR  := $(dir $(MKFILE_PATH))
STAGE       := dev

help:  ## Show this help
	@grep -E '^[a-zA-Z0-9_ -]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# https://stackoverflow.com/a/46188210/13166837
venv: venv/marker

venv/marker: requirements.txt test-requirements.txt
	@test -d venv || virtualenv venv
	. venv/bin/activate
	pip3 install $(?:%=-r %)
	touch $@

lint:                ## Enforce linting rules through flake8
	flake8 src

unit-test: venv      ## Run unit tests (in virtual env)
	. venv/bin/activate
	PYTHONPATH=$(MKFILE_DIR) BUCKET_NAME=$(BUCKET_NAME) TABLE_NAME=$(TABLE_NAME) \
			   pytest --cov --cov-report html --cov-report term

integration-test:    ## Run integration tests via Serverless Framework
	sls test --config serverless.03.api.yml --stage dev

# Example: make url=https://www.google.com path=google run
run:            ## Invoke the Lambda function with the given params
	sls generate-event -t aws:apiGateway -b '{"url":"$(url)", "custom_path": "$(path)"}' | \
		sls invoke -f shorten

deploy-01-dns:    ## Create hosted zone and API custom domain name in AWS
	sls deploy -v --config serverless.01.dns.yml
	sls create_domain --config serverless.01.dns.yml

deploy-02-resources:    ## Create resources stack in AWS
	sls deploy -v --config serverless.02.resources.yml --stage $(STAGE)

deploy-03-api:    ## Create API and functions in AWS
	sls deploy -v --config serverless.03.api.yml --stage $(STAGE)

undeploy-01-dns:    ## Remove hosted zone and API custom domain name from AWS
	sls delete_domain --config serverless.01.dns.yml
	sls remove --config serverless.01.dns.yml

undeploy-02-resources:    ## Remove resources from AWS
	sls remove -v --config serverless.02.resources.yml --stage $(STAGE)

undeploy-03-api:    ## Remove API and functions from AWS
	sls remove -v --config serverless.03.api.yml --stage $(STAGE)

clean:          ## Delete temporary files and build artifacts
	rm -rf venv .serverless .pytest_cache
	find . -type d -name "__pycache__" | xargs rm -rf
	rm .coverage
