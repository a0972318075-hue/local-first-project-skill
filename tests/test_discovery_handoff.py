import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/local-first-project/scripts'))
from discovery_handoff import summarize


class DiscoveryHandoffTests(unittest.TestCase):
    def test_passes_only_allowlisted_evidence_and_recomputes_status(self):
        receipt = summarize({'schema_version': 1, 'status': 'ready', 'evidence': [
            {'source': 'path', 'status': 'not-found', 'details': ['private']},
            {'source': 'known-path', 'status': 'found', 'details': ['private']},
            {'source': 'start-menu', 'status': 'found'},
            {'source': 'start-menu', 'status': 'error'},
            {'source': 'registry:private', 'status': 'found'},
        ]})
        self.assertEqual(receipt, {'route': 'reported-evidence', 'status': 'found-unverified',
                                  'sources': {'path': 'not-found', 'known-path': 'found',
                                              'start-menu': 'found'}})

    def test_preserves_errors_and_unchecked_sources(self):
        receipt = summarize({'schema_version': 1, 'evidence': [
            {'source': 'start-menu', 'status': 'not-found'},
            {'source': 'start-menu', 'status': 'error'},
        ]})
        self.assertEqual(receipt['status'], 'unknown')
        self.assertEqual(receipt['sources'], {'path': 'unchecked', 'known-path': 'unchecked',
                                             'start-menu': 'error'})

    def test_rejects_invalid_selected_status(self):
        with self.assertRaises(ValueError):
            summarize({'schema_version': 1, 'evidence': [{'source': 'path', 'status': 'ready'}]})
