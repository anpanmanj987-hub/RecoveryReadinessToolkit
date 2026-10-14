import random
import unittest
from tests.helpers import base_model, edge

class GraphTests(unittest.TestCase):
    def api(self):
        try:
            from cleanroomcheck.graph import control_paths, effect_path, network_paths
        except ImportError:
            self.fail('typed authority graph is not implemented')
        return control_paths,effect_path,network_paths

    def test_azure_admin_infers_only_matching_subscriptions(self):
        paths,_,_=self.api(); m=base_model()
        result=paths(m,m['scenarios'][0])
        self.assertIn('prod-sub',result); self.assertNotIn('rec-sub',result)
        self.assertEqual(result['prod-sub'][0]['inferred'],'AZURE_GLOBAL_ADMIN')
        m['nodes'][3]['tenant']='prod-tenant'
        self.assertIn('rec-sub',paths(m,m['scenarios'][0]))

    def test_non_admin_scenario_does_not_infer_azure_role(self):
        paths,_,_=self.api(); m=base_model(); m['scenarios'][0]['azure_global_admin_tenants']=[]
        self.assertNotIn('prod-sub',paths(m,m['scenarios'][0]))

    def test_other_edge_types_never_propagate_control(self):
        paths,_,_=self.api()
        for relation in ['network_reach','depends_on','can_delete','can_disable']:
            m=base_model(); edge(m,'prod-sub','vault',relation); edge(m,'vault','rec-sub')
            with self.subTest(relation=relation):
                self.assertNotIn('vault',paths(m,m['scenarios'][0]))
                self.assertNotIn('rec-sub',paths(m,m['scenarios'][0]))

    def test_cycles_terminate_and_control_is_directed(self):
        paths,_,_=self.api(); m=base_model()
        edge(m,'prod-sub','vault'); edge(m,'vault','prod-sub'); edge(m,'vault','rec-sub')
        result=paths(m,m['scenarios'][0]); self.assertIn('rec-sub',result)
        reverse=base_model(); edge(reverse,'rec-sub','prod-sub')
        self.assertNotIn('rec-sub',paths(reverse,reverse['scenarios'][0]))

    def test_destructive_permission_is_terminal(self):
        paths,effect,_=self.api(); m=base_model()
        edge(m,'prod-sub','key','can_disable'); edge(m,'key','rec-sub')
        closure=paths(m,m['scenarios'][0])
        self.assertIsNotNone(effect(m,closure,'key',{'can_delete','can_disable'}))
        self.assertNotIn('key',closure); self.assertNotIn('rec-sub',closure)

    def test_network_path_preserves_control_prefix_but_never_escalates(self):
        paths,_,network=self.api(); m=base_model()
        edge(m,'prod-sub','vault','network_reach'); edge(m,'vault','rec-sub','network_reach')
        result=network(m,paths(m,m['scenarios'][0]))
        self.assertIn('rec-sub',result)
        self.assertEqual(result['rec-sub'][-1]['relation'],'network_reach')

    def test_500_random_graphs_against_independent_closure(self):
        paths,_,_=self.api(); rng=random.Random(8426)
        for run in range(500):
            n=rng.randint(3,18)
            m={'nodes':[{'id':str(i),'kind':'identity','provider':'generic'} for i in range(n)],'edges':[]}
            adjacency=[set() for _ in range(n)]
            for j in range(rng.randint(0,n*n)):
                source,target=rng.randrange(n),rng.randrange(n)
                relation=rng.choice(['controls','network_reach','depends_on','can_delete','can_disable'])
                m['edges'].append({'id':str(j),'source':str(source),'target':str(target),'relation':relation,'evidence':[]})
                if relation=='controls': adjacency[source].add(target)
            expected={0}
            while True:
                new=expected|{t for s in expected for t in adjacency[s]}
                if new==expected: break
                expected=new
            got=paths(m,{'compromised':['0'],'azure_global_admin_tenants':[]})
            self.assertEqual({str(i) for i in expected},set(got),msg=f'run {run}')

    def test_control_of_target_is_not_itself_a_network_connection(self):
        paths,_,network=self.api(); m=base_model(); edge(m,'prod-sub','rec-sub','controls')
        self.assertIn('rec-sub',paths(m,m['scenarios'][0]))
        self.assertNotIn('rec-sub',network(m,paths(m,m['scenarios'][0])))
