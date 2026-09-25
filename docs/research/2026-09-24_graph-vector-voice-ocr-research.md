# Graph + Vector + Voice research: litigation evidence graph and later stages

**As of:** 2026-09-24. All prices are USD list prices found by web search on 2026-09-24 unless noted. The proxy blocked direct fetches of vendor pricing pages (neo4j.com, aws.amazon.com, learn.microsoft.com), so many figures come from search-result snippets and third-party pricing trackers. **Check any figure on the vendor console before you commit money.** `UNVERIFIED` = no reliable source found or sources disagree.

---

## 0. TL;DR

- **Litigation graph v1:** Neo4j (AuraDB Free for the prototype, then Professional at 2–4 GB) holding entities, relationships and events, with SharePoint as the system of record. Nodes store only SharePoint `driveItem` IDs and URLs. Keep vectors small (1024-d or smaller, with quantization) or put them in pgvector, because Aura charges per GB of RAM.
- **Cheapest all-Microsoft option:** Azure PostgreSQL Flexible Server with **Apache AGE (GA May 2026) and pgvector/DiskANN** in one database. It costs about $12–50/mo, runs inside the Azure tenant and falls under the Microsoft BAA/DPA.
- **Embeddings:** voyage-law-2 or voyage-4 for legal text (the free-token grants cover most small matters). text-embedding-3-small is the commodity default. Embedding costs are negligible next to LLM extraction costs.
- **Privilege:** after *US v. Heppner* (SDNY, Feb 2026), send privileged material only to enterprise API endpoints with no training and ZDR or Modified Abuse Monitoring, used at counsel's direction and documented. Never use consumer chat tools for it.
- **Pipeline (§7):** for a 50k-page / 200k-email corpus, OCR costs ~$75 (Azure DI Read) and one combined LLM pass costs ~$55 (Grok 4.1 Fast) to ~$740 (GPT-5.6 Terra). Human review is the real cost. Purview eDiscovery Premium handles hold, dedupe and threading in-tenant. Never rename evidence originals: rename working copies, or store the canonical name in metadata, with a dry-run manifest.
- **xAI/Grok (§8):**
  - The API has no training on API data, 30-day retention, ZDR on Enterprise, a US endpoint (+10%) and a BAA on request.
  - Grok 4.1 Fast ($0.20/$0.50) is the cheapest bulk extractor.
  - Grok Business ($30/seat) has SharePoint/OneDrive connectors.
  - Collections is a good RAG index but **not** a canonical evidence store: 100k-file / 100 GB caps, and no documented legal hold.
  - The Grok Voice Agent ($0.08/min, ~0.7 s to first audio) queries the graph through function tools. Its BAA status is unconfirmed.
- **Voice (medical):** the BAA is what decides the platform. Vapi charges a +$2k/mo HIPAA add-on, LiveKit requires the $500/mo Scale plan, and Retell/ElevenLabs/Bland put the BAA behind Enterprise. Realtime *audio* BAA coverage is **disputed**: one source (May 2026) says OpenAI/Azure realtime audio is not covered, while OpenAI's HIPAA-eligible list (help.openai.com article 20001069, cited in review, not re-verified here) reportedly includes `/v1/realtime` with an executed BAA and Modified Retention. Confirm with OpenAI in writing; until then STT → text LLM → TTS is the safe default. Azure is assessed separately [i10].

---

## 1. Graph databases

| Product | Model / query | Vector | Hosting | Entry price | Realistic small-team $/mo | Licensing gotchas (commercial/SaaS) | Best fit |
|---|---|---|---|---|---|---|---|
| **Neo4j AuraDB** | Property graph / Cypher (GQL-aligned) | Native HNSW vector index; quantization on by default; rescored binary is the default for new indexes in 2026.09 [a3] | Managed on AWS/GCP/Azure (incl. Azure Marketplace) | **Free:** 1 instance, 200k nodes/400k rels per FAQ (another page says 50k/175k, so UNVERIFIED) [a2]. **Professional:** $65/GB-mo, 1 GB min (~$0.09/hr) [a1]. **Business Critical:** $146/GB-mo, 2 GB min, 99.95% SLA, 3-zone [a1]. **VDC/Enterprise:** quote. | $65–260 (1–4 GB Pro). Vectors inflate RAM, so 1M×1536-d float32 ≈ 6 GB → ~$400–520/mo unless quantized | Aura is a service with no distribution issue. Aura Graph Analytics (serverless GDS) is extra at $0.40/GB-hr [a3] | Litigation/investigation graphs, GraphRAG. Best tooling (neo4j-graphrag, LLM Graph Builder, Bloom) |
| **Neo4j self-hosted** | Same | Same | Your VM/K8s | Community: free, GPLv3. Enterprise: commercial license (quote) or AGPLv3 for OSS [a4] | VM cost only ($20–80) | Community is GPLv3: SaaS use without distribution is generally fine, but **embedding/OEM distribution triggers GPL obligations**. Community has no clustering/RBAC/hot backup. Claims that "Community can't power a product whose primary value is Neo4j" are UNVERIFIED (third-party blog [a4]). Enterprise for OEM/commercial needs a contract; there is a startup program [a4] | Dev, single-server internal apps |
| **Neo4j GraphRAG tooling** | `neo4j-graphrag` (Python, first-party, replaces neo4j-genai). KG-builder pipeline, retrievers (vector, hybrid, Text2Cypher). Supports Neo4j 2026.01+ SEARCH clause [a5]. LLM Graph Builder is the open-source Labs app (PDF/URL → KG) | | | Free (Apache-2.0) | — | Labs = not supported product | Fastest path to a prototype |
| **Amazon Neptune (DB)** | Property graph (Gremlin, openCypher) **and** RDF (SPARQL) | Vector search lives in Neptune Analytics, not the DB | AWS only | db.t4g.medium $0.093/hr (~$68/mo) + storage $0.10/GB-mo + I/O $0.20/M [b1]. Serverless $0.1098/NCU-hr, min 1 NCU (~$80/mo floor) [b2] | $80–200 | None (managed). AWS lock-in | AWS shops, RDF/ontology needs |
| **Neptune Analytics** | openCypher, in-memory analytics | Native vector similarity + graph algorithms | AWS | Billed per m-NCU-hr (1 GB RAM). Smallest size 32 m-NCU [b3]; paused = 10% of compute [b2]. Unit price UNVERIFIED (snippet says "16 m-NCU ≈ $0.48/hr", i.e. ~$0.03/m-NCU-hr → 32 m-NCU ≈ $700/mo) | ~$700 if always on (UNVERIFIED) | — | Periodic analytics/GraphRAG on AWS |
| **Azure Cosmos DB for Apache Gremlin** | Property graph / Gremlin only (no Cypher) | DiskANN vector search exists for Cosmos **NoSQL** API. Gremlin API vector support UNVERIFIED (not found) [c1] | Azure | Serverless $0.25/M RU; provisioned $0.008/100 RU/s-hr [c1] | $5–60 (serverless, light use) | None. Weak traversal performance and tooling vs Neo4j (common practitioner view, UNVERIFIED) | Only if the org mandates Cosmos |
| **PostgreSQL + Apache AGE** | Property graph / openCypher inside SQL | pgvector (+ DiskANN on Azure) in the **same DB** [c2][c3] | Self-host, or **Azure PG Flexible Server: AGE GA (PG16/17/18), May 2026** [c2] | Azure B1ms ~$12.41/mo; B2s ~$49.64/mo + storage [c3] | $15–60 | Apache-2.0: no restrictions | **Best cheap Microsoft-native choice**. One DB for relational + graph + vector. AGE Cypher is less mature than Neo4j's (UNVERIFIED qualitative) |
| **Memgraph** | Property graph / Cypher, in-memory | Native vector search. "AI Platform" license excludes vector memory from the licensed cap [d1] | Self-host (Memgraph Cloud status UNVERIFIED) | Community free (BSL); **Enterprise from $25k/yr for 16 GB** [d1] | $0 + VM (Community) | Community is **BSL**, which bars offering it as a DB service. Enterprise is expensive [d1] | Streaming/real-time graph, Neo4j-compatible |
| **FalkorDB** | Property graph / openCypher (Redis module, GraphBLAS) | Native vector index. GraphRAG-SDK with automatic ontology [d2] | Self-host; FalkorDB Cloud (AWS/GCP) | Free 100 MB (no persistence); **Startup $73/mo per GB** ($0.10/GB-hr); Pro from $350/mo (8 GB, HA) [d2] | $73–350 | **SSPLv1**: free to self-host/embed internally, can't offer FalkorDB-as-a-service [d2] | Low-latency GraphRAG (voice agents), multi-tenant graphs |
| **Kùzu** | Embedded property graph / Cypher | Had vector + FTS | Embedded | — | — | **Discontinued.** Apple acquired it (agreed 2025-10-09); repo archived 2025-10-10 [d3]. Forks: **LadybugDB** (most active, 20+ releases, 80+ contributors), RyuGraph, Bighorn (dormant until Aug 2026), Vela fork [d4] | Don't start new work on Kùzu. LadybugDB for embedded/local graphs |
| **TigerGraph** | Property graph / GSQL (+ openCypher/GQL subset) | Native vector (TigerVector) | Savanna cloud; self-host | Savanna $45/GB-mo; Business Critical $126/GB-mo; storage $0.025/GB-mo; free trial. **Community Edition free, even for production** (single server) [d5] | ~$90–200 | Proprietary. Enterprise is sales-led | Very large analytics (fraud, supply chain). Overkill here |
| **ArangoDB** | Multi-model (doc + graph) / AQL | Vector index (3.12+) | ArangoGraph/Oasis managed; self-host | Managed pricing is quote-based [d6] | UNVERIFIED | 3.12+ source is **BSL 1.1**. **Community Edition: 100 GB dataset cap and no commercial SaaS/OEM/embedded use** without an Enterprise license [d6] | Avoid for a commercial product unless you buy a license |
| **SurrealDB** | Multi-model (doc/graph/relational/vector) / SurrealQL | Native HNSW vector + FTS [d7] | SurrealDB Cloud; self-host | Cloud from ~$0.02/hr usage-based [d7] | $15–50 | **BSL 1.1** (converts to Apache 2.0 on 2030-01-01). Can't run it as a commercial DBaaS [d7] | Agent memory, app backends. Young ecosystem |
| **Microsoft Fabric graph** | Labeled property graph over OneLake / **GQL (ISO/IEC 39075)** | Not found in docs (UNVERIFIED) | Fabric capacity (F-SKU) | **GA at Build 2026** [e1]. Consumes Fabric CUs: 10 CU-sec per second of CPU uptime, **100 GB storage minimum** at OneLake cache rates [e2] | Needs an F-SKU (F2 ≈ $260/mo PAYG, UNVERIFIED) | Microsoft-only. Analytics-oriented, not an OLTP app DB | Enterprise BI/relationship analytics on data already in Fabric. Consulting clients on Fabric |
| **Microsoft GraphRAG (OSS lib)** | Pipeline, not a DB: LLM extracts entities/relations → communities → summaries → local/global search. Output goes to Parquet/LanceDB etc. | Uses a vector store | Your compute + LLM API | MIT, free | Cost = LLM tokens | Full GraphRAG indexing is costly. **LazyGraphRAG** has indexing cost ~0.1% of GraphRAG (noun-phrase extraction, LLM use deferred to query time) and was being merged into the main library as of Jan 2026 [e3] | Global "what are the themes" questions over a corpus. For evidence graphs, a **typed schema (Person/Org/Doc/Email/Event/Matter)** built with neo4j-graphrag beats generic communities |

