.PHONY: help venv test deploy undeploy clean
.DEFAULT_GOAL := help

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

test: venv      ## Run unit tests (in virtual env)
	. venv/bin/activate
	pytest --cov

deploy:         ## Deploy the service to AWS and upload static content
	sls deploy -v
	jq -r .bucket <config.json | xargs -I{} aws s3 sync static s3://{}

undeploy:       ## Delete all the resources from AWS
	sls remove

clean:          ## Delete temporary files and build artifacts
	rm -rf venv .serverless .pytest_cache
	find . -type d -name "__pycache__" | xargs rm -rf
	rm .coverage
