# HR Policy RAG System

This project implements a Retrieval-Augmented Generation (RAG) system using Python to answer questions based on HR policies.

## Overview

The system uses `chromadb` to store and search vector embeddings of document chunks, and relies on OpenAI's models (`text-embedding-3-small` for embeddings and `gpt-4o` for generating responses). It allows employees of a fictional startup, InnoTech Solutions, to query HR policies dynamically and get accurate, grounded answers.

## Prerequisites

To run this script, ensure you have the required dependencies installed. Typical dependencies include:

```bash
pip install openai chromadb python-dotenv
```

You must also have an OpenAI API key. Create a `.env` file in the project's root directory and add your key:

```env
OPENAI_API_KEY=your_api_key_here
```

**Note:** You also need to have text files in a folder named `documents` (relative to the script location) containing your HR policy text.

## Structure & Pipeline

The RAG pipeline operates in two main phases:

### 1. Pre-Processing Phase (Building Knowledge Base)
- **Document Loading & Chunking:** Reads text documents from the `.\documents` folder, splitting them into overlapping chunks (default chunk size: 120 words, overlap: 30 words).
- **Embedding Generation:** Uses OpenAI's `text-embedding-3-small` model to turn text chunks into embedding vectors.
- **Vector Storage:** Stores chunk text, metadata (like category and file source), and embeddings into a persistent ChromaDB instance (`./chroma_hr_policy_db`).

### 2. Runtime Phase (Query Answering)
- **Context Retrieval:** Takes a user query, generates its embedding, and performs a similarity search in ChromaDB to fetch the top 3 most relevant policy chunks.
- **Answer Generation:** Combines the retrieved context with the user query to build a strict prompt. It instructs `gpt-4o` to act as an HR Policy Assistant and formulate an answer using *only* the provided context.

## Usage

You can execute the system by running the script directly:

```bash
python hr_policy_rag.py
```

Upon execution, the script will:
1. Parse the documents and build the knowledge base in ChromaDB.
2. Run a set of test queries against the indexed HR policies.
3. Print the retrieved answers to the console.
