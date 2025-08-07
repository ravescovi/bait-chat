"""
RAG (Retrieval-Augmented Generation) engine for knowledge base
Manages vector store, document indexing, and similarity search
"""

import logging
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from config.settings import settings

# In production, these would be actual imports
# from langchain.embeddings import OpenAIEmbeddings
# from langchain.vectorstores import Chroma
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.document_loaders import TextLoader, DirectoryLoader, JSONLoader

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG system for device definitions, plan templates, and documentation"""
    
    def __init__(self):
        self.vector_store = None
        self.embeddings = None
        self.text_splitter = None
        self._initialized = False
        self.knowledge_base_path = Path("../knowledge_base")
        self.vector_db_path = Path("../vector_db")
    
    async def initialize(self):
        """Initialize RAG components and load knowledge base"""
        try:
            # Initialize embeddings
            # self.embeddings = OpenAIEmbeddings(
            #     api_key=settings.OPENAI_API_KEY
            # )
            
            # Initialize text splitter
            # self.text_splitter = RecursiveCharacterTextSplitter(
            #     chunk_size=1000,
            #     chunk_overlap=200,
            #     length_function=len,
            # )
            
            # Initialize or load vector store
            await self._initialize_vector_store()
            
            # Load knowledge base documents
            await self._load_knowledge_base()
            
            self._initialized = True
            logger.info("RAG engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            self._initialized = False
    
    async def _initialize_vector_store(self):
        """Initialize or load existing vector store"""
        try:
            # In production, use actual vector store
            # if self.vector_db_path.exists():
            #     self.vector_store = Chroma(
            #         persist_directory=str(self.vector_db_path),
            #         embedding_function=self.embeddings
            #     )
            #     logger.info("Loaded existing vector store")
            # else:
            #     self.vector_store = Chroma(
            #         persist_directory=str(self.vector_db_path),
            #         embedding_function=self.embeddings
            #     )
            #     logger.info("Created new vector store")
            
            # For development, simulate vector store
            self.vector_store = {"documents": [], "embeddings": []}
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            raise
    
    async def _load_knowledge_base(self):
        """Load and index all knowledge base documents"""
        try:
            documents = []
            
            # Load BITS device definitions
            devices_path = self.knowledge_base_path / "bits_devices"
            if devices_path.exists():
                documents.extend(await self._load_device_definitions(devices_path))
            
            # Load plan documentation
            plans_path = self.knowledge_base_path / "plans"
            if plans_path.exists():
                documents.extend(await self._load_plan_documentation(plans_path))
            
            # Load beamline documentation
            docs_path = self.knowledge_base_path / "documentation"
            if docs_path.exists():
                documents.extend(await self._load_documentation(docs_path))
            
            # Add documents to vector store
            if documents:
                # In production, add to actual vector store
                # texts = self.text_splitter.split_documents(documents)
                # self.vector_store.add_documents(texts)
                
                # For development, simulate
                self.vector_store["documents"].extend(documents)
                logger.info(f"Loaded {len(documents)} documents into vector store")
            
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
    
    async def _load_device_definitions(self, path: Path) -> List[Dict[str, Any]]:
        """Load BITS device definition files"""
        documents = []
        
        try:
            # Look for Python files with device definitions
            for file in path.glob("*.py"):
                with open(file, 'r') as f:
                    content = f.read()
                    
                documents.append({
                    "content": content,
                    "metadata": {
                        "source": str(file),
                        "type": "device_definition",
                        "filename": file.name
                    }
                })
            
            # Look for JSON device configurations
            for file in path.glob("*.json"):
                with open(file, 'r') as f:
                    content = f.read()
                    
                documents.append({
                    "content": content,
                    "metadata": {
                        "source": str(file),
                        "type": "device_config",
                        "filename": file.name
                    }
                })
            
            logger.info(f"Loaded {len(documents)} device definitions")
            
        except Exception as e:
            logger.error(f"Error loading device definitions: {e}")
        
        return documents
    
    async def _load_plan_documentation(self, path: Path) -> List[Dict[str, Any]]:
        """Load scan plan documentation"""
        documents = []
        
        try:
            # Load markdown documentation
            for file in path.glob("*.md"):
                with open(file, 'r') as f:
                    content = f.read()
                    
                documents.append({
                    "content": content,
                    "metadata": {
                        "source": str(file),
                        "type": "plan_documentation",
                        "filename": file.name
                    }
                })
            
            # Load plan examples
            for file in path.glob("*.py"):
                with open(file, 'r') as f:
                    content = f.read()
                    
                documents.append({
                    "content": content,
                    "metadata": {
                        "source": str(file),
                        "type": "plan_example",
                        "filename": file.name
                    }
                })
            
            logger.info(f"Loaded {len(documents)} plan documents")
            
        except Exception as e:
            logger.error(f"Error loading plan documentation: {e}")
        
        return documents
    
    async def _load_documentation(self, path: Path) -> List[Dict[str, Any]]:
        """Load general beamline documentation"""
        documents = []
        
        try:
            for file in path.glob("**/*.md"):
                with open(file, 'r') as f:
                    content = f.read()
                    
                documents.append({
                    "content": content,
                    "metadata": {
                        "source": str(file),
                        "type": "documentation",
                        "filename": file.name
                    }
                })
            
            logger.info(f"Loaded {len(documents)} documentation files")
            
        except Exception as e:
            logger.error(f"Error loading documentation: {e}")
        
        return documents
    
    def is_initialized(self) -> bool:
        """Check if RAG engine is initialized"""
        return self._initialized
    
    async def search(
        self, 
        query: str, 
        limit: int = 5,
        filter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using similarity search
        
        Args:
            query: Search query
            limit: Maximum number of results
            filter_type: Filter by document type (device, plan, documentation)
        
        Returns:
            List of relevant documents with scores
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # In production, use actual vector store search
            # filter_dict = {"type": filter_type} if filter_type else None
            # results = self.vector_store.similarity_search_with_score(
            #     query, k=limit, filter=filter_dict
            # )
            
            # For development, return simulated results
            results = []
            
            # Simulate search based on query keywords
            if "motor" in query.lower() or "device" in query.lower():
                results.append({
                    "content": "Motor devices available: motor_x, motor_y, motor_z. These are standard stepper motors with 0.001mm resolution.",
                    "metadata": {
                        "source": "bits_devices/motors.py",
                        "type": "device_definition"
                    },
                    "score": 0.95
                })
            
            if "scan" in query.lower() or "plan" in query.lower():
                results.append({
                    "content": "Standard scan plans: scan() for continuous scans, count() for static counting, list_scan() for discrete positions.",
                    "metadata": {
                        "source": "plans/standard_plans.md",
                        "type": "plan_documentation"
                    },
                    "score": 0.90
                })
            
            if "pilatus" in query.lower() or "detector" in query.lower():
                results.append({
                    "content": "Pilatus 300K detector: 2D X-ray detector with 487x619 pixels, 172μm pixel size, 20Hz frame rate.",
                    "metadata": {
                        "source": "bits_devices/detectors.json",
                        "type": "device_config"
                    },
                    "score": 0.88
                })
            
            # Default result if nothing specific matched
            if not results:
                results.append({
                    "content": "Beamline control system uses Bluesky for experiment orchestration with QServer for remote operation.",
                    "metadata": {
                        "source": "documentation/overview.md",
                        "type": "documentation"
                    },
                    "score": 0.70
                })
            
            logger.info(f"Search '{query}' returned {len(results)} results")
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    async def search_devices(self, query: str) -> List[Dict[str, Any]]:
        """Search specifically for device information"""
        return await self.search(query, filter_type="device")
    
    async def search_plans(self, query: str) -> List[Dict[str, Any]]:
        """Search specifically for plan information"""
        return await self.search(query, filter_type="plan")
    
    async def search_documentation(self, query: str) -> List[Dict[str, Any]]:
        """Search general documentation"""
        return await self.search(query, filter_type="documentation")
    
    async def add_document(
        self, 
        content: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Add a new document to the knowledge base
        
        Args:
            content: Document content
            metadata: Document metadata (source, type, etc.)
        
        Returns:
            Success status
        """
        try:
            # In production, add to vector store
            # document = Document(page_content=content, metadata=metadata)
            # texts = self.text_splitter.split_documents([document])
            # self.vector_store.add_documents(texts)
            
            # For development, simulate
            self.vector_store["documents"].append({
                "content": content,
                "metadata": metadata
            })
            
            logger.info(f"Added document from {metadata.get('source', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
    
    async def update_index(self):
        """Rebuild the vector store index"""
        try:
            logger.info("Rebuilding vector store index...")
            
            # Clear existing store
            self.vector_store = {"documents": [], "embeddings": []}
            
            # Reload all documents
            await self._load_knowledge_base()
            
            logger.info("Vector store index rebuilt successfully")
            
        except Exception as e:
            logger.error(f"Error rebuilding index: {e}")
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            # In production, persist vector store
            # if self.vector_store:
            #     self.vector_store.persist()
            
            logger.info("RAG engine cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")