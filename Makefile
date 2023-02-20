# Dependencies:
#  * aws cli -- https://aws.amazon.com/es/cli/
#  * sls     -- https://www.serverless.com/
#  * newman  -- https://github.com/postmanlabs/newman
#  * flake8  -- https://flake8.pycqa.org/
#  * isort   -- https://pycqa.github.io/isort/

.PHONY: \
	lint sort-imports test \
	deploy-01-dns deploy-02-resources deploy-03-api \
	undeploy-01-dns undeploy-02-resources undeploy-03-api \
	logs help clean
.DEFAULT_GOAL := help

BUCKET_NAME    := migueli.to
stage          := dev

AWS_ACCESS_KEY        ?= $$(aws configure get $${AWS_PROFILE:-default}.aws_access_key_id)
AWS_SECRET_ACCESS_KEY ?= $$(aws configure get $${AWS_PROFILE:-default}.aws_secret_access_key)

help:  ## Show this help
	@grep -E '^[a-zA-Z0-9_ -]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

lint-src:  ## Lint source files through flake8
	flake8 src

lint-sls:  ## Validate serverless.yml files
	sls package --config serverless.01.dns.yml --stage dev
	sls package --config serverless.01.dns.yml --stage pro
	sls package --config serverless.02.resources.yml --stage dev
	sls package --config serverless.02.resources.yml --stage pro
	sls package --config serverless.03.api.yml --stage dev
	sls package --config serverless.03.api.yml --stage v1

sort-imports:  ## Rearrange imports in source code
	isort . --profile black

test:  ## Run integration tests via Postman (newman)
	newman run "postman/collections/Integration tests.postman_collection.json" \
		--environment postman/env/dev.postman_environment.json \
		--reporters htmlextra,cli \
		--reporter-htmlextra-export testResults/htmlreport.html \
		--env-var accessKey=$(AWS_ACCESS_KEY) \
		--env-var secretAccessKey=$(AWS_SECRET_ACCESS_KEY)

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

clean:  ## Delete temporary files and build artifacts
	rm -rf .serverless
	find . -type d -name "__pycache__" | xargs rm -rf