---

## 2. Embeddings and vector stores

### 2a. Embedding models

| Model | $/1M tokens | Dims | Notes | 1M tok | 10M tok | 100M tok |
|---|---|---|---|---|---|---|
| OpenAI text-embedding-3-small | $0.02 (batch $0.01) [f1] | 1536 (shortenable) | Commodity default | $0.02 | $0.20 | $2.00 |
| OpenAI text-embedding-3-large | $0.13 (batch $0.065) [f1] | 3072 (shortenable) | | $0.13 | $1.30 | $13.00 |
| **Voyage voyage-law-2** | $0.12, first 50M free [f2] | 1024 | Legal-tuned, 16k context | $0 | $0 | ~$6 after free |
| Voyage voyage-4 / -4-large / 3.5-lite | $0.06 / $0.12 / $0.02; voyage-4 has 200M free; batch −33% [f2] | 1024 (flex) | Voyage is owned by MongoDB (per [f2] listing; details UNVERIFIED) | $0 | $0 | $0 (inside 200M free) |
| Cohere embed-v4.0 | $0.12 text; $0.47/M image tokens [f3] | 256/512/1024/1536 | Multimodal (scanned exhibits). Also on Azure Foundry (UNVERIFIED) | $0.12 | $1.20 | $12 |
| Google gemini-embedding-001 | $0.15 [f4] | 3072 (MRL → 1536/768) | gemini-embedding-2-preview $0.20, multimodal [f4] | $0.15 | $1.50 | $15 |
| Open: Qwen3-Embedding-8B / BGE-M3 / nomic-embed / e5 | Self-host (GPU or CPU) | 1024–4096 | Qwen3-Embedding-8B tops MTEB multilingual [f5]. Everything stays on-prem, which is best for privilege | GPU time only | | |

Rule of thumb: 1 page ≈ 500 tokens, so 100M tokens ≈ 200k pages. **Embedding a large matter costs under $15. LLM entity extraction for the graph costs 100–1000× more**, so budget for extraction, not embedding.

### 2b. Storing ~1M vectors

Raw size: 1M × 1024-d float32 ≈ 4.1 GB; × 1536-d ≈ 6.1 GB; × 3072-d ≈ 12.3 GB. Add index overhead (1.2–2×). int8/binary quantization cuts this 4–32×.

| Store | Entry / pricing | ~1M vectors (1024–1536-d) est. $/mo | Notes |
|---|---|---|---|
| **pgvector** (Azure PG Flexible) | B1ms $12.41, B2s $49.64 + storage [c3] | $50–130 (B2s/D2s + 32–64 GB) | DiskANN on Azure. Same DB as AGE graph. Inside the Microsoft BAA/DPA boundary |
| Azure AI Search | Basic $75/mo; S1 $250/mo [g2]. Basic: ~5 GB vector quota/partition on new services [g2b] | $75 (quantized) – $250 (S1) | Hybrid + semantic ranker. Native SharePoint indexer (preview, UNVERIFIED) |
| Pinecone serverless | Free Starter 2 GB. Standard **$50/mo minimum**; $0.33/GB-mo; $16–18/M reads; $4–4.5/M writes [g1] | $50 (minimum dominates) | |
| Weaviate Cloud | Flex from $45/mo; Plus $280 [g3] | $45–150 | Hybrid BM25 built in |
| Qdrant Cloud | Free 1 GB RAM/4 GB disk (suspends after 1 week idle); paid ~$30–200 [g3] | $30–100 | OSS Apache-2.0. Easy to self-host |
| Milvus / Zilliz Cloud | Free 5 GB; serverless ~$0.096/CU-hr, storage $0.04/GB-mo [g4] | $10–60 | |
| Chroma Cloud | $2.50/GiB written; $0.33/GB-mo storage [g4] | ~$15 write + $2–4/mo | OSS Apache-2.0 |
| Turbopuffer | Launch minimum **$16/mo** (cut from $64 in June 2026) [g5] | $16–40 | Object-storage-first, cheapest at scale |
| LanceDB | OSS free. Cloud in beta, GA pricing pending [g5] | $0 (embedded) | Microsoft GraphRAG's default store |
| Neo4j vector index | Included in Aura RAM pricing ($65/GB) [a1] | $260–520 | Convenient (one query mixes graph + vector) but pricey. Use quantization/binary [a3] |
| MongoDB Atlas Vector | Flex $8 base, capped $30/mo; M10 ~$57/mo + search nodes from $0.12/hr [g6] | $30 (Flex, small) – $150+ | |

---

## 3. Voice agents and retrieval

### 3a. Latency budget (real-time phone)

