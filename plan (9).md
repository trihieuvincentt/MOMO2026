# ScamGuard AI --- Product & Development Plan

> **Product positioning:** An AI-powered Scam Investigation & Prevention
> Platform\
> **Tagline:** Don't just detect scams. Investigate them. Explain them.
> Prevent them.\
> **Project horizon:** 10--11 days\
> **Team size:** 2--3 members\
> **Target:** A reliable, demonstrable MVP for a competitive technology
> contest

------------------------------------------------------------------------

## 1. Executive Summary

ScamGuard AI helps people assess suspicious online interactions before
they lose money or disclose sensitive information. It accepts evidence
from multiple sources---messages, URLs, and screenshots---then analyzes
the evidence, identifies relevant risk indicators, explains its
findings, and recommends safe next steps.

The product should not be presented as a generic chatbot that labels
messages as scams. Its differentiator is an **evidence-based
investigation workflow**:

1.  Collect evidence from more than one input type.
2.  Analyze each input with the appropriate detection component.
3.  Correlate findings without assuming that correlation proves
    wrongdoing.
4.  Produce an explainable risk assessment with evidence and
    uncertainty.
5.  Recommend practical prevention or incident-response actions.

The MVP prioritizes a complete, dependable end-to-end experience over a
large number of partially implemented features.

## 2. Problem Statement

People encounter suspicious messages, websites, recruitment offers,
marketplace sellers, and payment requests across many channels. They may
not know which signals matter, how to verify a claim, or what to do
next.

Existing point solutions often inspect only one item at a time. A
message checker may not inspect the linked website; a URL checker may
not understand the conversation that led the user to that URL. Users
also need explanations and actionable guidance---not just a risk label.

**Problem to solve:** Help a user bring together relevant evidence from
a suspicious interaction and understand the risk, the reasons behind the
assessment, and the safest next action.

## 3. Target Users and Primary Use Cases

### Primary users

-   Everyday internet users who receive unexpected messages or links.
-   Students and job seekers exposed to fake recruitment offers and
    advance-fee scams.
-   Online shoppers who need to assess suspicious sellers, payment
    requests, or stores.

### MVP use cases

1.  A user pastes a suspicious SMS, email, or chat message.
2.  A user submits a URL they received from an unknown sender.
3.  A user uploads a screenshot; the system extracts text and analyzes
    it.
4.  A user combines a message and a URL in one investigation.
5.  A user asks the AI Advisor what to do before paying or after
    interacting with a suspicious party.

## 4. Product Principles

-   **Evidence before conclusions:** Every risk indicator shown to the
    user must be traceable to an input or a named data source.
-   **Explain uncertainty:** Distinguish confirmed matches, suspicious
    indicators, and information that could not be verified.
-   **Prevention over alarm:** Give practical next steps instead of
    relying on frightening language.
-   **Human decision remains central:** ScamGuard advises; it does not
    independently accuse a person or guarantee that a transaction is
    safe.
-   **Privacy by design:** Collect the minimum information needed,
    protect uploaded evidence, and avoid exposing credentials, OTPs, or
    unnecessary personal data.
-   **Safe URL handling:** Do not fetch arbitrary URLs from the main
    application environment. Use trusted reputation services or an
    isolated, restricted analysis service.

## 5. Product Scope

### 5.1 MVP --- Must Have

  -----------------------------------------------------------------------
  Feature                 Description             Acceptance criteria
  ----------------------- ----------------------- -----------------------
  Message Scanner         Analyze pasted message  User receives a
                          text for scam           structured report with
                          indicators such as      indicators, quoted
                          urgency, impersonation, evidence, risk
                          credential requests,    category, uncertainty,
                          advance fees, and       and recommended
                          suspicious payment      actions.
                          instructions.           

  URL Scanner             Parse and assess a      User receives
                          submitted URL using     domain/URL
                          safe URL features and   observations,
                          an available reputation reputation lookup
                          source.                 status, evidence, and
                                                  clear limitations.

  Screenshot OCR          Accept an image,        User can inspect
                          extract readable text,  extracted text and run
                          and pass extracted text the same analysis flow;
                          to the Message Scanner. OCR failures are
                                                  handled clearly.

  Investigation Case      Combine two or more     Report shows each
                          submitted evidence      item's findings and any
                          items, such as a        supported cross-item
                          message and a URL, into relationships.
                          one case.               

  Explainable Risk        Aggregate evidence into Each displayed reason
  Assessment              a transparent risk      is linked to evidence;
                          level.                  no unsupported
                                                  numerical certainty is
                                                  presented.

  AI Security Advisor     Answer questions using  Advice is relevant,
                          a curated safety        cites retrieved
                          knowledge base and the  knowledge sources where
                          current case context.   available, and does not
                                                  invent verification
                                                  results.

  Investigation Report    Present summary,        A user can understand
                          evidence, findings,     why the case was
                          unknowns, and next      flagged and what to do
                          steps.                  without reading raw
                                                  model output.
  -----------------------------------------------------------------------

