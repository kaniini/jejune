# Jejune.

![Matrix](https://img.shields.io/matrix/jejune:ariadne.space?logo=matrix&server_fqdn=dendrite.ariadne.space&style=for-the-badge)

Jejune is a work in progress ActivityPub server designed to use constructions
which provide functional security and resilience.  Unlike most other
implementations, Jejune does not use SQL databases, but instead uses a
filesystem inspired by Linked Data concepts and RDF, which can be replicated
in real-time using IPFS.

It has some level of API compatibility with Mastodon and Pleroma applications.

**This is alpha-quality software and does not yet support many features necessary
for running a secure instance, it also lacks moderation tools.  You should not
run this software in production yet.**

# Installation

1. `python3 -m virtualenv prod`
2. `source ./prod/bin/activate`
3. `pip3 install -r requirements.txt`
