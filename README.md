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

These instructions assume the user is using Alpine Linux.  If you are using a
different OS, you will need to translate the directions accordingly.

Before you proceed, you will need to install some dependencies:

```
# apk add build-base python3-dev openssl-dev
```

You will also want to create a user.  Do not run Jejune as root!

```
# adduser jejune
[...]
# su - jejune
$ git clone https://github.com/kaniini/jejune
[...]
$ cd jejune
```

We recommend the use of a Python `virtualenv`.  First, create a `virtualenv` using
the `virtualenv` module and enter it:

```
$ python3 -m virtualenv prod
$ source ./prod/bin/activate
```

Next, install the dependencies:

```
(prod) $ pip3 install -r requirements.txt
```

You will need to configure your instance.  Copy `config.yaml.example` and edit it:

```
(prod) $ cp config.yaml.example config.yaml
(prod) $ nano config.yaml
```

Finally, you will need to create your admin user:

```
(prod) $ JEJUNE_CONFIG=config.yaml python3 -m jejune.tasks.create_user
[...]
```

You can now launch the Jejune server, which will listen on localhost:8080.  You should
configure nginx or caddy or whatever server you use to proxy requests to localhost:8080.

```
(prod) $ JEJUNE_CONFIG=config.yaml python3 -m jejune
[...]
Starting webserver on 127.0.0.1:8080
```

At this point, you can go to `/.well-known/jejune` on your instance to access
jejune-client.  Happy blogging!