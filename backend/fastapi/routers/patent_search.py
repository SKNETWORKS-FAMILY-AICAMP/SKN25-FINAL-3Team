from fastapi import APIRouter, Query, HTTPException
import os, urllib.parse, requests, xmltodict

router = APIRouter()

@router.get("/patent-search")
def search_patents(query: str = Query(...)):
    service_key = os.getenv("KIPRIS_API_KEY")
    encoded = urllib.parse.quote(query)
    url = f"http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch?word={encoded}&ServiceKey={service_key}&numOfRows=15"

    res = requests.get(url, timeout=10)
    data = xmltodict.parse(res.text)

    response = data.get("response", {})
    body = response.get("body")

    if not body:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "KIPRIS 응답에 body가 없습니다.",
                "kipris_response": data,
            },
        )

    items = body.get("items", {}).get("item", [])

    if not items:
        return []

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