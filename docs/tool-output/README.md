# Tool output that works in Intric

What Intric does with a tool's return value, and how to shape it.

## Return one dict

Intric reads a tool's structured result when there is one, and its text content otherwise. Return a `dict` from a tool: the client receives it as structured content, and Intric can read fields from it, such as `knowledge_sources`. A string is never parsed, even when it holds JSON. Neither is a list: FastMCP wraps it as `{"result": [...]}`, so a `knowledge_sources` inside never reaches the top level.

## Citations: `knowledge_sources`

Add a `knowledge_sources` list to the dict, and Intric shows each entry as a citation the user can open. Example: `define_temperature_unit` and `make_knowledge_source` in `tools.py`.

| Field | Required | What Intric does with it |
|---|---|---|
| `title` | yes | An entry without a title is dropped. |
| `url` | no | The link the citation opens. |
| `text` | no | An excerpt stored with the citation. The model does not see it. |
| `source_type` | no | `"url"` (the default when the key is missing) or `"pdf"`. Any other value, `null` included, drops the entry. |
| `id` | no | Leave it out and Intric assigns one. If you set it, it must be a UUID, or the entry is dropped. |

Intric removes `knowledge_sources` before the model sees the result. In its place it adds `sources`: a list of `source_id`, `title` and `url` per entry. The model is told to cite those ids. So:

- Put every fact the model needs in the rest of the dict. The model does not see `text`.
- Do not use a key named `sources` yourself. Intric replaces it whenever at least one entry is valid.
- A dropped entry does not fail the call. The tool still succeeds, with fewer citations. `tests/test_smoke.py` checks the entries of every tool listed in `CITING_TOOLS`.

## Size

When a result is too large for the model's context, the model first sees only the top of it. Intric writes the dict as indented JSON with the keys sorted alphabetically, shows the first lines, and adds a note that the rest is withheld. The model can read further in a later step, but every step costs time and context, and it may answer from the first part. Which fields fall below the cut depends on their names, not on their order in your code, and the `sources` list Intric adds can be one of them.

Do not rely on that cut. Return a focused result: filter on the server, cap the number of items, and shorten long text fields. When you cap a list, say so in the result with honest counts, for example `"total": 240, "returned": 20, "truncated": true`, so the model knows to narrow its query instead of treating 20 items as everything.

## Time

Intric waits up to 120 seconds for a tool call. A slower call fails, and the model gets a protocol error instead of your message. If the upstream system can be slow, set a shorter timeout on your HTTP client and return `{"error": ...}` with a message the model can act on.

## Placeholders

When a value is missing upstream and you fill in a fallback, make the fallback read as one: `"unknown"` or `null`, not a value that looks real. The model repeats what it gets.

## Images

To show an image in the chat, return the URL of a PNG or JPEG that Intric can fetch, as markdown: `![Route map](https://example.com/maps/123.png)`. In Intric's chat, inline SVG, HTML, and an MCP image content block holding an SVG did not render as pictures. Check it by running the tool in a real Intric chat: a test cannot see what the chat shows.
