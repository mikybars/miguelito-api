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

# npm install -g newman newman-reporter-htmlextra
# Run integration tests via Postman (needs newman)
test:
	newman run "postman/collections/Integration tests.postman_collection.json" \
		--environment postman/env/dev.postman_environment.json \
		--reporters htmlextra,cli \
		--reporter-htmlextra-export testResults/htmlreport.html \
		--env-var awsAccessKeyId=${AWS_ACCESS_KEY_ID} \
		--env-var awsSecretAccessKey=${AWS_SECRET_ACCESS_KEY}

setup-ci:
    gh secret set -f .env

deploy stage='dev' region='eu-west-1':
    sls deploy --verbose --stage {{stage}} --region {{region}}

undeploy stage='dev' region='eu-west-1':
	sls remove --verbose --stage {{stage}} --region {{region}}

# Print logs of the specified function
logs fn stage='dev' region='eu-west-1':
	sls logs --function {{fn}} --stage {{stage}} --region {{region}}
