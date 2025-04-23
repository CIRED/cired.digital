# Testing report [PaperQA2](https://github.com/Future-House/paper-qa/tree/main)

HDM, 2025-04-23

Installation was very easy.
```bash
uv venv venv
source venv/bin/activate
uv pip install paper-qa
```

We make a pdfs/ directory with two articles.
```bash
ls pdfs/
cirad_03043734.pdf  cirad_04094506.pdf
```

CLI interface is straightforward:
```bash
cd pdfs
pqa ask 'How to reduce hunger?'
```

It seems to use my $OPENAI_API_KEY correctly out of the box.

It stores index and dialog history in ~/.pqa.

The indexing fails with OpenAI error 429 RateLimit 'You exceeded your current quota'.

I retry with ```pqa --settings 'tier1_limits' ask 'How to reduce hunger?'```
The tool proceeds to the "Generating answer" step but again fails with the litellm.RateLimitError.

I retry with ```pqa --summary_llm_config '{"rate_limit": {"gpt-4o-2024-11-20": "30000 per 1 minute"}}' ask 'How to solve hunger?'```
Same failure.

