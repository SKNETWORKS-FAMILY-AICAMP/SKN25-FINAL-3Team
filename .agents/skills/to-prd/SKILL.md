---
name: to-prd
description: Turn the current conversation context into a PRD and publish it to the project issue tracker. Use when user wants to create a PRD from the current context.
---

This skill takes the current conversation context and codebase understanding and produces a PRD. Do NOT interview the user — just synthesize what you already know.

The issue tracker and triage label vocabulary should have been provided to you — run `/setup-matt-pocock-skills` if not.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the PRD, and respect any ADRs in the area you're touching.

2. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can.

Check with the user that these seams match their expectations.

3. Write the PRD using the template below, then publish it to the project issue tracker. Apply the `ready-for-agent` triage label - no need for additional triage.

<prd-template>

**작성일:** {date}
**상태:** Ready for Implementation
**요구사항 유형:** {one of below}

> - **기능 요구사항**: 사용자가 시스템으로 무언가를 할 수 있어야 하는 것. 없으면 기능이 동작 안 함.
> - **비기능 요구사항**: 성능·보안·가용성 등 품질 속성. 없어도 기능은 동작하지만 품질이 나쁨.
> - **개발자/품질 요구사항**: 테스트·CI·코드 컨벤션 등 팀 내부 체계. 대상이 end user가 아닌 개발팀.

---

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## 유저 스토리

A LONG, numbered list of user stories in Korean. Each user story should be in the format of:

1. {actor}로서, {기능}을 원한다. {benefit} 때문이다.

<user-story-example>
1. 모바일 뱅킹 고객으로서, 계좌 잔액을 확인하고 싶다. 지출에 대해 더 나은 결정을 내릴 수 있기 때문이다.
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this PRD.

## Further Notes

Any further notes about the feature.

</prd-template>
