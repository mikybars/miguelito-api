# Dependencies:
#  * aws cli -- https://aws.amazon.com/es/cli/
#  * sls     -- https://www.serverless.com/
#  * newman  -- https://github.com/postmanlabs/newman
#  * flake8  -- https://flake8.pycqa.org/
#  * isort   -- https://pycqa.github.io/isort/
set dotenv-load

alias t := test
alias d := deploy

[private]
default:
	@just --list

# Lint source files through flake8
lint-src:
	flake8 src

# Rearrange imports in the source code
sort-imports:
	isort . --profile black

# Validate serverless.yml files
lint-sls:
	#!/usr/bin/env bash
	for stack in dns resources api; do
		just lint-config $stack dev
		just lint-config $stack `[[ $stack != api ]] && echo pro || echo v1`
	done

[private]
lint-config stack stage:
	sls package --config serverless*{{stack}}.yml --stage {{stage}}

# npm install -g newman newman-reporter-htmlextra
# Run integration tests via Postman (needs newman)
test:
	newman run "postman/collections/Integration tests.postman_collection.json" \
		--environment postman/env/dev.postman_environment.json \
		--reporters htmlextra,cli \
		--reporter-htmlextra-export testResults/htmlreport.html \
		--env-var awsAccessKeyId=${AWS_ACCESS_KEY_ID} \
		--env-var awsSecretAccessKey=${AWS_SECRET_ACCESS_KEY}

# Run integration tests via Postman (needs gh)
setup-ci:
  gh secret set -f .env

deploy stack stage:
	#!/usr/bin/env bash
	sls deploy --verbose --config serverless*.{{stack}}.yml --stage {{stage}}
	if [[ {{stack}} == dns ]]; then
		sls create_domain --config serverless*.dns.yml
	fi

# Remove hosted zone and API custom domain name from AWS
undeploy stack stage:
	#!/usr/bin/env bash
	if [[ {{stack}} == dns ]]; then
		sls delete_domain --config serverless*.dns.yml
	fi
	sls remove --config serverless*.{{stack}}.yml --stage {{stage}}

# Print logs of the specified function
logs fn stage:
	sls logs --config serverless*.api.yml --function {{fn}} --stage {{stage}}
