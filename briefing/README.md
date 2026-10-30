# Briefing: everything about today, for the agents building

**Our case: FraAlliance runway forecast.** It is in `../CHALLENGE_FRAALLIANCE.md` and includes the full pitch transcript. Start there.

## The event

- **Name:** "OpenAI Codex Enterprise Hackathon", part of AIW Hack, the Builders Day of AI Week Frankfurt, at THE SQUAIRE, Frankfurt Airport, on Fri 30 Oct 2026.
- **Organisers:** AI Hub Frankfurt, together with **OpenAI** and **statworx**, an OpenAI services partner. Sebastian Heinz is CEO of both statworx and AI Hub.
- **Participants:** about 100, **hand-selected for engineering quality**. The organiser said he looked at people's LinkedIn profiles.
- **Schedule:**
  - 10:15 to 16:00: build
  - 16:00: final submissions
  - 17:00: finals and awards, with short "elevator" pitches per team
  - 18:00: closing and after-party
- **Team rules:** teams of 2 to 4, no solo work. Register with the form using the code "Let's Hack AI Week", then choose the case on the team dashboard. The dashboard also has the company briefings and slides to download.
- **Credits:**
  - After registering, OpenAI invites the team to a ChatGPT workspace. Pick the **statworx partner workspace**; everything there is free.
  - An **OpenAI API key** is provided for use inside the app. Never commit it.
- **Help on the floor:** people from FraAlliance, KfW IPEX and Condor are on the floor all day for questions and **scope alignment**. Ask them early.

## What the organisers and OpenAI like

From the kick-off, see `transcripts/01_kickoff_organiser_and_codex_showcase.md`.

- **A deployed, shareable app.**
  - OpenAI (Daniel, Munich) built and deployed a site live in under 5 minutes with Codex. He pushed sharing a deployed site with the company partners for feedback: "the site is a super easy way".
  - So: **ship a live URL**, not only localhost.
- **Using Codex well, and the right model for the job:**

  | model | what OpenAI said |
  |---|---|
  | GPT-6 Astra | most capable: complex builds, computer use, visual |
  | GPT-6.1 Sol | about 20% of Astra's price, a good default for coding and API use |
  | GPT-6.1 Terra | middle tier, new this week, good at visual |
  | GPT-6 Luna | very fast and cheap, for high volume |

  Their line: "tokenomics is a big topic … there still has to be the business case behind it". Showing that we picked a cost-efficient model is a plus.
- **OpenAI APIs they recommended:**
  - the **Responses API** (chat or agent loop)
  - a very fast classification-style API that returns choices with probabilities, "10x faster than Luna". Name unclear in the recording; ask an OpenAI person.
  - the **Agents API**, a hosted Codex harness with a sandbox and computer use
  - **GPT Live** for audio
  - built-in **ImageGen**: "Sunburst" (high fidelity) and "Flare" (fast)
- **Codex features they showed:**
  - plan mode
  - side chat (`/side`)
  - `/sketch` to draw a UI
  - ultra-fast mode
  - cloud VMs you can text from your phone
- **Impact for the company.** The host called all three cases "very, very high impact". FraAlliance's is "for the whole airport operations".

## What FraAlliance likes

From their pitch, see `../CHALLENGE_FRAALLIANCE.md`, bottom.

- **A real ML forecast 48 h ahead**, based on **open source data**.
- **Their own rule set** from the one-pager (tailwind limits, runway 18 closure, direction change) applied faithfully.
- Framing around **planning and the passenger**:
  - ground handling staff and equipment repositioned in time
  - transfer passengers making their connections
  - less rescheduling
  - "a better experience for the cooperation behind all of the partners that are making this airport work"
- **Numbers they care about:**
  - 156 direction changes a year, about 3 a week
  - runway 18 carries 6 of 10 departures
  - up to 110 movements in the peak hour
  - 1,260 movements a day

## The other two cases (context only, not ours)

- **KfW IPEX-Bank ("Max", business process manager):** a "process intelligence" tool. It ingests work instructions and process diagrams, analyses them against goals (speed, risk, role clarity) and visualises the process interactively, with recommendations.
- **Condor (customer care operations):** AI for complaint handling, about 15,000 complaints a month and 100,000 to 150,000 a year. It learns from quality-checked past outputs, starts with simple cases with human review, asks customers for missing info, and uses EU261 and the knowledge base. No real data is given, so it needs mock data. Prize if a Condor team wins the whole hackathon: a free business upgrade on a long-haul flight. **This is our plan B.**

## Our team

- **Jayden Bruck:** builds with many coding agents in parallel; owns the UI and demo polish. **Leaves at 16:45**, so he is not at the 17:00 finals.
- **Kai Detmers:** Expert AI Solution Engineer at Lufthansa Industry Solutions. Full stack, agentic coding, aviation context. Build co-lead for model and data.
- **Hugo Hader:** AI Transformation at Parloa. Business case, demo script, and **presents at 17:00**.
- **Luca Schultz:** economics at Goethe University; risk and banking background. Domain research, sample data, business case numbers and slides, demo tester, backup presenter.

## Transcripts

- `transcripts/FRAALLIANCE_PITCH_FULL.md`: the FraAlliance pitch, complete and verbatim.
- `transcripts/02_challenge_pitches.md`: all three challenge pitches, complete.
- `transcripts/01_kickoff_organiser_and_codex_showcase.md`: organiser rules plus the OpenAI Codex showcase.
- `transcripts/03_registration.md`: registration, workspace and API key instructions.