### 5.2 Should Have --- If Core MVP Is Stable

-   Save recent investigation cases for the current user/session.
-   Export or copy a concise report.
-   Include a "What should I do now?" action panel for common incidents.
-   Add a small dashboard with aggregate counts from test/demo data.

### 5.3 Out of Scope for the 10--11 Day MVP

-   Direct integration with MoMo, banks, or payment rails.
-   Automatic blocking or stopping of transfers.
-   Definitive verification of a bank transfer from a screenshot.
-   Community-wide reporting and reputation scoring of individuals.
-   Voice-call deepfake detection or real-time call monitoring.
-   Browser extension and native mobile application.
-   Automated crawling of arbitrary suspicious websites.
-   Claims that an account holder or phone number is a criminal based
    only on user reports.

These may be described as future opportunities, not as completed
capabilities.

## 6. Core User Journey

1.  **Start an investigation:** User chooses message, URL, or
    screenshot.
2.  **Add evidence:** User pastes text, enters a URL, or uploads an
    image.
3.  **Review extraction:** For images, user can review OCR output before
    analysis.
4.  **Analyze:** Relevant scanners run and return structured findings.
5.  **Add related evidence:** User may add another message, URL, or
    screenshot to the same case.
6.  **Correlate:** Investigation Engine identifies supported
    relationships and contradictions.
7.  **Review report:** User sees risk level, evidence,
    confidence/limitations, and recommended next steps.
8.  **Ask Advisor:** User asks follow-up questions grounded in the case
    and safety knowledge base.

## 7. Differentiating Product Capabilities

### 7.1 Multi-source Scam Investigation

The key product differentiator is the ability to examine a suspicious
interaction as a case rather than treating each input as an isolated
classification request.

Example scenario:

-   A job seeker receives a message offering unusually attractive pay.
-   The sender asks for an upfront "verification fee."
-   The message includes a recruitment website URL.
-   The user submits the message and URL together.

ScamGuard analyzes the message and URL separately, then creates a
unified report. It may identify that the message requests an advance
payment and that the domain has not been verified as an official
recruitment site. It must not claim the site is malicious unless a
reliable source supports that conclusion.

### 7.2 Explainable AI

The report should answer:

-   What exactly triggered concern?
-   Which part of the submitted evidence supports each finding?
-   Was a finding confirmed by an external source or inferred from
    content?
-   What could not be checked?
-   What should the user do next?

Use evidence labels such as:

-   **Verified match:** A trusted source returned a matching result.
-   **Suspicious indicator:** The content contains a known risk pattern.
-   **Unverified:** Available data is insufficient to confirm or dismiss
    the concern.
-   **No signal found:** The check did not identify a known indicator;
    this is not a guarantee of safety.

### 7.3 Before You Pay

Provide a guided, advisory checklist before a user makes a payment:

-   Is the request unexpected or urgent?
-   Is an upfront fee requested for a job, prize, loan, or release of
    funds?
-   Does the recipient/payment information match the claimed
    organization?
-   Can the seller or organization be contacted through an independently
    found official channel?
-   Is the user being asked for an OTP, password, recovery code, or
    remote access?

The MVP can assess user-provided context and provide a recommendation.
It must not imply that it has checked a real bank account or can stop a
transfer.

### 7.4 Incident Response Guidance

If a user has already interacted with a suspected scam, provide safe,
general steps appropriate to the situation. Examples include contacting
the bank or payment provider through official channels, changing exposed
passwords, revoking active sessions where possible, enabling
multi-factor authentication, and reporting the incident to the relevant
authorities. The Advisor should ask for no OTPs, passwords, or full
payment credentials.

## 8. System Architecture

