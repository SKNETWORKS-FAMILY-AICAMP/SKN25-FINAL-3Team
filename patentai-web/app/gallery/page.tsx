'use client'

import { useState } from 'react'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

const drawings = [
  { id: 'sample_block',       file: '/drawings/sample_block.svg',       title: '이미지 분류 시스템',             type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '딥러닝 기반 이미지 분류 시스템 전체 구성도.',                      grade: 'A', score: 100 },
  { id: 'sample_flow',        file: '/drawings/sample_flow.svg',        title: '이미지 분류 처리 흐름도',         type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '이미지 분류 방법의 단계별 처리 흐름.',                           grade: 'A', score: 95  },
  { id: 'patent_block',       file: '/drawings/patent_block.svg',       title: '문장 제공 장치 구성도',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '사용자 입력 기반 문장 제공 장치 블록도.',                        grade: 'A', score: 90  },
  { id: 'patent_flow',        file: '/drawings/patent_flow.svg',        title: '문장 제공 방법 흐름도',          type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '사용자 입력 기반 문장 제공 방법 순서도.',                        grade: 'B', score: 85  },
  { id: 'ai_block',           file: '/drawings/ai_block.svg',           title: 'AI 시스템 구성도',              type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 시스템 전체 구성 블록도.',                             grade: 'A', score: 100 },
  { id: 'ai_flow',            file: '/drawings/ai_flow.svg',            title: 'AI 처리 흐름도',               type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: 'AI 시스템 데이터 처리 흐름.',                                 grade: 'A', score: 100 },
  { id: 'rag_block',          file: '/drawings/rag_block.svg',          title: 'RAG 시스템 구성도',             type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'RAG 기반 검색 증강 생성 시스템 구성도.',                        grade: 'A', score: 100 },
  { id: 'rag_flow',           file: '/drawings/rag_flow.svg',           title: 'RAG 처리 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: 'RAG 시스템 질의 처리 흐름.',                                  grade: 'A', score: 100 },
  { id: 'medical_block',      file: '/drawings/medical_block.svg',      title: '의료 영상 진단 시스템',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 의료 영상 진단 보조 시스템 구성도.',                     grade: 'A', score: 100 },
  { id: 'medical_flow',       file: '/drawings/medical_flow.svg',       title: '의료 진단 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: 'AI 기반 의료 진단 프로세스 흐름.',                             grade: 'A', score: 100 },
  { id: 'iot_block',          file: '/drawings/iot_block.svg',          title: '스마트 공장 모니터링',           type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'IoT 기반 스마트 공장 모니터링 시스템 구성도.',                   grade: 'A', score: 100 },
  { id: 'iot_flow',           file: '/drawings/iot_flow.svg',           title: '설비 모니터링 흐름도',           type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: 'IoT 설비 모니터링 프로세스 흐름.',                             grade: 'A', score: 100 },
  { id: 'nlp_block',          file: '/drawings/nlp_block.svg',          title: '법률 문서 분석 시스템',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '자연어 처리 기반 법률 문서 분석 시스템.',                        grade: 'A', score: 100 },
  { id: 'nlp_flow',           file: '/drawings/nlp_flow.svg',           title: '문서 분석 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '법률 문서 분석 프로세스 흐름.',                                grade: 'A', score: 100 },
  { id: 'autonomous_block',   file: '/drawings/autonomous_block.svg',   title: '자율주행 감지 시스템',           type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '자율주행 장애물 감지 및 경로 계획 시스템.',                      grade: 'A', score: 100 },
  { id: 'autonomous_flow',    file: '/drawings/autonomous_flow.svg',    title: '자율주행 경로 흐름도',           type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '장애물 감지 및 경로 계획 프로세스.',                            grade: 'A', score: 100 },
  { id: 'smarthome_block',    file: '/drawings/smarthome_block.svg',    title: '스마트홈 에너지 관리',           type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'IoT 기반 스마트홈 에너지 관리 시스템.',                         grade: 'A', score: 100 },
  { id: 'smarthome_flow',     file: '/drawings/smarthome_flow.svg',     title: '에너지 관리 흐름도',            type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '스마트홈 에너지 관리 프로세스.',                               grade: 'A', score: 100 },
  { id: 'fintech_block',      file: '/drawings/fintech_block.svg',      title: '금융 사기 탐지 시스템',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 실시간 금융 사기 탐지 시스템.',                         grade: 'A', score: 100 },
  { id: 'fintech_flow',       file: '/drawings/fintech_flow.svg',       title: '사기 탐지 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '금융 사기 탐지 프로세스 흐름.',                               grade: 'A', score: 100 },
  { id: 'wearable_block',     file: '/drawings/wearable_block.svg',     title: '웨어러블 건강 모니터링',         type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '웨어러블 기기 기반 실시간 건강 모니터링 시스템.',                 grade: 'A', score: 100 },
  { id: 'wearable_flow',      file: '/drawings/wearable_flow.svg',      title: '건강 모니터링 흐름도',           type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '웨어러블 건강 모니터링 프로세스.',                             grade: 'A', score: 100 },
  { id: 'robot_block',        file: '/drawings/robot_block.svg',        title: '협동 로봇 제어 시스템',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '협동 로봇 작업 자동화 제어 시스템.',                            grade: 'A', score: 100 },
  { id: 'robot_flow',         file: '/drawings/robot_flow.svg',         title: '로봇 작업 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '협동 로봇 작업 자동화 프로세스.',                              grade: 'A', score: 100 },
  { id: 'blockchain_block',   file: '/drawings/blockchain_block.svg',   title: '블록체인 의료 정보 공유',        type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '블록체인 기반 의료 정보 공유 시스템.',                          grade: 'A', score: 100 },
  { id: 'blockchain_flow',    file: '/drawings/blockchain_flow.svg',    title: '의료 정보 공유 흐름도',          type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '블록체인 의료 정보 공유 프로세스.',                            grade: 'A', score: 100 },
  { id: 'semiconductor_block',file: '/drawings/semiconductor_block.svg',title: '반도체 결함 검사 시스템',        type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '딥러닝 기반 반도체 웨이퍼 결함 검사 시스템.',                    grade: 'A', score: 100 },
  { id: 'semiconductor_flow', file: '/drawings/semiconductor_flow.svg', title: '결함 검사 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '반도체 결함 검사 프로세스 흐름.',                             grade: 'A', score: 100 },
  { id: 'agritech_block',     file: '/drawings/agritech_block.svg',     title: '드론 스마트 농업 시스템',        type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '드론 기반 스마트 농업 작물 관리 시스템.',                       grade: 'A', score: 100 },
  { id: 'agritech_flow',      file: '/drawings/agritech_flow.svg',      title: '작물 관리 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '드론 기반 작물 관리 프로세스.',                               grade: 'A', score: 100 },
  { id: 'smartgrid_block',    file: '/drawings/smartgrid_block.svg',    title: '스마트 전력망 시스템',           type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 스마트 전력망 수요 예측 시스템.',                       grade: 'A', score: 100 },
  { id: 'smartgrid_flow',     file: '/drawings/smartgrid_flow.svg',     title: '전력 수요 예측 흐름도',          type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '스마트 전력망 수요 예측 프로세스.',                            grade: 'A', score: 100 },
  { id: 'edutech_block',      file: '/drawings/edutech_block.svg',      title: '맞춤형 학습 추천 시스템',        type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 개인 맞춤형 학습 추천 시스템.',                         grade: 'A', score: 100 },
  { id: 'edutech_flow',       file: '/drawings/edutech_flow.svg',       title: '학습 추천 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: 'AI 학습 추천 프로세스.',                                     grade: 'A', score: 100 },
  { id: 'resume_match_block', file: '/drawings/resume_match_block.svg', title: '이력서 채용 자동 지원',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '이력서 기반 채용 플랫폼 자동 지원 시스템.',                      grade: 'A', score: 100 },
  { id: 'resume_match_flow',  file: '/drawings/resume_match_flow.svg',  title: '채용 지원 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '이력서 기반 채용 플랫폼 자동 지원 프로세스.',                    grade: 'A', score: 100 },
  { id: 'speech_block',       file: '/drawings/speech_block.svg',       title: '실시간 음성 인식 번역',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '딥러닝 기반 실시간 음성 인식 번역 시스템.',                      grade: 'A', score: 100 },
  { id: 'speech_flow',        file: '/drawings/speech_flow.svg',        title: '음성 번역 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '음성 인식 번역 프로세스.',                                   grade: 'A', score: 100 },
  { id: 'security_block',     file: '/drawings/security_block.svg',     title: 'AI 영상 보안 감지',             type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 영상 보안 침입 감지 시스템.',                           grade: 'A', score: 100 },
  { id: 'security_flow',      file: '/drawings/security_flow.svg',      title: '침입 감지 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '영상 보안 침입 감지 프로세스.',                               grade: 'A', score: 100 },
  { id: 'chatbot_cs_block',   file: '/drawings/chatbot_cs_block.svg',   title: '고객 서비스 자동 응대',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '자연어 처리 기반 고객 서비스 자동 응대 시스템.',                  grade: 'A', score: 100 },
  { id: 'chatbot_cs_flow',    file: '/drawings/chatbot_cs_flow.svg',    title: '고객 응대 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '고객 서비스 자동 응대 프로세스.',                             grade: 'A', score: 100 },
  { id: 'supply_chain_block', file: '/drawings/supply_chain_block.svg', title: '블록체인 공급망 관리',           type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '블록체인 기반 공급망 추적 관리 시스템.',                        grade: 'A', score: 100 },
  { id: 'supply_chain_flow',  file: '/drawings/supply_chain_flow.svg',  title: '공급망 추적 흐름도',            type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '블록체인 공급망 추적 프로세스.',                              grade: 'A', score: 100 },
  { id: 'drug_discovery_block',file:'/drawings/drug_discovery_block.svg',title:'신약 후보 스크리닝 시스템',       type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 신약 후보 물질 스크리닝 시스템.',                       grade: 'A', score: 100 },
  { id: 'drug_discovery_flow', file:'/drawings/drug_discovery_flow.svg', title:'신약 스크리닝 흐름도',           type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '신약 후보 물질 스크리닝 프로세스.',                           grade: 'A', score: 100 },
  { id: 'traffic_block',      file: '/drawings/traffic_block.svg',      title: 'AI 교통 신호 최적화',           type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 교통 신호 최적화 시스템.',                             grade: 'A', score: 100 },
  { id: 'traffic_flow',       file: '/drawings/traffic_flow.svg',       title: '교통 신호 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '교통 신호 최적화 프로세스.',                                 grade: 'A', score: 100 },
  { id: 'ar_nav_block',       file: '/drawings/ar_nav_block.svg',       title: 'AR 실내 네비게이션',            type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '증강현실 기반 실내 네비게이션 시스템.',                         grade: 'A', score: 100 },
  { id: 'ar_nav_flow',        file: '/drawings/ar_nav_flow.svg',        title: 'AR 네비게이션 흐름도',          type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: 'AR 실내 네비게이션 프로세스.',                               grade: 'A', score: 100 },
  { id: 'recycling_block',    file: '/drawings/recycling_block.svg',    title: '재활용 자동 분류 시스템',        type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 재활용 쓰레기 자동 분류 시스템.',                       grade: 'A', score: 100 },
  { id: 'recycling_flow',     file: '/drawings/recycling_flow.svg',     title: '분류 처리 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '재활용 자동 분류 프로세스.',                                 grade: 'A', score: 100 },
  { id: 'mental_health_block',file: '/drawings/mental_health_block.svg',title: '정신건강 모니터링 시스템',       type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 정신건강 모니터링 및 상담 추천 시스템.',                 grade: 'A', score: 100 },
  { id: 'mental_health_flow', file: '/drawings/mental_health_flow.svg', title: '정신건강 관리 흐름도',          type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '정신건강 모니터링 및 상담 연결 프로세스.',                      grade: 'A', score: 100 },
  { id: 'ocr_doc_block',      file: '/drawings/ocr_doc_block.svg',      title: 'AI 문서 OCR 변환 시스템',       type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 문서 OCR 자동 변환 시스템.',                           grade: 'A', score: 100 },
  { id: 'ocr_doc_flow',       file: '/drawings/ocr_doc_flow.svg',       title: 'OCR 문서 처리 흐름도',          type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: 'AI 문서 OCR 처리 프로세스.',                                grade: 'A', score: 100 },
  { id: 'recommend_block',    file: '/drawings/recommend_block.svg',    title: '상품 추천 시스템',              type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '협업 필터링 기반 상품 추천 시스템.',                            grade: 'A', score: 100 },
  { id: 'recommend_flow',     file: '/drawings/recommend_flow.svg',     title: '추천 생성 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '협업 필터링 추천 생성 프로세스.',                             grade: 'A', score: 100 },
  { id: 'emotion_block',      file: '/drawings/emotion_block.svg',      title: '실시간 감정 인식 시스템',        type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '딥러닝 기반 실시간 감정 인식 시스템.',                          grade: 'A', score: 100 },
  { id: 'emotion_flow',       file: '/drawings/emotion_flow.svg',       title: '감정 인식 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '감정 인식 및 피드백 프로세스.',                               grade: 'A', score: 100 },
  { id: 'plagiarism_block',   file: '/drawings/plagiarism_block.svg',   title: '논문 표절 탐지 시스템',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 학술 논문 표절 탐지 시스템.',                          grade: 'A', score: 100 },
  { id: 'plagiarism_flow',    file: '/drawings/plagiarism_flow.svg',    title: '표절 탐지 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '논문 표절 탐지 프로세스.',                                  grade: 'A', score: 100 },
  { id: 'inventory_block',    file: '/drawings/inventory_block.svg',    title: '스마트 재고 관리 시스템',        type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 스마트 재고 관리 최적화 시스템.',                       grade: 'A', score: 100 },
  { id: 'inventory_flow',     file: '/drawings/inventory_flow.svg',     title: '재고 관리 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '스마트 재고 관리 최적화 프로세스.',                           grade: 'A', score: 100 },
  { id: 'translation_block',  file: '/drawings/translation_block.svg',  title: '전문 용어 번역 시스템',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '신경망 기반 전문 용어 번역 시스템.',                            grade: 'A', score: 100 },
  { id: 'translation_flow',   file: '/drawings/translation_flow.svg',   title: '번역 처리 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '전문 용어 번역 프로세스.',                                  grade: 'A', score: 100 },
  { id: 'parking_block',      file: '/drawings/parking_block.svg',      title: '스마트 주차장 관리',            type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 스마트 주차장 관리 시스템.',                           grade: 'A', score: 100 },
  { id: 'parking_flow',       file: '/drawings/parking_flow.svg',       title: '주차 관리 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '스마트 주차장 관리 프로세스.',                               grade: 'A', score: 100 },
  { id: 'quality_block',      file: '/drawings/quality_block.svg',      title: '제조 품질 검사 자동화',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '딥러닝 기반 제조 품질 검사 자동화 시스템.',                      grade: 'A', score: 100 },
  { id: 'quality_flow',       file: '/drawings/quality_flow.svg',       title: '품질 검사 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '제조 품질 검사 자동화 프로세스.',                             grade: 'A', score: 100 },
  { id: 'chatgpt_patent_block',file:'/drawings/chatgpt_patent_block.svg',title:'LLM 특허 명세서 작성 시스템',    type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'LLM 기반 특허 명세서 자동 작성 시스템.',                        grade: 'A', score: 100 },
  { id: 'chatgpt_patent_flow', file:'/drawings/chatgpt_patent_flow.svg', title:'명세서 작성 흐름도',             type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: 'LLM 특허 명세서 작성 프로세스.',                             grade: 'A', score: 100 },
  { id: 'satellite_block',    file: '/drawings/satellite_block.svg',    title: '위성 영상 환경 모니터링',        type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '위성 영상 기반 환경 모니터링 시스템.',                          grade: 'A', score: 100 },
  { id: 'satellite_flow',     file: '/drawings/satellite_flow.svg',     title: '환경 모니터링 흐름도',           type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '위성 영상 환경 변화 감지 프로세스.',                           grade: 'A', score: 100 },
  { id: 'defect_predict_block',file:'/drawings/defect_predict_block.svg',title:'설비 예지 보전 시스템',           type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 설비 예지 보전 시스템.',                               grade: 'A', score: 100 },
  { id: 'defect_predict_flow', file:'/drawings/defect_predict_flow.svg', title:'고장 예측 흐름도',               type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '설비 예지 보전 프로세스.',                                  grade: 'A', score: 100 },
  { id: 'food_safety_block',  file: '/drawings/food_safety_block.svg',  title: '식품 안전 검사 시스템',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 식품 안전 검사 시스템.',                               grade: 'A', score: 100 },
  { id: 'food_safety_flow',   file: '/drawings/food_safety_flow.svg',   title: '식품 안전 검사 흐름도',          type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '식품 안전 검사 프로세스.',                                  grade: 'A', score: 100 },
  { id: 'insurance_block',    file: '/drawings/insurance_block.svg',    title: '사고 영상 보험 청구 시스템',     type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 사고 영상 분석 보험 청구 시스템.',                      grade: 'A', score: 100 },
  { id: 'insurance_flow',     file: '/drawings/insurance_flow.svg',     title: '보험 청구 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '사고 영상 분석 보험 청구 프로세스.',                          grade: 'A', score: 100 },
  { id: 'code_review_block',  file: '/drawings/code_review_block.svg',  title: 'AI 코드 자동 검토 시스템',      type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 소프트웨어 코드 자동 검토 시스템.',                     grade: 'A', score: 100 },
  { id: 'code_review_flow',   file: '/drawings/code_review_flow.svg',   title: '코드 검토 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: 'AI 코드 검토 프로세스.',                                    grade: 'A', score: 100 },
  { id: 'water_block',        file: '/drawings/water_block.svg',        title: '스마트 수질 모니터링',           type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'IoT 기반 스마트 수질 모니터링 시스템.',                         grade: 'A', score: 100 },
  { id: 'water_flow',         file: '/drawings/water_flow.svg',         title: '수질 모니터링 흐름도',           type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '스마트 수질 모니터링 프로세스.',                              grade: 'A', score: 100 },
  { id: 'sign_lang_block',    file: '/drawings/sign_lang_block.svg',    title: '수어 인식 번역 시스템',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '딥러닝 기반 수어 인식 번역 시스템.',                            grade: 'A', score: 100 },
  { id: 'sign_lang_flow',     file: '/drawings/sign_lang_flow.svg',     title: '수어 인식 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '수어 인식 및 번역 프로세스.',                                grade: 'A', score: 100 },
  { id: '3d_print_block',     file: '/drawings/3d_print_block.svg',     title: '3D 프린팅 품질 최적화',         type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 3D 프린팅 품질 최적화 시스템.',                         grade: 'A', score: 100 },
  { id: '3d_print_flow',      file: '/drawings/3d_print_flow.svg',      title: '3D 프린팅 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '3D 프린팅 품질 최적화 프로세스.',                             grade: 'A', score: 100 },
  { id: 'hr_matching_block',  file: '/drawings/hr_matching_block.svg',  title: '인재 채용 매칭 시스템',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 인재 역량 평가 채용 매칭 시스템.',                      grade: 'A', score: 100 },
  { id: 'hr_matching_flow',   file: '/drawings/hr_matching_flow.svg',   title: '채용 매칭 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: 'AI 인재 채용 매칭 프로세스.',                                grade: 'A', score: 100 },
  { id: 'noise_cancel_block', file: '/drawings/noise_cancel_block.svg', title: 'AI 소음 제거 시스템',           type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 실시간 소음 제거 오디오 시스템.',                       grade: 'A', score: 100 },
  { id: 'noise_cancel_flow',  file: '/drawings/noise_cancel_flow.svg',  title: '소음 제거 흐름도',              type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '실시간 소음 제거 프로세스.',                                 grade: 'A', score: 100 },
  { id: 'legal_contract_block',file:'/drawings/legal_contract_block.svg',title:'법률 계약서 자동 검토',          type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 기반 법률 계약서 자동 검토 시스템.',                         grade: 'A', score: 100 },
  { id: 'legal_contract_flow', file:'/drawings/legal_contract_flow.svg', title:'계약서 검토 흐름도',             type: 'flowchart',     typeLabel: 'FLOWCHART',     desc: '법률 계약서 자동 검토 프로세스.',                             grade: 'A', score: 100 },
]

const PAGE_SIZE = 12
const typeFilters = [
  { id: 'all', label: '전체' },
  { id: 'block_diagram', label: '블록도' },
  { id: 'flowchart', label: '흐름도' },
]

export default function GalleryPage() {
  const [filter, setFilter]   = useState('all')
  const [page, setPage]       = useState(1)
  const [selected, setSelected] = useState<typeof drawings[0] | null>(null)

  const filtered = filter === 'all' ? drawings : drawings.filter(d => d.type === filter)
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE)
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  function handleFilter(f: string) { setFilter(f); setPage(1) }

  return (
    <div className="site">
      <style>{`
        .gallery-filter { display:flex; gap:.5rem; margin-bottom:2.5rem; flex-wrap:wrap; }
        .gallery-filter-btn { padding:.45rem 1.2rem; border:1px solid #E8E4DC; background:white; color:#666; font-size:.78rem; font-weight:600; cursor:pointer; letter-spacing:.06em; transition:.15s; font-family:inherit; }
        .gallery-filter-btn:hover { border-color:#C9A84C; color:#C9A84C; }
        .gallery-filter-btn.active { background:#111128; border-color:#111128; color:#C9A84C; }

        .gallery-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:1px; background:#E0DDD8; }
        .gallery-card { background:white; cursor:pointer; transition:background .15s; overflow:hidden; }
        .gallery-card:hover { background:#FAFAF8; }
        .gallery-svg-wrap { width:100%; aspect-ratio:4/3; overflow:hidden; background:#FEFEFE; border-bottom:1px solid #F0EDE8; display:flex; align-items:center; justify-content:center; transition:opacity .15s; }
        .gallery-svg-wrap img { width:100%; height:100%; object-fit:contain; padding:.5rem; }
        .gallery-card-body { padding:1.2rem 1.4rem; }
        .gallery-type { color:#C9A84C; font-size:.65rem; font-weight:700; letter-spacing:.2em; margin-bottom:.4rem; }
        .gallery-title { font-weight:700; color:#0A0A16; font-size:.88rem; margin-bottom:.3rem; }
        .gallery-desc { font-size:.78rem; color:#666; line-height:1.6; margin-bottom:.7rem; }
        .gallery-meta { display:flex; align-items:center; justify-content:space-between; }
        .gallery-grade { font-size:.68rem; font-weight:700; letter-spacing:.1em; padding:2px 8px; border:1px solid; }
        .grade-A { border-color:rgba(39,174,96,.3); color:#27ae60; background:rgba(39,174,96,.05); }
        .grade-B { border-color:rgba(243,156,18,.3); color:#f39c12; background:rgba(243,156,18,.05); }
        .gallery-score { font-size:.75rem; color:#999; }

        .pagination { display:flex; align-items:center; justify-content:center; gap:.4rem; margin-top:2.5rem; }
        .page-btn { width:36px; height:36px; border:1px solid #E8E4DC; background:white; color:#666; font-size:.82rem; cursor:pointer; font-family:inherit; transition:.15s; display:flex; align-items:center; justify-content:center; }
        .page-btn:hover { border-color:#C9A84C; color:#C9A84C; }
        .page-btn.active { background:#111128; border-color:#111128; color:#C9A84C; font-weight:700; }
        .page-btn:disabled { opacity:.3; cursor:not-allowed; }

        .gallery-modal-bg { position:fixed; inset:0; background:rgba(0,0,0,.75); z-index:9999; display:flex; align-items:center; justify-content:center; padding:2rem; animation:fadeIn .2s ease; }
        @keyframes fadeIn { from{opacity:0} to{opacity:1} }
        .gallery-modal { background:white; max-width:1000px; width:100%; max-height:90vh; display:flex; flex-direction:column; overflow:hidden; }
        .gallery-modal-header { padding:1.2rem 1.6rem; border-bottom:1px solid #E8E4DC; display:flex; align-items:center; justify-content:space-between; flex-shrink:0; }
        .gallery-modal-title { font-weight:700; color:#0A0A16; font-size:1rem; }
        .gallery-modal-close { background:none; border:none; font-size:1.4rem; cursor:pointer; color:#999; transition:color .15s; line-height:1; padding:0; }
        .gallery-modal-close:hover { color:#C9A84C; }
        .gallery-modal-body { flex:1; overflow:auto; padding:1.5rem; }
        .gallery-modal-body img { width:100%; height:auto; }
        .gallery-modal-footer { padding:1rem 1.6rem; border-top:1px solid #E8E4DC; display:flex; gap:.8rem; flex-shrink:0; }
        .gallery-dl-btn { padding:.6rem 1.4rem; border:1px solid #111128; background:#111128; color:#C9A84C; font-size:.78rem; font-weight:700; cursor:pointer; text-decoration:none; letter-spacing:.06em; transition:.15s; display:inline-block; }
        .gallery-dl-btn:hover { background:#C9A84C; color:#111128; border-color:#C9A84C; }
        .gallery-dl-btn.outline { background:white; color:#111128; border-color:#E8E4DC; }
        .gallery-dl-btn.outline:hover { border-color:#C9A84C; color:#C9A84C; }

        @media(max-width:900px){ .gallery-grid { grid-template-columns:1fr 1fr; } }
        @media(max-width:480px){ .gallery-grid { grid-template-columns:1fr; } }
      `}</style>

      <Nav />

      <div className="hero">
        <div className="tag">DRAWING GALLERY</div>
        <h1>특허 도면 갤러리</h1>
        <p>PatentAI가 자동 생성한 실제 특허 도면 샘플입니다.<br />다양한 기술 분야의 SVG 도면을 확인하세요.</p>
      </div>

      <div className="section">
        {/* 통계 */}
        <div style={{ display:'flex', gap:'3rem', marginBottom:'3rem', paddingBottom:'2rem', borderBottom:'1px solid #E8E4DC', flexWrap:'wrap' }}>
          {[
            { num: drawings.length, label: '총 도면 수' },
            { num: drawings.filter(d => d.type === 'block_diagram').length, label: '블록도' },
            { num: drawings.filter(d => d.type === 'flowchart').length, label: '흐름도' },
            { num: drawings.filter(d => d.grade === 'A').length, label: 'A등급' },
          ].map(s => (
            <div key={s.label}>
              <div style={{ fontFamily:"'Noto Serif KR',serif", fontSize:'1.8rem', fontWeight:200, color:'#0A0A16' }}>{s.num}</div>
              <div style={{ fontSize:'.72rem', color:'#999', letterSpacing:'.08em', textTransform:'uppercase', marginTop:'3px' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* 필터 */}
        <div className="gallery-filter">
          {typeFilters.map(f => (
            <button key={f.id} className={`gallery-filter-btn ${filter === f.id ? 'active' : ''}`} onClick={() => handleFilter(f.id)}>
              {f.label}
            </button>
          ))}
        </div>

        {/* 그리드 */}
        <div className="gallery-grid">
          {paged.map(d => (
            <div key={d.id} className="gallery-card" onClick={() => setSelected(d)}>
              <div className="gallery-svg-wrap">
                <img src={d.file} alt={d.title} loading="lazy" />
              </div>
              <div className="gallery-card-body">
                <div className="gallery-type">{d.typeLabel}</div>
                <div className="gallery-title">{d.title}</div>
                <div className="gallery-desc">{d.desc}</div>
                <div className="gallery-meta">
                  <span className={`gallery-grade grade-${d.grade}`}>{d.grade}등급</span>
                  <span className="gallery-score">{d.score}점</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* 페이지네이션 */}
        {totalPages > 1 && (
          <div className="pagination">
            <button className="page-btn" onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1}>‹</button>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
              <button key={p} className={`page-btn ${p === page ? 'active' : ''}`} onClick={() => setPage(p)}>{p}</button>
            ))}
            <button className="page-btn" onClick={() => setPage(p => Math.min(totalPages, p+1))} disabled={page === totalPages}>›</button>
          </div>
        )}

        {/* CTA */}
        <div style={{ marginTop:'3rem', background:'#08081A', padding:'3rem', display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:'1.5rem' }}>
          <div>
            <div style={{ color:'#C9A84C', fontSize:'.7rem', fontWeight:700, letterSpacing:'.2em', marginBottom:'.5rem' }}>DRAWING AGENT</div>
            <div style={{ fontFamily:"'Noto Serif KR',serif", fontSize:'1.4rem', fontWeight:300, color:'#F0EDE6', marginBottom:'.3rem' }}>내 발명의 도면을 자동 생성해보세요</div>
            <div style={{ color:'#555577', fontSize:'.86rem' }}>발명 내용이나 PDF를 입력하면 바로 생성됩니다.</div>
          </div>
          <Link href="/service/demo" style={{ display:'inline-block', padding:'.9rem 2.5rem', border:'1px solid #C9A84C', color:'#C9A84C', fontSize:'.82rem', fontWeight:700, letterSpacing:'.1em', textDecoration:'none', whiteSpace:'nowrap' }}>
            도면 생성 데모 →
          </Link>
        </div>
      </div>

      {/* 모달 */}
      {selected && (
        <div className="gallery-modal-bg" onClick={() => setSelected(null)}>
          <div className="gallery-modal" onClick={e => e.stopPropagation()}>
            <div className="gallery-modal-header">
              <div>
                <div style={{ color:'#C9A84C', fontSize:'.65rem', fontWeight:700, letterSpacing:'.2em', marginBottom:'3px' }}>{selected.typeLabel}</div>
                <div className="gallery-modal-title">{selected.title}</div>
              </div>
              <button className="gallery-modal-close" onClick={() => setSelected(null)}>×</button>
            </div>
            <div className="gallery-modal-body">
              <img src={selected.file} alt={selected.title} />
            </div>
            <div className="gallery-modal-footer">
              <a className="gallery-dl-btn" href={selected.file} download={`${selected.id}.svg`}>SVG 다운로드</a>
              <button className="gallery-dl-btn outline" onClick={() => setSelected(null)}>닫기</button>
              <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:'.5rem' }}>
                <span className={`gallery-grade grade-${selected.grade}`}>{selected.grade}등급</span>
                <span style={{ color:'#999', fontSize:'.78rem' }}>{selected.score}점 / 100점</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  )
}
