Source: https://www.pcso.gov.ph/SearchLottoResult.aspx (official PCSO "Search Lotto Draw Result by Date", default GET view)
Fetch path: searxng MCP web_url_read via the homelab LiteLLM gateway (https://litellm.lab.znp.pw/mcp/searxng), URL with a no-op query string (?r=20260926) to bypass the gateway cache; the page's "Today's National Draw" block read "Sat, September 26, 2026 9:00 pm" (current view); direct urllib/curl returns HTTP 403.
Fetched: 2026-09-26 PHT (+0800). Format: markdown conversion by the reader (raw HTML not available through this path).
Rows below are the 6/N rows copied verbatim from the returned table (3D/2D/4D/6D rows omitted).

| LOTTO GAME       | COMBINATIONS      | DRAW DATE | JACKPOT (PHP)  | WINNERS |
| ---------------- | ----------------- | --------- | -------------- | ------- |
| Ultra Lotto 6/58 | 41-29-43-16-54-27 | 9/25/2026 | 330,176,341.88 | 0       |
| Megalotto 6/45   | 37-33-38-14-45-32 | 9/25/2026 | 75,233,668.75  | 0       |
| Superlotto 6/49  | 30-39-34-17-47-11 | 9/24/2026 | 25,396,508.95  | 0       |
| Lotto 6/42       | 01-36-07-23-15-03 | 9/24/2026 | 58,291,713.31  | 0       |
| Grand Lotto 6/55 | 29-47-22-32-50-46 | 9/23/2026 | 219,836,261.65 | 0       |
| Megalotto 6/45   | 44-05-04-40-45-07 | 9/23/2026 | 71,193,623.60  | 0       |
