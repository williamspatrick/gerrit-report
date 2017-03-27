# Purpose

Generate information on next-steps for outstanding Gerrit commits per
the OpenBMC merge policies.

# Requirements

1. python3
2. An ssh alias to Gerrit `openbmc.gerrit`

# Usages

## Default use

Generate a report for all commits untouched in the last day:

```gerrit-report.py report```

## Individual developer

List the current status on all your own commits.

```gerrit-report.py --age=0d --owner=<github_id> report```

## Team lead

List the current status of your teams commits.

```gerrit-report.py --age=0d --owner=<github0> --owner=<github1> ... report```

This has the effect of a Gerrit query such as
`(owner:github0 OR owner:github1)`.
