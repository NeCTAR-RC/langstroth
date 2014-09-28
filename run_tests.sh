#!/bin/bash
set -e

#Usage:
# cd into the test directory then execute:
# export DJANGO_TEST=True;../../run_tests.sh --settings=langstroth.settings

DIR=$(cd -P -- "$(dirname -- "$0")" && pwd -P)

cd $DIR

if [ -n "$*" ]; then
    TESTS="$@"
else
    TESTS="langstroth nectar_allocations"
fi

./manage.py test --settings=langstroth.settings_test -v 2 $TESTS
