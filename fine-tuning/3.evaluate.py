import json
import numpy as np
import sys
import os
import re
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score

# ==========================================
# 🚨 [강제 설정] 시스템 기본 인코딩 고정
# ==========================================
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
os.environ["PYTHONIOENCODING"] = "utf-8"

def calculate_jaccard(preds, targets):
    set_pred = set(preds)
    set_target = set(targets)
    
    if not set_pred and not set_target:
        return None
        
    intersection = len(set_pred.intersection(set_target))
    union = len(set_pred.union(set_target))
    
    return intersection / union

# ==========================================
# 🛠️ [궁극의 파싱 무기] 정규식(Regex) 데이터 구조대
# ==========================================
def salvage_via_regex(text):
    """
    JSON 문법이 완전히 박살난 텍스트에서도
    정규식을 이용해 is_approved 값과 claims 배열의 숫자들만 무력으로 뜯어옵니다.
    """
    # 1. is_approved 추출 (따옴표 유무, 띄어쓰기 무시)
    is_app_match = re.search(r'\"?is_approved\"?\s*:\s*(true|false)', text, re.IGNORECASE)
    is_app = False
    if is_app_match:
        is_app = (is_app_match.group(1).lower() == 'true')
        
    # 2. claims 배열 추출 ("claims": [1, 2, 3] 형태 탐색)
    claims_matches = re.findall(r'\"?claims\"?\s*:\s*\[(.*?)\]', text)
    rejections = []
    for match_str in claims_matches:
        # 괄호 안의 문자열에서 숫자만 쏙쏙 빼서 리스트로 만듦
        nums = re.findall(r'\d+', match_str)
        if nums:
            claims_list = [int(n) for n in nums]
            rejections.append({"claims": claims_list})
            
    return {"is_approved": is_app, "rejections": rejections}

def extract_payload(text):
    """
    1차: 깔끔한 JSON 파싱 시도 (중첩된 examiner_result 껍데기 자동 해제)
    2차: 실패 시 Regex 구조대 투입
    """
    if not isinstance(text, str):
        text = str(text)
        
    text = text.replace('```json', '').replace('```', '').strip()
    
    start_idx = text.find('{')
    if start_idx != -1:
        decoder = json.JSONDecoder()
        try:
            obj, _ = decoder.raw_decode(text[start_idx:])
            
            # [핵심] 모델이 "examiner_result" 껍데기를 여러 번 씌운 경우(마트료시카) 벗겨냄
            while isinstance(obj, dict) and "examiner_result" in obj:
                obj = obj["examiner_result"]
                
            if isinstance(obj, bool):
                return {"is_approved": obj, "rejections": []}
                
            is_app = obj.get("is_approved", False)
            rejs = obj.get("rejections", [])
            return {"is_approved": is_app, "rejections": rejs}
            
        except (json.JSONDecodeError, AttributeError):
            pass # 파싱 실패 시 아래의 구조대 로직으로 넘어감

    # JSON 파싱에 실패했거나 '{'가 아예 없는 경우 Regex 구조대 호출
    return salvage_via_regex(text)


def evaluate_predictions(val_file_path, pred_file_path):
    with open(val_file_path, "r", encoding="utf-8-sig") as f:
        targets = [json.loads(line) for line in f if line.strip()]
        
    with open(pred_file_path, "r", encoding="utf-8-sig") as f:
        predictions = [json.loads(line) for line in f if line.strip()]
        
    if len(targets) != len(predictions):
        raise ValueError(f"데이터 개수 불일치! 정답: {len(targets)}항, 예측: {len(predictions)}항")

    y_true_approved = []
    y_pred_approved = []
    jaccard_scores = []
    
    success_count = 0
    salvaged_count = 0

    for idx, (target_raw, pred_raw) in enumerate(zip(targets, predictions)):
        try:
            # [정답 처리]
            if "messages" in target_raw:
                target_res = extract_payload(target_raw["messages"][-1]["content"])
            else:
                target_res = extract_payload(str(target_raw))
            
            # [예측 처리]
            pred_text = pred_raw["messages"][-1]["content"] if "messages" in pred_raw else str(pred_raw)
            pred_res = extract_payload(pred_text)
            
            # (통계용) 정규식으로 구조된 데이터인지 확인
            if "Unterminated" in pred_text or pred_text.count('{') != pred_text.count('}'):
                 # 완벽하진 않지만 대략적인 문법 파괴 데이터 카운팅
                 salvaged_count += 1
                
            true_app = 1 if target_res.get("is_approved", False) else 0
            pred_app = 1 if pred_res.get("is_approved", False) else 0
            
            y_true_approved.append(true_app)
            y_pred_approved.append(pred_app)

            # 거절 케이스 자카드 점수 계산
            if true_app == 0:
                true_claims = []
                for rej in target_res.get("rejections", []):
                    if isinstance(rej, dict): 
                        true_claims.extend(rej.get("claims", []))
                    
                pred_claims = []
                for rej in pred_res.get("rejections", []):
                    if isinstance(rej, dict): 
                        pred_claims.extend(rej.get("claims", []))

                true_claims = list(set(true_claims))
                pred_claims = list(set(pred_claims))

                jaccard = calculate_jaccard(pred_claims, true_claims)
                if jaccard is not None:
                    jaccard_scores.append(jaccard)
                    
            success_count += 1
            
        except Exception as e:
            print(f"[경고] {idx}번째 라인 알 수 없는 에러 발생. (스킵됨) | 사유: {e}")
            continue

    print("\n" + "=" * 50)
    print("              [ 특허 심사 모델 검증 리포트 ]")
    print("=" * 50)
    print(f"✅ 총 {len(targets)}건 중 {success_count}건 채점 완료")
    print(f"🛠️ (참고) 문법이 깨져서 정규식(Regex)으로 강제 복구한 데이터: 약 {salvaged_count}건 예상\n")
    
    if success_count == 0:
        print("파싱에 성공한 데이터가 없습니다.")
        return

    print("1. 등록/거절 여부 (is_approved) 이진 분류 성능")
    print("-" * 50)
    print(f"정확도 (Precision) : {precision_score(y_true_approved, y_pred_approved, average='macro', zero_division=0):.4f}")
    print(f"재현율 (Recall)    : {recall_score(y_true_approved, y_pred_approved, average='macro', zero_division=0):.4f}")
    print(f"F1-Score (Macro)   : {f1_score(y_true_approved, y_pred_approved, average='macro', zero_division=0):.4f}")
    
    print(f"\n2. 거절 청구항 매칭 정확도 (유효한 거절 정답 {len(jaccard_scores)}건 기준)")
    print("-" * 50)
    if len(jaccard_scores) > 0:
        print(f"평균 자카드 유사도 (Mean Jaccard) : {np.mean(jaccard_scores):.4f}")
        print(f"완벽 매칭 비율 (Exact Match Rate) : {np.mean([1.0 if x == 1.0 else 0.0 for x in jaccard_scores]) * 100:.2f}%")
    else:
        print("평가할 유효한 거절 케이스가 없습니다.")
    print("=" * 50)

if __name__ == "__main__":
    VAL_FILE = "final_ft_test.jsonl"      
    PRED_FILE = "test_predictions.jsonl"  
    
    evaluate_predictions(VAL_FILE, PRED_FILE)