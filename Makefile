.PHONY: help venv test deploy undeploy clean
.DEFAULT_GOAL := help

BUCKET_NAME := migueli.to
MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MKFILE_DIR  := $(dir $(MKFILE_PATH))

export SLS_DEPRECATION_DISABLE=*

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# https://stackoverflow.com/a/46188210/13166837
venv: venv/marker

venv/marker: requirements.txt test-requirements.txt
	@test -d venv || virtualenv venv
	. venv/bin/activate
	pip3 install $(?:%=-r %)
	touch $@

unit-test: venv      ## Run unit tests (in virtual env)
	. venv/bin/activate
	PYTHONPATH=$(MKFILE_DIR) BUCKET_NAME=$(BUCKET_NAME) \
			   pytest --cov --cov-report html --cov-report term

integration-test:    ## Run integration tests via Serverless Framework
	sls test

# Example: make url=https://www.google.com path=google run
run:            ## Invoke the Lambda function with the given params
	sls generate-event -t aws:apiGateway -b '{"url":"$(url)", "custom_path": "$(path)"}' | \
		sls invoke -f shorten

deploy:         ## Deploy the service to AWS
	SLS_DEPRECATION_DISABLE="" sls deploy -v

undeploy:       ## Delete all the resources from AWS
	sls remove

clean:          ## Delete temporary files and build artifacts
	rm -rf venv .serverless .pytest_cache
	find . -type d -name "__pycache__" | xargs rm -rf
	rm .coverage
