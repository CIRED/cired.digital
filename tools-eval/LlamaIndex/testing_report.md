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

Une heure après.
```
python3 build_index_mistral.py
📚 Building index from scratch...
Indexing PDFs: 100%|██████████████████████████████████████████████████████████████████████████████████████████████| 2/2 [00:00<00:00,  2.42file/s]
✅ Index ready. Launching chat...
💬 Chat with your PDFs (type 'exit' to quit):
> 2+2 ? 
I'm unable to provide an answer to that query based on the information available.
> Faut il un revenu d'existence en France, pour qui, combien?
L'idée d'un revenu d'existence, souvent appelé allocation universelle (AU), a été proposée sous différentes formes et par divers auteurs. Voici quelques points clés à considérer :

1. **Pour qui ?** : L'allocation universelle serait destinée à tous les individus, indépendamment de leur situation professionnelle ou de leur niveau de revenu. Cela inclut les chômeurs, les travailleurs à temps partiel, les artistes, les éducateurs, et ceux impliqués dans des activités sociales ou culturelles.

2. **Combien ?** : Le montant exact de l'allocation universelle n'est pas précisé dans les discussions théoriques. Cependant, l'idée est qu'elle devrait être suffisante pour couvrir les besoins de base, permettant ainsi aux individus de choisir entre travail et loisir sans craindre de tomber dans la pauvreté.

3. **Justifications** : Plusieurs arguments plaident en faveur de l'AU. Par exemple, elle pourrait rendre viables des activités d'utilité sociale qui ne sont pas suffisamment rentables pour financer un salaire substantiel. Elle pourrait également réduire la stigmatisation des chômeurs en reconnaissant la légitimité de choix de vie alternatifs.

4. **Critiques et Débats** : Il existe des débats sur la faisabilité et la pertinence de l'AU. Certains estiment qu'une aide plus directe aux activités sociales et culturelles serait moins coûteuse. D'autres s'interrogent sur la compatibilité de l'AU avec les principes de réciprocité et de contribution à la société.

En résumé, l'allocation universelle est une proposition complexe avec des implications économiques et sociales importantes. Elle vise à offrir une sécurité financière de base à tous, mais sa mise en œuvre nécessiterait une réflexion approfondie sur ses modalités et ses impacts.
```

