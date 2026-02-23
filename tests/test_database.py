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


def test_get_active_path_for_app(temp_db):
    """Test retrieving active path for specific app package."""
    # Create multiple paths for different apps
    temp_db.create_path("path_001", "Path 1", "android", "com.app1")
    temp_db.create_path("path_002", "Path 2", "android", "com.app2") 
    temp_db.create_path("path_003", "Path 3", "android", "com.app1")
    
    # Set one path as inactive
    temp_db.set_path_active("path_001", False)
    
    # Get active path for app1 (should be path_003 - most recent active)
    active_path = temp_db.get_active_path_for_app("com.app1")
    assert active_path is not None
    assert active_path['path_id'] == "path_003"
    
    # Get active path for app2
    active_path = temp_db.get_active_path_for_app("com.app2")
    assert active_path is not None
    assert active_path['path_id'] == "path_002"
    
    # Get active path for non-existent app
    active_path = temp_db.get_active_path_for_app("com.nonexistent")
    assert active_path is None


def test_create_or_get_active_path(temp_db):
    """Test create or get active path functionality."""
    # First call should create new path
    path_id1 = temp_db.create_or_get_active_path(
        app_package="com.newapp",
        name="New App Path",
        platform="android",
        description="Test path"
    )
    assert path_id1 is not None
    
    # Second call should return same path
    path_id2 = temp_db.create_or_get_active_path(
        app_package="com.newapp", 
        name="Different Name",
        platform="android",
        description="Different description"
    )
    assert path_id1 == path_id2
    
    # Verify path exists
    path = temp_db.get_path_by_id(path_id1)
    assert path['app_package'] == "com.newapp"
    assert path['is_active'] == 1


def test_set_path_active(temp_db):
    """Test setting path active status."""
    # Create path
    temp_db.create_path("test_path", "Test", "android", "com.test")
    
    # Set inactive
    success = temp_db.set_path_active("test_path", False)
    assert success
    
    # Verify status changed
    path = temp_db.get_path_by_id("test_path") 
    assert path['is_active'] == 0
    
    # Set active again
    success = temp_db.set_path_active("test_path", True)
    assert success
    
    path = temp_db.get_path_by_id("test_path")
    assert path['is_active'] == 1
    
    # Test non-existent path
    success = temp_db.set_path_active("nonexistent", False)
    assert not success


def test_update_last_step_number(temp_db):
    """Test updating last step number."""
    # Create path
    temp_db.create_path("test_path", "Test", "android", "com.test")
    
    # Update last step number
    success = temp_db.update_last_step_number("test_path", 5)
    assert success
    
    # Verify update
    path = temp_db.get_path_by_id("test_path")
    assert path['last_step_number'] == 5
    
    # Test non-existent path
    success = temp_db.update_last_step_number("nonexistent", 10)
    assert not success


def test_schema_migration(temp_db):
    """Test that new columns exist in paths table."""
    # Verify new columns exist by creating and checking a path
    temp_db.create_path("migration_test", "Migration Test", "android", "com.test")
    
    path = temp_db.get_path_by_id("migration_test")
    
    # New columns should be present with default values
    assert 'is_active' in path
    assert 'last_step_number' in path
    assert path['is_active'] == 1
    assert path['last_step_number'] == 0
