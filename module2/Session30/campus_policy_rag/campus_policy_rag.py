import os
import re
import random
from openai import OpenAI
from pypdf import PdfReader
import chromadb
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

LLM_MODEL = "gpt-4o"
EMBEDDING_MODEL = "text-embedding-3-small"

def infer_policy_type(filename):
    """
    Figures out the type of policy from the file name.
    For example: 'refund_policy.pdf' → 'refund'
    """
    name = filename.lower()
    
    if "withdrawal" in name:
        return "withdrawal"
    elif "refund" in name:
        return "refund"
    elif "hostel" in name:
        return "hostel"
    elif "library" in name:
        return "library"
    else:
        return "general"

def clean_text(raw_text):
    """
    Cleans raw text extracted from a PDF by removing noise.
    - Replaces newline characters with spaces
    - Removes extra/multiple spaces
    """
    # Step 1: Replace all newline characters (\n) with a single space
    text = raw_text.replace("\n", " ")
    
    # Step 2: Use regex to replace multiple consecutive spaces with one space
    text = re.sub(r'\s+', ' ', text)
    
    # Step 3: Strip leading and trailing whitespace
    text = text.strip()
    
    return text  # return the cleaned, single-line text

def make_document(text, metadata):
    """
    Creates a standard document dictionary for every page.
    Having a consistent structure makes it easy to handle thousands of documents.
    """
    return {
        "text": text,          # the actual cleaned text of this page
        "metadata": metadata   # extra info like file path, page number, policy type
    }

def load_pdf_file(file_path):
    """
    Loads a single PDF file and returns a list of documents (one per page).
    Each document contains the page's text and metadata.
    """
    documents = []          # empty list to collect all page documents
    policy_type = infer_policy_type(os.path.basename(file_path))  # get policy type from filename
    
    # Open and read the PDF file using PdfReader
    reader = PdfReader(file_path)
    
    # Iterate through every page of the PDF (enumerate gives index + value)
    for page_num, page in enumerate(reader.pages, start=1):
        
        raw_text = page.extract_text()  # extract raw text from this page
        
        if not raw_text:
            continue  # skip empty pages (some PDFs have blank pages)
        
        clean = clean_text(raw_text)  # remove noise from the extracted text
        
        if clean:  # only add the document if there is actual content
            metadata = {
                "source": file_path,         # full path of the source PDF file
                "page": page_num,            # page number within the PDF
                "policy_type": policy_type   # type of policy (refund/return/shipping)
            }
            documents.append(make_document(clean, metadata))  # add to list
    
    return documents  # return all page-documents from this PDF

def load_all_documents(folder_path):
    """
    Loads ALL PDF files from a given folder automatically.
    You just point it to a folder — it finds every PDF and loads all pages.
    No need to call load_pdf_file manually for each file.
    """
    all_documents = []  # master list to collect documents from all PDFs
    
    # Walk through every file in the given folder
    for filename in os.listdir(folder_path):
        
        if filename.endswith(".pdf"):  # only process PDF files, ignore others
            
            file_path = os.path.join(folder_path, filename)  # build full path
            docs = load_pdf_file(file_path)                  # load that PDF
            all_documents.extend(docs)  # add all pages from this PDF to master list
            print(f"Loaded {len(docs)} pages from: {filename}")
    
    print(f"\nTotal documents loaded: {len(all_documents)}")
    return all_documents  # return all documents from all PDFs in the folder

def chunk_text(text, chunk_size=120, overlap=30):
    """
    Splits a single piece of text into overlapping word-based chunks.
    
    chunk_size = 120 → each chunk has up to 120 words
    overlap = 30    → each new chunk starts 30 words before the previous chunk ended
    
    Example with chunk_size=120, overlap=30:
    - Chunk 1: words 1 to 120
    - Chunk 2: words 91 to 210  (starts at 120 - 30 = 90, i.e. index 90)
    - Chunk 3: words 181 to 300 (starts at 210 - 30 = 180, i.e. index 180)
    """
    words = text.split()  # split the text into individual words using spaces
    chunks = []           # list to store all created chunks
    
    start = 0  # pointer for the starting position of the current chunk
    
    # Keep creating chunks until we reach the end of the word list
    while start < len(words):
        end = start + chunk_size  # calculate where this chunk should end
        
        # Slice the words list to get only this chunk's words
        chunk_words = words[start:end]
        
        # Join the words back into a string with spaces
        chunk = " ".join(chunk_words)
        
        chunks.append(chunk)  # add this chunk to our list
        
        # Move the start pointer forward, but go back by 'overlap' words
        # This ensures the next chunk starts slightly before this one ended
        start += chunk_size - overlap
    
    return chunks  # return all chunks created from this text


