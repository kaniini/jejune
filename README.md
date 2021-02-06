# Jejune.

![Matrix](https://img.shields.io/matrix/jejune:ariadne.space?logo=matrix&server_fqdn=dendrite.ariadne.space&style=for-the-badge)

Jejune is a work in progress personal ActivityPub server designed to use constructions
which provide functional security and resilience.  Unlike most other
implementations, Jejune does not use SQL databases, but instead uses a
filesystem inspired by Linked Data concepts and RDF, which can be replicated
in real-time using IPFS.

It provides a public website that can be themed by the end user, powered by Jinja
templates and CSS variables.

![Screenshot (public frontend, default theme)](https://ariadne.space/.well-known/jejune/upload/69528f56-0d63-4ca6-80d2-5a9491932f58.jpg)

For posting on the go, it has some level of API compatibility with Mastodon and
Pleroma applications, but normally, it is driven by the ActivityPub client protocol
and [jejune-client](https://github.com/kaniini/jejune-client).

![Screenshot of jejune-client](https://ariadne.space/.well-known/jejune/upload/5d9b55f6-ce69-4992-82f1-8c2e2c9d337b.jpg)

## Important

**This is alpha-quality software and does not yet support many features necessary
for running a secure instance, it also lacks moderation tools.  You should not
run this software in production yet.**

## Installation

1. `python3 -m virtualenv prod`
2. `source ./prod/bin/activate`
3. `pip3 install -r requirements.txt`
