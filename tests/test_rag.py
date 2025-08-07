"""
RAG engine tests
Tests for knowledge base functionality
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.rag_engine import RAGEngine


class TestRAGEngine:
    """Test RAG engine functionality"""
    
    @pytest.fixture
    def temp_knowledge_base(self):
        """Create temporary knowledge base directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            kb_path = Path(temp_dir) / "knowledge_base"
            kb_path.mkdir()
            
            # Create sample files
            devices_dir = kb_path / "bits_devices"
            devices_dir.mkdir()
            
            plans_dir = kb_path / "plans"
            plans_dir.mkdir()
            
            docs_dir = kb_path / "documentation"
            docs_dir.mkdir()
            
            # Sample device file
            (devices_dir / "motors.py").write_text("""
# Motor device definitions
motor_x = EpicsMotor('XF:28IDC:ES{Dif:1-Ax:X}Mtr', name='motor_x')
motor_y = EpicsMotor('XF:28IDC:ES{Dif:1-Ax:Y}Mtr', name='motor_y')
""")
            
            # Sample plan file
            (plans_dir / "standard_plans.md").write_text("""
# Standard Scan Plans

## scan
Continuous scan over a motor range while collecting detector data.

## count
Take repeated measurements at the current position.
""")
            
            # Sample documentation
            (docs_dir / "beamline_overview.md").write_text("""
# Beamline Overview

This beamline uses Bluesky for experiment control.
Available detectors include Pilatus and ion chambers.
""")
            
            yield kb_path
    
    @pytest.fixture
    def rag_engine(self, temp_knowledge_base):
        """Create RAG engine with temporary knowledge base"""
        engine = RAGEngine()
        engine.knowledge_base_path = temp_knowledge_base
        return engine
    
    @pytest.mark.asyncio
    async def test_initialization(self, rag_engine):
        """Test RAG engine initialization"""
        await rag_engine.initialize()
        
        assert rag_engine.is_initialized() == True
        assert rag_engine.vector_store is not None
    
    @pytest.mark.asyncio
    async def test_load_device_definitions(self, rag_engine):
        """Test loading device definition files"""
        devices_path = rag_engine.knowledge_base_path / "bits_devices"
        documents = await rag_engine._load_device_definitions(devices_path)
        
        assert len(documents) > 0
        
        # Check document structure
        doc = documents[0]
        assert "content" in doc
        assert "metadata" in doc
        assert doc["metadata"]["type"] == "device_definition"
        assert "motor_x" in doc["content"]
    
    @pytest.mark.asyncio
    async def test_load_plan_documentation(self, rag_engine):
        """Test loading plan documentation"""
        plans_path = rag_engine.knowledge_base_path / "plans"
        documents = await rag_engine._load_plan_documentation(plans_path)
        
        assert len(documents) > 0
        
        doc = documents[0]
        assert "content" in doc
        assert "metadata" in doc
        assert doc["metadata"]["type"] == "plan_documentation"
        assert "scan" in doc["content"] or "count" in doc["content"]
    
    @pytest.mark.asyncio
    async def test_load_documentation(self, rag_engine):
        """Test loading general documentation"""
        docs_path = rag_engine.knowledge_base_path / "documentation"
        documents = await rag_engine._load_documentation(docs_path)
        
        assert len(documents) > 0
        
        doc = documents[0]
        assert "content" in doc
        assert "metadata" in doc
        assert doc["metadata"]["type"] == "documentation"
        assert "Bluesky" in doc["content"]
    
    @pytest.mark.asyncio
    async def test_search_general(self, rag_engine):
        """Test general search functionality"""
        await rag_engine.initialize()
        
        results = await rag_engine.search("motor", limit=3)
        
        assert isinstance(results, list)
        assert len(results) <= 3
        
        if results:
            result = results[0]
            assert "content" in result
            assert "metadata" in result
            assert "score" in result
    
    @pytest.mark.asyncio
    async def test_search_devices(self, rag_engine):
        """Test device-specific search"""
        await rag_engine.initialize()
        
        results = await rag_engine.search_devices("motor position")
        
        assert isinstance(results, list)
        
        # Results should be device-related
        for result in results:
            assert "motor" in result["content"].lower() or "device" in result["content"].lower()
    
    @pytest.mark.asyncio
    async def test_search_plans(self, rag_engine):
        """Test plan-specific search"""
        await rag_engine.initialize()
        
        results = await rag_engine.search_plans("scan continuous")
        
        assert isinstance(results, list)
        
        # Results should be plan-related
        for result in results:
            content_lower = result["content"].lower()
            assert "scan" in content_lower or "plan" in content_lower
    
    @pytest.mark.asyncio
    async def test_search_documentation(self, rag_engine):
        """Test documentation search"""
        await rag_engine.initialize()
        
        results = await rag_engine.search_documentation("beamline control")
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_add_document(self, rag_engine):
        """Test adding new documents to knowledge base"""
        await rag_engine.initialize()
        
        new_content = "Test motor for scanning applications"
        new_metadata = {
            "source": "test_motor.py",
            "type": "device_definition",
            "added_by": "test"
        }
        
        success = await rag_engine.add_document(new_content, new_metadata)
        
        assert success == True
        
        # Search for the new document
        results = await rag_engine.search("Test motor")
        
        # Should find the newly added document
        assert len(results) > 0
        found = any("Test motor" in r["content"] for r in results)
        assert found == True
    
    @pytest.mark.asyncio
    async def test_update_index(self, rag_engine):
        """Test rebuilding the vector store index"""
        await rag_engine.initialize()
        
        # Add some documents first
        await rag_engine.add_document(
            "Original document", 
            {"source": "test1.txt", "type": "documentation"}
        )
        
        # Rebuild index
        await rag_engine.update_index()
        
        # Should still be initialized
        assert rag_engine.is_initialized() == True
    
    @pytest.mark.asyncio
    async def test_cleanup(self, rag_engine):
        """Test cleanup functionality"""
        await rag_engine.initialize()
        await rag_engine.cleanup()
        
        # Should handle cleanup without errors
        assert True  # If we get here, cleanup succeeded
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, rag_engine):
        """Test search with type filters"""
        await rag_engine.initialize()
        
        # Test device filter
        device_results = await rag_engine.search("motor", filter_type="device")
        assert isinstance(device_results, list)
        
        # Test plan filter
        plan_results = await rag_engine.search("scan", filter_type="plan")
        assert isinstance(plan_results, list)
        
        # Test documentation filter
        doc_results = await rag_engine.search("beamline", filter_type="documentation")
        assert isinstance(doc_results, list)
    
    @pytest.mark.asyncio
    async def test_search_empty_query(self, rag_engine):
        """Test search with empty query"""
        await rag_engine.initialize()
        
        results = await rag_engine.search("", limit=1)
        
        # Should handle empty query gracefully
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_search_no_results(self, rag_engine):
        """Test search with no matching results"""
        await rag_engine.initialize()
        
        results = await rag_engine.search("xyzabc123nonexistent", limit=5)
        
        # Should return empty or default results
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_error_handling(self, rag_engine):
        """Test error handling in RAG operations"""
        # Test search without initialization
        results = await rag_engine.search("test")
        
        # Should handle gracefully and auto-initialize or return empty
        assert isinstance(results, list)


