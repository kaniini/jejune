# Jejune Milestone 2 (v0.0.2) [February 18, 2021]

* Many jejune-client improvements:
  - Search for and follow users
  - Better display of interactions
  - Lightbox
  - Infinite scrolling on the dashboard

* Improved support for HTTP signatures:
  - Support for validating HS2019 signatures (we still send RSA-SHA256 signatures for now)

* Numerous ActivityStreams/ActivityPub improvements:
  - Support for the `replies` collection
  - Support for the `liked` and `likes` collections
  - Support for the `shares` and `jejune:shared` collections
  - Collection rendering for clients

* Implemented support for signed object fetches

* Improved `Accept` header handling

* Improved inbox processing worker robustness

# Jejune Milestone 1 (v0.0.1) [February 6, 2021]

* Initial release!
