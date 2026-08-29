# Policy reference

Policies are YAML documents with a strict versioned schema. Unknown fields, negative durations,
unsupported versions, and malformed YAML are rejected instead of silently ignored.

```yaml
version: 1
retention:
  stopped_containers: 168h
  dangling_images: 72h
  build_cache: 168h
protection:
  labels:
    keep: "true"
  image_tags:
    - latest
volumes:
  allow_named_volume_deletion: false
networks:
  allow_custom_network_deletion: false
build_cache:
  allow_deletion: false
```

## Durations

A duration is a positive integer followed by one unit:

| Unit | Meaning | Example |
|---|---|---|
| `s` | seconds | `30s` |
| `m` | minutes | `45m` |
| `h` | hours | `72h` |
| `d` | days | `7d` |
| `w` | weeks | `2w` |

Decimal, zero, and negative durations are invalid.

## Retention

- `stopped_containers` uses the finish time when available, otherwise the creation time.
- `dangling_images` applies only to untagged images not referenced by any container.
- `build_cache` applies only when cache deletion is enabled and the entry is not in use.

## Protection

`labels` is an exact key/value match. A matching resource is protected. `image_tags` accepts shell
patterns and compares both the complete tag and its value after the final colon.

Policy settings cannot disable hard invariants such as running-container or default-network
protection.

## Destructive opt-ins

Named volumes and custom networks are protected until their matching opt-in is `true`. Build cache
can be classified as a candidate when enabled, but V1 reports it as skipped during execution because
targeted deletion cannot be guaranteed by the Docker prune API.

