# PaperQA Testing with Makefile

Makefile to automate the setup, testing, and cleanup of [PaperQA](https://github.com/Future-House/paper-qa/tree/main).

## Prerequisites:

 - [uv](https://astral.sh/uv)
 - An OpenAI API key (`OPENAI_API_KEY`)
 - A Mistral API key (`MISTRAL_API_KEY`) (for rate limit testing)

## Installation:

1.  Clone the repository
2.  Set the `OPENAI_API_KEY` environment variable:

    ```
    export OPENAI_API_KEY="Open AI key"
    ```

    For Mistral rate limit testing, also set the `MISTRAL_API_KEY` environment variable:

    ```
    export MISTRAL_API_KEY="Mistral key"
    ```

## Usage:

The `Makefile` provides the following targets:

##setup:
    - Creates a virtual environment using `uv` and installs PaperQA.
    
##install:
    - Installs PaperQA in the virtual environment (requires `setup` to be run first).
    
##Test:
    -  Runs a basic PaperQA test, verifying that the API key is set and that PaperQA can process a dummy PDF.
    
##test_mistral_rate_limit:
    - Tests the handling of Mistral API rate limits. Requires the `MISTRAL_API_KEY` to be set.
    
##clean:
   -  Removes the virtual environment and any test PDFs created.


##Compilation Makefile:

  - 1.Set up the virtual environment and install PaperQA:

    ```
    make setup
    ```

  - 2.Run the basic tests:

    ```
    make test
    ```
  - 3. Run the Mistral rate limit tests:
       ```
        make test_mistral_rate_limit
        ```

  - 4.Clean up the environment:

    ```
    make clean
    ```

## Troubleshooting:

   - OPENAI_API_KEY not set Make sure you have set the `OPENAI_API_KEY` environment variable before running `make test`.
   - Mistral API Rate Limit If you encounter rate limit errors, ensure that your Mistral API key is valid and that your account has sufficient credits.

## Notes:

 - The `test` target creates a dummy PDF file in the `pdfs` directory.
 - The tests rely on `grep` to check the output of `pqa ask`.  If the output format of PaperQA changes, the tests may need to be updated.
 -The default location for the PaperQA index is `~/.pqa`.

