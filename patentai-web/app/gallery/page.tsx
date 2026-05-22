'use client'

import { useState } from 'react'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'

const drawings = [
  { id: '3d_print_block', file: '/drawings/3d_print_block.svg', title: '3D 프린팅 최적화 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '3D 프린팅 최적화 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: '3d_print_flow', file: '/drawings/3d_print_flow.svg', title: '3D 프린팅 최적화 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '3D 프린팅 최적화 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'agritech_block', file: '/drawings/agritech_block.svg', title: '드론 스마트 농업 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '드론 스마트 농업 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'agritech_flow', file: '/drawings/agritech_flow.svg', title: '드론 스마트 농업 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '드론 스마트 농업 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'ai_block', file: '/drawings/ai_block.svg', title: 'AI 시스템 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 시스템 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'ai_flow', file: '/drawings/ai_flow.svg', title: 'AI 시스템 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: 'AI 시스템 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'air_quality_block_diagram', file: '/drawings/air_quality_block_diagram.svg', title: '실내 공기질 관리 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '실내 공기질 관리 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'air_quality_circuit', file: '/drawings/air_quality_circuit.svg', title: '실내 공기질 관리 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '실내 공기질 관리 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'air_quality_flowchart', file: '/drawings/air_quality_flowchart.svg', title: '실내 공기질 관리 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '실내 공기질 관리 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'air_quality_sequence', file: '/drawings/air_quality_sequence.svg', title: '실내 공기질 관리 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '실내 공기질 관리 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'air_quality_ui_screen', file: '/drawings/air_quality_ui_screen.svg', title: '실내 공기질 관리 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '실내 공기질 관리 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'ar_nav_block', file: '/drawings/ar_nav_block.svg', title: 'AR 실내 네비게이션 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AR 실내 네비게이션 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'ar_nav_flow', file: '/drawings/ar_nav_flow.svg', title: 'AR 실내 네비게이션 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: 'AR 실내 네비게이션 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'ar_surgery_block_diagram', file: '/drawings/ar_surgery_block_diagram.svg', title: 'AR 수술 보조 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AR 수술 보조 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'ar_surgery_circuit', file: '/drawings/ar_surgery_circuit.svg', title: 'AR 수술 보조 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: 'AR 수술 보조 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'ar_surgery_flowchart', file: '/drawings/ar_surgery_flowchart.svg', title: 'AR 수술 보조 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: 'AR 수술 보조 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'ar_surgery_sequence', file: '/drawings/ar_surgery_sequence.svg', title: 'AR 수술 보조 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: 'AR 수술 보조 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'ar_surgery_ui_screen', file: '/drawings/ar_surgery_ui_screen.svg', title: 'AR 수술 보조 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: 'AR 수술 보조 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'autonomous_block', file: '/drawings/autonomous_block.svg', title: '자율주행 감지 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '자율주행 감지 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'autonomous_flow', file: '/drawings/autonomous_flow.svg', title: '자율주행 감지 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '자율주행 감지 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'biometric_pay_block_diagram', file: '/drawings/biometric_pay_block_diagram.svg', title: '생체인증 결제 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '생체인증 결제 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'biometric_pay_circuit', file: '/drawings/biometric_pay_circuit.svg', title: '생체인증 결제 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '생체인증 결제 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'biometric_pay_flowchart', file: '/drawings/biometric_pay_flowchart.svg', title: '생체인증 결제 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '생체인증 결제 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'biometric_pay_sequence', file: '/drawings/biometric_pay_sequence.svg', title: '생체인증 결제 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '생체인증 결제 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'biometric_pay_ui_screen', file: '/drawings/biometric_pay_ui_screen.svg', title: '생체인증 결제 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '생체인증 결제 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'blockchain_block', file: '/drawings/blockchain_block.svg', title: '블록체인 의료 정보 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '블록체인 의료 정보 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'blockchain_flow', file: '/drawings/blockchain_flow.svg', title: '블록체인 의료 정보 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '블록체인 의료 정보 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'blood_glucose_block_diagram', file: '/drawings/blood_glucose_block_diagram.svg', title: '혈당 연속 모니터링 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '혈당 연속 모니터링 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'blood_glucose_circuit', file: '/drawings/blood_glucose_circuit.svg', title: '혈당 연속 모니터링 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '혈당 연속 모니터링 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'blood_glucose_flowchart', file: '/drawings/blood_glucose_flowchart.svg', title: '혈당 연속 모니터링 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '혈당 연속 모니터링 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'blood_glucose_sequence', file: '/drawings/blood_glucose_sequence.svg', title: '혈당 연속 모니터링 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '혈당 연속 모니터링 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'blood_glucose_ui_screen', file: '/drawings/blood_glucose_ui_screen.svg', title: '혈당 연속 모니터링 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '혈당 연속 모니터링 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'brain_bci_block_diagram', file: '/drawings/brain_bci_block_diagram.svg', title: 'BCI 뇌-컴퓨터 인터페이스 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'BCI 뇌-컴퓨터 인터페이스 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'brain_bci_circuit', file: '/drawings/brain_bci_circuit.svg', title: 'BCI 뇌-컴퓨터 인터페이스 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: 'BCI 뇌-컴퓨터 인터페이스 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'brain_bci_flowchart', file: '/drawings/brain_bci_flowchart.svg', title: 'BCI 뇌-컴퓨터 인터페이스 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: 'BCI 뇌-컴퓨터 인터페이스 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'brain_bci_sequence', file: '/drawings/brain_bci_sequence.svg', title: 'BCI 뇌-컴퓨터 인터페이스 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: 'BCI 뇌-컴퓨터 인터페이스 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'brain_bci_ui_screen', file: '/drawings/brain_bci_ui_screen.svg', title: 'BCI 뇌-컴퓨터 인터페이스 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: 'BCI 뇌-컴퓨터 인터페이스 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'chatbot_cs_block', file: '/drawings/chatbot_cs_block.svg', title: '고객 서비스 응대 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '고객 서비스 응대 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'chatbot_cs_flow', file: '/drawings/chatbot_cs_flow.svg', title: '고객 서비스 응대 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '고객 서비스 응대 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'chatgpt_patent_block', file: '/drawings/chatgpt_patent_block.svg', title: 'LLM 특허 명세서 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'LLM 특허 명세서 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'chatgpt_patent_flow', file: '/drawings/chatgpt_patent_flow.svg', title: 'LLM 특허 명세서 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: 'LLM 특허 명세서 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'co2_capture_block_diagram', file: '/drawings/co2_capture_block_diagram.svg', title: '이산화탄소 포집 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '이산화탄소 포집 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'co2_capture_circuit', file: '/drawings/co2_capture_circuit.svg', title: '이산화탄소 포집 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '이산화탄소 포집 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'co2_capture_flowchart', file: '/drawings/co2_capture_flowchart.svg', title: '이산화탄소 포집 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '이산화탄소 포집 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'co2_capture_sequence', file: '/drawings/co2_capture_sequence.svg', title: '이산화탄소 포집 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '이산화탄소 포집 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'co2_capture_ui_screen', file: '/drawings/co2_capture_ui_screen.svg', title: '이산화탄소 포집 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '이산화탄소 포집 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'code_review_block', file: '/drawings/code_review_block.svg', title: 'AI 코드 검토 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 코드 검토 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'code_review_flow', file: '/drawings/code_review_flow.svg', title: 'AI 코드 검토 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: 'AI 코드 검토 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'cold_chain_block_diagram', file: '/drawings/cold_chain_block_diagram.svg', title: '콜드체인 온도 관리 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '콜드체인 온도 관리 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'cold_chain_circuit', file: '/drawings/cold_chain_circuit.svg', title: '콜드체인 온도 관리 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '콜드체인 온도 관리 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'cold_chain_flowchart', file: '/drawings/cold_chain_flowchart.svg', title: '콜드체인 온도 관리 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '콜드체인 온도 관리 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'cold_chain_sequence', file: '/drawings/cold_chain_sequence.svg', title: '콜드체인 온도 관리 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '콜드체인 온도 관리 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'cold_chain_ui_screen', file: '/drawings/cold_chain_ui_screen.svg', title: '콜드체인 온도 관리 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '콜드체인 온도 관리 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'crop_yield_block_diagram', file: '/drawings/crop_yield_block_diagram.svg', title: '작물 수확량 예측 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '작물 수확량 예측 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'crop_yield_circuit', file: '/drawings/crop_yield_circuit.svg', title: '작물 수확량 예측 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '작물 수확량 예측 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'crop_yield_flowchart', file: '/drawings/crop_yield_flowchart.svg', title: '작물 수확량 예측 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '작물 수확량 예측 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'crop_yield_sequence', file: '/drawings/crop_yield_sequence.svg', title: '작물 수확량 예측 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '작물 수확량 예측 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'crop_yield_ui_screen', file: '/drawings/crop_yield_ui_screen.svg', title: '작물 수확량 예측 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '작물 수확량 예측 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'defect_predict_block', file: '/drawings/defect_predict_block.svg', title: '설비 예지 보전 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '설비 예지 보전 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'defect_predict_flow', file: '/drawings/defect_predict_flow.svg', title: '설비 예지 보전 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '설비 예지 보전 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'drone_delivery_block_diagram', file: '/drawings/drone_delivery_block_diagram.svg', title: '드론 자율 배송 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '드론 자율 배송 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'drone_delivery_circuit', file: '/drawings/drone_delivery_circuit.svg', title: '드론 자율 배송 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '드론 자율 배송 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'drone_delivery_flowchart', file: '/drawings/drone_delivery_flowchart.svg', title: '드론 자율 배송 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '드론 자율 배송 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'drone_delivery_sequence', file: '/drawings/drone_delivery_sequence.svg', title: '드론 자율 배송 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '드론 자율 배송 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'drone_delivery_ui_screen', file: '/drawings/drone_delivery_ui_screen.svg', title: '드론 자율 배송 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '드론 자율 배송 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'drug_discovery_block', file: '/drawings/drug_discovery_block.svg', title: '신약 후보 스크리닝 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '신약 후보 스크리닝 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'drug_discovery_flow', file: '/drawings/drug_discovery_flow.svg', title: '신약 후보 스크리닝 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '신약 후보 스크리닝 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'earthquake_early_block_diagram', file: '/drawings/earthquake_early_block_diagram.svg', title: '지진 조기 경보 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '지진 조기 경보 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'earthquake_early_circuit', file: '/drawings/earthquake_early_circuit.svg', title: '지진 조기 경보 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '지진 조기 경보 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'earthquake_early_flowchart', file: '/drawings/earthquake_early_flowchart.svg', title: '지진 조기 경보 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '지진 조기 경보 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'earthquake_early_sequence', file: '/drawings/earthquake_early_sequence.svg', title: '지진 조기 경보 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '지진 조기 경보 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'earthquake_early_ui_screen', file: '/drawings/earthquake_early_ui_screen.svg', title: '지진 조기 경보 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '지진 조기 경보 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'edutech_block', file: '/drawings/edutech_block.svg', title: '맞춤형 학습 추천 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '맞춤형 학습 추천 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'edutech_flow', file: '/drawings/edutech_flow.svg', title: '맞춤형 학습 추천 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '맞춤형 학습 추천 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'elderly_care_block_diagram', file: '/drawings/elderly_care_block_diagram.svg', title: '독거노인 돌봄 IoT 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '독거노인 돌봄 IoT 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'elderly_care_circuit', file: '/drawings/elderly_care_circuit.svg', title: '독거노인 돌봄 IoT 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '독거노인 돌봄 IoT 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'elderly_care_flowchart', file: '/drawings/elderly_care_flowchart.svg', title: '독거노인 돌봄 IoT 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '독거노인 돌봄 IoT 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'elderly_care_sequence', file: '/drawings/elderly_care_sequence.svg', title: '독거노인 돌봄 IoT 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '독거노인 돌봄 IoT 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'elderly_care_ui_screen', file: '/drawings/elderly_care_ui_screen.svg', title: '독거노인 돌봄 IoT 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '독거노인 돌봄 IoT 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'emotion_block', file: '/drawings/emotion_block.svg', title: '감정 인식 시스템 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '감정 인식 시스템 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'emotion_flow', file: '/drawings/emotion_flow.svg', title: '감정 인식 시스템 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '감정 인식 시스템 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'ev_charge_block_diagram', file: '/drawings/ev_charge_block_diagram.svg', title: '전기차 스마트 충전 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '전기차 스마트 충전 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'ev_charge_circuit', file: '/drawings/ev_charge_circuit.svg', title: '전기차 스마트 충전 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '전기차 스마트 충전 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'ev_charge_flowchart', file: '/drawings/ev_charge_flowchart.svg', title: '전기차 스마트 충전 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '전기차 스마트 충전 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'ev_charge_sequence', file: '/drawings/ev_charge_sequence.svg', title: '전기차 스마트 충전 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '전기차 스마트 충전 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'ev_charge_ui_screen', file: '/drawings/ev_charge_ui_screen.svg', title: '전기차 스마트 충전 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '전기차 스마트 충전 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'exoskeleton_block_diagram', file: '/drawings/exoskeleton_block_diagram.svg', title: '착용형 외골격 로봇 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '착용형 외골격 로봇 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'exoskeleton_circuit', file: '/drawings/exoskeleton_circuit.svg', title: '착용형 외골격 로봇 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '착용형 외골격 로봇 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'exoskeleton_flowchart', file: '/drawings/exoskeleton_flowchart.svg', title: '착용형 외골격 로봇 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '착용형 외골격 로봇 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'exoskeleton_sequence', file: '/drawings/exoskeleton_sequence.svg', title: '착용형 외골격 로봇 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '착용형 외골격 로봇 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'exoskeleton_ui_screen', file: '/drawings/exoskeleton_ui_screen.svg', title: '착용형 외골격 로봇 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '착용형 외골격 로봇 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'fintech_block', file: '/drawings/fintech_block.svg', title: '금융 사기 탐지 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '금융 사기 탐지 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'fintech_flow', file: '/drawings/fintech_flow.svg', title: '금융 사기 탐지 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '금융 사기 탐지 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'food_safety_block', file: '/drawings/food_safety_block.svg', title: '식품 안전 검사 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '식품 안전 검사 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'food_safety_flow', file: '/drawings/food_safety_flow.svg', title: '식품 안전 검사 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '식품 안전 검사 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'forest_fire_block_diagram', file: '/drawings/forest_fire_block_diagram.svg', title: '산불 조기 감지 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '산불 조기 감지 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'forest_fire_circuit', file: '/drawings/forest_fire_circuit.svg', title: '산불 조기 감지 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '산불 조기 감지 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'forest_fire_flowchart', file: '/drawings/forest_fire_flowchart.svg', title: '산불 조기 감지 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '산불 조기 감지 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'forest_fire_sequence', file: '/drawings/forest_fire_sequence.svg', title: '산불 조기 감지 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '산불 조기 감지 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'forest_fire_ui_screen', file: '/drawings/forest_fire_ui_screen.svg', title: '산불 조기 감지 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '산불 조기 감지 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'hr_matching_block', file: '/drawings/hr_matching_block.svg', title: '인재 채용 매칭 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '인재 채용 매칭 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'hr_matching_flow', file: '/drawings/hr_matching_flow.svg', title: '인재 채용 매칭 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '인재 채용 매칭 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'insurance_block', file: '/drawings/insurance_block.svg', title: '사고 영상 보험 청구 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '사고 영상 보험 청구 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'insurance_flow', file: '/drawings/insurance_flow.svg', title: '사고 영상 보험 청구 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '사고 영상 보험 청구 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'inventory_block', file: '/drawings/inventory_block.svg', title: '스마트 재고 관리 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 재고 관리 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'inventory_flow', file: '/drawings/inventory_flow.svg', title: '스마트 재고 관리 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 재고 관리 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'iot_block', file: '/drawings/iot_block.svg', title: '스마트 공장 모니터링 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 공장 모니터링 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'iot_flow', file: '/drawings/iot_flow.svg', title: '스마트 공장 모니터링 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 공장 모니터링 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'laser_cutting_block_diagram', file: '/drawings/laser_cutting_block_diagram.svg', title: '레이저 정밀 가공 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '레이저 정밀 가공 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'laser_cutting_circuit', file: '/drawings/laser_cutting_circuit.svg', title: '레이저 정밀 가공 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '레이저 정밀 가공 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'laser_cutting_flowchart', file: '/drawings/laser_cutting_flowchart.svg', title: '레이저 정밀 가공 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '레이저 정밀 가공 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'laser_cutting_sequence', file: '/drawings/laser_cutting_sequence.svg', title: '레이저 정밀 가공 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '레이저 정밀 가공 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'laser_cutting_ui_screen', file: '/drawings/laser_cutting_ui_screen.svg', title: '레이저 정밀 가공 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '레이저 정밀 가공 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'legal_contract_block', file: '/drawings/legal_contract_block.svg', title: '법률 계약서 검토 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '법률 계약서 검토 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'legal_contract_flow', file: '/drawings/legal_contract_flow.svg', title: '법률 계약서 검토 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '법률 계약서 검토 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'medical_block', file: '/drawings/medical_block.svg', title: '의료 영상 진단 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '의료 영상 진단 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'medical_flow', file: '/drawings/medical_flow.svg', title: '의료 영상 진단 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '의료 영상 진단 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'mental_health_block', file: '/drawings/mental_health_block.svg', title: '정신건강 모니터링 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '정신건강 모니터링 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'mental_health_flow', file: '/drawings/mental_health_flow.svg', title: '정신건강 모니터링 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '정신건강 모니터링 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'micro_plastic_block_diagram', file: '/drawings/micro_plastic_block_diagram.svg', title: '미세플라스틱 검출 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '미세플라스틱 검출 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'micro_plastic_circuit', file: '/drawings/micro_plastic_circuit.svg', title: '미세플라스틱 검출 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '미세플라스틱 검출 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'micro_plastic_flowchart', file: '/drawings/micro_plastic_flowchart.svg', title: '미세플라스틱 검출 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '미세플라스틱 검출 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'micro_plastic_sequence', file: '/drawings/micro_plastic_sequence.svg', title: '미세플라스틱 검출 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '미세플라스틱 검출 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'micro_plastic_ui_screen', file: '/drawings/micro_plastic_ui_screen.svg', title: '미세플라스틱 검출 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '미세플라스틱 검출 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'neural_implant_block_diagram', file: '/drawings/neural_implant_block_diagram.svg', title: '신경 임플란트 인터페이스 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '신경 임플란트 인터페이스 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'neural_implant_circuit', file: '/drawings/neural_implant_circuit.svg', title: '신경 임플란트 인터페이스 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '신경 임플란트 인터페이스 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'neural_implant_flowchart', file: '/drawings/neural_implant_flowchart.svg', title: '신경 임플란트 인터페이스 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '신경 임플란트 인터페이스 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'neural_implant_sequence', file: '/drawings/neural_implant_sequence.svg', title: '신경 임플란트 인터페이스 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '신경 임플란트 인터페이스 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'neural_implant_ui_screen', file: '/drawings/neural_implant_ui_screen.svg', title: '신경 임플란트 인터페이스 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '신경 임플란트 인터페이스 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'newborn_monitor_block_diagram', file: '/drawings/newborn_monitor_block_diagram.svg', title: '신생아 집중 치료 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '신생아 집중 치료 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'newborn_monitor_circuit', file: '/drawings/newborn_monitor_circuit.svg', title: '신생아 집중 치료 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '신생아 집중 치료 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'newborn_monitor_flowchart', file: '/drawings/newborn_monitor_flowchart.svg', title: '신생아 집중 치료 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '신생아 집중 치료 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'newborn_monitor_sequence', file: '/drawings/newborn_monitor_sequence.svg', title: '신생아 집중 치료 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '신생아 집중 치료 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'newborn_monitor_ui_screen', file: '/drawings/newborn_monitor_ui_screen.svg', title: '신생아 집중 치료 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '신생아 집중 치료 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'nlp_block', file: '/drawings/nlp_block.svg', title: '법률 문서 분석 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '법률 문서 분석 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'nlp_flow', file: '/drawings/nlp_flow.svg', title: '법률 문서 분석 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '법률 문서 분석 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'noise_cancel_block', file: '/drawings/noise_cancel_block.svg', title: 'AI 소음 제거 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 소음 제거 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'noise_cancel_flow', file: '/drawings/noise_cancel_flow.svg', title: 'AI 소음 제거 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: 'AI 소음 제거 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'nuclear_arm_block_diagram', file: '/drawings/nuclear_arm_block_diagram.svg', title: '핵폐기물 처리 로봇팔 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '핵폐기물 처리 로봇팔 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'nuclear_arm_circuit', file: '/drawings/nuclear_arm_circuit.svg', title: '핵폐기물 처리 로봇팔 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '핵폐기물 처리 로봇팔 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'nuclear_arm_flowchart', file: '/drawings/nuclear_arm_flowchart.svg', title: '핵폐기물 처리 로봇팔 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '핵폐기물 처리 로봇팔 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'nuclear_arm_sequence', file: '/drawings/nuclear_arm_sequence.svg', title: '핵폐기물 처리 로봇팔 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '핵폐기물 처리 로봇팔 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'nuclear_arm_ui_screen', file: '/drawings/nuclear_arm_ui_screen.svg', title: '핵폐기물 처리 로봇팔 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '핵폐기물 처리 로봇팔 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'nuclear_monitor_block_diagram', file: '/drawings/nuclear_monitor_block_diagram.svg', title: '원자력 발전소 감지 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '원자력 발전소 감지 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'nuclear_monitor_circuit', file: '/drawings/nuclear_monitor_circuit.svg', title: '원자력 발전소 감지 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '원자력 발전소 감지 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'nuclear_monitor_flowchart', file: '/drawings/nuclear_monitor_flowchart.svg', title: '원자력 발전소 감지 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '원자력 발전소 감지 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'nuclear_monitor_sequence', file: '/drawings/nuclear_monitor_sequence.svg', title: '원자력 발전소 감지 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '원자력 발전소 감지 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'nuclear_monitor_ui_screen', file: '/drawings/nuclear_monitor_ui_screen.svg', title: '원자력 발전소 감지 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '원자력 발전소 감지 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'ocean_monitor_block_diagram', file: '/drawings/ocean_monitor_block_diagram.svg', title: '해양 환경 모니터링 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '해양 환경 모니터링 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'ocean_monitor_circuit', file: '/drawings/ocean_monitor_circuit.svg', title: '해양 환경 모니터링 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '해양 환경 모니터링 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'ocean_monitor_flowchart', file: '/drawings/ocean_monitor_flowchart.svg', title: '해양 환경 모니터링 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '해양 환경 모니터링 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'ocean_monitor_sequence', file: '/drawings/ocean_monitor_sequence.svg', title: '해양 환경 모니터링 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '해양 환경 모니터링 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'ocean_monitor_ui_screen', file: '/drawings/ocean_monitor_ui_screen.svg', title: '해양 환경 모니터링 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '해양 환경 모니터링 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'ocr_doc_block', file: '/drawings/ocr_doc_block.svg', title: '문서 OCR 변환 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '문서 OCR 변환 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'ocr_doc_flow', file: '/drawings/ocr_doc_flow.svg', title: '문서 OCR 변환 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '문서 OCR 변환 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'parking_block', file: '/drawings/parking_block.svg', title: '스마트 주차장 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 주차장 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'parking_flow', file: '/drawings/parking_flow.svg', title: '스마트 주차장 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 주차장 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'patent_block', file: '/drawings/patent_block.svg', title: '문장 제공 장치 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '문장 제공 장치 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'patent_flow', file: '/drawings/patent_flow.svg', title: '문장 제공 장치 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '문장 제공 장치 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'pet_health_block_diagram', file: '/drawings/pet_health_block_diagram.svg', title: '반려동물 건강 모니터링 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '반려동물 건강 모니터링 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'pet_health_circuit', file: '/drawings/pet_health_circuit.svg', title: '반려동물 건강 모니터링 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '반려동물 건강 모니터링 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'pet_health_flowchart', file: '/drawings/pet_health_flowchart.svg', title: '반려동물 건강 모니터링 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '반려동물 건강 모니터링 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'pet_health_sequence', file: '/drawings/pet_health_sequence.svg', title: '반려동물 건강 모니터링 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '반려동물 건강 모니터링 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'pet_health_ui_screen', file: '/drawings/pet_health_ui_screen.svg', title: '반려동물 건강 모니터링 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '반려동물 건강 모니터링 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'plagiarism_block', file: '/drawings/plagiarism_block.svg', title: '논문 표절 탐지 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '논문 표절 탐지 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'plagiarism_flow', file: '/drawings/plagiarism_flow.svg', title: '논문 표절 탐지 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '논문 표절 탐지 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'plant_factory_block_diagram', file: '/drawings/plant_factory_block_diagram.svg', title: '식물 공장 자동화 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '식물 공장 자동화 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'plant_factory_circuit', file: '/drawings/plant_factory_circuit.svg', title: '식물 공장 자동화 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '식물 공장 자동화 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'plant_factory_flowchart', file: '/drawings/plant_factory_flowchart.svg', title: '식물 공장 자동화 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '식물 공장 자동화 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'plant_factory_sequence', file: '/drawings/plant_factory_sequence.svg', title: '식물 공장 자동화 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '식물 공장 자동화 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'plant_factory_ui_screen', file: '/drawings/plant_factory_ui_screen.svg', title: '식물 공장 자동화 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '식물 공장 자동화 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'quality_block', file: '/drawings/quality_block.svg', title: '제조 품질 검사 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '제조 품질 검사 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'quality_flow', file: '/drawings/quality_flow.svg', title: '제조 품질 검사 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '제조 품질 검사 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'quantum_crypto_block_diagram', file: '/drawings/quantum_crypto_block_diagram.svg', title: '양자 암호 통신 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '양자 암호 통신 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'quantum_crypto_circuit', file: '/drawings/quantum_crypto_circuit.svg', title: '양자 암호 통신 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '양자 암호 통신 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'quantum_crypto_flowchart', file: '/drawings/quantum_crypto_flowchart.svg', title: '양자 암호 통신 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '양자 암호 통신 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'quantum_crypto_sequence', file: '/drawings/quantum_crypto_sequence.svg', title: '양자 암호 통신 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '양자 암호 통신 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'quantum_crypto_ui_screen', file: '/drawings/quantum_crypto_ui_screen.svg', title: '양자 암호 통신 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '양자 암호 통신 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'rag_block', file: '/drawings/rag_block.svg', title: 'RAG 시스템 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'RAG 시스템 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'rag_flow', file: '/drawings/rag_flow.svg', title: 'RAG 시스템 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: 'RAG 시스템 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'recommend_block', file: '/drawings/recommend_block.svg', title: '상품 추천 시스템 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '상품 추천 시스템 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'recommend_flow', file: '/drawings/recommend_flow.svg', title: '상품 추천 시스템 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '상품 추천 시스템 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'recycling_block', file: '/drawings/recycling_block.svg', title: '재활용 자동 분류 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '재활용 자동 분류 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'recycling_flow', file: '/drawings/recycling_flow.svg', title: '재활용 자동 분류 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '재활용 자동 분류 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'resume_match_block', file: '/drawings/resume_match_block.svg', title: '이력서 채용 매칭 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '이력서 채용 매칭 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'resume_match_flow', file: '/drawings/resume_match_flow.svg', title: '이력서 채용 매칭 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '이력서 채용 매칭 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'robot_block', file: '/drawings/robot_block.svg', title: '협동 로봇 제어 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '협동 로봇 제어 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'robot_flow', file: '/drawings/robot_flow.svg', title: '협동 로봇 제어 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '협동 로봇 제어 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'sample_block', file: '/drawings/sample_block.svg', title: '이미지 분류 시스템 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '이미지 분류 시스템 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'sample_flow', file: '/drawings/sample_flow.svg', title: '이미지 분류 시스템 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '이미지 분류 시스템 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'satellite_block', file: '/drawings/satellite_block.svg', title: '위성 영상 모니터링 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '위성 영상 모니터링 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'satellite_comm_block_diagram', file: '/drawings/satellite_comm_block_diagram.svg', title: '저궤도 위성 통신 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '저궤도 위성 통신 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'satellite_comm_circuit', file: '/drawings/satellite_comm_circuit.svg', title: '저궤도 위성 통신 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '저궤도 위성 통신 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'satellite_comm_flowchart', file: '/drawings/satellite_comm_flowchart.svg', title: '저궤도 위성 통신 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '저궤도 위성 통신 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'satellite_comm_sequence', file: '/drawings/satellite_comm_sequence.svg', title: '저궤도 위성 통신 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '저궤도 위성 통신 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'satellite_comm_ui_screen', file: '/drawings/satellite_comm_ui_screen.svg', title: '저궤도 위성 통신 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '저궤도 위성 통신 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'satellite_flow', file: '/drawings/satellite_flow.svg', title: '위성 영상 모니터링 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '위성 영상 모니터링 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'security_block', file: '/drawings/security_block.svg', title: 'AI 영상 보안 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 영상 보안 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'security_flow', file: '/drawings/security_flow.svg', title: 'AI 영상 보안 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: 'AI 영상 보안 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'semiconductor_block', file: '/drawings/semiconductor_block.svg', title: '반도체 결함 검사 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '반도체 결함 검사 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'semiconductor_flow', file: '/drawings/semiconductor_flow.svg', title: '반도체 결함 검사 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '반도체 결함 검사 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'sign_lang_block', file: '/drawings/sign_lang_block.svg', title: '수어 인식 번역 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '수어 인식 번역 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'sign_lang_flow', file: '/drawings/sign_lang_flow.svg', title: '수어 인식 번역 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '수어 인식 번역 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_bandage_block_diagram', file: '/drawings/smart_bandage_block_diagram.svg', title: '스마트 상처 치료 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 상처 치료 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_bandage_circuit', file: '/drawings/smart_bandage_circuit.svg', title: '스마트 상처 치료 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 상처 치료 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_bandage_flowchart', file: '/drawings/smart_bandage_flowchart.svg', title: '스마트 상처 치료 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 상처 치료 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_bandage_sequence', file: '/drawings/smart_bandage_sequence.svg', title: '스마트 상처 치료 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 상처 치료 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_bandage_ui_screen', file: '/drawings/smart_bandage_ui_screen.svg', title: '스마트 상처 치료 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 상처 치료 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_bed_block_diagram', file: '/drawings/smart_bed_block_diagram.svg', title: '스마트 수면 분석 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 수면 분석 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_bed_circuit', file: '/drawings/smart_bed_circuit.svg', title: '스마트 수면 분석 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 수면 분석 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_bed_flowchart', file: '/drawings/smart_bed_flowchart.svg', title: '스마트 수면 분석 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 수면 분석 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_bed_sequence', file: '/drawings/smart_bed_sequence.svg', title: '스마트 수면 분석 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 수면 분석 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_bed_ui_screen', file: '/drawings/smart_bed_ui_screen.svg', title: '스마트 수면 분석 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 수면 분석 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_bridge_block_diagram', file: '/drawings/smart_bridge_block_diagram.svg', title: '스마트 교량 안전 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 교량 안전 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_bridge_circuit', file: '/drawings/smart_bridge_circuit.svg', title: '스마트 교량 안전 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 교량 안전 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_bridge_flowchart', file: '/drawings/smart_bridge_flowchart.svg', title: '스마트 교량 안전 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 교량 안전 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_bridge_sequence', file: '/drawings/smart_bridge_sequence.svg', title: '스마트 교량 안전 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 교량 안전 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_bridge_ui_screen', file: '/drawings/smart_bridge_ui_screen.svg', title: '스마트 교량 안전 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 교량 안전 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_crosswalk_block_diagram', file: '/drawings/smart_crosswalk_block_diagram.svg', title: '스마트 횡단보도 안전 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 횡단보도 안전 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_crosswalk_circuit', file: '/drawings/smart_crosswalk_circuit.svg', title: '스마트 횡단보도 안전 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 횡단보도 안전 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_crosswalk_flowchart', file: '/drawings/smart_crosswalk_flowchart.svg', title: '스마트 횡단보도 안전 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 횡단보도 안전 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_crosswalk_sequence', file: '/drawings/smart_crosswalk_sequence.svg', title: '스마트 횡단보도 안전 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 횡단보도 안전 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_crosswalk_ui_screen', file: '/drawings/smart_crosswalk_ui_screen.svg', title: '스마트 횡단보도 안전 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 횡단보도 안전 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_diaper_block_diagram', file: '/drawings/smart_diaper_block_diagram.svg', title: '스마트 기저귀 감지 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 기저귀 감지 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_diaper_circuit', file: '/drawings/smart_diaper_circuit.svg', title: '스마트 기저귀 감지 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 기저귀 감지 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_diaper_flowchart', file: '/drawings/smart_diaper_flowchart.svg', title: '스마트 기저귀 감지 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 기저귀 감지 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_diaper_sequence', file: '/drawings/smart_diaper_sequence.svg', title: '스마트 기저귀 감지 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 기저귀 감지 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_diaper_ui_screen', file: '/drawings/smart_diaper_ui_screen.svg', title: '스마트 기저귀 감지 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 기저귀 감지 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_factory2_block_diagram', file: '/drawings/smart_factory2_block_diagram.svg', title: 'AI 스마트 공장 자동화 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'AI 스마트 공장 자동화 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_factory2_circuit', file: '/drawings/smart_factory2_circuit.svg', title: 'AI 스마트 공장 자동화 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: 'AI 스마트 공장 자동화 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_factory2_flowchart', file: '/drawings/smart_factory2_flowchart.svg', title: 'AI 스마트 공장 자동화 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: 'AI 스마트 공장 자동화 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_factory2_sequence', file: '/drawings/smart_factory2_sequence.svg', title: 'AI 스마트 공장 자동화 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: 'AI 스마트 공장 자동화 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_factory2_ui_screen', file: '/drawings/smart_factory2_ui_screen.svg', title: 'AI 스마트 공장 자동화 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: 'AI 스마트 공장 자동화 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_farm2_block_diagram', file: '/drawings/smart_farm2_block_diagram.svg', title: '스마트 팜 정밀 농업 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 팜 정밀 농업 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_farm2_circuit', file: '/drawings/smart_farm2_circuit.svg', title: '스마트 팜 정밀 농업 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 팜 정밀 농업 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_farm2_flowchart', file: '/drawings/smart_farm2_flowchart.svg', title: '스마트 팜 정밀 농업 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 팜 정밀 농업 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_farm2_sequence', file: '/drawings/smart_farm2_sequence.svg', title: '스마트 팜 정밀 농업 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 팜 정밀 농업 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_farm2_ui_screen', file: '/drawings/smart_farm2_ui_screen.svg', title: '스마트 팜 정밀 농업 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 팜 정밀 농업 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_glasses_block_diagram', file: '/drawings/smart_glasses_block_diagram.svg', title: '스마트 안경 보조 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 안경 보조 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_glasses_circuit', file: '/drawings/smart_glasses_circuit.svg', title: '스마트 안경 보조 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 안경 보조 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_glasses_flowchart', file: '/drawings/smart_glasses_flowchart.svg', title: '스마트 안경 보조 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 안경 보조 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_glasses_sequence', file: '/drawings/smart_glasses_sequence.svg', title: '스마트 안경 보조 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 안경 보조 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_glasses_ui_screen', file: '/drawings/smart_glasses_ui_screen.svg', title: '스마트 안경 보조 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 안경 보조 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_gym_block_diagram', file: '/drawings/smart_gym_block_diagram.svg', title: '스마트 헬스장 AI 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 헬스장 AI 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_gym_circuit', file: '/drawings/smart_gym_circuit.svg', title: '스마트 헬스장 AI 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 헬스장 AI 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_gym_flowchart', file: '/drawings/smart_gym_flowchart.svg', title: '스마트 헬스장 AI 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 헬스장 AI 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_gym_sequence', file: '/drawings/smart_gym_sequence.svg', title: '스마트 헬스장 AI 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 헬스장 AI 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_gym_ui_screen', file: '/drawings/smart_gym_ui_screen.svg', title: '스마트 헬스장 AI 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 헬스장 AI 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_helmet_block_diagram', file: '/drawings/smart_helmet_block_diagram.svg', title: '스마트 안전모 IoT 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 안전모 IoT 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_helmet_circuit', file: '/drawings/smart_helmet_circuit.svg', title: '스마트 안전모 IoT 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 안전모 IoT 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_helmet_flowchart', file: '/drawings/smart_helmet_flowchart.svg', title: '스마트 안전모 IoT 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 안전모 IoT 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_helmet_sequence', file: '/drawings/smart_helmet_sequence.svg', title: '스마트 안전모 IoT 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 안전모 IoT 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_helmet_ui_screen', file: '/drawings/smart_helmet_ui_screen.svg', title: '스마트 안전모 IoT 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 안전모 IoT 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_irrigation_block_diagram', file: '/drawings/smart_irrigation_block_diagram.svg', title: '정밀 관개 자동화 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '정밀 관개 자동화 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_irrigation_circuit', file: '/drawings/smart_irrigation_circuit.svg', title: '정밀 관개 자동화 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '정밀 관개 자동화 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_irrigation_flowchart', file: '/drawings/smart_irrigation_flowchart.svg', title: '정밀 관개 자동화 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '정밀 관개 자동화 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_irrigation_sequence', file: '/drawings/smart_irrigation_sequence.svg', title: '정밀 관개 자동화 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '정밀 관개 자동화 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_irrigation_ui_screen', file: '/drawings/smart_irrigation_ui_screen.svg', title: '정밀 관개 자동화 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '정밀 관개 자동화 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_meter2_block_diagram', file: '/drawings/smart_meter2_block_diagram.svg', title: '스마트 에너지 미터링 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 에너지 미터링 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_meter2_circuit', file: '/drawings/smart_meter2_circuit.svg', title: '스마트 에너지 미터링 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 에너지 미터링 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_meter2_flowchart', file: '/drawings/smart_meter2_flowchart.svg', title: '스마트 에너지 미터링 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 에너지 미터링 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_meter2_sequence', file: '/drawings/smart_meter2_sequence.svg', title: '스마트 에너지 미터링 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 에너지 미터링 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_meter2_ui_screen', file: '/drawings/smart_meter2_ui_screen.svg', title: '스마트 에너지 미터링 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 에너지 미터링 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_port_block_diagram', file: '/drawings/smart_port_block_diagram.svg', title: '스마트 항만 물류 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 항만 물류 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_port_circuit', file: '/drawings/smart_port_circuit.svg', title: '스마트 항만 물류 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 항만 물류 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_port_flowchart', file: '/drawings/smart_port_flowchart.svg', title: '스마트 항만 물류 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 항만 물류 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_port_sequence', file: '/drawings/smart_port_sequence.svg', title: '스마트 항만 물류 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 항만 물류 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_port_ui_screen', file: '/drawings/smart_port_ui_screen.svg', title: '스마트 항만 물류 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 항만 물류 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_prison_block_diagram', file: '/drawings/smart_prison_block_diagram.svg', title: '스마트 교정시설 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 교정시설 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_prison_circuit', file: '/drawings/smart_prison_circuit.svg', title: '스마트 교정시설 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 교정시설 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_prison_flowchart', file: '/drawings/smart_prison_flowchart.svg', title: '스마트 교정시설 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 교정시설 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_prison_sequence', file: '/drawings/smart_prison_sequence.svg', title: '스마트 교정시설 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 교정시설 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_prison_ui_screen', file: '/drawings/smart_prison_ui_screen.svg', title: '스마트 교정시설 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 교정시설 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_shelf_block_diagram', file: '/drawings/smart_shelf_block_diagram.svg', title: '스마트 진열대 재고 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 진열대 재고 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_shelf_circuit', file: '/drawings/smart_shelf_circuit.svg', title: '스마트 진열대 재고 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 진열대 재고 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_shelf_flowchart', file: '/drawings/smart_shelf_flowchart.svg', title: '스마트 진열대 재고 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 진열대 재고 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_shelf_sequence', file: '/drawings/smart_shelf_sequence.svg', title: '스마트 진열대 재고 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 진열대 재고 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_shelf_ui_screen', file: '/drawings/smart_shelf_ui_screen.svg', title: '스마트 진열대 재고 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 진열대 재고 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_shoe_block_diagram', file: '/drawings/smart_shoe_block_diagram.svg', title: '스마트 신발 보행 분석 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 신발 보행 분석 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_shoe_circuit', file: '/drawings/smart_shoe_circuit.svg', title: '스마트 신발 보행 분석 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 신발 보행 분석 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_shoe_flowchart', file: '/drawings/smart_shoe_flowchart.svg', title: '스마트 신발 보행 분석 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 신발 보행 분석 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_shoe_sequence', file: '/drawings/smart_shoe_sequence.svg', title: '스마트 신발 보행 분석 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 신발 보행 분석 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_shoe_ui_screen', file: '/drawings/smart_shoe_ui_screen.svg', title: '스마트 신발 보행 분석 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 신발 보행 분석 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_toilet2_block_diagram', file: '/drawings/smart_toilet2_block_diagram.svg', title: '공중화장실 청결 관리 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '공중화장실 청결 관리 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_toilet2_circuit', file: '/drawings/smart_toilet2_circuit.svg', title: '공중화장실 청결 관리 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '공중화장실 청결 관리 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_toilet2_flowchart', file: '/drawings/smart_toilet2_flowchart.svg', title: '공중화장실 청결 관리 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '공중화장실 청결 관리 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_toilet2_sequence', file: '/drawings/smart_toilet2_sequence.svg', title: '공중화장실 청결 관리 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '공중화장실 청결 관리 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_toilet2_ui_screen', file: '/drawings/smart_toilet2_ui_screen.svg', title: '공중화장실 청결 관리 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '공중화장실 청결 관리 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_toilet_block_diagram', file: '/drawings/smart_toilet_block_diagram.svg', title: '스마트 건강 화장실 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 건강 화장실 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_toilet_circuit', file: '/drawings/smart_toilet_circuit.svg', title: '스마트 건강 화장실 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 건강 화장실 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_toilet_flowchart', file: '/drawings/smart_toilet_flowchart.svg', title: '스마트 건강 화장실 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 건강 화장실 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_toilet_sequence', file: '/drawings/smart_toilet_sequence.svg', title: '스마트 건강 화장실 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 건강 화장실 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_toilet_ui_screen', file: '/drawings/smart_toilet_ui_screen.svg', title: '스마트 건강 화장실 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 건강 화장실 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smart_window_block_diagram', file: '/drawings/smart_window_block_diagram.svg', title: '스마트 창문 제어 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 창문 제어 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smart_window_circuit', file: '/drawings/smart_window_circuit.svg', title: '스마트 창문 제어 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 창문 제어 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'smart_window_flowchart', file: '/drawings/smart_window_flowchart.svg', title: '스마트 창문 제어 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 창문 제어 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smart_window_sequence', file: '/drawings/smart_window_sequence.svg', title: '스마트 창문 제어 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 창문 제어 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'smart_window_ui_screen', file: '/drawings/smart_window_ui_screen.svg', title: '스마트 창문 제어 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 창문 제어 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'smartgrid_block', file: '/drawings/smartgrid_block.svg', title: '스마트 전력망 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 전력망 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smartgrid_flow', file: '/drawings/smartgrid_flow.svg', title: '스마트 전력망 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 전력망 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'smarthome_block', file: '/drawings/smarthome_block.svg', title: '스마트홈 에너지 관리 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트홈 에너지 관리 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'smarthome_flow', file: '/drawings/smarthome_flow.svg', title: '스마트홈 에너지 관리 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트홈 에너지 관리 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'space_debris_block_diagram', file: '/drawings/space_debris_block_diagram.svg', title: '우주 파편 추적 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '우주 파편 추적 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'space_debris_circuit', file: '/drawings/space_debris_circuit.svg', title: '우주 파편 추적 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '우주 파편 추적 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'space_debris_flowchart', file: '/drawings/space_debris_flowchart.svg', title: '우주 파편 추적 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '우주 파편 추적 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'space_debris_sequence', file: '/drawings/space_debris_sequence.svg', title: '우주 파편 추적 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '우주 파편 추적 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'space_debris_ui_screen', file: '/drawings/space_debris_ui_screen.svg', title: '우주 파편 추적 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '우주 파편 추적 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'speech_block', file: '/drawings/speech_block.svg', title: '음성 인식 번역 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '음성 인식 번역 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'speech_flow', file: '/drawings/speech_flow.svg', title: '음성 인식 번역 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '음성 인식 번역 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'supply_chain_block', file: '/drawings/supply_chain_block.svg', title: '블록체인 공급망 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '블록체인 공급망 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'supply_chain_flow', file: '/drawings/supply_chain_flow.svg', title: '블록체인 공급망 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '블록체인 공급망 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'telemedicine_block_diagram', file: '/drawings/telemedicine_block_diagram.svg', title: '스마트 원격 진료 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 원격 진료 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'telemedicine_circuit', file: '/drawings/telemedicine_circuit.svg', title: '스마트 원격 진료 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '스마트 원격 진료 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'telemedicine_flowchart', file: '/drawings/telemedicine_flowchart.svg', title: '스마트 원격 진료 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 원격 진료 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'telemedicine_sequence', file: '/drawings/telemedicine_sequence.svg', title: '스마트 원격 진료 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '스마트 원격 진료 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'telemedicine_ui_screen', file: '/drawings/telemedicine_ui_screen.svg', title: '스마트 원격 진료 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '스마트 원격 진료 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'traffic_block', file: '/drawings/traffic_block.svg', title: '교통 신호 최적화 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '교통 신호 최적화 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'traffic_flow', file: '/drawings/traffic_flow.svg', title: '교통 신호 최적화 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '교통 신호 최적화 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'translation_block', file: '/drawings/translation_block.svg', title: '전문 용어 번역 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '전문 용어 번역 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'translation_flow', file: '/drawings/translation_flow.svg', title: '전문 용어 번역 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '전문 용어 번역 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'tunnel_safety_block_diagram', file: '/drawings/tunnel_safety_block_diagram.svg', title: '터널 안전 모니터링 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '터널 안전 모니터링 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'tunnel_safety_circuit', file: '/drawings/tunnel_safety_circuit.svg', title: '터널 안전 모니터링 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '터널 안전 모니터링 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'tunnel_safety_flowchart', file: '/drawings/tunnel_safety_flowchart.svg', title: '터널 안전 모니터링 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '터널 안전 모니터링 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'tunnel_safety_sequence', file: '/drawings/tunnel_safety_sequence.svg', title: '터널 안전 모니터링 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '터널 안전 모니터링 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'tunnel_safety_ui_screen', file: '/drawings/tunnel_safety_ui_screen.svg', title: '터널 안전 모니터링 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '터널 안전 모니터링 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'underwater_robot_block_diagram', file: '/drawings/underwater_robot_block_diagram.svg', title: '수중 탐사 로봇 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '수중 탐사 로봇 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'underwater_robot_circuit', file: '/drawings/underwater_robot_circuit.svg', title: '수중 탐사 로봇 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '수중 탐사 로봇 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'underwater_robot_flowchart', file: '/drawings/underwater_robot_flowchart.svg', title: '수중 탐사 로봇 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '수중 탐사 로봇 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'underwater_robot_sequence', file: '/drawings/underwater_robot_sequence.svg', title: '수중 탐사 로봇 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '수중 탐사 로봇 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'underwater_robot_ui_screen', file: '/drawings/underwater_robot_ui_screen.svg', title: '수중 탐사 로봇 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '수중 탐사 로봇 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'voice_id_block_diagram', file: '/drawings/voice_id_block_diagram.svg', title: '화자 인식 보안 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '화자 인식 보안 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'voice_id_circuit', file: '/drawings/voice_id_circuit.svg', title: '화자 인식 보안 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: '화자 인식 보안 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'voice_id_flowchart', file: '/drawings/voice_id_flowchart.svg', title: '화자 인식 보안 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '화자 인식 보안 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'voice_id_sequence', file: '/drawings/voice_id_sequence.svg', title: '화자 인식 보안 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: '화자 인식 보안 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'voice_id_ui_screen', file: '/drawings/voice_id_ui_screen.svg', title: '화자 인식 보안 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: '화자 인식 보안 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'vr_rehab_block_diagram', file: '/drawings/vr_rehab_block_diagram.svg', title: 'VR 재활 치료 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: 'VR 재활 치료 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'vr_rehab_circuit', file: '/drawings/vr_rehab_circuit.svg', title: 'VR 재활 치료 회로도', type: 'circuit', typeLabel: 'CIRCUIT', desc: 'VR 재활 치료 특허 도면 — 회로도.', grade: 'A', score: 100 },
  { id: 'vr_rehab_flowchart', file: '/drawings/vr_rehab_flowchart.svg', title: 'VR 재활 치료 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: 'VR 재활 치료 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'vr_rehab_sequence', file: '/drawings/vr_rehab_sequence.svg', title: 'VR 재활 치료 시퀀스 다이어그램', type: 'sequence', typeLabel: 'SEQUENCE', desc: 'VR 재활 치료 특허 도면 — 시퀀스 다이어그램.', grade: 'A', score: 100 },
  { id: 'vr_rehab_ui_screen', file: '/drawings/vr_rehab_ui_screen.svg', title: 'VR 재활 치료 화면 예시도', type: 'ui_screen', typeLabel: 'UI SCREEN', desc: 'VR 재활 치료 특허 도면 — 화면 예시도.', grade: 'A', score: 100 },
  { id: 'water_block', file: '/drawings/water_block.svg', title: '스마트 수질 모니터링 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '스마트 수질 모니터링 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'water_flow', file: '/drawings/water_flow.svg', title: '스마트 수질 모니터링 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '스마트 수질 모니터링 특허 도면 — 흐름도.', grade: 'A', score: 100 },
  { id: 'wearable_block', file: '/drawings/wearable_block.svg', title: '웨어러블 건강 모니터링 블록도', type: 'block_diagram', typeLabel: 'BLOCK DIAGRAM', desc: '웨어러블 건강 모니터링 특허 도면 — 블록도.', grade: 'A', score: 100 },
  { id: 'wearable_flow', file: '/drawings/wearable_flow.svg', title: '웨어러블 건강 모니터링 흐름도', type: 'flowchart', typeLabel: 'FLOWCHART', desc: '웨어러블 건강 모니터링 특허 도면 — 흐름도.', grade: 'A', score: 100 },
]

const PAGE_SIZE = 12
const typeFilters = [
  { id: 'all',          label: '전체' },
  { id: 'block_diagram',label: '블록도' },
  { id: 'flowchart',    label: '흐름도' },
  { id: 'sequence',     label: '시퀀스' },
  { id: 'ui_screen',    label: '화면예시도' },
  { id: 'circuit',      label: '회로도' },
]

const TYPE_COLOR: Record<string, string> = {
  block_diagram: '#1a6fb5',
  flowchart:     '#27ae60',
  sequence:      '#8e44ad',
  ui_screen:     '#e67e22',
  circuit:       '#c0392b',
}

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
                <div className="gallery-type" style={{ color: TYPE_COLOR[d.type] ?? '#C9A84C' }}>{d.typeLabel}</div>
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
