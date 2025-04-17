"""
harvest_fulltext.py

Extract full texts for CIRED publications from the HALvest dataset on Hugging Face
This script loads the docids from publications.json created by scrape.py
and filters the HALvest dataset to get full texts for these publications

Requirements:
- pip install datasets
- pip install pandas
"""

import json
import logging
import os
from typing import List, Dict, Set

from datasets import load_dataset
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# File paths
PUBLICATIONS_JSON = "publications.json"
OUTPUT_FILE = "cired_fulltext.json"

def load_publication_ids() -> Set[str]:
    """Load the docids from the publications.json file."""
    try:
        logging.info(f"Loading publication IDs from {PUBLICATIONS_JSON}")
        with open(PUBLICATIONS_JSON, 'r', encoding='utf-8') as f:
            publications = json.load(f)
        
        # Extract docids (these might be stored in different ways)
        docids = set()
        for pub in publications:
            # Try different possible id fields
            if 'docid' in pub:
                docids.add(str(pub['docid']))
            elif 'halId_s' in pub:
                docids.add(str(pub['halId_s']))
            elif 'id' in pub:
                docids.add(str(pub['id']))
        
        logging.info(f"Loaded {len(docids)} publication IDs")
        return docids
    
    except FileNotFoundError:
        logging.error(f"Could not find {PUBLICATIONS_JSON}. Run scrape.py first.")
        return set()
    except json.JSONDecodeError:
        logging.error(f"Error parsing {PUBLICATIONS_JSON}. The file may be corrupted.")
        return set()

def get_cired_fulltext(publication_ids: Set[str]) -> pd.DataFrame:
    """
    Load the HALvest dataset and filter for CIRED publications.
    Instead of loading only the English subset, we load the entire dataset
    and filter for CIRED publications based on docids.
    """
    try:
        logging.info("Loading HALvest dataset... this may take some time")
        
        # Load all available subsets (configurations) of the HALvest dataset
        available_configs = load_dataset("almanach/HALvest", split=None)
        logging.info(f"Available configurations: {list(available_configs.keys())}")
        
        # Instead of just loading "en", we'll load all configurations one by one
        # and filter for our publication IDs
        all_results = []
        
        for config_name in available_configs.keys():
            logging.info(f"Loading configuration: {config_name}")
            try:
                ds = load_dataset("almanach/HALvest", config_name)
                
                # Convert to pandas DataFrame for easier filtering
                df = ds["train"].to_pandas()
                
                # Filter for our publication IDs
                filtered_df = df[df['docid'].astype(str).isin(publication_ids)]
                
                if not filtered_df.empty:
                    logging.info(f"Found {len(filtered_df)} matching documents in {config_name} configuration")
                    all_results.append(filtered_df)
                else:
                    logging.info(f"No matching documents found in {config_name} configuration")
                
            except Exception as e:
                logging.error(f"Error loading {config_name}: {str(e)}")
                continue
        
        # Combine all results
        if all_results:
            combined_df = pd.concat(all_results, ignore_index=True)
            logging.info(f"Combined dataset has {len(combined_df)} documents")
            return combined_df
        else:
            logging.warning("No matching documents found in any configuration")
            return pd.DataFrame()
        
    except Exception as e:
        logging.error(f"Error loading HALvest dataset: {str(e)}")
        return pd.DataFrame()

def save_results(df: pd.DataFrame) -> None:
    """Save the filtered dataset to a JSON file."""
    if df.empty:
        logging.warning("No data to save.")
        return
    
    try:
        # Convert to dict records for JSON serialization
        results = df.to_dict(orient='records')
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        
        logging.info(f"Saved {len(results)} documents to {OUTPUT_FILE}")
    except Exception as e:
        logging.error(f"Error saving results: {str(e)}")

def main() -> None:
    """Main function to orchestrate the extraction process."""
    logging.info("Starting CIRED full text extraction")
    
    # Load publication IDs from previous script output
    publication_ids = load_publication_ids()
    if not publication_ids:
        logging.error("No publication IDs found. Exiting.")
        return
    
    # Get full texts for CIRED publications
    df = get_cired_fulltext(publication_ids)
    
    # Save results
    save_results(df)
    
    logging.info("Extraction complete")

if __name__ == "__main__":
    main()
