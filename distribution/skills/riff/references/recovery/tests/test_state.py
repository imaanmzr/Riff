import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from state import checkpoint, save, load, reconcile, fingerprint

class RecoveryTests(unittest.TestCase):
    def sample(self):
        return checkpoint({'revision':1,'tasks':[{'id':'A'},{'id':'B','dependencies':['A']}]},
          {'status':'running','tasks':{'A':{'state':'integrated','reviews':[{'verdict':'pass'}]},'B':{'state':'running'}}}, {'src':'hash'})
    def test_atomic_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'; saved=save(p,self.sample(),0)
            self.assertEqual(saved,load(p)); self.assertEqual(1,saved['generation'])
    def test_stale_writer(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state'; save(p,self.sample(),0)
            with self.assertRaises(ValueError): save(p,self.sample(),0)
            self.assertEqual(1,load(p)['generation'])
    def test_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state'; save(p,self.sample(),0)
            data=json.loads(p.read_text()); data['payload']['generation']=8; p.write_text(json.dumps(data))
            with self.assertRaises(ValueError): load(p)
    def test_failed_replace_preserves_previous(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state'; save(p,self.sample(),0)
            with patch('state.os.replace',side_effect=OSError('interrupted')):
                with self.assertRaises(OSError): save(p,self.sample(),1)
            self.assertEqual(1,load(p)['generation'])
    def test_interrupted(self):
        s=self.sample(); r=reconcile(s,s['plan'],s['manifest'])
        self.assertEqual('integrated',r['run']['tasks']['A']['state'])
        self.assertEqual('blocked',r['run']['tasks']['B']['state'])
        self.assertEqual('running',s['run']['tasks']['B']['state'])
    def test_plan_edit_without_bump(self):
        s=self.sample(); p=dict(s['plan'],description='changed')
        r=reconcile(s,p,s['manifest']); self.assertTrue(r['recovery']['plan_changed'])
        self.assertEqual('blocked',r['run']['tasks']['A']['state'])
    def test_source_drift(self):
        s=self.sample(); r=reconcile(s,s['plan'],{'src':'new'})
        self.assertEqual([],r['run']['tasks']['A']['reviews'])
        self.assertTrue(r['history']); self.assertEqual('blocked',r['run']['status'])
    def test_unchanged_completed(self):
        s=self.sample(); s['run']['tasks']['B']['state']='integrated'; s['run']['status']='complete'
        r=reconcile(s,s['plan'],s['manifest']); self.assertEqual('complete',r['run']['status'])
    def test_added_file(self):
        s=self.sample(); self.assertIn('new',reconcile(s,s['plan'],{'src':'hash','new':'x'})['recovery']['changed_files'])
    def test_deleted_file(self):
        s=self.sample(); self.assertIn('src',reconcile(s,s['plan'],{})['recovery']['changed_files'])
    def test_task_set_change(self):
        s=self.sample(); r=reconcile(s,{'tasks':[{'id':'C'}]},s['manifest'])
        self.assertEqual(['C'],r['recovery']['added_tasks']); self.assertEqual(['A','B'],r['recovery']['removed_tasks'])
    def test_fingerprints_and_escape(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'src'; p.write_text('old'); a=fingerprint(d,['src','absent'])
            p.write_text('new'); self.assertNotEqual(a,fingerprint(d,['src','absent']))
            with self.assertRaises(ValueError): fingerprint(d,['../outside'])
            (Path(d)/'link').symlink_to(p)
            with self.assertRaises(ValueError): fingerprint(d,['link'])

if __name__=='__main__': unittest.main()
