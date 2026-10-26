# Security Policy

## Scope

This project is an **unofficial** Home Assistant integration that talks to the
Rockcore RC-C cloud backend (`app.rc-ess.com`). It is not affiliated with,
endorsed by, or supported by Rockcore / Shanghai Rockcore Electronics
Technology.

## Supported Versions

Only the latest release on the `main` branch receives fixes.

| Version | Supported |
| ------- | --------- |
| latest  | ✅        |
| older   | ❌        |

## Reporting a Vulnerability

Please **do not open public GitHub issues for security problems.**

Instead, use **GitHub Security Advisories** on this repository
(*Security → Report a vulnerability*), or email the maintainer privately.

When reporting, include:

- A description of the issue and its impact.
- Steps to reproduce.
- Affected version/commit.

You can expect an initial acknowledgement within a reasonable time for a
hobby project. Fixes are best-effort.

## Handling of Credentials & Secrets

This integration stores your RC-C **email and password** in Home Assistant's
config entry storage, because the upstream API requires a username/password
login to obtain a bearer token (there is no OAuth or API-key option).

Security considerations you should be aware of:

- **Credentials are sent over HTTPS** to `app.rc-ess.com`.
- The access token is kept **in memory only** and refreshed by re-login on
  `401`. It is never written to disk by this integration.
- Your Home Assistant instance protects the stored password; treat your HA
  backups as secrets.
- **Never commit** credentials, bearer tokens, or captured traffic
  (`*.flows`, `*.har`, `*.pcap`) to this repository. They are excluded in
  `.gitignore`.

## Responsible Use

The API contract was reverse-engineered by inspecting the traffic of the
author's **own account and hardware** on the author's own network. Only use
this integration with accounts and devices you own. The upstream API is
undocumented and may change or break at any time.
