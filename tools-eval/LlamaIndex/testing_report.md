# Testing report LlamaIndex

HDM, 2025-04-23

We make a pdfs/ directory with two articles.
```bash
mkdir pdfs/
cp ../../data/raw/hal/pdfs/hal_00119451.pdf pdfs/
cp ../../data/raw/hal/pdfs/halshs_00619168.pdf pdfs/
```

Installation.
```bash
uv venv venv
source venv/bin/activate
uv pip install llama-index llama-index-vector-stores-chroma chromadb.
```

Indexing.
```bash
mkdir index
python3 build_index.py
```

It seems to use my $OPENAI_API_KEY correctly out of the box.

The indexing fails with OpenAI error 429 RateLimit 'You exceeded your current quota'.

I create an API key on Mistral's website
```bash
pip install llama-index llama-index-llms-mistralai llama-index-embeddings-mistralai
```

I vibecode ```build_index_mistral.py```
It fails with RateLimitmistralai.models.sdkerror.SDKError: API error occurred: Status 429 {"message":"Requests rate limit exceeded"}

I prepay €10 into my Mistral account. Same error.
I upgrade my plan to Scale. Same error.