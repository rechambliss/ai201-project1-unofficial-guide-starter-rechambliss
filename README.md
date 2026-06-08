# The Unofficial Guide Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text. If a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain
<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->

Off Campus Living at Liberty University.

Liberty University has specific requirements for off-campus housing and offers some partnerships for student only housing complexes. Students who want to live off campus have to figure out eligibility rules, the approval process through the Res Life Portal, transportation, and different housing options. This information is spread out across university pages, apartment listings, and student discussions.

This system brings that information into one searchable resource. It is useful because the official university pages are spread out and do not always show what students actually experience. Reddit and student discussions have real student experiences but they are unstructured and harder to search through. Together both types of sources can give students a better picture of off campus living.

---

## Document Sources

| #  | Source                                               | Type                     | URL or file path                                                                                                                             |
| -- | ---------------------------------------------------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | Housing Eligibility                                  | Official University page | https://www.liberty.edu/residence-life/housing/eligibility/                                                                                  |
| 2  | Liberty Housing Selection / Apply to Live Off Campus | Official University page | https://www.liberty.edu/residence-life/housing/                                                                                              |
| 3  | Transportation and Parking                           | Official University page | https://www.liberty.edu/students/student-life/transportation-and-parking/                                                                    |
| 4  | Liberty New Commuter Information                     | Official University page | https://www.liberty.edu/students/student-life/commuter/new-commuter-info/                                                                    |
| 5  | The Oasis University Sponsored Off Campus Housing    | Apartment listing        | https://offcampushousing.liberty.edu/housing/property/the-oasis-student-housing/7x29svw                                                      |
| 6  | The Vue at College Square Student Only Housing       | Apartment listing        | https://offcampushousing.liberty.edu/housing/property/new-furnished-townhouse-at-the-vue-at-college-square-4br-with-private-baths/ocp60rjkns |
| 7  | Reddit Discussion about The Oasis                    | Reddit thread            | https://www.reddit.com/r/LibertyUniversity/comments/1lqx8gv/oasis/                                                                           |
| 8  | Question about The Oasis on r/LibertyUniversity      | Reddit thread            | https://www.reddit.com/r/LibertyUniversity/comments/13kf4f7/the_oasisa_good_place_to_live/                                                   |
| 9  | Housing Question on r/LibertyUniversity              | Reddit thread            | https://www.reddit.com/r/LibertyUniversity/comments/1erbbnt/housing/                                                                         |
| 10 | Off Campus Living on r/LibertyUniversity             | Reddit thread            | https://www.reddit.com/r/LibertyUniversity/comments/1ddr6an/offcampus_living/                                                                |

---

## Chunking Strategy
<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** about 250 tokens

**Overlap:** 50 tokens

**Why these choices fit your documents:**

I used recursive token-aware chunking because my source documents are all formatted differently. Some are formal university pages. Some are apartment listings with prices and amenities. Some are Reddit threads with student comments. A simple fixed character splitter could cut through sentences or split important information in a weird place.

250 tokens is large enough to keep useful information together like an eligibility rule or a full Reddit comment. It is also small enough that retrieval can still find specific information. The 50 token overlap helps when important context is near the edge of a chunk.

If the chunks were too fragmented I would increase the chunk size. If one chunk had too many unrelated topics I would decrease the chunk size.

**Final chunk count:** 44

---

## Embedding Model

**Model used:** 'sentence-transformers/all-MiniLM-L6-v2', run locally. Embeddings are stored and retrieved using ChromaDB. The top 5 chunks, k = 5, are retrieved for each query.

I chose this model because it is lightweight and runs locally without an API call. It is made for semantic similarity over sentence and paragraph sized text which fits the chunks from the Liberty pages, apartment listings, and Reddit threads. Top-k = 5 gives the LLM enough context without giving it too many unrelated chunks.

I also changed retrieval so the embedded text includes metadata like the source title and source type. This helped with questions that mention a specific property like The Oasis or The Vue.

**Production tradeoff reflection:**

Semantic search helps the system find relevant chunks even when the user does not use the exact same words from the source. For example a question about bus access can still match chunks about free bus services, commuter routes, shuttle service, or Greater Lynchburg Transit Company.

If this was used in production I would think about context length, multilingual support, retrieval accuracy, latency, cost, and whether the model should run locally or through an API. A larger embedding model might work better with informal student language and apartment nicknames but it could also cost more and be slower. For this project local inference and decent semantic search over short chunks made 'all-MiniLM-L6-v2' a good fit.

---

## Grounded Generation
<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**LLM:** Groq 'llama-3.3-70b-versatile'

**System prompt grounding instruction:**

The generation prompt tells the model to answer only using the retrieved source context. If the retrieved context does not have enough information then the model should say it does not have enough information in the provided sources. The model should not use outside knowledge.

The prompt also tells the model to cite sources with labels like '[Source 1]', '[Source 2]', and so on.

**How source attribution is surfaced in the response:**

The answer includes source labels in the generated response. The interface also shows a separate Sources section under the answer. Each source includes the source title, source type, URL, filename, and chunk numbers used. Source metadata is added from the retrieved chunks instead of relying only on the model to remember sources.

---

