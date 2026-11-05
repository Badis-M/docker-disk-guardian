# Examples

## Inspect only images and containers

```bash
docker-disk-guardian inspect --include image --include container
```

## Exclude build cache from inventory

```bash
docker-disk-guardian inspect --exclude build_cache
```

## Export a Markdown plan for review

```bash
docker-disk-guardian plan \
  --policy examples/policy.yaml \
  --format markdown \
  --output cleanup-plan.md
```

## Allow named-volume deletion

Use this only after reviewing the exact named volumes reported by `plan`:

```yaml
version: 1
volumes:
  allow_named_volume_deletion: true
```

Existing container references and protection labels still take precedence over this opt-in.

## Run the isolated integration test

The test requires an already available `busybox:1.36` image and never pulls it automatically:

```bash
DDG_RUN_INTEGRATION=1 pytest -m integration
```


Markdown reports escape markup and line breaks in resource names and decision text.

File output replaces the destination atomically with a private report. Existing symlinks are rejected.

JSON inventory lists resources by ID within each resource type for stable comparisons.
