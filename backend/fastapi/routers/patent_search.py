from fastapi import APIRouter, Query
import os, urllib.parse, requests, xmltodict

router = APIRouter()

@router.get("/patent-search")
def search_patents(query: str = Query(...)):
    service_key = os.getenv("KIPRIS_API_KEY")
    encoded = urllib.parse.quote(query)
    url = f"http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch?word={encoded}&ServiceKey={service_key}&numOfRows=10"
    
    res = requests.get(url)
    data = xmltodict.parse(res.text)
    items = data['response']['body']['items']['item']
    if isinstance(items, dict):
        items = [items]
    
    return [
        {
            "title": item.get("inventionTitle", ""),
            "applicationNumber": item.get("applicationNumber", ""),
            "applicant": item.get("applicantName", ""),
            "date": item.get("applicationDate", ""),
            "abstract": item.get("astrtCont", ""),
        }
        for item in items
    ]