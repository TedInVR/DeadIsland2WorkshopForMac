"""Synthetic storage/schema checks; personal checkpoints never enter the repo."""
import base64,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import story_editor as story,story_points
from save_core import put
class PointStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,{'DI2_WORKSHOP_STORY_DIR':self.temp.name});self.env.start();self.header=b'example header bytes!'
        self.assertEqual(len(self.header),21)
    def tearDown(self):self.env.stop();self.temp.cleanup()
    def point(self,ng=False):return dict(version=1,header=self.header.hex(),ng=ng,pieces={},counters={},summary=[])
    def test_modes_builds_and_once_only_persistence(self):
        value=self.point();self.assertIsNone(story_points.load(self.header,False));story_points.save_once(self.header,False,value)
        self.assertEqual(story_points.load(self.header,False),value);self.assertIsNone(story_points.load(self.header,True));self.assertIsNone(story_points.load(b'other header bytes!!!',False))
        changed=dict(value,counters={'changed':1});story_points.save_once(self.header,False,changed);self.assertEqual(story_points.load(self.header,False),value)
        story_points.save_once(self.header,True,self.point(True));self.assertEqual(story_points.load(self.header,True)['ng'],True)
    def test_corrupt_checkpoint_is_rejected(self):
        story_points.save_once(self.header,False,self.point());p=story_points.path(self.header,False);raw=json.loads(p.read_text());raw['checkpoint']['counters']={'changed':1};p.write_text(json.dumps(raw))
        with self.assertRaisesRegex(story_points.PointError,'checksum'):story_points.load(self.header,False)
    def test_unknown_build_and_incomplete_checkpoint_cannot_reset(self):
        fake=SimpleNamespace(b=self.header)
        for point in (self.point(),dict(self.point(),header='00'),dict(self.point(),ng=True)):
            with self.assertRaises(ValueError):story.validate_point(fake,point,False)
    def test_no_reset_is_byte_identical_and_invalid_targets_fail(self):
        fake=SimpleNamespace(b=b'unchanged',sections=[])
        self.assertEqual(story.apply(fake,[]),fake.b)
        for requests in ({},[{}],[{'target':'missing'}],[{'target':'a','reference':'b'}]):
            with self.assertRaises(story.StoryError):story.apply(fake,requests)
    def test_mission_denominators_and_unrelated_stats_are_not_selected(self):
        keys=['MainMissionsCompleted','SideMissionsCompleted_Zone','TertiaryMissionsCompleted_Zone','MainMissionsCompleted_Total','PlayerChallenges','ZombiesKilled']
        chosen=[k for k in keys if story.COUNTER.match(k)and not k.endswith('_Total')]
        self.assertEqual(chosen,keys[:3])
    def test_missing_checkpoint_does_not_erase_campaign(self):
        fake=SimpleNamespace(b=self.header,sections=[dict(name='target',profile=dict(ng=False))])
        with patch.object(story,'ensure_points',return_value=({},{})),self.assertRaisesRegex(story.StoryError,'No saved post-tutorial'):
            story.apply(fake,[{'target':'target'}])
if __name__=='__main__':unittest.main()
