# Security Model

CareCompass is designed for a public capstone repository. It avoids storing secrets and avoids sending private text to external APIs in the default path.

## Controls

- PII redaction for common emails, phone numbers, and student identifiers.
- Prompt-injection detection for attempts to bypass instructions or reveal secrets.
- Tool allowlisting through `ToolRegistry`.
- Crisis and regulated-advice escalation.
- Safe traces that show agent behavior without raw contact details.
- Public resource catalog with official URLs and publicly listed contact channels.

## Boundaries

CareCompass is a routing assistant. It does not provide:

- Emergency services
- Medical diagnosis
- Legal, immigration, or tenancy advice
- Financial advice
- Guaranteed resource availability

## Public Repository Checklist

- No `.env` files.
- No API keys, OAuth tokens, passwords, or private URLs.
- No real user requests in tests or docs.
- Keep `data/resources.json` limited to verified public data only.
- Re-check public contact details before recording a demo or submitting a writeup.
- Review generated traces before using them in a public video or writeup.
