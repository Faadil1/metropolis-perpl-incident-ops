from pathlib import Path
from html.parser import HTMLParser

class StructureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack=[]
        self.opened_inside_lab=[]
        self.lab_open=False
        self.lab_closed=False
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=="details" and attrs.get("id")=="researchLab":
            self.lab_open=True
        if attrs.get("id") in ("create","frame","ingest","negativeReview"):
            self.opened_inside_lab.append((attrs.get("id"),self.lab_open and not self.lab_closed))
    def handle_endtag(self,tag):
        if tag=="details" and self.lab_open:
            self.lab_closed=True

def test_live_negative_review_first_and_manual_lab_secondary():
    html=(Path(__file__).resolve().parent.parent/"operator.html").read_text(encoding="utf-8")
    assert html.index('id="negativeReview"') < html.index('id="researchLab"')
    assert "MANUAL_UNVERIFIED" in html
    parser=StructureParser()
    parser.feed(html)
    assert ("negativeReview",False) in parser.opened_inside_lab
    assert ("create",True) in parser.opened_inside_lab
    assert ("frame",True) in parser.opened_inside_lab
    assert parser.lab_closed
