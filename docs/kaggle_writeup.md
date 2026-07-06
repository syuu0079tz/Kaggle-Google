# CareCompass Agent

## Subtitle

A privacy-first multi-agent routing assistant for Monash student support resources in Australia.

## Track

Agents for Good

## Problem

Monash students often ask for help when they are already stressed: rent is due, exams are close, wellbeing is declining, or the right service is unclear. A normal chatbot can produce generic advice, but it may also collect too much personal data, hallucinate resources, miss urgent safety language, or provide advice that belongs to qualified professionals.

CareCompass Agent solves a narrow version of that problem. It converts a messy support request into a safe, practical action plan using a verified public catalog of Monash and Australian support resources. The app shows official URLs so judges can inspect the recommendation source.

## Target Audience And Functional Scope

The target users are current Monash students in Australia, especially first-year and international students, plus staff, mentors, or peers helping a student find the right official channel.

The app is in scope for support routing: classifying needs, matching official resources, suggesting a first contact and backup path, adding privacy reminders, and escalating urgent safety language to human or emergency support.

The app is out of scope for counselling, emergency response, legal, visa, medical, or financial advice. It does not book appointments, send messages, collect documents, store case records, or recommend services outside the verified catalog.

## Solution

CareCompass uses a four-agent workflow:

1. Intake Agent redacts PII and classifies need categories such as academic, wellbeing, finance, housing, international support, health, accessibility, career, legal, or crisis.
2. Resource Matcher Agent calls an allowlisted catalog tool. It ranks support resources by detected needs, location, urgency, and safety relevance.
3. Planner Agent creates a short next-step plan with a first contact, backup path, preparation guidance, and a privacy reminder.
4. Safety Reviewer Agent adds guardrails, crisis escalation language, and a safe public trace.

The user gets a concise plan instead of a long essay. Judges can inspect the agent trace without seeing private phone numbers, email addresses, or student identifiers.

## Course Concepts Demonstrated

**Agent / multi-agent system.** The deterministic implementation is in `src/care_compass/agents.py`, coordinated by `CareCompassOrchestrator`. The ADK-ready entrypoint in `src/care_compass/adk_app.py` exposes the same workflow as a Google ADK tool.

**MCP server.** `src/care_compass/mcp_server.py` exposes the catalog and safety tools over a dependency-free JSON-RPC server. `src/care_compass/mcp_fastmcp.py` shows the official FastMCP path when optional MCP dependencies are installed.

**Security features.** The app redacts PII, detects prompt-injection attempts, uses an allowlisted tool registry, avoids secrets, and escalates crisis or regulated-advice cases. Tests cover these behaviors.

**Agent skills.** The `skills/` directory contains portable `SKILL.md` files for intake safety, resource matching, and follow-up planning. The agents load the relevant skill only when the specialist runs.

**Evaluation and deployability.** `evals/cases.json` and `scripts/run_evals.py` run local checks for expected needs, PII-free traces, human review routing, and tool allowlisting. The Dockerfile runs the web demo on port 8080 and can be deployed to Cloud Run.

## Technical Implementation

The core app uses Python standard library modules only, which makes it easy to run in Kaggle, locally, or in a container. The web demo is served by `http.server`, and the CLI is available through `python -m care_compass.cli`. The local catalog is stored in `data/resources.json`.

The most important design choice is that the agent is not allowed to invent resources or tools. It can only call `search_resources`, `get_resource`, and `safety_check` through `ToolRegistry`. This keeps behavior auditable and reduces the risk of hallucinated support routes.

## Demo

Example request:

> I am a first-year international student. I am behind on rent, anxious about exams, and I do not know which campus service to contact first.

Expected output:

- The request does not require personal contact details.
- Needs include international, finance, wellbeing, and academic support.
- Top recommendations include international support, financial aid, wellbeing, academic skills, and general student services.
- The safety notice says this is a routing assistant, not emergency, medical, legal, or financial advice.

## Future Work

The next iteration would add scheduled re-verification for public contact details, human-in-the-loop approvals for resource updates, more multilingual cases, and deploy the ADK version with managed observability.
