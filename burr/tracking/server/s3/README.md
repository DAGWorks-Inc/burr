# S3-backed server

## Architecture

## Deployment

## Migrating/Initializing

- make sure aerich is installed

To reset, do:
```bash
rm -rf ~/.burr_server &&
mkdir ~/.burr_server &&
rm -rf ./burr/tracking/server/s3/migrations &&
aerich init -t burr.tracking.server.s3.settings.TORTOISE_ORM --location ./burr/tracking/server/s3/migrations  &&
aerich init-db &&
AWS_PROFILE=dagworks burr --no-open
```
```
- `rm -rf ~/.burr_server` (will be turned to an env variable)
- `mkdir ~/.burr_server` (ditto)
- (from git root) `rm -rf ./burr/tracking/server/s3/migrations`
- (from git root) `aerich init -t burr.tracking.server.s3.settings.TORTOISE_ORM  --location ./burr/tracking/server/s3/migrations`
- (from git root) `aerich init-db`
