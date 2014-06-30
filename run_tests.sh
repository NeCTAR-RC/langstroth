#!/bin/bash
set -e

DIR=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

cd $DIR

if [ -n "$*" ]; then
    TESTS="$@"
else
    TESTS="langstroth"
fi

./manage.py test --settings=langstroth.tests.settings -v 2 $TESTS
