# PL-0037 — Stream Deck MCP Server Evaluation

Status: Captured
Priority: High
Category: AI Integration / Estate Tooling
Originator: Pat / Steward
Date Captured: 2026-08-06
Target Milestone: After current Comms8 startup and integration work is stable

## Idea

Investigate Elgato Stream Deck's built-in Model Context Protocol (MCP) server and determine whether it can become a first-class integration point for the Estate.

Recent Stream Deck releases include an MCP server that can be enabled directly from Stream Deck. Evaluate how this capability could improve the Estate's interaction with AI systems compared to the current approach.

Areas to investigate include:

- Direct integration with ChatGPT, Codex, and other MCP-capable AI clients.
- Whether Estate services can expose tools through or consume tools from the Stream Deck MCP server.
- Opportunities to simplify current Stream Deck automation.
- Using MCP as a cleaner interface for launching Estate actions, workflows, notifications, and context-aware controls.
- Security, permissions, local-only operation, and coexistence with Estate Comms8 and other MCP providers.

## Why It Is Parked

The Estate already makes extensive operational use of the Stream Deck, but investigating a new MCP integration would interrupt higher-priority engineering work. The capability appears promising and should be evaluated deliberately after the current campaign is complete.

## Promotion Condition

Promote when the current Comms8 engineering campaign is stable or when Stream Deck MCP capabilities become strategically important for Estate automation or AI orchestration.

## Explicit Non-Action

Do not enable, configure, redesign, or replace existing Stream Deck automation solely because this capability exists. Treat this as an architectural investigation until intentionally promoted.

## Related Evidence

- Existing Estate Stream Deck operational integration.
- Stream Deck built-in MCP server feature announced by Elgato.
- Future evaluation should compare the built-in MCP capability against existing Estate automation and integration approaches.