| Stage | Target | Source |
|---|---|---|
| Total voice-to-voice turn | **~800 ms** target (≤1 s tolerable); sub-500 ms feels human | [h1] |
| STT final / endpointing | 100–300 ms | [h1] (range, UNVERIFIED per vendor) |
| **Retrieval (embed query + vector/graph lookup)** | **≤100 ms total, ideally <50 ms** for the vector search itself; a typical vector DB query adds 50–300 ms, which is too slow for inline | [h1] |
| LLM time to first token | 150–400 ms | [h1] |
| TTS first audio | 50–200 ms | [h1] |

Design implications:
- Pre-fetch context at call start (caller ID → CRM/graph lookup).
- Use a fast in-memory store (FalkorDB, Redis, or the platform's built-in knowledge base).
- Put slow graph reasoning behind a tool call with a filler phrase.
- Consider the dual-agent/speculative-retrieval pattern (VoiceAgentRAG) [h1].

### 3b. Platforms

| Platform | Per-minute pricing | KB / RAG / tools | HIPAA / BAA |
|---|---|---|---|
| **Vapi** | $0.05/min platform + STT/LLM/TTS/telephony pass-through → **~$0.12–0.24/min all-in** [i1] | Built-in KB, custom tools (webhooks), MCP (UNVERIFIED) | **HIPAA add-on ~$2,000/mo; ZDR add-on ~$1,000/mo** (sources conflict) [i1] |
| **Retell AI** | From $0.07/min voice engine; **$0.11–0.18/min realistic** [i2] | KB: first 10 free, then $8/mo each + $0.005/min when used; function calling [i2] | BAA **Enterprise only**, not on PAYG [i2] |
| **Bland** | ~$0.09–0.14/min [i3] | Tools, KB, pathways | BAA available, but Enterprise-gated [i3] |
| **ElevenLabs Agents** | ~$0.08/min overage + LLM + telephony billed separately; plan bundles (price cut May 2026) [i4] | Native KB with RAG index; tools; MCP (UNVERIFIED) | BAA **Enterprise only**, with Zero Retention Mode [i4] |
| **LiveKit Agents** (OSS framework + Cloud) | Cloud agent-session $0.01/min over quota; plans Build free / Ship $50 / **Scale $500** [i5] | You code RAG/tools yourself (Python/Node). Plugins for OpenAI, xAI, Deepgram etc. | **BAA on Scale ($500/mo) and Enterprise** [i5] |
| **Pipecat** (OSS) / Pipecat Cloud (Daily) | From $0.01/agent-min [i5] | Code-first pipeline, any retriever | Pipecat Cloud says HIPAA-compliant (BAA terms UNVERIFIED) [i5] |
| **OpenAI Realtime API** | gpt-realtime: $32/M audio in, $64/M audio out (≈$0.02/min in, ~$0.08/min out); mini $10/$20 [i6] | Function calling, remote MCP; no built-in KB | BAA coverage **disputed / UNVERIFIED**: [i6] (May 2026) says realtime audio is not covered; OpenAI's HIPAA-eligible list reportedly includes `/v1/realtime` with a BAA + Modified Retention (help.openai.com 20001069, not re-verified). Azure OpenAI realtime: not covered per [i10] |
| **xAI Grok Voice Agent API** | grok-voice-think-fast-2.0 **$0.08/audio-min** (v1.0 $0.05, deprecated) [i7] | OpenAI-Realtime-compatible; LiveKit plugin; tools, web/X search | No BAA found (UNVERIFIED): treat as non-HIPAA |
| **Deepgram Voice Agent API** | ~$0.075/min bundled ($4.50/hr); $0.05–0.16/min depending on BYO LLM/TTS [i8] | Function calling; BYO LLM | BAA via enterprise sales (UNVERIFIED terms) [i8] |
| **Azure Voice Live / Azure AI Speech** | Voice Live Pro: $4.40/M text in, $17/M audio in; Standard/Lite $15/M audio; BYO-model $12.50/$30 per M [i9] | Foundry agents, Azure AI Search grounding, tools | **Azure Speech STT/TTS are HIPAA-covered.** GPT-realtime audio path is **not** covered [i10]. Voice Live coverage UNVERIFIED |

**Medical-office pattern that works under a BAA today:** Azure Speech STT → Azure OpenAI or Claude API (HIPAA-ready, direct API) text LLM → Azure TTS, orchestrated with LiveKit (Scale) or Pipecat. Alternatively, pay Vapi's HIPAA add-on or sign an Enterprise deal with Retell/ElevenLabs/Bland.

---

## 4. Microsoft side

| Item | Facts | Source |
|---|---|---|
| **M365 Copilot** | Enterprise $30/user/mo (annual) on top of a base license. **Copilot Business (≤300 users) $21**, promo $18 through 2026. Requires Business Std/Prem or E3/E5 etc. | [j1] |
| What Copilot sees | Anything the signed-in user can already access in Graph (mail, Teams, SharePoint/OneDrive) via the semantic index, plus Copilot connector content. It is permission-trimmed, so **over-shared SharePoint is the main risk for privileged folders** | [j4] (general doc; permission-trimming is standard Microsoft guidance) |
| **Copilot Studio** | No per-user fee. Copilot Credits $0.01 PAYG or packs of 25,000 for $200/mo ($0.008). Unused credits don't roll over. Agents grounding on SharePoint/connectors consume credits | [j2][j4] |
| **Copilot Retrieval API** | Returns chunks from the M365 semantic index (SharePoint/OneDrive/connectors). **Free for Copilot-licensed users; $0.10/call PAYG otherwise**. Lets your own app do RAG over SharePoint **without copying docs** | [j5] |
| **Copilot (Graph) connectors** | 50M items tenant index quota at no extra cost, 5M items per connection default. Microsoft-built connectors are free; ingestion is free | [j4] |
| Can Copilot query an external graph? | **Yes, via Copilot Studio / declarative agents with MCP tools** (streamable transport; the wizard adds each MCP tool) or API plugins/custom connectors. A Neo4j/AGE MCP server can be exposed this way. Connectors can also push graph-derived "items" into the index | [j6] |
| **Dataverse capacity** | Extra DB capacity **~$40/GB-mo**; file $2/GB-mo; log $10/GB-mo | [j3] |
| SharePoint Lists vs Dataverse vs Excel | Lists: 30M item cap, 5,000 list-view threshold, sluggish past ~100k items in Power Apps, delegation limits 500–2,000. Dataverse for Teams: 2 GB / 1M rows. Full Dataverse: relational, row-level security, but $40/GB. Excel tables: no concurrency, no security, prototype only | [j7] |
| **Purview / eDiscovery** | eDiscovery Premium: in E5 / E5 Compliance (~$12 above E3) or **Purview Suite for Business Premium $10/user/mo** (≤300 users). Copilot prompts/responses are discoverable and holdable like mail/Teams | [j8][j9] |

**Implication:** keep evidence files in SharePoint (legal hold, retention labels, Purview review sets). The graph holds pointers and extracted facts only. Tag graph nodes with SharePoint item IDs and sensitivity labels so privilege status is inherited.

---

## 5. Legal-specific

### 5a. Privilege and confidentiality when using hosted AI

| Topic | Finding | Source |
|---|---|---|
| **US v. Heppner (SDNY, Rakoff J., Feb 2026)** | Defendant's own Claude (consumer) chats were **not privileged/work product**: no attorney direction, and the consumer privacy policy allowed training and disclosure to regulators. First ruling of its kind | [k1] |
| ABA Formal Op. 512 (Jul 2024) | Self-learning tools: **informed client consent is required** before inputting client info. Lawyers must vet vendor terms (retention, training, access) | [k2] |
| OpenAI API | No training on API data by default. ZDR for eligible customers. BAA covers ZDR-eligible endpoints only (chat/responses) | [k3] |
| Azure OpenAI | Default 30-day abuse-monitoring retention. **Modified Abuse Monitoring (ZDR) only for managed EA/MCA-E customers**, not PAYG. DataZone (US/EU) or Standard (in-geo) deployments for residency | [k4] |
| Anthropic Claude API | ZDR arrangement available. HIPAA-ready API requires 30-day retention (not ZDR). **HIPAA readiness is not available for Claude on AWS/Microsoft Foundry** | [k5] |
| Graph/vector hosts | Neo4j Aura, Pinecone etc. are ordinary processors (DPA, SOC 2). Privilege risk comes from third-party *access/use*, not storage. Prefer tenant-resident (Azure PG, self-host) for privileged text. Store embeddings + excerpts, not whole documents, where possible | Practice guidance (UNVERIFIED as legal advice) |

**Controls checklist:**
1. Build under counsel direction (a Kovel-style engagement memo).
2. Use enterprise/API tiers only, with no-training + ZDR/MAM, a signed DPA, and a BAA if PHI is involved.
3. Pin US data residency.
4. Put a privilege flag and matter ID on every node; build retrieval ACLs from SharePoint permissions.
5. Keep an audit log of every LLM call.
6. Keep a separate graph (or DB) per matter/client. No cross-matter embeddings.
7. Get client informed consent per Op. 512.

### 5b. Legal graph use cases
- **Entity/relationship extraction:** Person, Org, Document, Email, Event, Matter, Claim, Exhibit. Relationships include SENT/RECEIVED/CC, AUTHORED, MENTIONS, EMPLOYED_BY, PARTY_TO, PRIVILEGED_WITH.
- **Timeline:** events ordered by date and linked to supporting docs.
- **"Who knew what when":** `(:Person)-[:RECEIVED {date}]->(:Email)-[:MENTIONS]->(:Fact)`.
- **Other uses:** privilege-log generation, custodian mapping, deposition prep, contradiction finding.
- **Evidence:** graph+LLM eDiscovery ranking (DISCOG) reports ~98% review-cost reduction in deployments [k6]. Generic GraphRAG joint extraction misses fine-grained legal entities, so use typed schemas and multi-pass extraction [k6].

---

## 6. Recommendation matrix

Monthly estimates exclude M365 licenses and LLM extraction tokens, which vary with volume.

| Tier | Graph | Vector / search | Embedding | OCR + extraction pipeline (§7) | OpenAI / xAI role (§8) | Voice | Est. $/mo |
|---|---|---|---|---|---|---|---|
| **Personal / litigation v1 (<$100)** | Neo4j **AuraDB Free** (prototype), or **Azure PG Flexible B1ms/B2s + Apache AGE** | pgvector in the same PG, or Neo4j vector index (small) | voyage-law-2 (50M free) or text-embedding-3-small | Azure DI Read ($1.50/1k pages) or Docling/PaddleOCR locally. **Grok 4.1 Fast or GPT-5.6 Luna (batch)** for extraction/summary/sentiment/classify/rename proposals | xAI API (**no-training, 30-day retention**) as the cheap extraction LLM **for items that passed the §7c step-0 privilege screen**; privileged candidates only via a contracted ZDR endpoint or in-tenant (Azure OpenAI). SuperGrok/ChatGPT Plus for *non-privileged* exploration only | None, or Grok Voice ($0.08/min) / Vapi PAYG demos (non-PHI) | **$0–60** + one-off corpus run ~$150–700 (see §7c) |
| **Small multi-company ($100–500)** | **Neo4j AuraDB Professional 2–4 GB** ($130–260), one DB per company/matter group, or AGE on Azure PG D2s | pgvector on Azure PG (~$100), or Azure AI Search Basic ($75) for hybrid over SharePoint | voyage-4 / voyage-law-2; text-embedding-3-small via Azure OpenAI for tenant residency | Azure DI Layout for statements/tax forms; LLM pass via Azure OpenAI (in-tenant) or xAI API; rename manifest in a SharePoint list | **Grok Business $30/seat** (SharePoint/OneDrive connectors, no training) *or* ChatGPT Business $20–25/seat. xAI Collections for a *working copy* corpus | LiveKit/Pipecat OSS + **Grok Voice Agent** via LiveKit xAI plugin, graph via tool/MCP; Copilot Studio agent (MCP → graph) internally | **$250–500** |
| **Commercial product LitigationForce/LexVault ($500–2k)** | Neo4j Aura Professional 8–16 GB or Business Critical (HA) — or Enterprise via startup program; **FalkorDB Pro ($350+)** for multi-tenant low-latency. Avoid ArangoDB/Memgraph Community licenses for SaaS | Turbopuffer ($16+) / Pinecone ($50+), or **Elastic Serverless** (BM25 + ELSER + vector hybrid, ~$25+ small) / Azure AI Search S1 ($250) | voyage-law-2 + Cohere v4 (scanned exhibits). BYO-key/ZDR options for customers | Reducto/LlamaParse for hard layouts; Azure DI for M365-tenant customers | **xAI API Enterprise (ZDR, US endpoint, BAA on request)** and/or OpenAI API (ZDR) as swappable LLM backends. Offer customer-choice of provider | Grok Voice / OpenAI Realtime for sales (non-PHI); Vapi + HIPAA add-on ($2k) *or* LiveKit Scale ($500) with STT→text LLM→TTS for medical | **$800–2,000** + per-minute voice (~$0.08–0.20/min) |
| **Enterprise / consulting (>$2k)** | Client's platform: Neo4j Enterprise/Aura BC, **Microsoft Fabric graph (GQL)** for Fabric shops, Neptune (+Analytics) for AWS shops | Azure AI Search S1+/S2, Elastic Cloud Hosted, OpenSearch (AWS), Cosmos DB NoSQL DiskANN | Azure OpenAI (MAM/ZDR, DataZone) or self-hosted Qwen3/BGE for air-gapped legal | Azure DI + Purview eDiscovery Premium review sets for litigation; Textract/Document AI for AWS/GCP clients | ChatGPT Enterprise (~$45–75/seat, 150-seat min) or Grok Enterprise (custom, Enterprise Vault/CMEK) per client standard | Azure Speech + Azure OpenAI text (BAA), orchestrated with LiveKit/Pipecat; Retell/ElevenLabs Enterprise BAA | **$2k–10k+** |

**Suggested first build:**
1. Ingest the SharePoint litigation library via Graph API (delta queries).
2. Extract with neo4j-graphrag `SimpleKGPipeline` using a fixed legal schema.
3. Store in Neo4j AuraDB Free/Pro, keeping `sharepointItemId` on each node.
4. Chunk vectors with voyage-law-2 (1024-d, quantized).
5. Expose through an MCP server to Claude and Copilot Studio.

Revisit Azure PG + AGE if cost or tenant residency outweighs Neo4j's tooling.

---

## 7. Search engines and document-processing pipelines (vs the graph/vector stack)

### 7a. Search engines

| Engine | Retrieval | Pricing | In M365/Azure tenant? | Role vs graph/vector |
|---|---|---|---|---|
| **Elastic Cloud Serverless** | BM25 + dense vector + **ELSER** sparse via `semantic_text` (auto-chunk and embed at ingest), BBQ quantization, RRF hybrid, rerank [l1] | Search VCU $0.14/hr; ingest/ML VCUs from $0.07/hr; storage per GB; **no minimum**, ~$24–27/mo for a ~2 GB dev project [l1][l2] | No (Elastic-operated; Azure-region deployments possible, UNVERIFIED) | Best *hybrid keyword + semantic* search for eDiscovery-style queries (exact names, Bates numbers, phrases). Pair with the graph for relationships |
| **Elastic Cloud Hosted** | Same features | From ~$99/mo Standard; realistic production $1.5k–8k/mo [l2] | Hosted on Azure/AWS/GCP in Elastic's account. Self-managed on Azure VMs = in-tenant | Enterprise/consulting |
| **Amazon OpenSearch Serverless** | BM25 + k-NN vector, hybrid, neural plugins | $0.24/OCU-hr. Classic collections ~2 OCU min (~$350/mo). **NextGen collections (GA 2026-05-28) scale to zero** [l3] | No (AWS) | AWS clients, Bedrock KBs |
| **Azure AI Search** | BM25 + vector + semantic ranker; integrated vectorization; SharePoint/Blob indexers | Basic $75/mo, S1 $250/mo [g2] | **Yes** (Azure subscription, Microsoft DPA/BAA) | Default for M365-heavy clients. Security trimming possible |
| **Purview eDiscovery (Premium)** | KQL search across M365 + review sets with **near-dup, email threading, themes, predictive coding/TAR**, legal hold, export [l4] | In E5/E5 Compliance (~$12/user over E3) or Purview Suite for Business Premium $10/user. Some review-set storage for non-M365 data is PAYG per GB [j8][j9][l4] | **Yes, and data never leaves M365** | **The litigation-grade alternative for collection, hold, dedupe/threading and review.** Use it for defensible collection, then export review sets to the graph pipeline |

### 7b. OCR / parsing options (price per 1,000 pages)

| Option | $/1k pages | Notes | In tenant? |
|---|---|---|---|
| **Azure AI Document Intelligence** | **Read $1.50**; Layout/prebuilt (invoice, bank statement, tax W-2/1099 etc.) **$10**; custom extraction $30; classifier $3; add-ons $6. Free F0 500 pages/mo [m1] | Prebuilt bank-statement/tax models (model list UNVERIFIED per version). Container/disconnected option (UNVERIFIED terms) | **Yes** |
| AWS Textract | DetectText $1.50; Tables $15; Forms $50; Expense $8 [m2] | Strong forms | No (AWS) |
| Google Document AI | Enterprise OCR $1.50 (→ $0.60 over 5M/mo); Layout Parser $10; Form/Custom $30 [m2] | | No (GCP) |
| Mistral OCR | $1–5 (sources conflict: OCR 3 ~$2 + annotations $3; batch ~50% off) — UNVERIFIED [m3] | Markdown output, good tables | No (self-deploy option UNVERIFIED) |
| Reducto | r-1 parse ~$10; extract $20 (includes parse); 15k free credits [m3] | Best on messy layouts per vendor claims | No (VPC/on-prem enterprise UNVERIFIED) |
| LlamaParse | $1.25 per 1k credits; 1/3/10/45 credits/page → **$1.25 / $3.75 / $12.50 / $56** per 1k pages [m4] | Agentic modes use LLMs | No |
| Unstructured.io API | ~$30 (15k pages free) [m4] | 50+ file types incl. .eml/.msg | No; **OSS library self-hostable = in-tenant** |
| **Open source:** Tesseract, docTR, PaddleOCR (PP-StructureV3, PaddleOCR-VL-1.5), **Docling**, Unstructured OSS | $0 + compute | Tesseract <1 s/page/core on clean scans. PaddleOCR-VL-1.5: 94.5% OmniDocBench. Docling gives clean Markdown but is weak on scans/handwriting, so pair it with an OCR engine [m5] | **Yes** (Azure VM/Container Apps) |
| **Vision LLM as OCR** (Grok, GPT) | Token-priced. Roughly $0.3–3 per 1k pages at cheap-model rates (UNVERIFIED; depends on image tokens) | Good for handwriting/stamps; can hallucinate. Keep a classic OCR text layer for evidence | Only Azure OpenAI is in-tenant |

### 7c. End-to-end ingestion pipeline (legal/financial)

**Stages:**
0. **Privilege screen before anything leaves the tenant:** classify every item as privileged-candidate or not *before* any external
   API sees it: in-tenant rules (attorney/counsel email domains, "privileged"/"attorney-client" markers, custodians, legal-site paths),
   optionally Purview eDiscovery or Azure OpenAI in the tenant. Privileged candidates go **only** to an approved, contracted
   endpoint (ZDR / Modified Retention, DPA, at counsel's direction) or stay in-tenant. The ordinary xAI/OpenAI API tiers
   (30-day retention) get only items screened as non-privileged.
1. **Ingest:** Purview export or Graph API delta from SharePoint/Exchange. Capture SHA-256, `driveItem` ID, custodian and original path.
2. **De-dupe and thread:** Purview near-dup/threading, or hash + `Message-ID`/`In-Reply-To`.
3. **OCR:** skip native-text PDFs/emails; OCR scans only.
4. **Entity/relationship extraction** into the canonical ontology (Person, Org, Account, Matter, Event, DocType).
5. **Summarization.**
6. **Sentiment/tone.**
7. **Classification** (DocType, privilege-candidate flag, responsiveness).
8. **Rename proposal** in the form `YYYY-MM-DD_<Entity>_<Subject>_<DocType>.ext` using canonical entity short names from the ontology.
9. **Before→after manifest** with human review.
10. **Apply**, then write to graph, vector store and search index.

Stages 4–8 fit in **one structured-output LLM call per document/chunk**, which cuts cost.

**Rename rules (evidence integrity):**
- **Never rename originals under legal hold or in the collection set.**
- Either (a) rename in a *working* library copy, or (b) store the canonical name in a SharePoint column (e.g. `CanonicalName`) and leave `Name` alone.
- A Graph `PATCH driveItem {name}` keeps the item ID and version history (standard Graph behavior; hold/preservation-library interaction is UNVERIFIED).
- The script is **dry-run by default** and logs every action (matches repo AGENTS.md §4).

Manifest columns: `sha256, item_id, original_path, original_name, proposed_name, doc_date, date_source(header|body|metadata), entity_id, subject, doctype, confidence, privilege_flag, reviewer, status, applied_at`.

**Corpus estimate: 50,000 pages + 200,000 emails**

Assumptions: ~500 tokens/page, ~600 tokens/email body after quote-stripping, so ~145M tokens. One combined LLM pass ≈ 190M input (with prompt) + 30M output tokens.

| Cost item | Per 1,000 pages (≈ per 1,000 emails) | Whole corpus |
|---|---|---|
| OCR — Azure DI Read / Textract / Google OCR | $1.50 | ~$75 (if all 50k pages need OCR) |
| OCR — Azure DI Layout / Google Layout (tables, statements) | $10 | ~$500 |
| OCR — Reducto / LlamaParse cost-effective / Unstructured | $10 / $3.75 / $30 | $500 / $190 / $1,500 |
| OCR — open source on Azure VM | ~$0 + VM (~$0.10–0.50, UNVERIFIED) | ~$20–50 of compute |
| LLM pass — **Grok 4.1 Fast** ($0.20/$0.50) [n2] | ~$0.19 | **~$55** |
| LLM pass — **GPT-5.6 Luna** ($0.20/$1.20; batch −50%) [n6] | ~$0.27 (batch $0.14) | ~$75 (batch ~$37) |
| LLM pass — Grok 4.3 ($1.25/$2.50) [n2] | ~$1.10 | ~$310 |
| LLM pass — **Grok 4.6** ($2/$6) [n2] | ~$2.00 | ~$560 |
| LLM pass — GPT-5.6 Terra ($2/$12; batch −50%) [n6] | ~$2.75 (batch $1.37) | ~$740 (batch ~$370) |
| LLM pass — GPT-5.6 Sol ($5/$30) [n6] | ~$6.85 | ~$1,850 |
| Embeddings (145M tok) — 3-small / voyage-law-2 / gemini-001 | ~$0.01–0.10 | ~$3 / ~$11 / ~$22 |

**Realistic total for the corpus:**
- Budget build (DI Read + Grok 4.1 Fast or Luna for bulk, a stronger model on the ~5–10% flagged privileged/hot docs, voyage-law-2): **~$150–400 one-off**.
- Quality build (DI Layout + Grok 4.6/Terra everywhere): **~$1,000–1,500**.
- Human review of rename/privilege flags is the real cost.

**Throughput:**
- Batch LLM APIs return within a 24-hour window (OpenAI [n6]).
- Online calls are rate-limit-bound (tier-dependent, UNVERIFIED).
- Azure DI async runs in parallel. Hundreds of pages/min is typical, but UNVERIFIED for your tier.
- OSS Tesseract at ~1 page/s/core does 50k pages in ~2 h on 8 cores [m5].
- **The whole corpus is feasible in 1–2 days wall-clock.**

**Options that stay inside the M365/Azure tenant boundary:**
- Purview
- SharePoint
- Azure DI
- Azure OpenAI (Standard or DataZone US; MAM for ZDR needs EA/MCA-E [k4])
- Azure AI Search
- Azure PG (AGE + pgvector)
- OSS OCR on Azure compute
- Copilot Retrieval API

These leave the tenant: xAI, OpenAI direct, Elastic Cloud, Reducto, LlamaParse, Mistral, Voyage, Neo4j Aura. Use them under a DPA with no-training + ZDR, and ideally only on non-privileged or pre-screened sets.

---

## 8. OpenAI/ChatGPT and xAI/Grok as the pipeline platform

### 8a. OpenAI / ChatGPT

| Surface | Price | Pipeline-relevant features | Data terms |
|---|---|---|---|
| ChatGPT Free/Plus/Pro | Plus ~$20; Pro $100 / $200 tiers [n7] | Projects, file uploads, deep research, custom GPTs, connectors (per-tier availability UNVERIFIED) | **Trains by default** unless "Improve the model for everyone" is off. Temporary chats deleted after 30 days [n7]. **Not for privileged material** (see *Heppner* [k1]) |
| **ChatGPT Business** (ex-Team) | **$20/seat/mo annual, $25 monthly, 2-seat min** (cut 2026-04-02) [n8] | Shared projects, connectors incl. SharePoint/Drive, deep research, GPTs | **No training by default** [n8] |
| **ChatGPT Enterprise** | Quote. Reported ~$45–75/seat, ~150-seat minimum [n8] | Synced SharePoint connector (**US data residency only**), SSO/SCIM, compliance export, **Microsoft Purview integration for ChatGPT Enterprise** (audit/DLP/eDiscovery) [n8][n9] | No training. Custom retention ≥90 days. Data residency options [n8] |
| **OpenAI API** — models | GPT-6 Astra $10/$50. **GPT-5.6 Sol $5/$30, Terra $2/$12, Luna $0.20/$1.20** per 1M in/out. **Batch −50%**, cached input 10% [n6] | Responses API, structured outputs, vision (OCR), tools, remote MCP | No training by default. 30-day abuse retention unless ZDR. **ZDR for eligible customers**. BAA covers ZDR-eligible endpoints only (chat/responses) [k3]. NYT blanket preservation order ended 2025-09-26 [n7] |
| OpenAI API — `file_search` / vector stores | **$0.10/GB-day (first 1 GB free) + $2.50 per 1k tool calls** [n5] | Managed chunk/embed/hybrid search | Stored until deleted. ZDR-compatibility of stored files UNVERIFIED |
| OpenAI API — embeddings | 3-small $0.02, 3-large $0.13 per 1M (batch −50%) [f1] | | |
| OpenAI API — Realtime voice | gpt-realtime $32/$64 per 1M audio tok (~$0.02 in / ~$0.08 out per min); mini $10/$20 [i6] | Function calling, MCP | BAA coverage disputed (see §3b row); confirm with OpenAI before PHI |

### 8b. xAI / Grok (user priority)

| Surface | Price | Pipeline-relevant features | Data terms |
|---|---|---|---|
| **grok.com / Grok mobile & desktop apps** | Free; SuperGrok Lite $10, **SuperGrok $30**, Plus $100, Heavy $300/mo [n10] | Chat, file upload, DeepSearch, voice mode, projects (UNVERIFIED) | **Trains on content unless "Improve the model" is off**. Private Chat deleted within ~30 days (with law-enforcement/safety exceptions) [n10]. **Consumer = not for privileged data** |
| **Grok in X** | Bundled with X Premium tiers | Q&A over X posts | X uses public posts and Grok interactions for training by default outside the EU; opt-out under Settings → Privacy → Grok & Third-party Collaborators [n11]. **Never use for client data** |
| **Grok Business** | **$30/user/mo** [n12] | Team workspaces/projects; **connectors: Google Drive, Gmail, Calendar, Microsoft 365, SharePoint, OneDrive, Teams, Salesforce, GitHub, Notion** [n12] | **No training by default**; custom retention settings [n12] |
| **Grok Enterprise** | Custom [n12] | SSO, SCIM, audit, **Enterprise Vault** (data isolation, customer-managed keys) [n12] | Enterprise terms (x.ai/legal/terms-of-service-enterprise). Privilege-relevant clauses UNVERIFIED (not read, fetch blocked) |
| **Grok Build (CLI)** | Needs SuperGrok or X Premium+ subscription. grok-build model pricing conflicts ($0.20/M in vs $1/$2) — UNVERIFIED [n13][n2] | Terminal agent, 8 parallel subagents in git worktrees, plan-first, **MCP/skills/hooks**. Apache-2.0 since 2026-07-15. v1.0 on 2026-08-07 [n13] | Runs on the consumer subscription, so consumer terms likely apply (UNVERIFIED). Keep it away from privileged data |
| **xAI API — models** | **Grok 4.7** $2/$6 (<200k ctx; $4/$12 ≥200k). **Grok 4.6** $2/$6. **Grok 4.3** $1.25/$2.50. **Grok 4.1 Fast** $0.20/$0.50, 2M context. Cached input discounts. **US regional endpoint `us.api.x.ai` (4.7/4.6 only) is +10%** [n2][n4] | Vision input (OCR-capable), structured outputs, function calling, **Remote MCP tools (no per-call fee, tokens only)**. Server tools: web/X search $5/1k, code exec $5/1k, **collections_search $2.50/1k** [n3] | **No training on API data**. 30-day retention for abuse audit. **ZDR = Enterprise only** [n4]. Processor under xAI DPA [n4]. SOC 2 Type 2. **BAA on request (questionnaire), ZDR must be enabled before PHI** [n4] |
| **xAI API — Files & Collections** | Files $0.025/GiB-day. **Collections $0.10/GiB-day**. Search $2.50/1k calls. Indexing/storage free for the first week [n1] | Launched 2025-12-22. **PDF, TXT, DOCX, MD, CSV, HTML** (plus code/Excel per announcement). **OCR + layout-aware parsing** of PDFs. **Semantic, keyword and hybrid search with reranker/RRF**. **Limits: 100 MB/file, 100,000 files, 100 GB per account** (contact xAI to raise) [n1][n14] | Stored files are retained until deleted, which is inherently incompatible with ZDR (UNVERIFIED how xAI reconciles this) |
| **xAI API — embeddings** | No standalone public embeddings endpoint confirmed. `grok-embedding-small` is used inside Collections [n15] | Can't export Grok embeddings to your own vector DB, so use Voyage/OpenAI/etc. for pgvector/Neo4j (UNVERIFIED if gRPC exposes it) | |
| **xAI Voice Agent API** | **grok-voice-think-fast-2.0 $0.08/min** (+ $0.004 text input); v1.0 $0.05 deprecated [i7] | Native speech-to-speech over WebSocket, OpenAI-Realtime-compatible, **LiveKit xAI plugin**, **function calling (tool calls often start before the first sentence ends)**. TTFA ~0.70–0.78 s [n16] | BAA status for voice UNVERIFIED. Treat as non-PHI until xAI confirms in writing |

### 8c. Practical answers

**Can xAI Collections be the canonical corpus for a litigation evidence set?** Not as the system of record. Use it as a derived retrieval index at most.

| Criterion | xAI Collections | SharePoint + Azure AI Search | Elastic | Neo4j |
|---|---|---|---|---|
| Capacity | 100k files / 100 GB per account [n14]. **200k emails exceed the file cap**: bundle by thread/day or request a raise | 30M items/list; TB-scale libraries | Unlimited (cost-bound) | Graph only (store pointers) |
| Legal hold / retention / chain of custody | Not documented (UNVERIFIED) | **Purview holds, retention labels, preservation library, audit** | Via snapshots/ILM, not legal hold | No |
| Versioning / export | Not documented. Files API download UNVERIFIED | Native version history, Purview export | Snapshots, reindex | Dump/export |
| Access control | API-key/team level. Per-document ACL not documented (UNVERIFIED) | Entra ID permissions + security trimming | Document-level security (paid tiers) | RBAC (Enterprise/Aura) |
| Retrieval quality | Hybrid + rerank, built-in OCR | Hybrid + semantic ranker | Best keyword+semantic hybrid | Relationships, timelines |
| Cost for ~15 GB corpus | ~$45/mo storage + $2.50/1k searches | $75–250/mo | ~$25–100/mo serverless | $65–260/mo |

**Verdict:**
- SharePoint (+ Purview) remains the canonical store.
- Neo4j/AGE holds the relationships.
- Azure AI Search or Elastic serves full-text/hybrid search.
- xAI Collections is a reasonable quick RAG index for Grok-based agents over a curated, non-privileged or ZDR-cleared subset, rebuilt from SharePoint by a sync job.

**How a Grok voice agent queries the graph/vector store:**
1. Run **Grok Voice Agent API** directly or via the **LiveKit xAI plugin** [i7][n16].
2. Declare function tools, e.g. `lookup_person(name)`, `timeline(matter, from, to)`, `search_docs(query)`.
3. The agent emits a tool call. Your backend runs a parameterized Cypher query (Neo4j/AGE) plus a pgvector/Azure AI Search query and returns ≤1–2 KB of text.
4. Keep the backend under ~100 ms (see §3a). Pre-fetch the caller's context at call start.
5. Alternatives:
   - For text/agent flows, the xAI Responses API's **Remote MCP tools** can call a Neo4j MCP server directly with no per-call fee [n3].
   - `collections_search` ($2.50/1k) can query an xAI Collection.
   - Remote MCP support *inside the voice WebSocket* is UNVERIFIED (checked 2026-09-24). Use client-side function calls, or LiveKit's agent-side tool/MCP support (UNVERIFIED).
6. **Medical use:** the Grok voice BAA is unconfirmed, so use the STT → BAA LLM → TTS pattern in §3b.

---

## Sources

**Graph**
- [a1] Neo4j pricing via search snippets: https://checkthat.ai/brands/neo4j/pricing ; https://www.modern-datatools.com/tools/neo4j/pricing ; https://neo4j.com/docs/aura/billing/billing-dimensions/ (as of 2026-09-24)
- [a2] https://neo4j.com/cloud/platform/aura-graph-database/faq/ ; https://support.neo4j.com/s/article/16094506528787-Support-resources-and-FAQ-for-Aura-Free-Tier (2026-09-24)
- [a3] https://neo4j.com/docs/aura/graph-analytics/ ; https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/vector-indexes/ ; https://neo4j.com/docs/aura/managing-instances/vector-optimization/ (2026-09-24)
- [a4] https://db-news.com/navigating-the-neo4j-licensing-maze-a-deep-dive-into-agpl-enterprise-and-open-source-implications ; https://www.packtpub.com/networking-ee/learning/tech-news/neo4j-enterprise-edition-is-now-available-under-a-commercial-license (2026-09-24)
- [a5] https://github.com/neo4j/neo4j-graphrag-python ; https://pypi.org/project/neo4j-graphrag/ (2026-09-24)
- [b1] https://calculator.holori.com/aws/rds/db.t4g.medium ; https://www.usage.ai/blogs/aws/database-savings-plans/neptune-pricing/ (2026-09-24)
- [b2] https://www.usage.ai/blogs/aws/database-savings-plans/neptune/serverless-ncu-pricing/ ; https://aws.amazon.com/neptune/pricing (2026-09-24)
- [b3] https://aws.amazon.com/about-aws/whats-new/2024/07/amazon-neptune-analytics-smaller-capacity-units (2026-09-24)
- [c1] https://holori.com/azure-cosmos-db-pricing-guide/ ; https://learn.microsoft.com/en-us/azure/cosmos-db/serverless (2026-09-24)
- [c2] https://techcommunity.microsoft.com/blog/adforpostgresql/postgresql-as-your-graph-database-in-the-ai-era/4516323 ; https://learn.microsoft.com/en-us/azure/postgresql/azure-ai/generative-ai-age-overview (2026-09-24)
- [c3] https://www.bytebase.com/dbcost/azure-flexible-server-pricing/ ; https://azure.microsoft.com/en-us/products/postgresql (2026-09-24)
- [d1] https://memgraph.com/pricing ; https://github.com/memgraph/memgraph/blob/master/licenses/BSL.txt (2026-09-24)
- [d2] https://docs.falkordb.com/cloud/free-tier.html ; https://github.com/FalkorDB/docs/blob/main/cloud/startup-tier.md ; https://docs.falkordb.com/References/license.html (2026-09-24)
- [d3] https://www.macrumors.com/2026/02/11/apple-acquires-new-database-app/ ; https://gdotv.com/blog/kuzu-legacy-embedded-graph-database-landscape/ (2026-09-24)
- [d4] https://szarnyasg.org/posts/kuzu-forks/ ; https://thedataquarry.com/blog/from-kuzu-to-ladybug/ (2026-09-24)
- [d5] https://www.tigergraph.com/savanna-pricing/ ; https://www.tigergraph.com/community-edition/ (2026-09-24)
- [d6] https://arangodb.com/2023/10/evolving-arangodbs-licensing-model-for-a-sustainable-future/ ; https://arango.ai/wp-content/uploads/2025/11/ADB-Community-License_31OCT2023.pdf (2026-09-24)
- [d7] https://surrealdb.com/pricing ; https://github.com/surrealdb/license (2026-09-24)
- [e1] https://community.fabric.microsoft.com/t5/Fabric-Updates-Blog/Graph-in-Fabric-Generally-Available/ba-p/5190748 (2026-09-24)
- [e2] https://learn.microsoft.com/en-us/fabric/graph/overview ; https://learn.microsoft.com/en-us/fabric/graph/gql-language-guide (2026-09-24)
- [e3] https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/ ; https://github.com/microsoft/graphrag (2026-09-24)

**Embeddings and vector stores**
- [f1] https://costgoat.com/pricing/openai-embeddings ; https://openai.com/index/new-embedding-models-and-api-updates/ (2026-09-24)
- [f2] https://docs.voyageai.com/docs/pricing ; https://embeddingcost.com/voyage (2026-09-24)
- [f3] https://pricepertoken.com/embedding/model/cohere-embed-4 ; https://vercel.com/ai-gateway/models/embed-v4.0 (2026-09-24)
- [f4] https://ai.google.dev/gemini-api/docs/embeddings ; https://embeddingcost.com/google (2026-09-24)
- [f5] https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models (2026-09-24)
- [g1] https://pecollective.com/tools/pinecone-pricing/ ; https://www.pinecone.io/pricing/estimate/ (2026-09-24)
- [g2] https://learn.microsoft.com/en-us/azure/search/search-sku-tier (2026-09-24)
- [g2b] https://learn.microsoft.com/en-us/azure/search/vector-search-index-size ; https://www.infoworld.com/article/2336726/microsoft-s-azure-ai-search-updated-with-increased-storage-vector-index-size.html (2026-09-24)
- [g3] https://qdrant.tech/pricing/ ; https://weaviate.io/pricing (2026-09-24)
- [g4] https://zilliz.com/pricing ; https://docs.trychroma.com/cloud/pricing (2026-09-24)
- [g5] https://turbopuffer.com/pricing ; https://costbench.com/software/vector-databases/lancedb/ (2026-09-24)
- [g6] https://www.mongodb.com/docs/atlas/billing/atlas-flex-costs/ ; https://www.cloudzero.com/blog/mongodb-pricing/ (2026-09-24)

**Voice**
- [h1] https://supermemory.ai/blog/latency-budgets-memory-retrieval ; https://www.spheron.network/blog/llm-inference-slo-ttft-itl-latency-budget-guide-2026/ ; https://arxiv.org/html/2603.02206v1 (2026-09-24)
- [i1] https://www.cloudtalk.io/blog/vapi-ai-pricing/ ; https://www.layer3labs.io/guides/vapi-pricing (2026-09-24)
- [i2] https://www.retellai.com/pricing ; https://www.cloudtalk.io/retell-ai-pricing/ (2026-09-24)
- [i3] https://www.bland.ai/pricing ; https://www.cloudtalk.io/blog/bland-ai-pricing/ (2026-09-24)
- [i4] https://elevenlabs.io/pricing/agents ; https://elevenlabs.io/docs/eleven-agents/legal/hipaa ; https://elevenlabs.io/docs/eleven-agents/customization/knowledge-base/rag (2026-09-24)
- [i5] https://livekit.com/pricing ; https://www.cekura.ai/blogs/livekit-pricing ; https://www.daily.co/pricing/pipecat-cloud/ (2026-09-24)
- [i6] https://www.layer3labs.io/guides/openai-realtime-api-pricing ; https://developers.openai.com/api/docs/pricing (2026-09-24)
- [i7] https://docs.x.ai/developers/models ; https://x.ai/news/grok-voice-agent-api (2026-09-24)
- [i8] https://deepgram.com/pricing ; https://diyai.io/ai-tools/speech-to-text/deepgram-pricing-2026/ (2026-09-24)
- [i9] https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/azure-ai-voice-live-api-what%E2%80%99s-new-and-the-pricing-announcement/4428687 (2026-09-24)
- [i10] https://learn.microsoft.com/en-us/answers/questions/5598862/is-the-gpt-realtime-model-in-azure-covered-under-b (2026-09-24)

**Microsoft**
- [j1] https://alphavima.com/blog/microsoft-365-copilot-pricing/ ; https://www.explainx.ai/blog/microsoft-365-copilot-pricing-licensing-2026 (2026-09-24)
- [j2] https://www.microsoft.com/en-us/microsoft-365-copilot/pricing/copilot-studio ; https://www.cloudzero.com/blog/copilot-studio-pricing/ (2026-09-24)
- [j3] https://airbyte.com/data-engineering-resources/microsoft-dataverse-pricing (2026-09-24)
- [j4] https://learn.microsoft.com/en-us/microsoft-365/copilot/connectors/overview ; https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/cost-considerations (2026-09-24)
- [j5] https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/api/ai-services/retrieval/overview (2026-09-24)
- [j6] https://learn.microsoft.com/en-us/microsoft-copilot-studio/mcp-add-existing-server-to-agent (2026-09-24)
- [j7] https://learn.microsoft.com/en-us/office365/servicedescriptions/sharepoint-online-service-description/sharepoint-online-limits ; https://www.wrvishnu.com/sharepoint-list-vs-dataverse/ (2026-09-24)
- [j8] https://www.2tolead.com/insights/microsoft-purview-licensing-e3-vs-e5-add-ons ; https://techcommunity.microsoft.com/blog/microsoft-security-blog/collecting-microsoft-365-copilot-data-with-microsoft-purview-ediscovery/4516489 (2026-09-24)
- [j9] https://www.microsoft.com/en-us/security/small-medium-business/microsoft-purview-suite-business-premium ; https://blog.ciaops.com/2025/10/06/microsoft-purview-ediscovery-premium-in-an-smb-environment-m365-business-premium/ (2026-09-24)

**Legal**
- [k1] https://harvardlawreview.org/blog/2026/03/united-states-v-heppner/ ; https://www.mcdermottlaw.com/insights/using-ai-without-waiving-privilege-lessons-from-heppner/ (2026-09-24)
- [k2] https://www.americanbar.org/news/abanews/aba-news-archives/2024/07/aba-issues-first-ethics-guidance-ai-tools/ (2026-09-24)
- [k3] https://developers.openai.com/api/docs/guides/your-data ; https://www.specode.ai/blog/openai-llm-api-hipaa (2026-09-24)
- [k4] https://learn.microsoft.com/en-us/answers/questions/5508723/azure-openai-abuse-monitoring-opt-out ; https://meetily.ai/llm-privacy/azure (2026-09-24)
- [k5] https://platform.claude.com/docs/en/manage-claude/api-and-data-retention ; https://support.claude.com/en/articles/8114513-business-associate-agreements-baa-for-commercial-customers (2026-09-24)
- [k6] https://arxiv.org/abs/2405.19164 ; https://arxiv.org/pdf/2510.26512 (2026-09-24)

**Search and OCR (§7)**
- [l1] https://www.elastic.co/pricing/serverless-search ; https://www.elastic.co/search-labs/blog/elasticsearch-serverless-pricing-vcus-ecus (2026-09-24)
- [l2] https://www.elastic.co/pricing/cloud-hosted ; https://neverblink.ai/kb/elastic-cloud-pricing-guide ; https://checkthat.ai/brands/elastic/pricing (2026-09-24)
- [l3] https://cloudburn.io/blog/amazon-opensearch-pricing ; https://coralogix.com/guides/opensearch/opensearch-pricing/ (2026-09-24)
- [l4] https://learn.microsoft.com/en-us/purview/ediscovery-overview ; https://learn.microsoft.com/en-us/purview/edisc-billing ; https://www.epcgroup.net/answers/microsoft-purview-ediscovery-premium-implementation-2026 (2026-09-24)
- [m1] https://docuocr.com/blog/azure-document-intelligence-pricing ; https://starnovai.com/azure-ai-document-intelligence-pricing (2026-09-24)
- [m2] https://aws.amazon.com/textract/pricing/ ; https://cloud.google.com/document-ai/pricing (2026-09-24)
- [m3] https://mistral.ai/pricing/ ; https://lenscopy.com/compare/mistral-ocr/ ; https://reducto.ai/pricing ; https://www.marktechpost.com/2026/09/07/reducto-releases-r-1-a-single-pass-document-parsing-model-that-cuts-errors-20-at-1-cent-per-page/ (2026-09-24)
- [m4] https://developers.llamaindex.ai/llamaparse/general/pricing/ ; https://markaicode.com/pricing/llamaparse-pricing/ ; https://www.usagepricing.com/blueprint/unstructured (2026-09-24)
- [m5] https://invoicedataextraction.com/blog/python-ocr-library-comparison-invoices ; https://unstract.com/blog/best-opensource-ocr-tools/ ; https://modal.com/blog/8-top-open-source-ocr-models-compared (2026-09-24)

**OpenAI and xAI (§8)**
- [n1] https://x.ai/news/grok-collections-api ; https://docs.x.ai/developers/files/collections ; https://www.eesel.ai/blog/xai-pricing (2026-09-24)
- [n2] https://docs.x.ai/developers/pricing ; https://benchlm.ai/xai/api-pricing ; https://costgoat.com/pricing/grok-api (2026-09-24)
- [n3] https://docs.x.ai/developers/tools/remote-mcp ; https://www.eesel.ai/blog/xai-pricing (2026-09-24)
- [n4] https://docs.x.ai/developers/faq/security ; https://meetily.ai/llm-privacy/xai ; https://x.ai/api ; https://aiprovidertrust.com/offerings/xai-api/ (2026-09-24)
- [n5] https://help.openai.com/en/articles/8550641-assistants-api-v2-faq ; https://www.eesel.ai/blog/openai-agents-api-pricing (2026-09-24)
- [n6] https://developers.openai.com/api/docs/pricing ; https://www.cloudzero.com/blog/openai-pricing/ ; https://devtk.ai/en/blog/openai-api-pricing-guide-2026/ (2026-09-24)
- [n7] https://intuitionlabs.ai/articles/chatgpt-plans-comparison ; https://www.engadget.com/ai/openai-no-longer-has-to-preserve-all-of-its-chatgpt-data-with-some-exceptions-192422093.html (2026-09-24)
- [n8] https://elephas.app/resources/chatgpt-business-pricing ; https://www.layer3labs.io/guides/chatgpt-enterprise-pricing ; https://openai.com/enterprise-privacy/ ; https://intuitionlabs.ai/articles/chatgpt-enterprise-connectors-office-365-azure (2026-09-24)
- [n9] https://learn.microsoft.com/en-us/purview/ai-chatgpt-enterprise (2026-09-24)
- [n10] https://suprmind.ai/hub/grok/pricing/ ; https://ai-chat-importer.com/blog/does-grok-use-your-conversations-for-training ; https://grokipedia.com/page/xAI_privacy_policy (2026-09-24)
- [n11] https://meprism.com/opt-out-guides/blog/x-grok-ai-training-opt-out ; https://trustscan.dev/blog/how-to-opt-out-grok-xai-data-training-2026 (2026-09-24)
- [n12] https://x.ai/grok/business ; https://www.channelinsider.com/ai/llms-chatbots-and-agents/grok-enterprise-plans/ ; https://www.usecarly.com/blog/grok-microsoft-365/ (2026-09-24)
- [n13] https://x.ai/news/grok-build-cli ; https://www.developersdigest.tech/blog/grok-build-developer-guide-2026 (2026-09-24)
- [n14] https://www.datastudios.org/post/grok-file-upload-and-supported-formats-explained-document-types-collections-image-inputs-and-sys ; https://grokipedia.com/page/Grok_Collections_API (2026-09-24; limits from secondary sources, confirm in console)
- [n15] https://www.promptfoo.dev/docs/providers/xai/ ; https://docs.x.ai/developers/grpc-api-reference (2026-09-24)
- [n16] https://x.ai/news/grok-voice-agent-api ; https://www.datacamp.com/tutorial/grok-voice-think-fast-2-0 ; https://www.eesel.ai/blog/grok-voice-think-fast-2-review (2026-09-24)
