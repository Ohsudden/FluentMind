import weaviate
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """Represents a single retrieved document with metadata."""
    uuid: str
    content: Dict[str, Any]
    distance: float
    collection: str


class RAGRetriever:
    """
    RAG retrieval system for FluentMind using Weaviate vector database.
    Supports searching across vocabulary, CEFR texts, and grammar profiles.
    """
    
    def __init__(self, weaviate_url: str = "http://localhost:8080"):
        """Initialize the RAG retriever with Weaviate connection."""
        self.weaviate_url = weaviate_url
        
    def retrieve_vocabulary(
        self,
        query: str,
        limit: int = 5,
        cefr_level: Optional[str] = None,
        pos: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve vocabulary items relevant to the query.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            cefr_level: Filter by CEFR level (A1, A2, B1, B2, C1, C2)
            pos: Filter by part of speech (noun, verb, adjective, etc.)
            
        Returns:
            List of RetrievalResult objects
        """
        with weaviate.connect_to_local() as client:
            collection = client.collections.get("Vocabulary")
            
            # Build query with filters if provided
            query_builder = collection.query.near_text(
                query=query,
                limit=limit,
                return_metadata=['distance']
            )
            
            # Apply filters if provided
            if cefr_level or pos:
                filters = []
                if cefr_level:
                    filters.append(f'CEFR == "{cefr_level}"')
                if pos:
                    filters.append(f'pos == "{pos}"')
                # Note: Weaviate v4 uses different filter syntax
                # This is a placeholder - adjust based on your Weaviate version
                
            response = query_builder
            
            results = []
            for obj in response.objects:
                results.append(RetrievalResult(
                    uuid=str(obj.uuid),
                    content=obj.properties,
                    distance=obj.metadata.distance if hasattr(obj.metadata, 'distance') else 0.0,
                    collection="Vocabulary"
                ))
            
            return results
    
    def retrieve_cefr_texts(
        self,
        query: str,
        limit: int = 3,
        target_level: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve CEFR-leveled texts relevant to the query.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            target_level: Filter by CEFR level
            
        Returns:
            List of RetrievalResult objects
        """
        with weaviate.connect_to_local() as client:
            collection = client.collections.get("CefrLeveledTexts")
            
            response = collection.query.near_text(
                query=query,
                limit=limit,
                return_metadata=['distance']
            )
            
            results = []
            for obj in response.objects:
                # Filter by level if specified
                if target_level and obj.properties.get('label') != target_level:
                    continue
                    
                results.append(RetrievalResult(
                    uuid=str(obj.uuid),
                    content=obj.properties,
                    distance=obj.metadata.distance if hasattr(obj.metadata, 'distance') else 0.0,
                    collection="CefrLeveledTexts"
                ))
            
            return results[:limit]  # Ensure we don't exceed limit after filtering
    
    def retrieve_grammar(
        self,
        query: str,
        limit: int = 5,
        cefr_level: Optional[str] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve grammar rules and patterns relevant to the query.
        
        Args:
            query: Search query string (e.g., "present perfect", "conditional")
            limit: Maximum number of results to return
            cefr_level: Filter by CEFR-J level
            
        Returns:
            List of RetrievalResult objects
        """
        with weaviate.connect_to_local() as client:
            collection = client.collections.get("CefrGrammarProfile")
            
            response = collection.query.near_text(
                query=query,
                limit=limit,
                return_metadata=['distance']
            )
            
            results = []
            for obj in response.objects:
                # Filter by level if specified
                if cefr_level and obj.properties.get('cefr_j_level') != cefr_level:
                    continue
                    
                results.append(RetrievalResult(
                    uuid=str(obj.uuid),
                    content=obj.properties,
                    distance=obj.metadata.distance if hasattr(obj.metadata, 'distance') else 0.0,
                    collection="CefrGrammarProfile"
                ))
            
            return results[:limit]
    
    def multi_collection_retrieve(
        self,
        query: str,
        collections: List[str] = None,
        limit_per_collection: int = 3
    ) -> Dict[str, List[RetrievalResult]]:
        """
        Retrieve from multiple collections simultaneously.
        
        Args:
            query: Search query string
            collections: List of collection names to search. 
                        Defaults to all collections.
            limit_per_collection: Results per collection
            
        Returns:
            Dictionary mapping collection names to results
        """
        if collections is None:
            collections = ["Vocabulary", "CefrLeveledTexts", "CefrGrammarProfile"]
        
        results = {}
        
        with weaviate.connect_to_local() as client:
            for collection_name in collections:
                try:
                    collection = client.collections.get(collection_name)
                    response = collection.query.near_text(
                        query=query,
                        limit=limit_per_collection,
                        return_metadata=['distance']
                    )
                    
                    collection_results = []
                    for obj in response.objects:
                        collection_results.append(RetrievalResult(
                            uuid=str(obj.uuid),
                            content=obj.properties,
                            distance=obj.metadata.distance if hasattr(obj.metadata, 'distance') else 0.0,
                            collection=collection_name
                        ))
                    
                    results[collection_name] = collection_results
                    
                except Exception as e:
                    print(f"Error retrieving from {collection_name}: {e}")
                    results[collection_name] = []
        
        return results
    
    def hybrid_search(
        self,
        query: str,
        collection_name: str = "Vocabulary",
        limit: int = 5,
        alpha: float = 0.5
    ) -> List[RetrievalResult]:
        """
        Perform hybrid search combining vector and keyword search.
        
        Args:
            query: Search query string
            collection_name: Name of collection to search
            limit: Maximum number of results
            alpha: Balance between vector (1.0) and keyword (0.0) search
            
        Returns:
            List of RetrievalResult objects
        """
        with weaviate.connect_to_local() as client:
            collection = client.collections.get(collection_name)
            
            response = collection.query.hybrid(
                query=query,
                limit=limit,
                alpha=alpha,
                return_metadata=['distance', 'score']
            )
            
            results = []
            for obj in response.objects:
                results.append(RetrievalResult(
                    uuid=str(obj.uuid),
                    content=obj.properties,
                    distance=obj.metadata.distance if hasattr(obj.metadata, 'distance') else 0.0,
                    collection=collection_name
                ))
            
            return results


def format_retrieval_results(results: List[RetrievalResult]) -> str:
    """
    Format retrieval results into a readable string for LLM context.
    
    Args:
        results: List of RetrievalResult objects
        
    Returns:
        Formatted string representation
    """
    if not results:
        return "No results found."
    
    formatted = []
    for i, result in enumerate(results, 1):
        formatted.append(f"--- Result {i} (Distance: {result.distance:.4f}) ---")
        formatted.append(f"Collection: {result.collection}")
        
        for key, value in result.content.items():
            if value:  # Only show non-empty values
                formatted.append(f"{key}: {value}")
        
        formatted.append("")  # Empty line between results
    
    return "\n".join(formatted)


# Example usage
if __name__ == "__main__":
    # Initialize retriever
    retriever = RAGRetriever()
    
    # Example 1: Retrieve vocabulary
    print("=== Vocabulary Search ===")
    vocab_results = retriever.retrieve_vocabulary("learn", limit=3)
    print(format_retrieval_results(vocab_results))
    
    # Example 2: Retrieve CEFR texts
    print("\n=== CEFR Text Search ===")
    text_results = retriever.retrieve_cefr_texts("education", limit=2)
    print(format_retrieval_results(text_results))
    
    # Example 3: Retrieve grammar
    print("\n=== Grammar Search ===")
    grammar_results = retriever.retrieve_grammar("present perfect", limit=3)
    print(format_retrieval_results(grammar_results))
    
    # Example 4: Multi-collection search
    print("\n=== Multi-Collection Search ===")
    multi_results = retriever.multi_collection_retrieve("learning English", limit_per_collection=2)
    for collection_name, results in multi_results.items():
        print(f"\n--- {collection_name} ---")
        print(format_retrieval_results(results))
