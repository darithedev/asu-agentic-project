"""Pure CAG (Cached Augmented Generation) implementation for Policy agent."""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CAGRetriever:
    """
    Pure CAG retriever for static document caching.
    
    Used by Policy agent to load static documents once per session
    and cache them for fast, consistent responses.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the CAG retriever.

        Args:
            data_dir: Path to directory containing policy documents
        """
        if data_dir is None:
            # Default to mock_data/policy directory
            backend_dir = Path(__file__).parent.parent.parent
            data_dir = backend_dir / "data" / "mock_data" / "policy"
        
        self.data_dir = Path(data_dir)
        self.cached_documents: Dict[str, List[str]] = {}
        logger.info(f"Initialized CAG retriever with data directory: {data_dir}")

    def load_documents(self, agent_type: str = "policy") -> List[str]:
        """
        Load all policy documents from the data directory.

        Args:
            agent_type: Type of agent (should be "policy")

        Returns:
            List of document contents as strings
        """
        if not self.data_dir.exists():
            logger.warning(f"Data directory does not exist: {self.data_dir}")
            return []

        documents = []
        text_files = list(self.data_dir.glob("*.txt"))

        if not text_files:
            logger.warning(f"No .txt files found in {self.data_dir}")
            return []

        for file_path in text_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Remove metadata markers for cleaner content
                    cleaned_content = re.sub(r"#\w+:\s*.+\n", "", content)
                    documents.append(cleaned_content.strip())
                    logger.debug(f"Loaded document: {file_path.name}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
                continue

        logger.info(f"Loaded {len(documents)} documents for agent type: {agent_type}")
        return documents

    def cache_documents(self, agent_type: str = "policy") -> None:
        """
        Cache documents for a session.

        Args:
            agent_type: Type of agent
        """
        if agent_type not in self.cached_documents:
            documents = self.load_documents(agent_type)
            self.cached_documents[agent_type] = documents
            logger.info(f"Cached {len(documents)} documents for {agent_type}")

    def get_cached_documents(self, agent_type: str = "policy") -> List[str]:
        """
        Retrieve cached documents.

        Args:
            agent_type: Type of agent

        Returns:
            List of cached document contents
        """
        if agent_type not in self.cached_documents:
            self.cache_documents(agent_type)
        
        return self.cached_documents.get(agent_type, [])

    def search_cached(
        self,
        query: str,
        agent_type: str = "policy",
        case_sensitive: bool = False,
    ) -> List[str]:
        """
        Simple keyword search in cached documents.

        Args:
            query: Search query
            agent_type: Type of agent
            case_sensitive: Whether search should be case-sensitive

        Returns:
            List of document snippets containing query keywords
        """
        documents = self.get_cached_documents(agent_type)
        query_terms = query.lower().split() if not case_sensitive else query.split()
        
        matching_docs = []
        for doc in documents:
            doc_lower = doc if case_sensitive else doc.lower()
            # Check if any query terms appear in the document
            if any(term in doc_lower for term in query_terms):
                matching_docs.append(doc)
        
        logger.info(f"Found {len(matching_docs)} matching documents for query: {query[:50]}...")
        return matching_docs

    def clear_cache(self, agent_type: Optional[str] = None) -> None:
        """
        Clear cached documents.

        Args:
            agent_type: Specific agent type to clear, or None to clear all
        """
        if agent_type:
            self.cached_documents.pop(agent_type, None)
            logger.info(f"Cleared cache for {agent_type}")
        else:
            self.cached_documents.clear()
            logger.info("Cleared all cached documents")

