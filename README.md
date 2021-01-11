# Jejune.

Jejune is a work in progress ActivityPub server designed to use constructions
which provide functional security and resilience.  Unlike most other
implementations, Jejune does not use SQL databases, but instead uses a
filesystem inspired by Linked Data concepts and RDF, which can be replicated
in real-time using IPFS.

It has some level of API compatibility with Mastodon and Pleroma applications.

# Installation

1. `python3 -m virtualenv prod`
2. `source ./prod/bin/activate`
3. `pip3 install -r requirements.txt`