``` text
                       Web Frontend
                  (React / Next.js)
                            |
                            v
                     FastAPI Backend
                            |
             +--------------+--------------+
             |              |              |
             v              v              v
       Message Scanner  URL Scanner    Image/OCR
             |              |              |
             +--------------+--------------+
                            |
                            v
                  Investigation Engine
                 - Normalize findings
                 - Link evidence items
                 - Track source and status
                 - Aggregate risk indicators
                            |
                +-----------+-----------+
                |                       |
                v                       v
          Risk Assessment          AI Advisor
          - Rules/weights          - LLM
          - Evidence mapping       - RAG retrieval
          - Uncertainty            - Case context
                |                       |
                +-----------+-----------+
                            |
                            v
                   Investigation Report
                            |
              +-------------+-------------+
              |                           |
              v                           v
        PostgreSQL                  Vector Store
        cases/findings              knowledge chunks
```

### Suggested technology stack

  -----------------------------------------------------------------------
  Layer                   Suggested technology    Notes
  ----------------------- ----------------------- -----------------------
  Frontend                React or Next.js        Choose the framework
                                                  the team can deliver
                                                  fastest.

  Backend                 Python + FastAPI        Typed request/response
                                                  schemas and modular
                                                  routers.

  LLM                     Gemini API or another   Keep provider calls
                          available model API     behind a small adapter.

  OCR                     PaddleOCR or a managed  Select based on setup
                          OCR API                 time and image quality.

  URL intelligence        Trusted URL reputation  Clearly distinguish
                          API / curated test data live lookup from demo
                                                  fixtures.

  Database                PostgreSQL              Store cases, evidence
                                                  metadata, findings, and
                                                  reports.

  Vector database         Qdrant, if needed       Use for the Advisor
                                                  knowledge base; do not
                                                  make it a blocker.

  Embeddings              Compatible embedding    Keep embedding model
                          API/model               and vector dimensions
                                                  consistent.

  Deployment              A simple managed        Prefer a reliable
                          frontend and API host   deployment path over
                                                  complex infrastructure.
  -----------------------------------------------------------------------

### Architecture constraints

-   Keep each scanner independent behind a consistent interface.
-   Use structured JSON outputs from model calls and validate them with
    schemas.
-   Keep API keys on the server; never expose them in frontend code.
-   Set file size/type limits and validate uploads.
-   Do not log raw sensitive user content unnecessarily.
-   Use timeouts, retries where safe, and graceful fallbacks for
    external APIs.
-   Treat model-generated findings as hypotheses unless supported by
    evidence.

## 9. Investigation Data Model

A minimal relational model:

### Case

-   `id`
-   `created_at`
-   `status`
-   `overall_risk`
-   `summary`

### EvidenceItem

-   `id`
-   `case_id`
-   `type` (`message`, `url`, `image`, `ocr_text`)
-   `content_reference` or protected content field
-   `created_at`

### Finding

-   `id`
-   `case_id`
-   `evidence_item_id` (nullable for cross-item findings)
-   `category`
-   `description`
-   `evidence_excerpt`
-   `source_type` (`user_input`, `rule`, `reputation_api`, `llm`,
    `knowledge_base`)
-   `verification_status`
-   `severity`

### Recommendation

-   `id`
-   `case_id`
-   `action`
-   `reason`
-   `priority`

### KnowledgeChunk

-   `id`
-   `source_title`
-   `source_url`
-   `chunk_text`
-   `embedding` (in vector store)

Avoid storing full sensitive content if a short-lived or redacted
representation is sufficient. Define a retention policy before
deployment.

## 10. Risk Assessment Design

Do not ask an LLM to invent a probability such as "95% scam." For the
MVP, use a transparent rule-based aggregation over structured findings.

Example categories:

-   **High risk:** Multiple strong indicators, or a verified malicious
    reputation match.
-   **Elevated risk:** One or more strong indicators that require the
    user to pause and verify.
-   **Caution:** Some suspicious or incomplete signals; more information
    is needed.
-   **No known signal found:** Checks did not identify known indicators;
    this does not mean the item is safe.

For every level, display: - Findings that contributed to the
assessment. - Evidence excerpts or source references. - Verification
status. - Important missing information. - Recommended next action.

Tune thresholds using the evaluation set. Avoid false precision and do
not present an unvalidated score as a calibrated probability.

## 11. AI Advisor and RAG Plan

### Knowledge sources

Prefer trustworthy, current sources such as: - Official cybersecurity
and consumer-protection guidance. - Official bank/payment-provider
safety guidance. - Official guidance on reporting cybercrime or fraud. -
Carefully reviewed educational material about common scam patterns.

For each document, preserve its title, publisher, URL, and retrieval
date.

### Retrieval flow

1.  Ingest and clean source documents.
2.  Split content into semantically useful chunks.
3.  Generate embeddings.
4.  Store chunks and metadata in Qdrant or another selected vector
    store.
