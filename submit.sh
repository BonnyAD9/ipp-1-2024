#!/usr/bin/sh

tar czf xstigl00.tgz -- *.py readme1.md rozsireni &&
    ./is_it_ok.sh xstigl00.tgz testout <<<y
