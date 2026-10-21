#!/bin/sh
# Resolve the isolated pakman prefix; no reference to the build store remains.
prefix=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export EMACSLOADPATH="$prefix/share/emacs/20.7/lisp"
export EMACSDATA="$prefix/share/emacs/20.7/etc"
export EMACSDOC="$EMACSDATA"
export EMACSPATH="$prefix/libexec/emacs/20.7/helpers"
export INFOPATH="$prefix/share/emacs/20.7/info${INFOPATH:+:$INFOPATH}"
exec "$prefix/libexec/emacs/20.7/emacs" "$@"
