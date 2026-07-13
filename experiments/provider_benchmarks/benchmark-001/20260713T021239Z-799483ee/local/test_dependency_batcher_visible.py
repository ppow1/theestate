import copy, unittest
from dependency_batcher import plan_batches, DependencyBatchError
class DependencyBatcherTests(unittest.TestCase):
    def test_success_order_and_immutability(self):
        tasks=[{"id":"a","duration":5,"priority":1,"depends_on":[]},{"id":"b","duration":1,"priority":3,"depends_on":["a"]},{"id":"c","duration":1,"priority":3,"depends_on":["a"]},{"id":"d","duration":2,"priority":2,"depends_on":[]}]
        original=copy.deepcopy(tasks); self.assertEqual(plan_batches(tasks,2), [["d","a"],["b","c"]]); self.assertEqual(tasks, original)
    def test_rejects_invalid(self):
        bad=[([{"id":"a","duration":True,"priority":1,"depends_on":[]}],1),([{"id":"a","duration":1,"priority":1,"depends_on":["z"]}],1),([{"id":"a","duration":1,"priority":1,"depends_on":["a"]}],1),([{"id":"a","duration":1,"priority":1,"depends_on":["b"]},{"id":"b","duration":1,"priority":1,"depends_on":["a"]}],1)]
        for tasks, mp in bad:
            with self.assertRaises(DependencyBatchError): plan_batches(tasks,mp)
    def test_deterministic(self):
        tasks=[{"id":x,"duration":1,"priority":1,"depends_on":[]} for x in ["b","a","c"]]; self.assertEqual(plan_batches(tasks,10), [["a","b","c"]])
if __name__ == "__main__": unittest.main()
