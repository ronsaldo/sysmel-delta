#!/bin/sh
set -ex

dot -Tsvg asgSyntax.dot > asgSyntax.svg
dot -Tsvg asgTypechecked.dot > asgTypechecked.svg
dot -Tsvg asgTypecheckedWithDerivation.dot > asgTypecheckedWithDerivation.svg
dot -Tsvg asgMir.dot > asgMir.svg
dot -Tsvg asgMirWithDerivation.dot > asgMirWithDerivation.svg
