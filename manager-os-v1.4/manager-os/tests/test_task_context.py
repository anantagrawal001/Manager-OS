import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from core.task_context import retrieve_task_context, render_task_context


class TaskContextTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'history.db'
        self.config = {'conversation': {'store_path': str(self.path)}}
        self.connection = sqlite3.connect(self.path)
        self.addCleanup(self.connection.close)
        self.connection.execute('CREATE TABLE conversations ('
                                'id INTEGER PRIMARY KEY, timestamp TEXT, '
                                'role TEXT, content TEXT)')

    def save(self, role, content, timestamp='2026-01-01T10:00:00'):
        cursor = self.connection.execute('INSERT INTO conversations '
            '(timestamp, role, content) VALUES (?, ?, ?)', (timestamp, role, content))
        self.connection.commit()
        return str(cursor.lastrowid)

    def test_finds_old_user_evidence_without_recycling_assistant_claims(self):
        quote = 'My inventory team has six employees and uses barcode scanners.'
        source_id = self.save('user', quote)
        self.save('assistant', 'Your inventory team has 100 employees.')
        self.save('manager', 'You own twenty inventory warehouses.')
        for number in range(70):
            self.save('user', f'I had lunch at restaurant number {number}.')
        result = retrieve_task_context(self.config, 'Build an inventory app')
        self.assertEqual(len(result['evidence']), 1)
        self.assertEqual(result['evidence'][0]['quote'], quote)
        self.assertEqual(result['evidence'][0]['message_id'], source_id)
        self.assertEqual(result['evidence'][0]['timestamp'], '2026-01-01T10:00:00')
        self.assertNotIn('100 employees', render_task_context(result))

    def test_prefers_relevant_evidence_and_retains_explicit_standing_preferences(self):
        self.save('user', 'I worked in SQL reporting and data engineering.')
        self.save('user', 'My garden has two rose bushes.')
        self.save('user', 'I prefer concise responses and local applications.')
        result = retrieve_task_context(self.config, 'Create a resume for data roles')
        quotes = [item['quote'] for item in result['evidence']]
        self.assertIn('I worked in SQL reporting and data engineering.', quotes)
        self.assertIn('I prefer concise responses and local applications.', quotes)
        self.assertFalse(any('rose bushes' in quote for quote in quotes))

    def test_drops_credentials_instead_of_quoting_or_summarizing_them(self):
        secrets = ['My inventory API key is sk-abc123ABC123abc123',
                   'My inventory password is example-do-not-use',
                   'I use inventory Bearer abc.def.ghi',
                   'My inventory login is https://alex:secret@example.test/',
                   'My inventory token is ' + 'X4ab' * 12,
                   'My inventory private key is confidential.',
                   'My inventory token is short-test-token',
                   'My inventory access uses https://example.test/?token=short',
                   'My inventory recovery phrase is a synthetic example.']
        for secret in secrets:
            self.save('user', secret)
        self.save('user', 'My inventory database runs on SQLite.')
        result = retrieve_task_context(self.config, 'Build inventory software')
        self.assertEqual([item['quote'] for item in result['evidence']],
                         ['My inventory database runs on SQLite.'])

    def test_bounds_and_quotes_are_exact_substrings_with_deduplication(self):
        content = 'Background notes. ' * 30 + 'My inventory requires batch tracking. ' * 40
        self.save('user', content)
        for number in range(20):
            self.save('user', f'My inventory location {number} holds medicine stock. ' * 30)
        config = dict(self.config, task_context={'max_items': 3, 'max_chars': 450,
                                                'excerpt_chars': 180})
        recent = [{'role': 'user', 'content': content}]
        result = retrieve_task_context(config, 'Build inventory tracking', recent)
        self.assertLessEqual(len(result['evidence']), 3)
        self.assertLessEqual(sum(len(item['quote']) for item in result['evidence']), 450)
        sources = [row[0] for row in self.connection.execute('SELECT content FROM conversations')]
        self.assertTrue(all(any(item['quote'] in source for source in sources)
                            for item in result['evidence']))
        quotes = [item['quote'] for item in result['evidence']]
        self.assertEqual(len(quotes), len(set(quotes)))
        self.assertLessEqual(len(render_task_context(result)), 7000)

    def test_current_request_is_not_reintroduced_as_historical_evidence(self):
        request = 'My inventory must support barcode scanning.'
        self.save('user', request)
        result = retrieve_task_context(self.config, request,
                                      [{'role': 'user', 'content': request}])
        self.assertEqual(result['evidence'], [])

    def test_recent_fallback_and_missing_database_do_not_create_a_store(self):
        missing = Path(self.directory.name) / 'missing.db'
        result = retrieve_task_context({'conversation': {'store_path': str(missing)}},
            'Build an inventory app', [
                {'role': 'assistant', 'content': 'Your inventory uses Oracle.'},
                {'role': 'user', 'content': 'My inventory uses SQLite.'}])
        self.assertEqual(result['evidence'][0]['quote'], 'My inventory uses SQLite.')
        self.assertEqual(result['evidence'][0]['source'], 'recent_user_message')
        self.assertFalse(missing.exists())

    def test_conflicting_statements_remain_attributed_and_newer_evidence_ranks_first(self):
        self.save('user', 'My inventory uses PostgreSQL.', '2025-01-01')
        self.save('user', 'My inventory uses SQLite.', '2026-01-01')
        result = retrieve_task_context(self.config, 'Build inventory')
        self.assertEqual(result['evidence'][0]['quote'], 'My inventory uses SQLite.')
        self.assertEqual(len(result['evidence']), 2)
        rendered = render_task_context(result)
        self.assertIn('may be outdated', rendered)
        self.assertIn('does not authorize', rendered)

    def test_incompatible_store_and_disabled_retrieval_are_nonfatal(self):
        self.connection.execute('DROP TABLE conversations')
        self.connection.commit()
        result = retrieve_task_context(self.config, 'Build inventory')
        self.assertTrue(result['history_unavailable'])
        self.assertEqual(result['evidence'], [])
        disabled = dict(self.config, task_context={'enabled': False})
        self.assertEqual(retrieve_task_context(disabled, 'Build inventory')['evidence'], [])

    def test_long_messages_are_omitted_if_full_credential_check_would_be_unbounded(self):
        self.save('user', 'My inventory works. ' * 500 + ' password is hidden-at-end')
        result = retrieve_task_context(self.config, 'Build inventory')
        self.assertEqual(result['evidence'], [])

    def test_standing_privacy_preferences_and_task_constraints_are_retrievable(self):
        self.save('user', 'Please never share my personal address.')
        self.save('user', 'The inventory app must work without internet.')
        result = retrieve_task_context(self.config, 'Build inventory software')
        self.assertEqual({item['quote'] for item in result['evidence']},
                         {'Please never share my personal address.',
                          'The inventory app must work without internet.'})


if __name__ == '__main__':
    unittest.main()
