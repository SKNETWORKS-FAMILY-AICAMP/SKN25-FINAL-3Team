import fitz  # PyMuPDF 라이브러리
import os
import glob

# 1. 현재 파이썬 파일이 있는 폴더에서 확장자가 .pdf인 모든 파일을 찾습니다.
pdf_files = glob.glob("*.pdf")

if not pdf_files:
    print("현재 폴더에 PDF 파일이 없습니다. PDF 파일들이 이 파이썬 파일과 같은 폴더에 있는지 확인해주세요!")
else:
    print(f"총 {len(pdf_files)}개의 PDF 파일을 찾았습니다. 텍스트 변환을 시작합니다...\n")

    # 2. 찾은 PDF 파일들을 하나씩 꺼내서 작업합니다.
    for pdf_path in pdf_files:
        # 새로운 텍스트 파일 이름 만들기 (예: 특허01.pdf -> 특허01.txt)
        txt_path = pdf_path.replace(".pdf", ".txt")
        
        try:
            # PDF 열기
            doc = fitz.open(pdf_path)
            all_text = ""
            
            # 문서의 처음부터 끝 페이지까지 돌면서 글자 긁어오기
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                # 페이지별 텍스트를 추출해서 all_text 변수에 차곡차곡 더합니다.
                all_text += page.get_text()
                all_text += "\n\n--- [페이지 구분] ---\n\n" # 페이지가 넘어갈 때 보기 좋게 구분선 추가
            
            # 3. 다 모은 텍스트를 txt 파일로 저장하기 (한글이 안 깨지도록 utf-8 인코딩 적용)
            with open(txt_path, "w", encoding="utf-8-sig") as f:
                f.write(all_text)
                
            print(f"✅ 성공: {pdf_path} 파일을 {txt_path}로 변환했습니다.")
            
        except Exception as e:
            print(f"❌ 에러 발생: {pdf_path} 처리 중 문제 발생 ({e})")
            
    print("\n🎉 모든 변환 작업이 완료되었습니다! VS Code 좌측 탐색기에서 새로 생긴 txt 파일들을 확인해 보세요.")