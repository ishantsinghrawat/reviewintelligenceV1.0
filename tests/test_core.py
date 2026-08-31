import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from common import sentiment_from_rating,confidence_band
from analyze import classify
class T(unittest.TestCase):
 def test_sentiment(self): self.assertEqual(sentiment_from_rating(5),'Positive');self.assertEqual(sentiment_from_rating(1),'Negative')
 def test_conf(self): self.assertEqual(confidence_band(.8),'High')
 def test_aspects(self):
  tax={'keywords':{'Wait Time':['wait'],'Service':['service']}};cats={x['category'] for x in classify('long wait and slow service',tax)};self.assertIn('Wait Time',cats);self.assertIn('Service',cats)
if __name__=='__main__':unittest.main()
