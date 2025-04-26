# TODO for data preparation

## Get the already extracted text versions from Halvest where available

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

## Split the oversized (>30MB) PDF documents

May be not necessary if we get textual versions from Halvest

## Deal with the special failure cases

May be not necessary if we get textual versions from Halvest

## Chunk smarter

Not priority. It's a nice-to-have, not a must-have.