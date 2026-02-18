"""Tests for the crawler database layer."""
import os
import tempfile
import pytest
from app_crawler.database import CrawlerDatabase


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db = CrawlerDatabase(path)
    yield db
    
    # Cleanup
    if os.path.exists(path):
        os.unlink(path)


def test_create_path(temp_db):
    """Test creating a new crawler path."""
    path_id = temp_db.create_path(
        path_id="test_path_001",
        name="Test Path",
        platform="android",
        app_package="com.example.app",
        description="Test description"
    )
    
    assert path_id > 0
    
    # Verify path was created
    path = temp_db.get_path_by_id("test_path_001")
    assert path is not None
    assert path['name'] == "Test Path"
    assert path['platform'] == "android"


def test_add_path_step(temp_db):
    """Test adding steps to a path."""
    # Create path first
    temp_db.create_path(
        path_id="test_path_002",
        name="Test Path 2",
        platform="android",
        app_package="com.example.app"
    )
    
    # Add step
    step_id = temp_db.add_path_step(
        path_id="test_path_002",
        step_number=1,
        action_type="click",
        element_selector="//button[@text='Login']",
        element_attributes={"text": "Login", "type": "button"},
        ai_reasoning="Click login button to proceed"
    )
    
    assert step_id > 0
    
    # Verify step was added
    steps = temp_db.get_path_steps("test_path_002")
    assert len(steps) == 1
    assert steps[0]['action_type'] == "click"
    assert steps[0]['ai_reasoning'] == "Click login button to proceed"


def test_get_all_paths(temp_db):
    """Test retrieving all paths."""
    # Create multiple paths
    temp_db.create_path("path_001", "Path 1", "android", "com.app1")
    temp_db.create_path("path_002", "Path 2", "ios", "com.app2")
    
    paths = temp_db.get_all_paths()
    assert len(paths) >= 2
    
    path_ids = [p['path_id'] for p in paths]
    assert "path_001" in path_ids
    assert "path_002" in path_ids


def test_update_path(temp_db):
    """Test updating path metadata."""
    # Create path
    temp_db.create_path(
        path_id="test_path_003",
        name="Original Name",
        platform="android",
        app_package="com.example.app"
    )
    
    # Update path
    success = temp_db.update_path(
        path_id="test_path_003",
        name="Updated Name",
        description="New description"
    )
    
    assert success
    
    # Verify update
    path = temp_db.get_path_by_id("test_path_003")
    assert path['name'] == "Updated Name"
    assert path['description'] == "New description"


def test_delete_path(temp_db):
    """Test deleting a path."""
    # Create path with steps
    temp_db.create_path(
        path_id="test_path_004",
        name="To Delete",
        platform="android",
        app_package="com.example.app"
    )
    temp_db.add_path_step(
        path_id="test_path_004",
        step_number=1,
        action_type="click",
        element_selector="//button",
        element_attributes={}
    )
    
    # Delete path
    success = temp_db.delete_path("test_path_004")
    assert success
    
    # Verify deletion
    path = temp_db.get_path_by_id("test_path_004")
    assert path is None
    
    steps = temp_db.get_path_steps("test_path_004")
    assert len(steps) == 0


def test_add_human_intervention(temp_db):
    """Test recording human interventions."""
    # Create path
    temp_db.create_path(
        path_id="test_path_005",
        name="Test Path 5",
        platform="android",
        app_package="com.example.app"
    )
    
    # Add intervention
    intervention_id = temp_db.add_human_intervention(
        path_id="test_path_005",
        step_number=5,
        intervention_type="decision",
        ai_question="What should I click next?",
        human_response="Click the submit button"
    )
    
    assert intervention_id > 0
    
    # Verify intervention
    interventions = temp_db.get_human_interventions("test_path_005")
    assert len(interventions) == 1
    assert interventions[0]['ai_question'] == "What should I click next?"


def test_path_not_found(temp_db):
    """Test handling of non-existent paths."""
    path = temp_db.get_path_by_id("nonexistent")
    assert path is None
    
    success = temp_db.update_path("nonexistent", name="Test")
    assert not success
    
    success = temp_db.delete_path("nonexistent")
    assert not success
