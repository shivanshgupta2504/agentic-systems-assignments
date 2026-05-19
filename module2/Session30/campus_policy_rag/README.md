# Campus Policy RAG

This is a small Retrieval-Augmented Generation (RAG) project designed to answer questions about university campus policies using a set of PDF documents.

## Overview

The script `campus_policy_rag.py` performs the following steps:
1. **Pre-processing Phase**: 
   - Loads campus policy PDFs from the `policy_pdfs` directory.
   - Extracts and cleans text from the pages.
   - Chunks the text.
   - Generates embeddings using OpenAI's `text-embedding-3-small` model.
   - Stores the text and embeddings in a local ChromaDB collection named `campus_policies`.
2. **Runtime Phase**: 
   - Takes a user query (like "What are the rules for the hostel?").
   - Generates an embedding for the query.
   - Retrieves the top matching chunks from ChromaDB.
   - Constructs a prompt with the context and asks OpenAI's `gpt-4o` model to answer the query.

## Setup

1. Ensure you have the required Python dependencies installed (e.g., `openai`, `pypdf`, `chromadb`, `python-dotenv`).
2. Add your `.env` file with your `OPENAI_API_KEY`.
3. Make sure the PDF documents you want to index are placed in the `policy_pdfs` folder.

## Usage

To run the pipeline and answer the test queries, simply execute:

```bash
python campus_policy_rag.py
```