5.  Retrieve relevant chunks for a user question.
6.  Optionally add keyword/hybrid retrieval if time permits.
7.  Generate an answer grounded in retrieved sources and case findings.
8.  Return source references and a clear uncertainty statement when
    evidence is insufficient.

### RAG acceptance criteria

-   Answers are relevant to the user's question.
-   Safety instructions are supported by retrieved sources where
    applicable.
-   The model does not claim it checked a bank account, identity, or
    website unless a tool actually performed that check.
-   If retrieval is weak, the Advisor says it cannot verify the point
    and gives safe general guidance.

**Time constraint:** A basic, reliable retrieval pipeline is more
important than adding hybrid search, reranking, or multiple agents. Add
those only after the core workflow works.

## 12. Evaluation and Testing

Create a small, documented evaluation set. A practical initial target
is:

-   30 scam or strongly suspicious examples.
-   20 benign examples.
-   10 ambiguous or insufficient-evidence examples.

These are initial project targets, not a statistically representative
benchmark. Use lawful, public, synthetic, or consented examples; remove
personal data and credentials.

### Test dimensions

  -----------------------------------------------------------------------
  Dimension                           Metrics / checks
  ----------------------------------- -----------------------------------
  Message classification              Precision, recall, F1,
                                      false-positive rate

  URL assessment                      Correct handling of known test
                                      URLs, unknown URLs, malformed URLs,
                                      and reputation API failures

  OCR                                 Successful extraction rate on
                                      selected screenshots; manual review
                                      of extraction errors

  Investigation                       Correct linking of evidence and no
                                      unsupported cross-item conclusions

  Explainability                      Each finding has a traceable
                                      evidence item or source

  Advisor                             Groundedness, relevance, source
                                      correctness, safe handling of
                                      uncertain questions

  Performance                         End-to-end response time and
                                      failure rate
  -----------------------------------------------------------------------

### Essential test cases

-   Benign message containing urgent language.
-   Scam-like message with no URL.
-   Suspicious URL with no reputation match.
-   Known test phishing URL returned by a trusted source.
-   Malformed URL.
-   Screenshot with poor image quality.
-   Message and URL that appear related.
-   Message and URL that are unrelated.
-   User asks whether an unverified person is a criminal.
-   User shares an OTP or password in the prompt.

Do not report only aggregate accuracy. Show false positives and false
negatives, and explain the limitations of the dataset.

## 13. 10--11 Day Delivery Roadmap

The roadmap assumes 2--3 people working consistently. Reduce scope if
the team has less time.

  ----------------------------------------------------------------------------------------
  Day                     Focus                   Deliverable
  ----------------------- ----------------------- ----------------------------------------
  1                       Product scope, user     Agreed MVP specification and project
                          journey, architecture,  skeleton
                          API contracts,          
                          repository setup        

  2                       Frontend shell, FastAPI App starts locally; health endpoint and
                          setup, schemas,         basic UI work
                          database models         

  3                       Message Scanner         Structured message analysis and evidence
                                                  excerpts

  4                       URL Scanner             Safe URL parsing and reputation
                                                  lookup/fallback

  5                       Image upload and OCR    Screenshot-to-text-to-message-analysis
                                                  flow

  6                       Investigation Engine    One case can contain multiple evidence
                                                  items and findings

  7                       Risk report and Before  Explainable assessment and actionable
                          You Pay                 recommendations

  8                       AI Advisor with curated Case-aware Q&A with source references
                          RAG                     

  9                       End-to-end integration  Test results, bug list, stable main
                          and evaluation          workflow

  10                      Deployment,             Public/staging deployment and
                          documentation, demo     reproducible demo
                          scenario                

  11 (buffer)             Final polish and        Submission-ready build, slides, and
                          contingency             recorded backup demo
  ----------------------------------------------------------------------------------------

### Daily working rule

At the end of each day: - Merge working changes into the shared
integration branch. - Run the main end-to-end flow. - Record blockers
and assign one owner per blocker. - Do not start a new feature while a
critical workflow is broken.

## 14. Team Responsibilities

### If there are 3 members

  -----------------------------------------------------------------------
  Role                                Ownership
  ----------------------------------- -----------------------------------
  Member 1 --- AI / Data              Message analysis, OCR integration,
                                      RAG, Advisor prompts and evaluation

  Member 2 --- Backend / Security     FastAPI, database, URL scanner,
                                      investigation and risk APIs, safe
                                      upload/URL handling

  Member 3 --- Frontend / Product     UX, case workflow, evidence report,
                                      dashboard, integration testing and
                                      demo
  -----------------------------------------------------------------------