def create_chunks(documents, chunk_size=120, overlap=30):
    """
    Creates chunks for ALL documents in the pipeline.
    For each document (page), it calls chunk_text to split that page into chunks.
    Each chunk also carries the original document's metadata.
    """
    all_chunks = []  # master list to hold every chunk from every document
    
    for doc in documents:  # go through each document (page)
        
        text_chunks = chunk_text(doc["text"], chunk_size, overlap)  # split text into chunks
        
        for i, chunk_text_content in enumerate(text_chunks):  # go through each chunk
            
            chunk_id = str(uuid4())  # generate a random unique ID for this chunk
            
            all_chunks.append({
                "id": chunk_id,                       # unique identifier for this chunk
                "text": chunk_text_content,           # the actual text of this chunk
                "metadata": doc["metadata"],          # carry forward the original document's metadata
                "chunk_index": i                      # which chunk number this is within the document
            })
    
    print(f"Total chunks created: {len(all_chunks)}")
    return all_chunks  # return all chunks ready for embedding

def create_embeddings(texts):
    """
    Converts a list of text strings into embedding vectors using OpenAI.
    Returns a list of embedding vectors (one per text input).
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,  # use the text-embedding-3-small model
        input=texts             # pass the list of texts to embed
    )
    
    # Extract just the embedding vectors from the API response
    embeddings = [item.embedding for item in response.data]
    
    return embeddings  # return list of vectors


def setup_vector_db(db_path="./chroma_db", collection_name="campus_policies"):
    """
    Sets up a persistent ChromaDB client and creates (or opens) a collection.
    'Persistent' means the data is saved to disk — it survives program restarts.
    """
    # Create a persistent ChromaDB client at the given path
    chroma_client = chromadb.PersistentClient(path=db_path)
    
    # Get or create a collection with the given name
    # If the collection already exists, it opens it; if not, it creates it
    collection = chroma_client.get_or_create_collection(name=collection_name)
    
    print(f"Vector DB ready. Collection: '{collection_name}'")
    return collection  # return the collection object


def index_chunks(chunks, collection):
    """
    Generates embeddings for all chunks and stores them in the vector database.
    This is the step where your knowledge base actually gets built.
    """
    # Extract just the text from each chunk to send to the embedding model
    texts = [chunk["text"] for chunk in chunks]
    
    print("Generating embeddings for all chunks...")
    embeddings = create_embeddings(texts)  # convert all chunk texts to vectors
    
    # Extract IDs, texts, metadatas, and embeddings in parallel lists
    ids = [chunk["id"] for chunk in chunks]                # list of all chunk IDs
    metadatas = [chunk["metadata"] for chunk in chunks]    # list of all metadata dicts
    
    # Store everything in ChromaDB in one batch operation
    # upsert = insert if new, update if ID already exists
    collection.upsert(
        ids=ids,              # unique IDs for each entry
        documents=texts,      # the actual text of each chunk
        embeddings=embeddings, # the vector representation of each chunk
        metadatas=metadatas   # the metadata (policy type, page, source file)
    )
    
    print(f"Successfully stored {len(chunks)} chunks in vector database.")

def build_knowledge_base(folder_path, collection, chunk_size=120, overlap=30):
    """
    Runs the entire pre-processing pipeline:
    1. Load all PDF documents from the folder
    2. Clean the text
    3. Create chunks with overlap
    4. Generate embeddings
    5. Store everything in the vector database
    
    Call this function ONCE to prepare your system before handling user queries.
    """
    print("=== Building Knowledge Base ===")
    print(f"Loading documents from: {folder_path}")
    
    # Step 1 & 2: Load and clean all documents
    documents = load_all_documents(folder_path)
    
    # Step 3: Split documents into overlapping chunks
    chunks = create_chunks(documents, chunk_size, overlap)
    
    # Steps 4 & 5: Generate embeddings and store in vector DB
    index_chunks(chunks, collection)
    
    print("=== Knowledge Base Ready ===\n")

def retrieve_chunks(query, collection, top_k=3, policy_filter=None):
    """
    Given a user query, finds the most relevant chunks from the database.
    
    top_k = 3 means: return the 3 most similar chunks to the query
    policy_filter = optional filter, e.g., only search refund-related chunks
    """
    # Step 1: Convert the user query into an embedding vector
    query_embedding = create_embeddings([query])[0]  # embed only one text (the query)
    
    # Step 2: Build optional filter for metadata (e.g., only refund policy chunks)
    where_filter = None
    if policy_filter:
        where_filter = {"policy_type": {"$eq": policy_filter}}  # ChromaDB filter syntax
    
    # Step 3: Perform similarity search in the vector database
    results = collection.query(
        query_embeddings=[query_embedding],  # the query's vector
        n_results=top_k,                     # how many top results to return
        where=where_filter                   # optional metadata filter
    )
    
    # Step 4: Package the results into a clean list of retrieved chunks
    retrieved = []
    if results["documents"] and results["documents"][0]:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            retrieved.append({
                "text": doc,        # the chunk text
                "metadata": meta    # the chunk's metadata
            })
    
    return retrieved  # return the top-k most relevant chunks

def build_prompt(query, retrieved_chunks):
    """
    Combines retrieved policy chunks and the user's query into a structured prompt.
    The LLM will use this prompt to generate a helpful, grounded answer.
    """
    # Combine all retrieved chunk texts into one context block
    context = "\n\n".join([chunk["text"] for chunk in retrieved_chunks])
    
    # Build the full prompt with system instructions + context + user question
    prompt = f"""You are a helpful assistant for a university campus.
    
