flowchart TD

%% STYLE
classDef mode fill:#e3f2fd,stroke:#1565c0,stroke-width:1px;
classDef decision fill:#fff3e0,stroke:#ef6c00,stroke-width:1px;
classDef doc fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px;
classDef risk fill:#ffebee,stroke:#c62828,stroke-width:1px;
classDef work fill:#f3e5f5,stroke:#6a1b9a,stroke-width:1px;

%% START
S0([Project Starts])

%% INTERVIEW / POLICY
S1[Interview Mode<br/>– gather requirements & constraints]:::mode
S2[Derive profile & tier<br/>– risk, size, criticality]:::mode
S3[Write PROJECT_POLICY.yaml<br/>+ ADR-0001 workflow & tier]:::doc

S0 --> S1 --> S2 --> S3

%% DESIGN & PLANNING
S4[Design Mode<br/>– architecture, data, APIs,<br/>test & observability & security strategy]:::mode
S5[Select tech stack<br/>+ create tech-stack ADRs]:::doc
S6[Planning Mode<br/>– define Epics, Features, Tasks/Bugs]:::mode
S7[Setup Mode<br/>repo scaffolding, CI/CD,<br/>issue templates, boards]:::mode
S8[Initial CODE_MAP.md + core docs<br/>README, VISION, REQUIREMENTS, etc.]:::doc

S3 --> S4 --> S5 --> S6 --> S7 --> S8

%% MAIN DELIVERY LOOP
subgraph EPIC_LOOP[Per Epic]
direction TB

  E0[Create or refine Epic<br/>+ Issues in board]:::work
  E1[Tag epic-<id>-start]:::doc
  E2[Select next Task or Feature<br/>from Ready column]:::work

  E0 --> E1 --> E2

  %% TASK WORKFLOW
  subgraph TASK_LOOP[Per Task or Feature]
  direction TB

    T0[Understand<br/>read ADRs, requirements,<br/>code & restate task]:::work
    T1[Plan<br/>3–7 steps covering code, tests,<br/>observability, security, risks]:::work
    T2[Implement changes<br/>aligned to architecture]:::work
    T3[Add or update tests<br/>meet coverage targets]:::work
    T4[Run static checks locally<br/>formatters, linters, type checks]:::work
    T5[Open or update PR<br/>link Issue and ADRs]:::doc

    T0 --> T1 --> T2 --> T3 --> T4 --> T5

    %% AMBIGUITY HANDLING
    D_AMB{Ambiguity<br/>or design decision}:::decision
    T0 --> D_AMB

    D_AMB -->|Tier 1<br/>low risk internal| A1[Self resolve conservatively<br/>log in Task or PR and Epic Decision Log]:::work --> T1
    D_AMB -->|Tier 2<br/>behaviour only| A2[Propose options A, B, C<br/>pick conservative default<br/>mark pending confirmation]:::work --> T1
    D_AMB -->|Tier 3<br/>high risk such as API, data, security, infra, cost, compliance| A3[Draft Supervisor Approval Needed ADR<br/>optional Proposal Branch<br/>wait for decision]:::work

    A3 --> D_APP{Supervisor responded<br/>within window}:::decision
    D_APP -->|Yes approved or modified| T1
    D_APP -->|No| A3_LOW[Continue only low risk in scope work<br/>Proposal Branch exploration allowed]:::work --> T1

    %% CI / CRITIC / MERGE
    C0[CI run<br/>on PR]:::work
    T5 --> C0

    D_FAIL{CI green}:::decision
    C0 -->|Yes| C1[Critic Pass as hostile reviewer<br/>add checklist note on PR]:::work
    C0 -->|No| F0[Analyse logs and adjust<br/>code, tests, config]:::work --> C0

    D_CRIT{Critic Pass OK<br/>no blocking issues}:::decision
    C1 --> D_CRIT
    D_CRIT -->|Yes| D_AUTO{Safe to auto merge<br/>coverage within limits<br/>no major risk}:::decision
    D_CRIT -->|No| F1[Fix issues from Critic Pass<br/>re run CI]:::work --> C0

    D_AUTO -->|Yes| M_AUTO[Auto merge PR]:::work
    D_AUTO -->|No or any doubt| M_HUMAN[Mark as needs human review<br/>label, comment, or review request]:::work

    %% CIRCUIT BREAKER
    D_CB{Reached 5 total CI attempts<br/>or 3 similar failures}:::decision
    F0 --> D_CB
    D_CB -->|Yes| B0[Trigger Circuit Breaker<br/>revert to known good state<br/>pre Task commit or checkpoint]:::risk
    D_CB -->|No| C0

    B0 --> B1[Create BLOCKER Issue<br/>mark Task as Blocked]:::risk

    %% MULTIPLE BLOCKERS PER EPIC
    B1 --> D_MULTI{Epic has at least 3 active Blockers}:::decision
    D_MULTI -->|Yes| B2[Create Epic level risk summary<br/>flag Epic as at risk<br/>request supervisor input]:::risk

    %% BLOCKER TIMEOUT
    B1 --> D_BTO{Supervisor responded<br/>within window}:::decision
    D_BTO -->|Yes| T0
    D_BTO -->|No| B3[Propose alternative approach<br/>optional Proposal Branch<br/>do not merge or deploy]:::risk --> E2

  end

  E2 --> TASK_LOOP --> E3[More Tasks or Features<br/>remaining in Epic]:::decision
  E3 -->|Yes| E2
  E3 -->|No| E4[Tag checkpoints for major Features<br/>epic-<id>-feature-...-done]:::doc

  %% EPIC COMPLETION
  E4 --> E5[Prepare Epic Review Bundle<br/>per tier]:::doc
  E5 --> E6[Update EPIC_LOG.md<br/>and CODE_MAP.md if needed]:::doc
  E6 --> E7[Move Epic to Ready for Human Review]:::work
  E7 --> D_EAPP{Supervisor Epic review<br/>and acceptance}:::decision
  D_EAPP -->|Accepted| E8[Mark Epic Done]:::work
  D_EAPP -->|Changes requested| E9[Create follow-up Issues or Epics<br/>iterate]:::work --> E2

end

S8 --> EPIC_LOOP

%% INCIDENT / RECOVERY
I0{{Incident detected<br/>or severe regression}}:::decision
EPIC_LOOP --> I0
I0 -->|Yes| I1[Incident and Recovery Mode<br/>RCA, fixes, rollback]:::risk --> EPIC_LOOP
I0 -->|No| EPIC_LOOP

%% PROJECT END
E8 --> END([Project or release milestone reached])
