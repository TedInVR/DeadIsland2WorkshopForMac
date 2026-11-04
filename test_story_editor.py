"""Regression containment: a story reset must never reach an exporter."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import story_editor as story
from save_core import Save,FormatError
class StorySuspensionTests(unittest.TestCase):
    def test_unavailable_even_for_an_unknown_or_empty_save(self):
        for save in (None,SimpleNamespace(b=b'original')):
            result=story.info(save)
            self.assertFalse(result['available']);self.assertIn('New Game',result['reason'])
    def test_any_nonempty_reset_fails_before_reading_or_editing(self):
        for requests in ([{'target':'example'}],[{'target':'example','reference':'other'}],[{}]):
            with self.assertRaisesRegex(story.StoryError,'temporarily unavailable'):story.apply(None,requests)
    def test_no_reset_preserves_input(self):
        s=SimpleNamespace(b=b'original bytes');self.assertEqual(story.apply(s,[]),s.b)
    def test_save_rebuild_blocks_resets_before_any_other_edit(self):
        s=Save.__new__(Save)
        with patch.object(story,'apply',side_effect=AssertionError('reset writer called')):
            with self.assertRaisesRegex(FormatError,'temporarily unavailable'):
                s.rebuild({'invalid':'invalid'},story_resets=[{'target':'example'}])
if __name__=='__main__':unittest.main()
