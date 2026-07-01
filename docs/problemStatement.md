# Problem Statement: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview

The objective of this project is to build a **facts-only FAQ assistant** for **HDFC Mutual Fund** schemes, using **Groww** as the reference product context. The assistant will answer objective, verifiable queries related to mutual funds by retrieving information exclusively from the specified Groww URLs.

The system must strictly avoid providing investment advice, opinions, or recommendations. Every response must include a single, clear source link and adhere to defined constraints around clarity, accuracy, and compliance.

---

## Objective

Design and implement a lightweight **Retrieval-Augmented Generation (RAG)**-based assistant that:

- Answers factual queries about mutual fund schemes
- Uses a curated corpus of official documents
- Provides concise, source-backed responses

---

## Target Users

- **Retail investors** comparing mutual fund schemes
- **Customer support and content teams** handling repetitive mutual fund queries

---

## Scope of Work

### 1. Corpus Definition

- **AMC Selected:** HDFC Mutual Fund (HDFC Asset Management Company)
- **Schemes Selected (5):** Covering category diversity across equity (large-cap, mid-cap, small-cap) and commodity (gold, silver)

| # | Scheme Name | Category | Groww URL |
|---|---|---|---|
| 1 | HDFC Large Cap Fund – Direct Plan – Growth | Large Cap | [Link](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth) |
| 2 | HDFC Mid-Cap Opportunities Fund – Direct Plan – Growth | Mid Cap | [Link](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth) |
| 3 | HDFC Small Cap Fund – Direct Plan – Growth | Small Cap | [Link](https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth) |
| 4 | HDFC Gold ETF Fund of Fund – Direct Plan – Growth | Gold ETF FoF | [Link](https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth) |
| 5 | HDFC Silver ETF Fund of Fund – Direct Plan – Growth | Silver ETF FoF | [Link](https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth) |

- **Corpus limit:** Use **only** the 5 specific Groww URLs provided above. Do not include external PDFs (like Factsheets, KIM, SID) or other external websites (like AMFI/SEBI).

### 2. FAQ Assistant Requirements

The assistant must answer **facts-only queries**, such as:

| Query Type | Example |
|---|---|
| Expense ratio | "What is the expense ratio of X scheme?" |
| Exit load | "What is the exit load for X fund?" |
| Minimum SIP | "What is the minimum SIP amount?" |
| ELSS lock-in | "What is the lock-in period for ELSS?" |
| Riskometer | "What is the riskometer classification?" |
| Benchmark index | "What is the benchmark index for X scheme?" |
| Statements | "How to download capital gains reports?" |

**Response constraints:**

- Each response is limited to a **maximum of 3 sentences**
- Each response includes **exactly one citation link**
- Each response includes a footer:
  > `"Last updated from sources: <date>"`

### 3. Refusal Handling

The assistant must **refuse** non-factual or advisory queries, such as:

- *"Should I invest in this fund?"*
- *"Which fund is better?"*

Refusal responses should:

- Be polite and clearly worded
- Reinforce the facts-only limitation
- Provide a relevant educational link (e.g., AMFI or SEBI resource)

### 4. User Interface (Minimal)

The solution should include a simple interface with:

- A **welcome message**
- **Three example questions**
- A visible disclaimer:
  > *"Facts-only. No investment advice."*

---

## Constraints

### Data and Sources

- Use **only** the 5 provided Groww URLs as the source of truth.
- Do **not** use external PDFs, third-party blogs, aggregator websites, or other official sources (like AMFI/SEBI).

### Privacy and Security

> [!CAUTION]
> The system must **not** collect, store, or process any of the following:
> - PAN or Aadhaar numbers
> - Account numbers
> - OTPs
> - Email addresses or phone numbers

### Content Restrictions

- No investment advice or recommendations
- No performance comparisons or return calculations
- For performance-related queries, provide a link to the official factsheet only

### Transparency

- Responses must be short, factual, and verifiable
- Every answer must include a **source link** and **last updated date**

---

## Expected Deliverables

| Deliverable | Details |
|---|---|
| **README Document** | Setup instructions, selected AMC and schemes, architecture overview (RAG approach), known limitations |
| **Disclaimer Snippet** | `"Facts-only. No investment advice."` |

---

## Success Criteria

- [x] Accurate retrieval of factual mutual fund information
- [x] Strict adherence to facts-only responses
- [x] Consistent inclusion of valid source citations
- [x] Proper refusal of advisory queries
- [x] Clean, minimal, and user-friendly interface

---

## Summary

> The goal is to build a **trustworthy, transparent, and compliant** mutual fund FAQ assistant that prioritizes **accuracy over intelligence**. The system should ensure that users receive only verified, source-backed financial information, without any advisory bias or speculative content.
