import os
import shutil
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from app.repositories.document.filesystem_document_repository import FilesystemDocumentRepository
from app.schemas.document.document_index_entry import DocumentIndexEntry

class TestDocumentRepository(unittest.TestCase):
    """Unit and concurrency tests for FilesystemDocumentRepository."""

    def setUp(self):
        # Create a temp directory for index.json to isolate tests
        self.test_dir = tempfile.mkdtemp()
        self.index_path = os.path.join(self.test_dir, "index.json")
        self.repo = FilesystemDocumentRepository(index_path=self.index_path)

    def tearDown(self):
        # Clean up temp files
        shutil.rmtree(self.test_dir)

    def test_save_and_retrieve_metadata(self):
        """Assert saving and getting index entries works correctly."""
        entry = DocumentIndexEntry(
            document_id="doc123",
            original_filename="resume.pdf",
            stored_filename="stored123.pdf",
            file_size=2048,
            uploaded_at=datetime.now(timezone.utc)
        )
        self.repo.save(entry)

        retrieved = self.repo.get("doc123")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.document_id, "doc123")
        self.assertEqual(retrieved.original_filename, "resume.pdf")
        self.assertEqual(retrieved.stored_filename, "stored123.pdf")
        self.assertEqual(retrieved.file_size, 2048)
        self.assertAlmostEqual(
            retrieved.uploaded_at.timestamp(),
            entry.uploaded_at.timestamp(),
            places=1
        )

    def test_missing_document_returns_none(self):
        """Assert looking up a non-existent document ID returns None."""
        retrieved = self.repo.get("non-existent-id")
        self.assertIsNone(retrieved)

    def test_duplicate_overwrite_behavior(self):
        """Assert saving an entry with an existing document_id updates it."""
        entry1 = DocumentIndexEntry(
            document_id="doc_id",
            original_filename="first.pdf",
            stored_filename="first_stored.pdf",
            file_size=10,
            uploaded_at=datetime.now(timezone.utc)
        )
        entry2 = DocumentIndexEntry(
            document_id="doc_id",
            original_filename="second.pdf",
            stored_filename="second_stored.pdf",
            file_size=20,
            uploaded_at=datetime.now(timezone.utc)
        )

        self.repo.save(entry1)
        self.repo.save(entry2)

        retrieved = self.repo.get("doc_id")
        self.assertEqual(retrieved.original_filename, "second.pdf")
        self.assertEqual(retrieved.file_size, 20)

    def test_corrupted_index_file_recovery(self):
        """Assert repository automatically recovers when loading corrupted/malformed JSON index."""
        # Write corrupted JSON to the file path
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, 'w') as f:
            f.write("{invalid: json, corrupted content}")

        # Loading should not crash, it should return None on query
        retrieved = self.repo.get("some_id")
        self.assertIsNone(retrieved)

        # Saving should succeed and overwrite the corrupted index file safely
        entry = DocumentIndexEntry(
            document_id="doc_new",
            original_filename="new.pdf",
            stored_filename="new_stored.pdf",
            file_size=100,
            uploaded_at=datetime.now(timezone.utc)
        )
        self.repo.save(entry)

        retrieved_after_save = self.repo.get("doc_new")
        self.assertEqual(retrieved_after_save.original_filename, "new.pdf")

    def test_thread_safety_concurrency(self):
        """Assert that multiple threads can concurrently call save and get without crashes or state corruption."""
        num_threads = 10
        threads = []
        errors = []

        def worker(thread_idx):
            try:
                doc_id = f"thread_doc_{thread_idx}"
                entry = DocumentIndexEntry(
                    document_id=doc_id,
                    original_filename=f"file_{thread_idx}.pdf",
                    stored_filename=f"stored_{thread_idx}.pdf",
                    file_size=thread_idx * 100,
                    uploaded_at=datetime.now(timezone.utc)
                )
                # Concurrently save and get
                self.repo.save(entry)
                retrieved = self.repo.get(doc_id)
                if retrieved.file_size != thread_idx * 100:
                    errors.append(f"Mismatched retrieved file size for thread {thread_idx}")
            except Exception as e:
                errors.append(f"Thread {thread_idx} raised exception: {str(e)}")

        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrency test errors: {errors}")
