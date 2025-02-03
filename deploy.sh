#!/bin/bash

npm i -g serverless@3.37.0 \
  serverless-python-requirements

export S3_DEPLOYMENT_BUCKET=
export ACCOUNT_NUMBER=
sls package
#unzip -l  .serverless/update-ip-restriction.zip
sls deploy --verbose
