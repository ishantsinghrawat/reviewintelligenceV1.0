import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from analyze import local_sentiment,classify_aspects
class TestV2(unittest.TestCase):
    def setUp(self):
        cats=['Food Quality','Taste','Portion Size','Price / Value','Service','Staff Behaviour','Wait Time','Order Accuracy','Cleanliness','Ambience','Delivery / Takeout','Parking / Accessibility','Menu Availability']
        self.tax={'categories':cats,'keywords':{'Food Quality':['food','fresh','cold'],'Taste':['delicious','taste'],'Portion Size':['portion'],'Price / Value':['price','worth'],'Service':['service','server'],'Staff Behaviour':['staff','rude'],'Wait Time':['wait','slow','minutes'],'Order Accuracy':['wrong order'],'Cleanliness':['dirty','clean'],'Ambience':['vibe'],'Delivery / Takeout':['delivery'],'Parking / Accessibility':['parking'],'Menu Availability':['sold out']}}
    def test_multi_aspect(self):
        r=classify_aspects('The food was delicious but service was slow and we waited 40 minutes.',self.tax,2)
        cats=[x['category'] for x in r]
        self.assertIn('Taste',cats); self.assertIn('Service',cats); self.assertIn('Wait Time',cats)
    def test_negation(self):
        s,_=local_sentiment("The food wasn't bad at all",4)
        self.assertEqual(s,'Positive')
    def test_wait_context(self):
        r=classify_aspects('Worth the wait. The food was delicious.',self.tax,5)
        w=[x for x in r if x['category']=='Wait Time']
        if w: self.assertNotEqual(w[0]['sentiment'],'Negative')
if __name__=='__main__': unittest.main()
