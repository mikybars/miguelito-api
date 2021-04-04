# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2021-04-04
### Added
- Custom paths.
- Copy to clipboard button.
- Custom 404 page.
- Dump S3 error messages to console.
- Warn about stupid errors like sending the URL in all uppercase (valid URL but S3 refuses to accept it as a correct `WebsiteRedirectLocation`).

### Changed

* Minor UI improvements.

### Fixed

* URL validation (https://www.google.com/ ✅ https://www.google.com ❌)

## [1.0.0] - 2020-12-23

[Unreleased]: https://github.com/mperezi/aws-lambda-url-shortener/compare/v1.1..HEAD

[1.1.0]: https://github.com/mperezi/aws-lambda-url-shortener/compare/v1.0..v1.1

[1.0.0]: https://github.com/mperezi/aws-lambda-url-shortener/releases/tag/v1.0
