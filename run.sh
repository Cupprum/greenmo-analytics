#!/usr/bin/env bash

set -e
set -u
set -o pipefail

set -a
source .env
set +a

go run .