### If there are 2 members

-   **Member 1:** AI components, OCR, RAG, risk logic, and AI/backend
    integration.
-   **Member 2:** Frontend, API/backend foundation, database
    integration, deployment, and end-to-end testing.

For a two-person team, use a managed service where appropriate and defer
nonessential persistence, dashboard, and advanced retrieval features.

## 15. Demo Story for Judges

Use one coherent scenario rather than showing disconnected features.

### Scenario: Suspicious online recruitment offer

1.  A student receives a message offering unusually high pay for simple
    work.
2.  The sender asks for an upfront "verification fee."
3.  The message includes a recruitment website URL.
4.  The user submits the screenshot and URL to one ScamGuard
    investigation.
5.  OCR extracts the message text.
6.  Message Scanner identifies the advance-fee request and urgency
    language.
7.  URL Scanner checks the domain and displays the actual lookup status.
8.  Investigation Engine combines the findings while preserving their
    individual sources.
9.  The report explains what is suspicious, what is verified, and what
    remains unknown.
10. The user asks the Advisor: "Should I pay this fee? What should I
    do?"
11. ScamGuard recommends pausing payment and verifying the organization
    through independently obtained official contact details.

### Demo requirements

-   Prepare a deterministic backup dataset in case an external API is
    unavailable.
-   Label simulated or fixture data clearly; never present it as a live
    lookup.
-   Show at least one benign example to demonstrate that the product
    does not flag everything.
-   Keep the main demo within 3--5 minutes.
-   Have a recorded demo available in case deployment or network access
    fails.

## 16. Risks and Mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Scope creep                         Freeze MVP scope after Day 1; keep
                                      future features out of the critical
                                      path.

  LLM hallucination                   Use structured outputs, evidence
                                      references, validation, and
                                      explicit uncertainty.

  False positives                     Test benign and ambiguous cases;
                                      tune rules and wording.

  External API outage or quota        Add timeout/fallback behavior and
                                      clearly labeled test fixtures.

  Unsafe URL fetching                 Prefer reputation APIs; isolate any
                                      content fetching with strict
                                      network and file restrictions.

  OCR errors                          Show extracted text for review and
                                      allow manual correction.

  Integration delays                  Define API contracts early and
                                      integrate daily.

  Privacy exposure                    Redact sensitive data, restrict
                                      access, minimize retention, and
                                      never request OTPs/passwords.

  Demo failure                        Prepare a known-good environment
                                      and recorded backup demo.
  -----------------------------------------------------------------------

## 17. Definition of Done

The MVP is ready for submission when:

-   [ ] A user can submit a message and receive an evidence-based
    report.
-   [ ] A user can submit a URL and see the actual status and
    limitations of the check.
-   [ ] A user can upload a screenshot, review extracted text, and
    analyze it.
-   [ ] A user can combine at least two evidence items in one
    investigation.
-   [ ] Findings identify their evidence and verification status.
-   [ ] Risk levels are explainable and do not claim unsupported
    certainty.
-   [ ] The Advisor can answer a case-related question using the curated
    knowledge base.
-   [ ] The product gives safe next steps before payment or after
    suspected exposure.
-   [ ] Benign, suspicious, and ambiguous test cases have been
    evaluated.
-   [ ] The application handles API failures and invalid inputs
    gracefully.
-   [ ] A complete demo can be run repeatedly.
-   [ ] README, setup instructions, known limitations, and demo data are
    included.

## 18. Future Roadmap

After the contest MVP, consider:

1.  Community threat intelligence with moderation, deduplication, and
    confidence levels.
2.  Browser extension for in-context URL and page warnings.
3.  Mobile app or share-sheet integration for messages and screenshots.
4.  Voice-call and audio scam analysis.
5.  Deeper payment-risk workflows through authorized financial-provider
    integrations.
6.  Organization dashboards for small businesses and support teams.
7.  Improved multilingual detection and localized scam-pattern datasets.

These are future directions, not MVP commitments.

## 19. Final Product Message

**ScamGuard AI is not just a classifier that says "scam" or "not
scam."**

It is an evidence-based assistant that helps people investigate
suspicious digital interactions, understand why they may be risky, and
take safer actions before money or sensitive information is lost.

The competitive advantage should come from the quality of the
investigation workflow, traceable evidence, responsible uncertainty
handling, and a convincing end-to-end demonstration---not from the
number of AI features listed.
