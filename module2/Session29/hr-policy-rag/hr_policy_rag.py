import os
import chromadb
from uuid import uuid4
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

FILES = os.listdir(r".\documents")
LLM_MODEL = "gpt-4o"
EMBEDDING_MODEL = "text-embedding-3-small"

# =====================================================================
# CHUNKING
# =====================================================================
def chunk_text(file, chunk_size: int, chunk_overlap: int = 30):
    chunks = []
    file_path = os.path.join("documents", file)
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        words = text.split(" ")
        start = 0

        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))
            start += chunk_size - chunk_overlap
    
    return chunks

def create_documents(file, chunk_size: int, chunk_overlap: int = 30):
    chunks = chunk_text(file, chunk_size, chunk_overlap)
    all_documents = []
    file_path = os.path.join("documents", file)
    for i, chunk in enumerate(chunks):
        id = uuid4()
        metadata = {
            "category": file.split(".")[0],
            "source": file_path
        }
        all_documents.append({
            "id": str(id),
            "text": chunk,
            "metadata": metadata,
            "chunk_index": i,
        })

    return all_documents

response = client.embeddings.create(
    input="Your text string goes here",
    model=EMBEDDING_MODEL,
)

def create_embeddings(texts):
    """
    Converts a list of text strings into embedding vectors using OpenAI.
    Returns a list of embedding vectors (one per text input).
    """
    response = client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL
    )

    # Extract just the embedding vectors from the API response
    embeddings = [item.embedding for item in response.data]

    return embeddings

def setup_vector_db(db_path="./chroma_hr_policy_db", collection_name="hr_policy_collection"):
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

def index_hr_documents(chunks, collection):
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

def build_knowledge_base(collection, chunk_size=120, overlap=30):
    """
    Runs the entire pre-processing pipeline:
    1. Load documents from the folder
    2. Create chunks with overlap
    3. Generate embeddings
    4. Store everything in the vector database
    
    Call this function ONCE to prepare your system before handling user queries.
    """
    print("=== Building Knowledge Base ===")
    
    for file in FILES:
        # Step 1: Split documents into overlapping chunks
        chunks = create_documents(file, chunk_size, overlap)
    
        # Steps 2: Generate embeddings and store in vector DB
        index_hr_documents(chunks, collection)
    
    print("=== Knowledge Base Ready ===\n")

def retrieve_hr_content(query, collection, top_k=3):
    """
    Given a user query, finds the most relevant chunks from the database.
    
    top_k = 3 means: return the 3 most similar chunks to the query
    policy_filter = optional filter, e.g., only search refund-related chunks
    """
    # Step 1: Convert the user query into an embedding vector
    query_embedding = create_embeddings([query])[0]  # embed only one text (the query)
    
    # Step 2: Perform similarity search in the vector database
    results = collection.query(
        query_embeddings=[query_embedding],  # the query's vector
        n_results=top_k,                     # how many top results to return
    )
    
    # Step 3: Package the results into a clean list of retrieved chunks
    retrieved = []
    if results["documents"] and results["documents"][0]:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            retrieved.append({
                "text": doc,        # the chunk text
                "metadata": meta    # the chunk's metadata
            })
    
    return retrieved  # return the top-k most relevant chunks

def build_grounded_prompt(query, retrieved_chunks):
    """
    Combines retrieved policy chunks and the user's query into a structured prompt.
    The LLM will use this prompt to generate a helpful, grounded answer.
    """
    # Combine all retrieved chunk texts into one context block
    context = "\n\n".join([chunk["text"] for chunk in retrieved_chunks])
    
    # Build the full prompt with system instructions + context + user question
    prompt = f"""You are a helpful HR Policy Assistant for a Startup named InnoTech Solutions.
    
Answer the employee's question using ONLY the policy information provided below.
Do NOT make up any details. If the answer is not in the context, say: "I don't have that information."
Keep your answer simple, clear, and employer-friendly.

--- POLICY CONTEXT ---
{context}
--- END OF CONTEXT ---

Customer Question: {query}

Answer:
"""
    
    return prompt  # return the complete prompt string

def generate_answer(query, retrieved_chunks):
    """
    Sends the constructed prompt to the LLM and returns the final answer.
    This is the Generator component of RAG.
    """
    # Build the prompt by combining context and query
    prompt = build_grounded_prompt(query, retrieved_chunks)
    
    # Call the LLM (GPT-4o) with the constructed prompt
    response = client.chat.completions.create(
        model=LLM_MODEL,  # use the configured LLM model
        messages=[
            {
                "role": "system",
                "content": "You are a helpful HR Policy Assistant."
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

def answer_with_rag(query, collection, top_k=3):
    """
    The main function that handles end-to-end question answering.
    1. Retrieve relevant chunks for the query
    2. Generate a polished answer using the LLM
    """
    print(f"\nUser Query: {query}")
    print("-" * 50)
    
    # Step 1: Retrieve the most relevant policy chunks
    retrieved = retrieve_hr_content(query, collection, top_k=top_k)
    
    if not retrieved:
        return "I'm sorry, I couldn't find relevant information to answer your question."
    
    print(f"Retrieved {len(retrieved)} relevant chunks.")
    
    # Step 2: Generate the final answer using the LLM
    answer = generate_answer(query, retrieved)
    
    return answer  # return the final customer-friendly answer

if __name__ == "__main__":
    
    # ----- PRE-PROCESSING PHASE (run once) -----
    collection = setup_vector_db()  # set up ChromaDB

    build_knowledge_base(collection)  # load, chunk, embed, store
    
    # ----- RUNTIME PHASE (for every user query) -----
    test_queries = [
        "How many days of annual leave am I entitled to per year?",
        "Do I need manager approval before working from home?",
        "When is the appraisal cycle conducted and how is the increment decided?",
    ]
    
    for query in test_queries:
        answer = answer_with_rag(query, collection)
        print(f"\nAnswer: {answer}")
        print("=" * 60)

