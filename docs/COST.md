# Cost Considerations

One goal of this project is to be **cheap to run and cheap to demo**. This page summarizes where costs come from and how to keep them near zero.

> **Prices change.** The figures below are rough guidance, not authoritative quotes. Always check current pricing on the official Google Cloud and Google AI pricing pages before deploying. Set a **budget alert** in GCP Billing.

---

## Local development — free

Running everything on your own machine costs nothing:

- **Local embeddings** (sentence-transformers or the hashing backend) run on your CPU — no API charges.
- Set **`LLM_PROVIDER=mock`** to avoid any AI calls entirely.
- The whole app, including Chroma, runs locally.

The only "cost" is the one-time download of the `all-MiniLM-L6-v2` model if you use the semantic backend.

---

## Gemini API

| Item | Notes |
| --- | --- |
| **`gemini-3.5-flash-lite` free tier** | Google AI Studio offers a **generous free tier** for this flash-lite model — often enough for a personal demo. **Check current limits and pricing at [ai.google.dev](https://ai.google.dev).** |
| **Paid usage** | Beyond the free tier, Gemini is billed per input/output token. `gemini-3.5-flash-lite` is one of the cheaper, fast models. |
| **How to minimize** | Use `mock` in tests/CI; keep `MAX_CONTEXT_CHARS` and `LLM_MAX_OUTPUT_TOKENS` reasonable; cache/avoid redundant calls. |

---

## Google Cloud (if you deploy)

| Resource | Cost driver | Rough cost for a demo |
| --- | --- | --- |
| **Cloud Run** | CPU/memory per request; **scales to zero** when idle | **~$0** when idle (with `min_instances = 0`); pennies under light traffic. Free tier covers meaningful request volume. |
| **Artifact Registry** | Image storage (GB-month) | Pennies for a couple of small images |
| **Secret Manager** | Active secret versions + access ops | Tiny — a few secrets is negligible |
| **GCS bucket (Chroma)** | Storage + operations + gcsfuse access | **Pennies/month** for a small knowledge base |
| **Network egress** | Data served out of GCP | Small for a demo; watch if traffic grows |
| **Gemini API** | Tokens (billed to your AI key) | Free tier for light use (see above) |

### Rough total

> A demo that is **scaled to zero** and lightly used should cost roughly **$0 to a few dollars per month**.

---

## How to keep it near zero

- **`min_instances = 0`** — never pay for idle Cloud Run instances.
- **Set a budget alert** in GCP Billing so you're warned before any surprise.
- **Use `mock`/hashing in CI** — no AI spend in automated runs.
- **`terraform destroy`** when you're done demoing — this removes the paid resources. (See [DEPLOYMENT.md](DEPLOYMENT.md).)
- **Right-size** `max_instances`, memory, and timeouts.
- **Monitor** the Cloud Run and Billing dashboards after deploying.

---

## Honest caveats

- "Scale to zero" means the **first request after idle is slower** (cold start) — a cost/latency tradeoff, not a hidden charge.
- The **free tiers and prices quoted by Google change over time** — treat everything here as directional and verify on the official pages.
- If you move to a **managed vector database** for scale (recommended for real use — see [DEPLOYMENT.md](DEPLOYMENT.md)), that becomes a new, non-trivial line item.

---

## Related docs

- [DEPLOYMENT.md](DEPLOYMENT.md) — `min_instances`, budget alerts, and teardown
- [CONFIGURATION.md](CONFIGURATION.md) — token/context settings that affect AI cost
