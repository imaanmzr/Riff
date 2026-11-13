import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'planning/tests'))
from gates import validate, ready
import test_validate

class ExecutionTests(unittest.TestCase):
    def setup_run(self):
        p=test_validate.GateTests().plan()
        r=dict(authorized=True,plan_revision=1,base_revision='abc',status='running',tasks={'T1':{'state':'pending'}})
        return p,r
    def complete(self):
        p,r=self.setup_run()
        check=dict(revision='candidate',command='test',exit_code=0,evidence='test.log')
        reviews=[dict(kind=k,revision='candidate',reviewer='review-agent',independent=True,verdict='pass',evidence='review.md') for k in ('spec','quality')]
        r['tasks']['T1']=dict(state='integrated',agent='implementer',candidate_revision='candidate',integration_revision='merged',checks=[check],reviews=reviews)
        r.update(status='complete',head_revision='merged',integration_owner='integrator',final=dict(requirements=['R1'],checks=[dict(check,revision='merged')],reviews=[dict(reviews[0],kind='integration',revision='merged')]))
        return p,r
    def test_ready(self):
        p,r=self.setup_run(); self.assertEqual(['T1'],ready(p,r))
    def test_complete(self): self.assertEqual([],validate(*self.complete()))
    def test_no_authorization(self):
        p,r=self.setup_run(); r['authorized']=False; self.assertTrue(validate(p,r)); self.assertEqual([],ready(p,r))
    def test_stale_plan(self):
        p,r=self.setup_run(); r['plan_revision']=2; self.assertTrue(validate(p,r))
    def test_unfinished(self):
        p,r=self.setup_run(); r['status']='complete'; self.assertTrue(validate(p,r))
    def test_failed_check(self):
        p,r=self.complete(); r['tasks']['T1']['checks'][0]['exit_code']=1; self.assertTrue(validate(p,r))
    def test_changed_candidate(self):
        p,r=self.complete(); r['tasks']['T1']['candidate_revision']='new'; self.assertTrue(validate(p,r))
    def test_self_review(self):
        p,r=self.complete(); r['tasks']['T1']['reviews'][0]['reviewer']='implementer'; self.assertTrue(validate(p,r))
    def test_stale_final(self):
        p,r=self.complete(); r['head_revision']='new'; self.assertTrue(validate(p,r))
    def test_dependency(self):
        p,r=self.setup_run(); p['tasks'].append(dict(p['tasks'][0],id='T2',dependencies=['T1'])); r['tasks']['T2']=dict(state='running',agent='second'); self.assertTrue(validate(p,r))
    def test_missing_final_coverage(self):
        p,r=self.complete(); r['final']['requirements']=[]; self.assertTrue(validate(p,r))
    def test_critical_audit(self):
        p,r=self.complete(); p['route']='critical'; self.assertTrue(validate(p,r))

if __name__=='__main__': unittest.main()
