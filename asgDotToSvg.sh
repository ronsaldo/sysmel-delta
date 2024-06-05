#!/bin/sh
set -ex

dot -Tsvg asgSyntax.dot > asgSyntax.svg
dot -Tsvg asgTypechecked.dot > asgTypechecked.svg
dot -Tsvg asgTypecheckedWithDerivation.dot > asgTypecheckedWithDerivation.svg
