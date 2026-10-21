# About Saeem Mehmood Sadiq

## Quick Facts About Saeem

- **Full name:** Saeem Mehmood Sadiq
- **Role:** Senior Software Engineer (backend), moving into Data and AI Engineering
- **Current company:** ILI Digital
- **Experience:** 5+ years of professional software engineering, starting December 2020
- **Primary languages:** Go, Elixir, Python
- **Location:** Lahore, Pakistan
- **Email:** saimmahmood61@gmail.com
- **LinkedIn:** https://www.linkedin.com/in/saimmahmood61
- **GitHub:** https://www.github.com/saim61
- **Booking a call:** https://calendar.app.google/czDkhWsVGq97Xqa47

---

## Professional Summary of Saeem

Saeem Mehmood Sadiq is a senior backend engineer with over five years of experience
building high-performance systems in Go, Elixir, and Python. He has worked across
real-time systems, iGaming, ticketing platforms, SaaS products, and distributed
architectures. Saeem is known for clean engineering, pragmatic decision-making, and
mentoring junior developers, and he typically owns projects end-to-end, from gathering
requirements through to production reliability.

---

## Saeem's Current Role — ILI Digital

**Period:** April, 2026 – Present

Saeem currently works at ILI Digital as a Senior Software Engineer, where he manages
projects built in Go, including a Go-based project for automated replies. Alongside this
role, he is transitioning into Data and AI Engineering by taking on tasks in his spare
time.

---

## Saeem's Experience at Code Graphers (Senior Software Engineer)

**Period:** June 2024 – March 2026

At Code Graphers, Saeem worked as a Senior Software Engineer, mainly in Go, across
software asset management and iGaming projects.

- Re-engineered the Python `imagehash` library in Go, keeping output parity across all
  hash types. This enabled a latency-critical image-matching pipeline to migrate to a
  faster Go backend.
- Built backend services in Go for a client's software asset management platform,
  improving reliability and observability.
- Reduced the client software's idle RAM usage from about 2 GB to about 40 MB (roughly a
  98% reduction) by finding memory hotspots and leaks and optimizing allocations and
  data structures so nothing was retained unnecessarily while idle.
- Built a small serverless pipeline for a client's test task: an AWS Lambda function,
  scheduled with EventBridge, periodically fetched currency data from an open-source
  source and stored it in DynamoDB, deployed with CloudFormation.
- Led feature development, bug resolution, and operational oversight for 13
  microservices in an iGaming ecosystem.
- Wrote tests across those 13 microservices, raising test coverage from about 10% to
  about 85%.
- Worked with senior engineers and external provider teams to architect and integrate
  two new live-casino provider integrations.
- Mentored junior developers on Go best practices and code review standards.

---

## How Saeem Reduced Idle RAM from 2 GB to 40 MB at Code Graphers

At Code Graphers, Saeem worked on the Go codebase of a client's agent software, which
used about 2 GB of RAM even while idle. He first studied the codebase to understand how
the whole system worked, then profiled the agent with pprof, both while it was working
and after it went idle.

The profiles pointed to three main problems:

- Long-running infinite loops that kept running after the agent's work was done.
- The same regular expressions being compiled more than 100,000 times. Saeem made each
  one compile once and be reused.
- API calls that fetched more than 150,000 records at once without pagination. He added
  pagination.

Fixing these meant reworking a large part of the codebase, all in Go. To measure each
change, he built the agent, let it finish its work on a machine, waited another 30 to 40
minutes, and then checked its idle RAM. Idle memory dropped from about 2 GB to about
40 MB, a reduction of roughly 98%.

---

## How Saeem Ported the imagehash Library from Python to Go

At Code Graphers, a client asked Saeem to rewrite the Python imagehash library in Go. He
mirrored the Python implementation closely and rewrote parts of the math himself,
because Go's math libraries gave results that differed from Python's by a bit or two.
To prove the two versions matched, he ran the same sample image through every hashing
algorithm in both languages and compared the outputs side by side. The Go version ran
significantly faster. While comparing outputs, he found a case where his Go version was
correct but the Python library had a bug in its ColorHash algorithm. He fixed it
upstream, and his pull request #216 was accepted:
https://github.com/JohannesBuchner/imagehash/pull/216

