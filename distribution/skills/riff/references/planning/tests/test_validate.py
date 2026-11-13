import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from validate import validate

class GateTests(unittest.TestCase):
    def plan(self):
        return dict(route='standard', status='READY', revision=1, source_revision='abc',
            requirements=['R1'], tasks=[dict(id='T1', dependencies=[], requirements=['R1'],
            **{k:'specified' for k in ('objective','inputs','scope','outputs','owner','capability','reviewer','verification')})],
            reviews=[dict(revision=1,source_revision='abc',verdict='pass',reviewer='other-session',independent=True)])
    def test_valid(self): self.assertEqual([], validate(self.plan()))
    def test_cycle(self):
        p=self.plan(); p['tasks'][0]['dependencies']=['T1']; self.assertTrue(validate(p))
    def test_unknown_dependency(self):
        p=self.plan(); p['tasks'][0]['dependencies']=['T2']; self.assertTrue(validate(p))
    def test_uncovered(self):
        p=self.plan(); p['requirements'].append('R2'); self.assertTrue(validate(p))
    def test_stale(self):
        p=self.plan(); p['source_revision']='def'; self.assertTrue(validate(p))
    def test_self_review(self):
        p=self.plan(); p['reviews'][0]['independent']=False; self.assertTrue(validate(p))
    def test_blocker(self):
        p=self.plan(); p['blockers']=['unknown provider semantics']; self.assertTrue(validate(p))
    def test_missing_check(self):
        p=self.plan(); del p['tasks'][0]['verification']; self.assertTrue(validate(p))

if __name__ == '__main__': unittest.main()
