.PHONY: \
	lint test \
	deploy-01-dns deploy-02-resources deploy-03-api \
	undeploy-01-dns undeploy-02-resources undeploy-03-api \
	help clean
.DEFAULT_GOAL := help

SERVERLESS_ORG := mperezi
BUCKET_NAME    := migueli.to
TABLE_NAME     := Url2
MKFILE_PATH    := $(abspath $(lastword $(MAKEFILE_LIST)))
MKFILE_DIR     := $(dir $(MKFILE_PATH))
stage          := dev

help:  ## Show this help
	@grep -E '^[a-zA-Z0-9_ -]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

lint:                ## Enforce linting rules through flake8
	flake8 src

test:    ## Run integration tests via Postman (newman)
	newman run postman/integration-tests.postman_collection.json \
		-e postman/dev.postman_environment.json \
		-r htmlextra,cli \
		--reporter-htmlextra-export testResults/htmlreport.html

deploy-01-dns:    ## Create hosted zone and API custom domain name in AWS
	sls deploy --verbose --config serverless.01.dns.yml
	sls create_domain --config serverless.01.dns.yml

deploy-02-resources:    ## Create resources stack in AWS
	sls deploy --verbose --config serverless.02.resources.yml --stage $(stage)

deploy-03-api:    ## Create API and functions in AWS
	sls deploy --verbose --config serverless.03.api.yml --stage $(stage)

undeploy-01-dns:    ## Remove hosted zone and API custom domain name from AWS
	sls delete_domain --config serverless.01.dns.yml
	sls remove --config serverless.01.dns.yml

undeploy-02-resources:    ## Remove resources from AWS
	sls remove --verbose --config serverless.02.resources.yml --stage $(stage)

undeploy-03-api:    ## Remove API and functions from AWS
	sls remove --verbose --config serverless.03.api.yml --stage $(stage)

logs:  ## Print logs of the specified function (make logs func=myfunc [stage=dev|v1..])
	sls logs --config serverless.03.api.yml --stage $(stage) -f $(func)

clean:          ## Delete temporary files and build artifacts
	rm -rf .serverless
	find . -type d -name "__pycache__" | xargs rm -rf