Answer the student's or staff's question using ONLY the campus policy information provided below.
Do NOT make up any details. If the answer is not in the context, say: "I don't have that information."
Keep your answer simple, clear, and helpful.

--- POLICY CONTEXT ---
{context}
--- END OF CONTEXT ---

Question: {query}

Answer:"""
    
    return prompt  # return the complete prompt string


def generate_answer(query, retrieved_chunks):
    """
    Sends the constructed prompt to the LLM and returns the final answer.
    This is the Generator component of RAG.
    """
    # Build the prompt by combining context and query
    prompt = build_prompt(query, retrieved_chunks)
    
    # Call the LLM (GPT-4o) with the constructed prompt
    response = client.chat.completions.create(
        model=LLM_MODEL,  # use the configured LLM model
        messages=[
            {
                "role": "system",
                "content": "You are a helpful university campus assistant."
            },
            {
                "role": "user",
                "content": prompt  # pass the full prompt (context + query)
            }
        ],
        temperature=0.2  # low temperature = more factual, less creative answers
    )
    
    # Extract and return just the text of the answer
    return response.choices[0].message.content


def answer_question(query, collection, top_k=3):
    """
    The main function that handles end-to-end question answering.
    1. Retrieve relevant chunks for the query
    2. Generate a polished answer using the LLM
    """
    print(f"\nUser Query: {query}")
    print("-" * 50)
    
    # Step 1: Retrieve the most relevant policy chunks
    retrieved = retrieve_chunks(query, collection, top_k=top_k)
    
    if not retrieved:
        return "I'm sorry, I couldn't find relevant information to answer your question."
    
    print(f"Retrieved {len(retrieved)} relevant chunks.")
    
    # Step 2: Generate the final answer using the LLM
    answer = generate_answer(query, retrieved)
    
    return answer  # return the final customer-friendly answer


# =====================================================================
# MAIN: Run the full pipeline
# =====================================================================

if __name__ == "__main__":
    
    # ----- PRE-PROCESSING PHASE (run once) -----
    collection = setup_vector_db()  # set up ChromaDB
    
    POLICY_FOLDER = "./policy_pdfs"  # path to your folder of PDF files
    build_knowledge_base(POLICY_FOLDER, collection)  # load, chunk, embed, store
    
    # ----- RUNTIME PHASE (for every user query) -----
    test_queries = [
        "Can I get a refund after dropping a course?",
        "What is the deadline for returning a library book?",
        "Are hostel visitors allowed on weekends?"
    ]
    
    for query in test_queries:
        answer = answer_question(query, collection)
        print(f"\nAnswer: {answer}")
        print("=" * 60)
