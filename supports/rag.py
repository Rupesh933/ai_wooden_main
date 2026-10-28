import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

import os
from pypdf import PdfReader
from django.conf import settings

BASE_DIR = getattr(settings, "BASE_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# initialize chromadb client
chroma_path = os.path.join(BASE_DIR, "chroma_db")
client = chromadb.PersistentClient(path=str(chroma_path))

embedding_fn = DefaultEmbeddingFunction()

# get_or_create_collection - just like table in mysql db
collection = client.get_or_create_collection(
    name="timbernest_docs",
    embedding_function=embedding_fn
)

# chunking function, actually our goal is to load document in chroma DB
def chunk_text(text, chunk_size=500):
    # chunks = [] --> I will learn Python --> [I will learn Python]
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0

    for word in words:
        current_chunk.append(word)
        current_size += len(word) + 1 # here 1 mean space

        if current_size >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_size = 0

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# this function is responsible for loading PDF files and storing their chunks.
def load_documents():
    docs_path = os.path.join(BASE_DIR, "supports", "documents")
    documents = []  # holding all our text chunks
    ids = [] # holding unique identifier

    if not os.path.exists(docs_path):
        print(f"Directory not found: {docs_path}")
        return

    for filename in os.listdir(docs_path):
        if filename.endswith(".pdf"):
            filepath = os.path.join(docs_path, filename)
            reader = PdfReader(filepath)

            raw_text = ""
            for page in reader.pages:
                raw_text += page.extract_text() or ""

            chunks = chunk_text(raw_text, chunk_size=500)

            for i, chunk in enumerate(chunks):
                # 0 chunk1
                # 1 chunk2
                # filename_{i} ==> refund_policy.pdf_0

                documents.append(chunk)
                ids.append(f"{filename}_{i}")

    if documents:
        collection.upsert(documents=documents, ids=ids)

    print(f"loaded {len(documents)} chunks into chromaDB")