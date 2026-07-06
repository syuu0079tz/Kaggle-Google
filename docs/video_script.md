# Five-Minute Video Script

## 0:00-0:30 Problem

Introduce CareCompass Agent. The target users are current Monash students in Australia, especially first-year and international students, plus staff or peers helping them find the right official support channel. Students often need support across finance, wellbeing, housing, academic issues, or international services, but they may not know where to start and may share private details in the process.

## 0:30-1:10 Why Agents

Explain why a multi-agent workflow is useful: one specialist handles safe intake, one searches verified Monash and Australia-wide public resources, one writes the plan, and one reviews safety. This is more controlled than a single open-ended chatbot.

## 1:10-2:10 Architecture

Show the diagram in the web app. Point to:

- Intake Agent
- Resource Matcher Agent
- Planner Agent
- Safety Reviewer Agent
- Local resource catalog
- MCP tool server
- Agent skills loaded from `skills/*/SKILL.md`

## 2:10-3:20 Demo

Paste the sample request:

```text
I am a first-year international student. I am behind on rent, anxious about exams, and I do not know which campus service to contact first.
```

Show that the agent detects international, finance, wellbeing, and academic needs. Show that the public trace avoids private contact details. Explain the first recommendation and backup path.

## 3:20-4:10 Security And Evaluation

Run:

```bash
python -m unittest discover -s tests
python scripts/run_evals.py
```

Mention prompt-injection detection, PII redaction, tool allowlisting, and crisis escalation.

## 4:10-4:50 Deployability

Show:

```bash
docker build -t care-compass-agent .
docker run -p 8080:8080 care-compass-agent
```

Mention Cloud Run deployment notes in `docs/deployment_cloud_run.md`.

## 4:50-5:00 Close

Summarize: CareCompass is a small but practical Agents for Good project for Monash student support routing. It demonstrates multi-agent design, MCP tools, skills, security, evaluation, and deployability.