## Evaluation Report
<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->
| # | Question                                                                                                                       | Expected answer                                                                                                                                                                                                                                                                                                 | System response summarized                                                                                                                                                                                                                    | Retrieval quality  | Response accuracy  |
| - | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------ |
| 1 | I am a freshman at Liberty University and want to move off campus next spring. Am I automatically eligible to live off campus? | No. A freshman is not automatically eligible just because they want to move off campus. The answer should explain that unmarried students under 21 are generally required to live on campus unless they meet an exception or approval criteria. It should also mention the Res Life Portal application process. | The system said the student is not automatically eligible and explained the 21 year old requirement or 20 year old requirement with GPA and academic hours. It also said the student may need to submit an off campus application for review. | Relevant           | Accurate           |
| 2 | I want to live off campus but I do not have a car. What transportation options could help me get to campus?                    | The answer should mention Liberty transportation or bus routes, Greater Lynchburg Transit Company, and apartment specific shuttle access where supported, such as The Oasis.                                                                                                                                    | The system mentioned Liberty free bus services, Greater Lynchburg Transit Company, and the Wards Road Pedestrian Tunnel.                                                                                                                      | Partially relevant | Partially accurate |
| 3 | What does The Oasis offer for Liberty students, and how much does it cost per bedroom?                                         | The Oasis offers 2 to 6 bedroom options, 12 month leases, by the bed leasing, roommate matching, LU shuttle service, included utilities and services, and rent around $450 to $855 per bedroom depending on floor plan. The system should note that listed prices are not guaranteed.                           | The system listed Oasis amenities like internet, keyed bedrooms, LU shuttle, water, sewer, trash, and roommate matching. It also listed bedroom prices by floor plan and included the $450 to $855 range.                                     | Relevant           | Accurate           |
| 4 | How does The Vue at College Square compare to The Oasis for a student who wants to be close to campus?                         | The answer should compare the two using retrieved listing information. It should mention The Vue being closer to Liberty’s main campus or listed as about 0.7 miles or 5 minutes away, while The Oasis is farther but offers shuttle and student housing features.                                              | The system said The Vue is about 5 minutes from Liberty and that Oasis has a private shuttle, but it said it could not directly compare because the retrieved Oasis context did not include the exact distance.                               | Partially relevant | Partially accurate |
| 5 | What do student discussions say about living at The Oasis as a graduate student or older student?                              | The answer should give a mixed answer. Some student comments say Oasis may be loud, party oriented, or undergrad heavy. Other comments and reviews say it has been good for graduate students and that parties were not an issue.                                                                               | The system gave a mixed answer. It mentioned positive graduate student experiences, comments saying there are many graduate students, and negative comments saying Oasis may be loud, party oriented, or mostly undergraduates.               | Relevant           | Accurate           |

**Retrieval quality:** Relevant / Partially relevant / Off-target
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis
<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->
**Question that failed:**

How does The Vue at College Square compare to The Oasis for a student who wants to be close to campus?

**What the system returned:**

The system said The Vue at College Square is located about 5 minutes from Liberty University and that The Oasis has a private shuttle to campus. It also said it could not directly compare the distance because the retrieved Oasis context did not include the exact distance from campus.

**Root cause tied to a specific pipeline stage:**

This was a retrieval issue. The Oasis distance information was in the documents but the retriever did not include the best Oasis distance chunk in the top 5 results for that question. Because that chunk was missing from the context, the generation step could not make the full comparison.

**What you would change to fix it:**

I would improve retrieval by adding hybrid search with keyword search, especially for words like distance, miles, campus, Vue, and Oasis. I would also consider reranking chunks when a query mentions two specific housing properties so the system is more likely to pull direct comparison information from both sources.

---

## Spec Reflection
<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->
**One way the spec helped you during implementation:**

The spec helped because it made me decide the domain, source documents, chunking strategy, embedding model, top-k value, evaluation questions, and architecture before writing code. This made it easier to prompt Claude Code with specific requirements instead of just asking it to make a generic RAG system.

**One way your implementation diverged from the spec, and why:**

The implementation changed from the original ingestion idea because I first used PDFs for the Reddit threads. The PDF text extraction included unrelated Reddit sidebar content, recommendation posts, and navigation text. I changed the Reddit sources into cleaned '.txt' files so the system would embed useful student discussion content instead of random Reddit page content.

---

## AI Usage
<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

* *What I gave the AI:* I gave Claude Code my planning.md, the local document format, and my chunking strategy.
* *What it produced:* Claude Code produced an ingestion and chunking script that loads local files, extracts metadata, cleans the text, and creates recursive token-aware chunks.
* *What I changed or overrode:* I inspected the sample chunks and found that the Reddit PDFs produced noisy chunks with unrelated Reddit recommendations. I replaced those PDFs with cleaned '.txt' files and reran the ingestion pipeline.

**Instance 2**

* *What I gave the AI:* I gave Claude Code my retrieval approach, architecture diagram, and processed chunks.
* *What it produced:* Claude Code produced ChromaDB indexing and retrieval code using 'sentence-transformers/all-MiniLM-L6-v2' and top-k retrieval.
* *What I changed or overrode:* After testing retrieval, I noticed one query retrieved The Vue before The Oasis for an Oasis specific question. I directed Claude Code to include metadata context like title and source type in the embedded text. Then I rebuilt the index and retested retrieval.

**Instance 3**

* *What I gave the AI:* I gave Claude Code the requirement for grounded generation and a Gradio interface.
* *What it produced:* Claude Code produced the generation flow and web interface.
* *What I changed or overrode:* I tested the interface manually by running the evaluation questions, checking that answers used retrieved sources, and confirming that the source list appeared underneath the answer.
