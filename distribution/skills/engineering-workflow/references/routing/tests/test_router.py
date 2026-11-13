import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'planning/tests'))
import test_validate
from router import propose

class RoutingTests(unittest.TestCase):
    def inputs(self):
        p=test_validate.GateTests().plan()
        p['tasks'][0].update(capability='coding',write_paths=['src/a'])
        p['tasks'].append(dict(p['tasks'][0],id='T2',write_paths=['src/b']))
        r=dict(authorized=True,plan_revision=1,base_revision='abc',status='running',tasks={i:dict(state='pending') for i in ('T1','T2')})
        c=dict(profiles=dict(fast='f',coding='c',deep_reasoning='d'),max_parallel=2,token_budget=100,task_token_budget=40,max_attempts=2)
        h=dict(parallel_agents=True,isolated_workspaces=True,available_slots=2,models={'f':['fast'],'c':['coding'],'d':['deep_reasoning']})
        return p,r,c,h
    def test_parallel(self): self.assertEqual(2,len(propose(*self.inputs())['assignments']))
    def test_overlap(self):
        p,r,c,h=self.inputs(); p['tasks'][1]['write_paths']=['src/a/nested']; self.assertEqual(1,len(propose(p,r,c,h)['assignments']))
    def test_unknown_scope_exclusive(self):
        p,r,c,h=self.inputs(); del p['tasks'][0]['write_paths']; self.assertEqual(1,len(propose(p,r,c,h)['assignments']))
    def test_serial_without_isolation(self):
        p,r,c,h=self.inputs(); h['isolated_workspaces']=False; self.assertEqual(1,len(propose(p,r,c,h)['assignments']))
    def test_budget(self):
        p,r,c,h=self.inputs(); r['routing']={'spent_tokens':30}; self.assertEqual(1,len(propose(p,r,c,h)['assignments']))
    def test_active_reservation(self):
        p,r,c,h=self.inputs(); r['tasks']['T1']=dict(state='running',agent='a',routing=dict(reserved_tokens=70)); self.assertEqual([],propose(p,r,c,h)['assignments'])
    def test_missing_active_accounting(self):
        p,r,c,h=self.inputs(); r['tasks']['T1']=dict(state='running',agent='a')
        with self.assertRaises(KeyError): propose(p,r,c,h)
    def test_recovery_blocked(self):
        p,r,c,h=self.inputs(); r.update(status='blocked',blockers=['reconcile']); self.assertEqual([],propose(p,r,c,h)['assignments'])
    def test_critical(self):
        p,r,c,h=self.inputs(); p['route']='critical'; self.assertEqual('d',propose(p,r,c,h)['assignments'][0]['proposed_model'])
    def test_unavailable_no_downgrade(self):
        p,r,c,h=self.inputs(); p['route']='critical'; del h['models']['d']; self.assertEqual([],propose(p,r,c,h)['assignments'])
    def test_fallback_up(self):
        p,r,c,h=self.inputs(); del h['models']['c']; self.assertEqual('d',propose(p,r,c,h)['assignments'][0]['proposed_model'])
    def test_attempt_exhaustion(self):
        p,r,c,h=self.inputs(); r['tasks']['T1']['routing']={'attempts':2}; self.assertEqual('T2',propose(p,r,c,h)['assignments'][0]['task'])
    def test_retry_escalation(self):
        p,r,c,h=self.inputs(); r['tasks']['T1']['routing']={'attempts':1}; self.assertEqual('deep_reasoning',propose(p,r,c,h)['assignments'][0]['selected_profile'])
    def test_dependency(self):
        p,r,c,h=self.inputs(); p['tasks'][1]['dependencies']=['T1']; self.assertEqual(1,len(propose(p,r,c,h)['assignments']))
    def test_bad_budget(self):
        p,r,c,h=self.inputs(); c['token_budget']=-1
        with self.assertRaises(ValueError): propose(p,r,c,h)
    def test_bad_path(self):
        p,r,c,h=self.inputs(); p['tasks'][0]['write_paths']=['../external']
        with self.assertRaises(ValueError): propose(p,r,c,h)
    def test_plan_not_ready(self):
        p,r,c,h=self.inputs(); p['status']='DRAFT'; self.assertEqual([],propose(p,r,c,h)['assignments'])
    def test_deterministic_no_mutation(self):
        import copy
        args=self.inputs(); original=copy.deepcopy(args)
        self.assertEqual(propose(*args),propose(*args)); self.assertEqual(original,args)

if __name__=='__main__': unittest.main()
