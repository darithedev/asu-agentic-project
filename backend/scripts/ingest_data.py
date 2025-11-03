"""
Data ingestion pipeline for Travel Agency Customer Service AI.

This script loads documents from mock data directories, chunks them appropriately,
generates embeddings, and stores them in ChromaDB with metadata for filtering.
"""

import argparse
import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DocumentIngester:
    """Handles document ingestion into ChromaDB."""

    def __init__(self, db_path: str, collection_name: str):
        """
        Initialize the document ingester.

        Args:
            db_path: Path to ChromaDB persistent storage
            collection_name: Name of the ChromaDB collection
        """
        # Validate OpenAI API key is set
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )
        
        self.db_path = Path(db_path)
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Using existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Travel Agency Knowledge Base"}
            )
            logger.info(f"Created new collection: {collection_name}")

    def parse_metadata(self, content: str) -> Tuple[Dict[str, str], str]:
        """
        Parse metadata markers from document content.

        Args:
            content: Document content with metadata markers

        Returns:
            Tuple of (metadata dictionary, cleaned content string)
        """
        metadata = {}
        # Look for metadata markers like #agent_type: value
        pattern = r"#(\w+):\s*(.+)"
        matches = re.findall(pattern, content)
        
        for key, value in matches:
            metadata[key] = value.strip()
        
        # Remove metadata markers from content
        cleaned_content = re.sub(r"#\w+:\s*.+\n", "", content)
        
        return metadata, cleaned_content

    def chunk_document(
        self, 
        content: str, 
        agent_type: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Tuple[str, Dict[str, str]]]:
        """
        Chunk a document based on agent type requirements.

        Args:
            content: Document content
            agent_type: Type of agent (travel_support, booking_payments, policy)
            chunk_size: Maximum size of chunks
            chunk_overlap: Overlap between chunks

        Returns:
            List of (chunk_text, metadata) tuples
        """
        # Adjust chunking strategy based on agent type
        if agent_type == "policy":
            # Policy documents: larger chunks, less overlap (for CAG strategy)
            chunk_size = 2000
            chunk_overlap = 100
        elif agent_type == "booking_payments":
            # Booking/payments: medium chunks (for hybrid strategy)
            chunk_size = 1500
            chunk_overlap = 200
        else:  # travel_support
            # Travel support: smaller chunks for FAQs, larger for guides (RAG strategy)
            # Check if it's an FAQ or guide
            if "faq" in content.lower() or "question" in content.lower():
                chunk_size = 800
                chunk_overlap = 150
            else:
                chunk_size = 1200
                chunk_overlap = 200

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        chunks = text_splitter.split_text(content)
        
        # Prepare chunks with metadata
        chunk_data = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                "agent_type": agent_type,
                "chunk_index": str(i),
                "total_chunks": str(len(chunks))
            }
            chunk_data.append((chunk, chunk_metadata))
        
        return chunk_data

    def load_documents_from_directory(self, directory: Path, agent_type: str) -> List[Tuple[str, Dict[str, str]]]:
        """
        Load and parse documents from a directory.

        Args:
            directory: Path to directory containing documents
            agent_type: Type of agent for these documents

        Returns:
            List of (content, metadata) tuples
        """
        documents = []
        
        if not directory.exists():
            logger.warning(f"Directory does not exist: {directory}")
            return documents

        # Get all text files in directory
        text_files = list(directory.glob("*.txt"))
        
        if not text_files:
            logger.warning(f"No .txt files found in {directory}")
            return documents

        for file_path in text_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Parse metadata from content
                metadata, cleaned_content = self.parse_metadata(content)
                
                # Add file-level metadata
                metadata["agent_type"] = agent_type
                metadata["source_file"] = file_path.name
                metadata["document_type"] = metadata.get("document_type", "general")
                
                # Chunk the document
                chunks = self.chunk_document(cleaned_content, agent_type)
                
                # Add file metadata to each chunk
                for chunk_text, chunk_metadata in chunks:
                    chunk_metadata.update({
                        "source_file": metadata["source_file"],
                        "document_type": metadata.get("document_type", "general"),
                        "destination": metadata.get("destination", ""),
                        "last_updated": metadata.get("last_updated", ""),
                        "effective_date": metadata.get("effective_date", ""),
                    })
                    documents.append((chunk_text, chunk_metadata))
                
                logger.info(f"Loaded {len(chunks)} chunks from {file_path.name}")
                
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
                continue

        return documents

    def ingest_documents(self, data_dir: Path):
        """
        Ingest all documents from the mock data directory structure.

        Args:
            data_dir: Path to the mock_data directory
        """
        # Map of subdirectories to agent types
        agent_mapping = {
            "travel_support": "travel_support",
            "booking_payments": "booking_payments",
            "policy": "policy",
        }

        all_documents = []
        
        # Load documents from each agent directory
        for subdir_name, agent_type in agent_mapping.items():
            subdir = data_dir / subdir_name
            logger.info(f"Loading documents from {subdir_name}...")
            
            docs = self.load_documents_from_directory(subdir, agent_type)
            all_documents.extend(docs)
            
            logger.info(f"Loaded {len(docs)} chunks from {subdir_name}")

        if not all_documents:
            logger.error("No documents loaded. Check data directory structure.")
            return

        logger.info(f"Total chunks to ingest: {len(all_documents)}")

        # Generate embeddings and store in ChromaDB
        batch_size = 100
        total_ingested = 0

        for i in range(0, len(all_documents), batch_size):
            batch = all_documents[i:i + batch_size]
            
            # Prepare batch data
            texts = [doc[0] for doc in batch]
            metadatas = [doc[1] for doc in batch]
            
            # Generate reliable IDs using hash to avoid conflicts and special character issues
            ids = []
            for j, (text, metadata) in enumerate(batch):
                # Create a hash-based ID from agent_type, source_file, chunk_index, and batch info
                id_string = f"{metadata.get('agent_type', 'unknown')}_{metadata.get('source_file', 'unknown')}_{metadata.get('chunk_index', j)}_{i+j}"
                # Use hash to sanitize and ensure uniqueness
                id_hash = hashlib.md5(id_string.encode('utf-8')).hexdigest()[:16]
                ids.append(f"{metadata.get('agent_type', 'unknown')}_{id_hash}")

            try:
                # Generate embeddings
                embeddings_list = self.embeddings.embed_documents(texts)
                
                # Add to collection
                self.collection.add(
                    embeddings=embeddings_list,
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )
                
                total_ingested += len(batch)
                logger.info(f"Ingested batch {i//batch_size + 1}: {len(batch)} chunks (Total: {total_ingested}/{len(all_documents)})")
                
            except Exception as e:
                logger.error(f"Error ingesting batch {i//batch_size + 1}: {e}")
                continue

        logger.info(f"Ingestion complete! Total chunks ingested: {total_ingested}")

    def clear_collection(self):
        """Clear the existing collection (use with caution)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Travel Agency Knowledge Base"}
            )
            logger.info(f"Cleared and recreated collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")


def main():
    """Main entry point for data ingestion."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Ingest travel agency documents into ChromaDB"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Automatically clear existing collection and re-ingest without prompting",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip ingestion if collection already contains documents",
    )
    args = parser.parse_args()

    # Get paths from environment or use defaults
    backend_dir = Path(__file__).parent.parent
    data_dir = backend_dir / "data" / "mock_data"
    db_path = backend_dir / "data" / "chroma_db"
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "travel_agency_kb")

    logger.info("Starting data ingestion pipeline...")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"ChromaDB path: {db_path}")
    logger.info(f"Collection name: {collection_name}")

    # Ensure data directory exists
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return

    # Create ChromaDB directory if it doesn't exist
    db_path.mkdir(parents=True, exist_ok=True)

    # Initialize ingester
    ingester = DocumentIngester(
        db_path=str(db_path),
        collection_name=collection_name
    )

    # Check if collection has data and handle accordingly
    collection_count = ingester.collection.count()
    if collection_count > 0:
        logger.info(f"Collection already contains {collection_count} documents.")
        
        if args.force:
            logger.info("--force flag set: clearing existing collection and re-ingesting...")
            ingester.clear_collection()
        elif args.skip_existing:
            logger.info("--skip-existing flag set: keeping existing data. Exiting.")
            return
        else:
            # Interactive prompt only if no flags provided
            try:
                response = input("Do you want to clear and re-ingest? (yes/no): ")
                if response.lower() == "yes":
                    ingester.clear_collection()
                else:
                    logger.info("Keeping existing data. Exiting.")
                    return
            except (EOFError, KeyboardInterrupt):
                # Handle non-interactive environments (e.g., CI/CD)
                logger.warning(
                    "Non-interactive environment detected. Use --force or --skip-existing flags."
                )
                return

    # Ingest documents
    ingester.ingest_documents(data_dir)
    
    # Verify ingestion
    final_count = ingester.collection.count()
    logger.info(f"Ingestion complete! Collection now contains {final_count} documents.")


if __name__ == "__main__":
    main()

