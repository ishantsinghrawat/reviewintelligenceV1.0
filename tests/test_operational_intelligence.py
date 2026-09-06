import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from analyze import rating_impact, negative_pair_patterns, positive_negative_patterns, menu_issue_links, health_score

def r(i,rating,aspects,menu=None):
    return {"review_id":str(i),"rating":rating,"sentiment":"Negative" if rating<=2 else "Positive",
            "aspects":[{"category":c,"sentiment":s} for c,s in aspects],"menu_items":menu or []}

class TestOperationalIntelligence(unittest.TestCase):
    def test_rating_impact(self):
        rows=[r(1,1,[("Wait Time","Negative")]),r(2,2,[("Wait Time","Negative")]),r(3,5,[("Taste","Positive")])]
        x=rating_impact("Wait Time",rows)
        self.assertLess(x["rating_gap"],0)
    def test_negative_pair(self):
        rows=[r(1,1,[("Service","Negative"),("Wait Time","Negative")]),r(2,2,[("Service","Negative"),("Wait Time","Negative")])]
        self.assertEqual(negative_pair_patterns(rows)[0]["reviews"],2)
    def test_tradeoff(self):
        rows=[r(1,2,[("Taste","Positive"),("Wait Time","Negative")]),r(2,2,[("Taste","Positive"),("Wait Time","Negative")])]
        self.assertEqual(positive_negative_patterns(rows)[0]["positive"],"Taste")
    def test_menu_issue(self):
        rows=[r(1,1,[("Portion Size","Negative")],["Biryani"]),r(2,2,[("Portion Size","Negative")],["Biryani"])]
        self.assertEqual(menu_issue_links(rows)[0]["top_negative_issues"][0]["category"],"Portion Size")
if __name__=="__main__": unittest.main()