---

## Saeem's Work on 13 iGaming Microservices at Code Graphers

On an iGaming platform of 13 Go microservices, Saeem's day-to-day work was fixing bugs,
reviewing pull requests, building new features, and working closely with senior
engineers. One of his biggest and most time-consuming tasks was writing tests for the Go
code across all 13 services, which raised test coverage from about 10% to about 85%.
While building two live-casino provider integrations, the hardest part was understanding
how Kafka was used: it connected all 13 services, which made events hard to trace and
bugs hard to debug.

---

## Saeem's Experience at Dycoders (Senior Software Engineer, Hybrid)

**Period:** July 2023 – January 2024

At Dycoders, Saeem led an Elixir/Phoenix engineering team.

- Led the team through sprints, architecture discussions, and CI/CD workflows.
- Established testing standards and code review processes, which reduced production
  bugs and improved deployment reliability.
- Built and optimized Phoenix and LiveView backends with a focus on maintainability and
  real-time performance.
- Mentored junior engineers through pair programming and structured feedback.

The team had about 10 backend and frontend engineers, led by Saeem together with a
colleague. The two of them managed the team and also took on the hardest programming
tasks. Every module had to come with its own tests, and CI/CD ran those tests before code
could be merged. QA engineers added manual and automated testing on top.

---

## Saeem's Experience at Automatiq (Senior Software Engineer, Contract, Remote)

**Period:** May 2022 – June 2023

At Automatiq, Saeem focused on integrating external providers into a ticketing platform.

- Onboarded more than 10 new providers by integrating external systems end-to-end,
  covering APIs, workflows, and edge cases, which expanded platform coverage and
  supported business growth.
- Delivered integrations with high operational stability through resilient error
  handling, retries and timeouts, and clear observability for faster production
  debugging.
- Improved response times and platform performance by optimizing backend endpoints and
  database interactions so the platform handled peak usage reliably.

The platform received ticket emails from many ticketing providers. Saeem's team analysed
each provider's email format and extracted details such as the event name, venue, seat
numbers, and number of people, which were saved in the database as a memo. The hardest
were two providers whose email formats kept changing, so the team built ways to detect
which format an email used and extract the details accordingly.

---

## Saeem's Experience at InvoZone (Software Engineer, Hybrid)

**Period:** December 2020 – May 2022

InvoZone was where Saeem started his professional career, working on real-time gaming
systems.

- Developed Elixir and Go microservices for real-time gaming systems using optimized
  concurrency patterns.
- Implemented gRPC and GraphQL services to improve modularity and scalability.
- Owned backend logic for multiple game modules and mentored junior engineers.

---

## Saeem's High Score Games Module at InvoZone

At InvoZone, Saeem worked in Elixir on a real-time competition app where two users
competed and the winner received a prize. He was solely responsible for its high score
games module: event-based and time-based games where users scored points and the top
players won prizes. An admin panel controlled the number of winners, the start and end
times, when prizes were distributed, and how. Saeem built all of it, from background
jobs (using Oban) to real-time leaderboards to prize distribution. Running many
scheduled jobs concurrently and in parallel with very few issues showed him the strength
of Elixir.

---

## Saeem's Career Timeline

Saeem's jobs in order, from the most recent to his first job:

1. ILI Digital: Senior Software Engineer, April 2026 – Present
2. Code Graphers: Senior Software Engineer, June 2024 – March 2026
3. Dycoders: Senior Software Engineer (Hybrid), July 2023 – January 2024
4. Automatiq: Senior Software Engineer (Contract, Remote), May 2022 – June 2023
5. InvoZone: Software Engineer (Hybrid), December 2020 – May 2022

---

## Saeem's Technical Skills

- **Backend languages:** Go, Elixir (Phoenix, OTP, LiveView), Python (FastAPI, Django)
- **Architecture:** Microservices, event-driven systems, REST, gRPC, GraphQL, WebSockets
- **Databases and data stores:** PostgreSQL, MySQL, DynamoDB, Redis
- **Data engineering:** Batch ETL pipelines, dbt, PySpark, Parquet, star-schema
  modeling, slowly changing dimensions (SCD2), data quality checks, idempotent and
  incremental loading with watermarks