class TestRAGEngineWithMockedVectorStore:
    """Test RAG engine with mocked vector store dependencies"""
    
    @pytest.fixture
    def mocked_rag_engine(self):
        """Create RAG engine with mocked dependencies"""
        with patch('backend.rag_engine.OpenAIEmbeddings'), \
             patch('backend.rag_engine.Chroma'), \
             patch('backend.rag_engine.RecursiveCharacterTextSplitter'):
            
            engine = RAGEngine()
            return engine
    
    @pytest.mark.asyncio
    async def test_mocked_initialization(self, mocked_rag_engine):
        """Test initialization with mocked dependencies"""
        await mocked_rag_engine.initialize()
        
        # Should initialize successfully even with mocked dependencies
        assert mocked_rag_engine.is_initialized() == True
    
    @pytest.mark.asyncio 
    async def test_mocked_vector_store_operations(self, mocked_rag_engine):
        """Test vector store operations with mocks"""
        await mocked_rag_engine.initialize()
        
        # Test search with mocked vector store
        results = await mocked_rag_engine.search("test query")
        
        assert isinstance(results, list)
        
        # Test add document
        success = await mocked_rag_engine.add_document(
            "test content", 
            {"source": "test.txt"}
        )
        
        assert success == True


@pytest.mark.slow
class TestRAGEnginePerformance:
    """Performance tests for RAG engine"""
    
    @pytest.mark.asyncio
    async def test_search_performance(self):
        """Test search performance with larger dataset"""
        engine = RAGEngine()
        await engine.initialize()
        
        import time
        
        # Perform multiple searches and measure time
        start_time = time.time()
        
        for i in range(10):
            results = await engine.search(f"test query {i}", limit=5)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / 10
        
        # Should complete searches reasonably quickly (< 1 second each on average)
        assert avg_time < 1.0
    
    @pytest.mark.asyncio
    async def test_concurrent_searches(self):
        """Test concurrent search operations"""
        engine = RAGEngine()
        await engine.initialize()
        
        # Run multiple searches concurrently
        tasks = [
            engine.search("motor"),
            engine.search("detector"),
            engine.search("scan plan"),
            engine.search("beamline"),
            engine.search("pilatus")
        ]
        
        results = await asyncio.gather(*tasks)
        
        # All searches should complete successfully
        assert len(results) == 5
        for result in results:
            assert isinstance(result, list)