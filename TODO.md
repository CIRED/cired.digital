# TODO for the RAG CIRED project

## Use GROBID versions instead of the PDF:

Use the dataset filtering function:
```
from datasets import load_dataset
# Load the HALvest dataset
dataset = load_dataset("almanach/HALvest", "en")  # Also load French, Vietnamese...
# Define the set of keys (halid) you want to filter by
keys_to_filter = {"halid1", "halid2", "halid3"}  # Replace with actual CIRED keys from publications.json (only the docs with a fulltext available)
# Filter the dataset based on the halid column
filtered_dataset = dataset.filter(lambda example: example["halid"] in keys_to_filter)
# Print the filtered dataset 
print(filtered_dataset)
```

## Enhancements for the push

- Better logging and journaling the push attempts.
- Separate the skipped, the failed
- Deal with API speed limitations. At some points it is unnecessary to push files because even if accepted, they are not processed.
- Tell R2R to NOT DO THE GRAPH

## Coding ideas

Compare OpenAI Codex CLI  to Aider, windsurf... 

https://github.com/openai/codex

## Deployment bugs

*hatchet engine is stuck on Starting on boot*.
Compose is configured to restart this service on-failure.
but it does not also restart its dependencies.
Solution: stop everything manually before starting.

*r2r container is stuck on stopping*. Solution: restart the whole docker service.

*compose complains that the volumes were created by another project*.
I changed project name in compose from the default "docker" to "myrag".
But there is no command to rename volumes.
Solution: Ignore the WARN messages and use the volumes as they are.

*network not found error on startup*
Solution: ?
