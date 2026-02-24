"""Tests for directed-graph cycle detection in the crawler and database layers."""
import os
import tempfile
import pytest

from app_crawler.database import CrawlerDatabase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_db():
    """Temporary SQLite database, cleaned up after each test."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    db = CrawlerDatabase(path)
    yield db
    if os.path.exists(path):
        os.unlink(path)


def _make_node(db: CrawlerDatabase, pkg: str, activity: str, state_hash: str) -> str:
    """Helper: create a graph node and return its node_id."""
    return db.create_or_get_node(
        app_package=pkg,
        activity_name=activity,
        state_hash=state_hash,
        dom_snapshot="<root/>",
        screenshot_path="",
        element_count=1,
    )


def _make_edge(db: CrawlerDatabase, from_id: str, to_id: str) -> str:
    """Helper: create a graph edge and return its edge_id."""
    return db.create_edge(
        from_node_id=from_id,
        to_node_id=to_id,
        action_type="click",
        element_selector="//button",
        element_text="Next",
        is_valid=True,
    )


# ---------------------------------------------------------------------------
# Database-level directed graph tests
# ---------------------------------------------------------------------------

class TestGraphNodes:
    def test_create_node_returns_id(self, temp_db):
        node_id = _make_node(temp_db, "com.app", "MainActivity", "hash_a")
        assert node_id.startswith("node_")

    def test_create_node_idempotent(self, temp_db):
        """Same state_hash must return the same node_id."""
        id1 = _make_node(temp_db, "com.app", "MainActivity", "hash_dup")
        id2 = _make_node(temp_db, "com.app", "MainActivity", "hash_dup")
        assert id1 == id2

    def test_get_node_by_hash(self, temp_db):
        _make_node(temp_db, "com.app", "Screen1", "hash_xyz")
        node = temp_db.get_node_by_hash("hash_xyz")
        assert node is not None
        assert node["activity_name"] == "Screen1"

    def test_get_node_by_hash_missing(self, temp_db):
        assert temp_db.get_node_by_hash("nonexistent_hash") is None


class TestGraphEdges:
    def test_create_edge(self, temp_db):
        n1 = _make_node(temp_db, "com.app", "A", "h1")
        n2 = _make_node(temp_db, "com.app", "B", "h2")
        edge_id = _make_edge(temp_db, n1, n2)
        assert edge_id.startswith("edge_")

    def test_get_edges_from_node(self, temp_db):
        n1 = _make_node(temp_db, "com.app", "A", "h1")
        n2 = _make_node(temp_db, "com.app", "B", "h2")
        n3 = _make_node(temp_db, "com.app", "C", "h3")
        _make_edge(temp_db, n1, n2)
        _make_edge(temp_db, n1, n3)
        edges = temp_db.get_edges_from_node(n1)
        assert len(edges) == 2
        assert all(e["from_node_id"] == n1 for e in edges)

    def test_get_edges_from_node_none(self, temp_db):
        n1 = _make_node(temp_db, "com.app", "A", "h1")
        assert temp_db.get_edges_from_node(n1) == []


class TestDatabaseDetectCycle:
    """Tests for the pure-Python ``CrawlerDatabase.detect_cycle`` helper."""

    def test_no_cycle_empty_path(self, temp_db):
        assert temp_db.detect_cycle("node_a", []) is None

    def test_no_cycle_single_node(self, temp_db):
        assert temp_db.detect_cycle("node_b", ["node_a"]) is None

    def test_detects_self_loop(self, temp_db):
        result = temp_db.detect_cycle("node_a", ["node_a"])
        assert result is not None
        assert "node_a" in result

    def test_detects_cycle_in_path(self, temp_db):
        path = ["node_a", "node_b", "node_c"]
        result = temp_db.detect_cycle("node_b", path)
        assert result is not None
        # Should start from node_b
        assert result[0] == "node_b"
        # Should close the cycle back to node_b
        assert result[-1] == "node_b"

    def test_no_cycle_new_node(self, temp_db):
        path = ["node_a", "node_b", "node_c"]
        assert temp_db.detect_cycle("node_d", path) is None


class TestJourney:
    def test_create_journey_cycle(self, temp_db):
        n1 = _make_node(temp_db, "com.app", "A", "h1")
        n2 = _make_node(temp_db, "com.app", "B", "h2")
        e1 = _make_edge(temp_db, n1, n2)
        e2 = _make_edge(temp_db, n2, n1)

        journey_id = temp_db.create_journey(
            app_package="com.app",
            start_node_id=n1,
            end_node_id=n1,
            path_edges=[e1, e2],
            journey_type="cycle",
        )
        assert journey_id.startswith("journey_")

    def test_graph_stats_count_cycles(self, temp_db):
        n1 = _make_node(temp_db, "com.app", "A", "h1")
        n2 = _make_node(temp_db, "com.app", "B", "h2")
        e1 = _make_edge(temp_db, n1, n2)
        e2 = _make_edge(temp_db, n2, n1)

        temp_db.create_journey(
            app_package="com.app",
            start_node_id=n1,
            end_node_id=n1,
            path_edges=[e1, e2],
            journey_type="cycle",
        )

        stats = temp_db.get_app_graph_stats("com.app")
        assert stats["node_count"] == 2
        assert stats["valid_edge_count"] == 2
        assert stats["cycle_count"] == 1


# ---------------------------------------------------------------------------
# Crawler-level cycle detection (no Appium required)
# ---------------------------------------------------------------------------

class _FakeCrawler:
    """Minimal stand-in for AppCrawler that exercises _detect_journey_cycle."""

    def __init__(self, db: CrawlerDatabase):
        self.db = db
        self.app_package = "com.test"
        self.current_node_id = None
        self.current_journey_path = []
        self.current_edge_path = []

        # Attach logger stub
        import logging
        self.logger = logging.getLogger("fake_crawler")

    # Pull the real implementation in without importing the full AppCrawler
    # (which would require Appium dependencies to be importable).
    from app_crawler.crawler import AppCrawler as _real
    _detect_journey_cycle = _real._detect_journey_cycle


class TestCrawlerCycleDetection:
    """Unit tests for AppCrawler._detect_journey_cycle using a lightweight stub."""

    @pytest.fixture
    def crawler(self, temp_db):
        return _FakeCrawler(temp_db)

    def _node(self, db, suffix):
        return _make_node(db, "com.test", f"Screen{suffix}", f"hash_{suffix}")

    def test_no_cycle_empty_path(self, crawler):
        crawler.current_node_id = "node_a"
        crawler.current_journey_path = []
        assert crawler._detect_journey_cycle("node_b") is None

    def test_no_cycle_target_not_in_path(self, crawler, temp_db):
        n1 = self._node(temp_db, "1")
        n2 = self._node(temp_db, "2")
        n3 = self._node(temp_db, "3")
        crawler.current_node_id = n2
        crawler.current_journey_path = [n1, n2]
        assert crawler._detect_journey_cycle(n3) is None

    def test_detects_cycle_to_earlier_node(self, crawler, temp_db):
        n1 = self._node(temp_db, "1")
        n2 = self._node(temp_db, "2")
        e1 = _make_edge(temp_db, n1, n2)
        crawler.current_node_id = n2
        crawler.current_journey_path = [n1, n2]
        crawler.current_edge_path = [e1]

        result = crawler._detect_journey_cycle(n1)  # navigating back to n1 = cycle
        assert result is not None
        assert result.startswith("journey_")

    def test_cycle_resets_journey_path(self, crawler, temp_db):
        n1 = self._node(temp_db, "1")
        n2 = self._node(temp_db, "2")
        e1 = _make_edge(temp_db, n1, n2)
        crawler.current_node_id = n2
        crawler.current_journey_path = [n1, n2]
        crawler.current_edge_path = [e1]

        crawler._detect_journey_cycle(n1)

        # After detection the path must be reset to contain only current_node_id
        assert crawler.current_journey_path == [n2]
        assert crawler.current_edge_path == []

    def test_no_false_cycle_current_node_first_visit(self, crawler, temp_db):
        """current_node_id should not trigger a false cycle on its first visit."""
        n1 = self._node(temp_db, "1")
        crawler.current_node_id = n1
        crawler.current_journey_path = [n1]
        # No target provided → check current_node against path[:-1] (empty) → no cycle
        assert crawler._detect_journey_cycle() is None

    def test_no_false_cycle_two_node_path(self, crawler, temp_db):
        """Being at node n2 with path [n1, n2] must not produce a spurious cycle."""
        n1 = self._node(temp_db, "1")
        n2 = self._node(temp_db, "2")
        e1 = _make_edge(temp_db, n1, n2)
        crawler.current_node_id = n2
        crawler.current_journey_path = [n1, n2]
        crawler.current_edge_path = [e1]
        # No target provided → check n2 against [n1] → not present → no cycle
        assert crawler._detect_journey_cycle() is None
