# FAQs about Jejune.

## What is Jejune?

Jejune is an ActivityPub server designed for personal use.  It
is designed to be forward-looking and make the most out of lower
spec machines.  While it should be perfectly scalable to large
instances in the future, this is not presently the focus of the
project.  It is designed to leverage the ActivityPub protocol
as presently implemented in a safe way.

## Why?

After years of working on other ActivityPub projects (Mastodon
and Pleroma), I decided to take a break for a while.  But it
seems that I still have things to say on the topic.  While
Mastodon and Pleroma have both made leaps and bounds in terms
of progress when it comes to building a safe federated social
network, there are still many design flaws.  One of the key
features I have argued for is that security primitives should
be rigid and clearly understood.  Because of the promises both
projects have made in the past, attempts to correct the
security defects in the respective implementations has focused
on attempts to add security after the point, by shoehorning in
security labels and OCAP.  It may be that these attempts may
provide some marginal security improvements, but if the core
is rotten, the security will still be fundamentally broken.

## Why "Jejune"?

Jejune is the state of being simplistic to the point that
something is boring and predictable.  This succinctly describes
the design goal of the implementation: the security primitives
in Jejune are effective while not depending on security labels,
OCAP or cryptography.

## Why does Jejune store its object graph in /.well-known/jejune?

Jejune, as a personal AP server, is meant to be overlaid on
top of a personal website.  This allows for a user to simply
forward the `/.well-known/jejune` and `/.well-known/webfinger`
paths to Jejune as well as the `/api/v1` path used by the
Mastodon API emulation.

## What moderation tools will Jejune support / already supports?

Jejune is planned to support the usual moderation tools,
such as deleting posts and blocking users from an instance.

Additionally, a fully programmable message filtering scheme
which is similar to Pleroma's MRF is planned, but some
amount of design work will be needed to implement.  Stay tuned,
this will be ready by v0.4 or so, hopefully.

## Governance?

Jejune is committed to using the Open Decision Framework as
advanced by Fedora.  In the event of lack of consensus, I
will make the final decision.

The Open Decision Framework has been lauded for its
effectiveness and fairness as a governance tool, ensuring
that traditionally marginalized voices have an equal seat
at the table.

## Will you maintain this forever?

No.  My plan is to implement the basic features and then
hand off maintenance to the community.

## Will you support interoperability with other implementations?

Jejune will support basic interoperability with Mastodon and
Pleroma, in situations where the security primitives allow
for it.  Jejune is not intended to interoperate with the
fediverse at large.

## Will you work with other projects on interoperability?

LOL.

## Will you work with the W3C on standardizing work in Jejune?

LOL.

## Jejune doesn't include a web client?

Correct.  If you need a web client, there are many good ones
that are already compatible, such as Pleroma FE and the
Mastodon Web Client.  Additionally, Mastodon and Pleroma
mobile apps are also compatible with Jejune.

## Why ISC license instead of something like CNPL?

While the goals of the CNPL are interesting, the license has
not been drafted by a lawyer.  The ISC license is a well-understood
license.  It is hoped that our commitment to a social contract
that puts all stakeholders first will make bigots use different
software.

And on that note, if you publish software on the Internet,
it does mean that anyone can download and use it.  Such usage
is protected by the Berne convention as fair use.  I am
therefore not convinced that copyright is an effective tool
for enforcing a specific code of ethical software use.
