#!/bin/sh
set -ex

dot -Tsvg asgSyntax.dot > asgSyntax.svg
dot -Tsvg asgAnalyzed.dot > asgAnalyzed.svg
dot -Tsvg asgAnalyzedWithDerivation.dot > asgAnalyzedWithDerivation.svg
dot -Tsvg asgMir.dot > asgMir.svg
dot -Tsvg asgMirWithDerivation.dot > asgMirWithDerivation.svg
