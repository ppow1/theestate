# Parking Lot Item

Status: Captured
Priority: Strategic
Classification: Estate Internal

## ID

PL-0030

## Idea

Evaluate creation of a permanent Estate office responsible for staging resident presence across live video, avatar, and conference-style experiences by coordinating canonical motion, voice, visual, environment, and camera assets.

Provisional working names:

- Office of Estate Performance
- Office of Presentation and Presence
- Estate Presentation Engine

The office would not own resident identity, visual canon, or voice canon. It would consume those authoritative sources and direct how they are presented in time.

Core concept:

- transform the planned motion library into a resident Performance Library
- add a Director Engine that maps conversational intent and runtime state to approved performances
- coordinate facial expression, gaze, listening, speaking, thinking, gestures, posture, movement, office tasks, camera selection, lighting, and environment state
- support FaceTime- or Zoom-like live resident conversations without generating every frame from scratch
- assemble reusable canonical clips and transitions into longer natural performances
- support multi-resident meetings in Estate conference environments

Potential runtime flow:

```text
Resident response and intent
    -> Director Engine
    -> Resident Performance Library
    -> Voice and lip-sync layer
    -> Camera and environment engine
    -> Live video/avatar output
```

Example performance assets:

- seated and standing idle states
- listening and speaking states
- nodding, smiling, concern, empathy, amusement, and thinking
- notebook, coffee, reading, computer, whiteboard, and document interactions
- sit, stand, turn, approach, depart, and walking transitions
- greetings, welcome, farewell, mentoring, collaboration, and celebration
- resident-specific mannerisms and relationship-aware behavior

The long-term result could be an Estate-native video-conferencing experience in which residents appear continuously present, responsive, and recognizable while their underlying foundation models remain implementation details.

## Category

Institutional Architecture / Resident Experience / Live Presentation

## Originator

Pat / Steward and Chief Architect discussion

## Date Captured

2026-07-13

## Optional Target Milestone

After the Visual Canon and initial Motion/Performance Library are materially implemented and Open WebUI resident instantiation is stable.

## Promotion Condition

Promote for active architectural design when all of the following are true:

1. Canonical resident visual packages are available for at least three residents.
2. Resident-specific voice bindings and reliable lip-sync are available.
3. A minimum reusable performance set exists for idle, listening, speaking, thinking, greeting, and basic office interaction.
4. Open WebUI or the Estate runtime can instantiate a resident package reliably.
5. The Steward decides that live resident presence is a higher priority than further still-image expansion.

## Notes

This proposal should remain parked until the current Visual Estate Initiative work packages are converted into real repository artifacts and the underlying libraries exist. It should not interrupt the current production run.

Constitutional question for later review:

Determine whether this capability justifies a new office or should remain a service under an existing office such as Visual Identity, Media Production, Experience Design, or Chief Architect. No office is authorized by this parking item.