- **Cloud:** AWS Lambda, EventBridge, DynamoDB, CloudFormation
- **Infrastructure and DevOps:** Docker, Docker Compose, Kubernetes, Helm, GitHub
  Actions, CI/CD
- **Observability:** Structured logging, Prometheus metrics, OpenTelemetry
- **Engineering practices:** Testing and TDD, code review, performance and memory
  optimization
- **Domains:** Real-time systems, iGaming, ticketing, SaaS, software asset management

---

## Saeem's Personal Projects and Open Source Work

All of Saeem's personal projects are public on his GitHub: https://www.github.com/saim61

Saeem's projects are Hookline (a webhook delivery service in Python), Podium (a real-time
leaderboard system in Go), fxflow (a foreign exchange rates ETL pipeline), the Olist
Analytics Platform (an e-commerce data warehouse), and a Go messaging app. His
open-source contribution is a bug fix in the ColorHash algorithm of the Python imagehash
library (pull request #216, accepted).

### Hookline — Webhook Delivery Service (Python)

Hookline is Saeem's reliable webhook delivery service, a smaller, readable
implementation of what products like Svix and Hookdeck offer. It accepts an event in
milliseconds and then delivers it to customers' HTTP endpoints with retries,
exponential backoff with jitter, per-endpoint circuit breakers, HMAC signatures,
idempotency keys, a dead letter queue, and a permanent audit trail of every delivery
attempt. The delivery worker uses a transactional outbox drained with
`SELECT ... FOR UPDATE SKIP LOCKED`, so multiple workers can run concurrently without
double-delivering. It includes an authenticated API, an operator dashboard, Prometheus
metrics, and a Helm chart, and is covered by 292 tests at 94% coverage. Saeem built it
for practice and to broaden his expertise.

- **Stack:** Python, FastAPI, PostgreSQL, SQLAlchemy (async), Redis, Alembic, HTMX,
  structlog, Prometheus, OpenTelemetry, Docker, Helm, GitHub Actions
- **Link:** https://github.com/saim61/hookline

### Podium — Real-Time Leaderboard System (Go)

Podium is Saeem's real-time leaderboard system written in Go. Five games run on the
server as state machines, so the server computes every score itself and clients can
never submit a forged score. Scores are stored durably in PostgreSQL, while Redis sorted
sets act as a derived read model that can be rebuilt from Postgres at any time.
Leaderboard updates reach browsers over WebSockets and travel through Redis Pub/Sub, so
real-time updates keep working across multiple server instances. It also includes
Argon2id authentication with refresh token rotation, period reports, rate limiting,
Prometheus metrics, an OpenAPI description, and a playable demo page, and is covered by
429 tests. Podium started as a backend challenge Saeem found online; he built it for
practice and to broaden his expertise.

- **Stack:** Go, PostgreSQL, Redis, WebSockets, sqlc, Docker, Prometheus
- **Link:** https://github.com/saim61/podium

### fxflow — Foreign Exchange Rates ETL Pipeline (Python)

fxflow is Saeem's batch ETL pipeline for foreign exchange rates, built to learn data
engineering fundamentals from first principles before using standard tooling. It pulls
daily European Central Bank reference rates from the Frankfurter API, stores them in an
immutable, append-only raw layer, transforms them into an analytics-ready fact table
with dbt, validates them with data quality tests, and serves them through a FastAPI
REST API. The pipeline is idempotent, uses watermarks to fetch only missing data and
backfill gaps, and records every run for observability.

- **Stack:** Python, PostgreSQL, SQLAlchemy, dbt, FastAPI, Docker
- **Link:** https://github.com/saim61/fxflow

### Olist Analytics Platform — E-Commerce Data Warehouse (Python)

The Olist project is Saeem's end-to-end batch data pipeline built on the public
Brazilian e-commerce dataset by Olist. It turns raw CSV data into a tested star-schema
warehouse and business-ready Parquet marts, answering questions such as which product
categories and states drive revenue, how revenue is trending, and where deliveries are
late. Data moves through source, raw, staging, and warehouse layers, with incremental
extraction using watermarks, a customer dimension tracked as a slowly changing
dimension (SCD2), quality gates that abort the run if checks fail, and PySpark jobs
that build partitioned Parquet marts. The whole platform is reproducible with Docker.

- **Stack:** Python, PostgreSQL, PySpark, Parquet, pandas, Docker
- **Link:** https://github.com/saim61/olist

### Go Message App

A real-time messaging backend built by Saeem with Go, WebSockets, Clean Architecture,
JWT authentication, and PostgreSQL.

### imagehash — Open-Source Contribution

Saeem fixed a bug in the ColorHash algorithm of the Python `imagehash` library. His
pull request #216 was accepted.

---

## Saeem's University Education

Saeem holds a BSc in Computer Science from FAST-NUCES (National University of Computer
and Emerging Sciences), Islamabad campus.

His final year project was a Twitter Cyber Bullying Detector, which analyzed tweets
from a user's Twitter home feed and alerted users about accounts that were potential
bullies. During university, Saeem particularly enjoyed the Software for Mobile Devices
course, where he learned to build native Android apps, as well as mathematics courses.

## Saeem's A Levels

Saeem completed his A Levels in 2013 at Arab Unity School in Dubai, UAE, under the
Edexcel board. His subjects were Mathematics, Physics, and Chemistry.

## Saeem's O Levels

Saeem completed his O Levels in 2011 at The Westminster School in Dubai, UAE, under the
Cambridge (CIE) board. His subjects were Mathematics, Physics, Chemistry, Information
and Communication Technology, Economics, English, and Urdu.

---

## Saeem's Background

Saeem was born and raised in the United Arab Emirates, where he completed both his
O Levels and A Levels in Dubai. He then studied Computer Science at FAST-NUCES in
Islamabad, Pakistan, and is now based in Lahore, Pakistan.

---

## What Saeem Is Learning and Where His Career Is Heading

Alongside backend engineering, Saeem is transitioning into Data and AI Engineering using
Python. He is also interested in Platform Engineering, Security Engineering, and AI
Systems Engineering as future directions. His fxflow and Olist projects are part of this
data engineering journey, and this "About Saeem" assistant is itself one of his learning
projects, built to understand embeddings and retrieval-augmented generation (RAG)
hands-on.

---

## Saeem's Hobbies and Fun Facts

Outside of work, Saeem enjoys going out with friends and loves hiking. He is especially
drawn to the mountains and enjoys a good hike that ends with a killer view. He has
travelled to many places in the Northern Areas of Pakistan and has also explored the
hilly areas around Baku, Azerbaijan. He also likes to hang out with his friends 
in his free time or watch movies/seasons

His most memorable trips were two university trips to Hunza and Gilgit, where his whole
batch travelled together. On both trips, everyone sat around a bonfire under the stars
and sang songs for hours.

---

## How Saeem Approaches a New Codebase or a Hard Bug

When Saeem joins a new codebase, he first uses AI tools such as Claude to understand the
project and get a quick picture of its architecture. He then runs the code locally and
traces how it flows, adding print statements and reading the log files. Once he
understands the problem, he writes a plan for the fix and works through it, always
checking for ripple effects on the rest of the system.

---

## Saeem's Favourite Programming Languages: Go and Elixir

Saeem enjoys both Go and Elixir, but if he had to pick one, he would choose Go, because
it is both powerful and simple. He finds Elixir equally powerful, but its functional
style makes it harder than more conventional languages.

---

## How to Contact Saeem

The best way to reach Saeem is by email at saimmahmood61@gmail.com. He can also be
found on LinkedIn and GitHub, and anyone can book a meeting with him through his
calendar.

- **Email:** saimmahmood61@gmail.com
- **LinkedIn:** https://www.linkedin.com/in/saimmahmood61
- **GitHub:** https://www.github.com/saim61
- **Booking a call:** https://calendar.app.google/czDkhWsVGq97Xqa47