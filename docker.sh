#!/usr/bin/env bash

set -e
set -u
set -o pipefail

case ${1:-} in
    build)
        docker build -t gemini-jail .
        ;;
    run)
        docker run -it\
            --rm \
            --userns=keep-id \
            -v "$(pwd):/home/gemini/workspace:z" \
            -v "$HOME/.gemini:/home/gemini/.gemini:z" \
            gemini-jail bash
        ;;
    *)
        echo "Usage: ./docker.sh [build|run]"
        exit 1
        ;;
esac
