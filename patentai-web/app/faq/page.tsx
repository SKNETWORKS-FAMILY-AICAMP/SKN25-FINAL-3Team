'use client'

import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import Nav from '@/components/Nav'
import Footer from '@/components/Footer'
import Link from 'next/link'
import { useLang } from '@/contexts/LangContext'
import { t, tr } from '@/lib/i18n'

const categories = [
  { id: 'all',      sub: 'ALL' },
  { id: 'filing',   sub: 'PATENT FILING' },
  { id: 'service',  sub: 'OUR SERVICE' },
  { id: 'priorart', sub: 'PRIOR ART' },
  { id: 'spec',     sub: 'SPECIFICATION' },
  { id: 'drawing',  sub: 'DRAWING' },
  { id: 'cost',     sub: 'COST & TIMELINE' },
  { id: 'usage',    sub: 'HOW TO USE' },
]

const faqs: { cat: string; q: string; a: string; ref: string | null }[] = [
  // ────────────────────────────────────────────────────────────────────
  // 특허 출원 (filing) — 20개
  // ────────────────────────────────────────────────────────────────────
  {
    cat: 'filing',
    q: '특허 출원이란 무엇인가요?',
    a: '특허 출원은 발명자가 특허청에 발명의 보호를 요청하는 법적 절차입니다. 출원서, 명세서(청구항·발명의 설명·도면)를 작성하여 특허청에 제출하면 심사를 거쳐 등록 여부가 결정됩니다. 출원일부터 20년간 독점적 실시권이 부여됩니다.',
    ref: '특허법 제42조',
  },
  {
    cat: 'filing',
    q: '출원서 작성부터 접수까지 얼마나 걸리나요?',
    a: '일반적으로 2~4주가 소요됩니다. PatentAI를 이용하면 명세서 초안을 수 시간 내 생성할 수 있어 전체 준비 기간을 대폭 단축할 수 있습니다. 특허청 심사 및 등록까지는 통상 14~18개월이 소요됩니다.',
    ref: '특허청 심사처리기간 기준',
  },
  {
    cat: 'filing',
    q: '해외 특허 출원은 어떻게 하나요?',
    a: 'PCT(특허협력조약) 국제출원을 통해 1건의 출원으로 160개국 이상에서 동시 보호를 받을 수 있습니다. 우선일로부터 30개월 내에 각국에 진입할 수 있으며, 미국(USPTO)·유럽(EPO)·일본(JPO)·중국(CNIPA) 직접 출원도 지원합니다.',
    ref: 'PCT 국제조약',
  },
  {
    cat: 'filing',
    q: '우선권 주장이란 무엇인가요?',
    a: '파리 협약에 따라 국내 최초 출원일로부터 12개월 내에 해외 출원 시 국내 출원일을 해외 출원일로 인정받는 제도입니다. 이를 통해 해외 출원 준비 기간을 확보하면서도 신규성을 유지할 수 있습니다.',
    ref: '파리 협약 제4조',
  },
  {
    cat: 'service',
    q: 'PatentAI는 어떤 서비스인가요?',
    a: 'PatentAI는 AI 기반 지식재산 상담 시스템으로, 발명 상담 구조화, 선행기술 조사, 명세서·청구항 작성, 특허 도면 자동 생성, 심사 대응까지 특허 출원 전 과정을 자동화합니다. 변리사의 핵심 업무를 AI가 보조하여 시간과 비용을 대폭 절감합니다.',
    ref: null,
  },
  {
    cat: 'service',
    q: 'AI가 작성한 명세서를 바로 출원에 사용할 수 있나요?',
    a: 'PatentAI가 생성하는 명세서는 고품질 초안입니다. 특허청 제출 전 전문 변리사의 최종 검토를 권장합니다. AI 초안을 활용하면 변리사 작업 시간이 60~80% 단축되어 전체 비용이 절감됩니다.',
    ref: null,
  },
  {
    cat: 'service',
    q: '상담 내용과 발명 정보는 어떻게 보호되나요?',
    a: '모든 상담 내용은 AES-256 암호화를 적용하여 저장됩니다. 제3자와의 정보 공유는 일절 없으며, 개인정보보호법 및 영업비밀보호법에 따라 발명 내용의 기밀성을 엄격히 보장합니다.',
    ref: '개인정보보호법 제24조',
  },
  {
    cat: 'service',
    q: '서비스 이용에 전문 지식이 필요한가요?',
    a: '전혀 필요하지 않습니다. 발명 아이디어만 있으면 충분합니다. PatentAI의 상담 에이전트가 단계별 질문을 통해 발명의 문제점·해결수단·효과·구성요소를 체계적으로 정리해 드립니다.',
    ref: null,
  },
  {
    cat: 'priorart',
    q: '선행기술 조사가 왜 중요한가요?',
    a: '선행기술 조사는 동일·유사 기술의 기존 특허 존재 여부를 사전에 파악하는 핵심 단계입니다. 조사 없이 출원하면 신규성·진보성 결여로 거절될 위험이 높으며, 등록 후에도 무효심판 위험이 있습니다. 조사 결과를 바탕으로 권리범위를 차별화하는 출원 전략을 수립할 수 있습니다.',
    ref: '특허법 제29조 (신규성·진보성)',
  },
  {
    cat: 'priorart',
    q: '어떤 데이터베이스를 활용하나요?',
    a: 'KIPRIS(한국), USPTO(미국), EPO(유럽), JPO(일본), CNIPA(중국) 등 주요국 특허 DB를 활용합니다. PatentAI는 단순 키워드 검색이 아닌 임베딩 벡터 유사도와 키워드 하이브리드 검색을 결합하여 더 정확한 관련 특허를 탐색합니다.',
    ref: 'KIPRIS · USPTO · EPO Espacenet',
  },
  {
    cat: 'priorart',
    q: '조사 결과 보고서는 어떻게 제공되나요?',
    a: '유사도 점수(0~1), 유사 특허 TOP-N 목록, 신규성·진보성 위험도 등급, 출원 전략 권고사항이 포함된 리포트를 제공합니다. 각 유사 특허의 청구항 비교표도 함께 제공됩니다.',
    ref: null,
  },
  {
    cat: 'spec',
    q: '청구항 작성 시 가장 중요한 것은 무엇인가요?',
    a: '청구항은 특허권의 보호범위를 결정하는 가장 중요한 부분입니다. 권리범위가 너무 넓으면 신규성·진보성 문제로 거절되고, 너무 좁으면 경쟁사가 쉽게 회피할 수 있습니다. PatentAI는 선행기술 조사 결과를 반영하여 적절한 권리범위의 독립항·종속항을 자동 생성합니다.',
    ref: '특허법 제42조 제4항',
  },
  {
    cat: 'spec',
    q: '명세서에는 어떤 내용이 포함되어야 하나요?',
    a: '특허 명세서는 발명의 명칭, 기술분야, 배경기술, 발명의 내용(과제·해결수단·효과), 도면의 간단한 설명, 발명을 실시하기 위한 구체적인 내용, 청구범위, 도면으로 구성됩니다. PatentAI는 상담 내용을 바탕으로 각 항목을 자동 초안화합니다.',
    ref: '특허법 제42조 제2항',
  },
  {
    cat: 'drawing',
    q: '특허 도면은 어떤 기준을 충족해야 하나요?',
    a: '특허청 도면 기준에 따라 흑백 선화로 작성해야 하며, 도면부호(참조번호)를 명시해야 합니다. 도면의 크기·여백·선 굵기 등 형식 요건도 충족해야 합니다. PatentAI는 이러한 특허청 실무 기준을 자동으로 반영하여 SVG/PNG 도면을 생성합니다.',
    ref: '특허법 시행규칙 별지 제15호',
  },
  {
    cat: 'drawing',
    q: '어떤 종류의 도면을 생성할 수 있나요?',
    a: '블록도(시스템 구성), 흐름도(알고리즘·절차), 시퀀스 다이어그램(통신·상호작용), 상태도(상태 전이), UI 화면도 등 5가지 유형을 지원합니다. 명세서 텍스트를 분석하여 적합한 도면 유형을 자동 판별합니다.',
    ref: null,
  },
  {
    cat: 'drawing',
    q: '도면 품질은 어떻게 보장되나요?',
    a: '생성된 도면에 대해 도면부호 완비 여부, 구성요소 충족 여부, 렌더링 품질을 자동 검증하여 100점 만점의 품질 점수와 A~D 등급을 산출합니다. 75점 미만 도면은 자동 보정 과정을 거칩니다.',
    ref: null,
  },
  {
    cat: 'cost',
    q: '특허 출원 관련 비용은 어떻게 되나요?',
    a: '특허청 관납료(출원료 56,000원~, 심사청구료 143,000원~/청구항)와 변리사 수수료(평균 150~350만원)로 구성됩니다. PatentAI 이용 시 명세서 초안 작성 비용을 절감하여 전체 비용을 20~40% 줄일 수 있습니다.',
    ref: '특허법 시행규칙 별표 3 관납료',
  },
  {
    cat: 'cost',
    q: '심사청구는 언제까지 해야 하나요?',
    a: '출원일로부터 3년 이내에 심사청구를 하지 않으면 출원이 취하된 것으로 간주됩니다. 조기 심사청구(우선심사)를 이용하면 평균 2~5개월 내에 심사결과를 받을 수 있으며, 벤처기업·중소기업·녹색기술 등은 우선심사 대상입니다.',
    ref: '특허법 제59조',
  },
  {
    cat: 'usage',
    q: '어떻게 시작하면 되나요?',
    a: '상담 신청 페이지에서 발명 내용을 간단히 기재해 주시면, 담당자가 영업일 기준 1~2일 내 연락드립니다. 또는 우측 하단 AI 상담 도우미를 통해 즉시 질문하실 수도 있습니다.',
    ref: null,
  },
  {
    cat: 'usage',
    q: '스타트업·개인 발명가도 이용할 수 있나요?',
    a: 'PatentAI는 대기업부터 스타트업·개인 발명가까지 모두 이용 가능합니다. 특히 특허 전담 부서가 없는 스타트업과 비용이 부담되는 개인 발명가에게 AI 자동화로 시간과 비용을 절감할 수 있어 더욱 유용합니다.',
    ref: null,
  },

  // ────────────────────────────────────────────────────────────────────
  // 특허 출원 추가 (filing)
  // ────────────────────────────────────────────────────────────────────
  { cat:'filing', q:'특허와 실용신안의 차이는 무엇인가요?', a:'특허는 고도의 창작물을 보호(보호기간 20년)하고, 실용신안은 물품의 형상·구조에 관한 고안을 보호(보호기간 10년)합니다. 실용신안은 심사가 간소하고 출원 비용이 낮지만 보호 수준도 상대적으로 낮습니다. 소프트웨어·방법 발명은 특허로만 출원 가능합니다.', ref:'특허법 제2조·실용신안법 제2조' },
  { cat:'filing', q:'특허를 받을 수 있는 발명의 조건은?', a:'특허를 받으려면 ① 신규성(출원 전 공지되지 않을 것) ② 진보성(통상의 기술자가 쉽게 발명할 수 없을 것) ③ 산업상 이용가능성(산업에 이용 가능할 것) 세 가지 요건을 충족해야 합니다. 공서양속에 반하는 발명은 특허를 받을 수 없습니다.', ref:'특허법 제29조' },
  { cat:'filing', q:'특허 출원 전에 발명을 공개하면 어떻게 되나요?', a:'원칙적으로 출원 전 공개는 신규성을 상실시킵니다. 다만 발명자 본인이 공개한 경우 공개일로부터 12개월 이내에 출원하면 신규성 상실 예외를 주장할 수 있습니다(공지예외주장). 논문 발표, 전시회 참가, 인터넷 게시 모두 적용됩니다.', ref:'특허법 제30조' },
  { cat:'filing', q:'공동 발명인 경우 출원은 어떻게 하나요?', a:'공동 발명의 경우 발명자 전원이 공동으로 출원해야 합니다. 출원인(권리자)은 발명자와 다를 수 있으며, 회사·연구소 등 법인도 출원인이 될 수 있습니다. 공동 발명자 일부가 누락된 경우 무효 사유가 될 수 있으므로 주의가 필요합니다.', ref:'특허법 제33조' },
  { cat:'filing', q:'직무발명이란 무엇인가요?', a:'직무발명은 종업원이 업무 범위 내에서 이룩한 발명입니다. 사용자(회사)는 사전 계약이나 근무규정이 있으면 직무발명에 대한 특허권을 승계받을 수 있으며, 이 경우 발명자에게 정당한 보상을 해야 합니다. 직무발명을 무단으로 유출하면 형사처벌 대상이 됩니다.', ref:'발명진흥법 제10조' },
  { cat:'filing', q:'특허 출원 후 심사까지 얼마나 걸리나요?', a:'일반 심사의 경우 심사청구 후 평균 14~18개월이 소요됩니다. 우선심사를 신청하면 2~5개월로 단축됩니다. 벤처기업·중소기업·녹색기술·재난안전기술 분야는 우선심사 신청이 가능합니다. 출원 공개는 출원일로부터 18개월 후 자동으로 이루어집니다.', ref:'특허법 제59조' },
  { cat:'filing', q:'분할출원이란 무엇인가요?', a:'하나의 출원에 두 가지 이상의 발명이 포함된 경우, 또는 심사 과정에서 일부 청구항을 분리하여 별도 출원하는 것입니다. 분할출원은 원출원의 출원일을 소급 적용받을 수 있어 신규성 판단에 유리합니다. 특허 결정 또는 거절 확정 전까지 가능합니다.', ref:'특허법 제52조' },
  { cat:'filing', q:'조약우선권이란 무엇인가요?', a:'파리 협약에 따라 최초 출원일(우선일)로부터 12개월 내에 다른 국가에 출원하면 최초 출원일을 기준으로 신규성·진보성을 판단받는 제도입니다. 이를 통해 해외 경쟁자가 그 기간 동안 같은 발명을 출원하더라도 우선권을 유지할 수 있습니다.', ref:'파리 협약 제4조' },
  { cat:'filing', q:'특허 등록 후에도 무효가 될 수 있나요?', a:'네. 제3자가 특허심판원에 무효심판을 청구하면 등록된 특허도 무효가 될 수 있습니다. 신규성·진보성 결여, 명세서 기재불비, 발명자 기재 오류 등이 주요 무효 사유입니다. 이 때문에 출원 전 철저한 선행기술 조사와 명세서 작성이 중요합니다.', ref:'특허법 제133조' },
  { cat:'filing', q:'특허권의 존속기간은 얼마인가요?', a:'특허권의 존속기간은 출원일로부터 20년입니다. 의약품·농약의 경우 허가 취득 기간을 고려한 존속기간 연장(최대 5년)이 가능합니다. 존속기간이 만료되면 누구나 자유롭게 해당 기술을 사용할 수 있습니다.', ref:'특허법 제88조' },
  { cat:'filing', q:'특허료를 납부하지 않으면 어떻게 되나요?', a:'등록 후 매년 특허료(연차료)를 납부해야 합니다. 납부 기간 내에 납부하지 않으면 특허권이 소멸합니다. 소멸 후 6개월 이내에 추납하면 회복이 가능하며, 추납 기간도 경과하면 권리가 완전히 소멸합니다.', ref:'특허법 제79조·제81조' },
  { cat:'filing', q:'특허 출원 후 발명 내용을 수정할 수 있나요?', a:'출원 후 보정은 출원일에 최초로 첨부된 명세서의 범위를 벗어나지 않는 한도에서 가능합니다(신규사항 추가 불가). 심사관의 거절이유 통지를 받은 경우 의견서와 함께 보정서를 제출할 수 있습니다. 등록 결정 후에는 청구항 삭제만 가능합니다.', ref:'특허법 제47조' },
  { cat:'filing', q:'국내 출원과 PCT 출원의 차이는?', a:'국내 출원은 국내 특허청에만 효력이 있는 출원이고, PCT 출원은 1건의 출원으로 160개국 이상에서 동시에 출원 효과를 가지는 국제출원입니다. PCT 출원 후 각국 진입 기한(우선일로부터 30개월)까지 실제 해외 출원을 결정할 수 있어 비용과 시간을 절약할 수 있습니다.', ref:'PCT 조약 제11조' },
  { cat:'filing', q:'특허와 영업비밀 중 어떤 것이 더 유리한가요?', a:'특허는 공개 대신 20년의 독점권을 얻지만, 만료 후 누구나 사용 가능합니다. 영업비밀은 공개하지 않아도 되고 기간 제한이 없지만, 비밀이 누출되거나 타인이 독자 개발하면 보호가 어렵습니다. 제조 공정처럼 역공학이 어려운 기술은 영업비밀로, 제품 구조처럼 역공학이 쉬운 기술은 특허로 보호하는 것이 일반적입니다.', ref:'부정경쟁방지법 제2조' },
  { cat:'filing', q:'임시 명세서 출원이란 무엇인가요?', a:'정식 명세서 없이 발명의 내용이 기재된 서류(임시 명세서)만으로 출원일을 확보하는 제도입니다. 12개월 내에 정식 명세서를 제출해야 하며, 이 기간 동안 발명을 보완하거나 해외 출원 여부를 결정할 수 있습니다. 조기에 출원일을 확보해야 할 때 유용합니다.', ref:'특허법 제42조의2' },
  { cat:'filing', q:'특허 침해 시 어떤 조치를 취할 수 있나요?', a:'특허권 침해에 대해 ① 민사상 침해금지 청구 ② 손해배상 청구 ③ 형사고소(7년 이하 징역 또는 1억원 이하 벌금)가 가능합니다. 먼저 경고장을 발송하거나 특허심판원에 권리범위확인심판을 청구하는 방법도 있습니다. 침해 증거 수집이 중요합니다.', ref:'특허법 제126조·제225조' },
  { cat:'filing', q:'특허 출원 전 비밀유지 계약(NDA)이 필요한가요?', a:'제3자에게 발명 내용을 공개하기 전에 비밀유지 계약(NDA)을 체결하는 것이 안전합니다. 미공개 상태에서 투자자·개발자 등과 협의가 필요한 경우 NDA 없이 공개하면 신규성을 잃을 수 있습니다. 단, 12개월 이내에 출원하면 신규성 상실 예외가 적용될 수 있습니다.', ref:'특허법 제30조' },
  { cat:'filing', q:'특허청에 직접 출원하는 것과 변리사를 통하는 것의 차이는?', a:'특허청에 직접 출원(셀프 출원)은 비용을 절약할 수 있지만, 청구범위 작성 미숙으로 권리 범위가 좁아지거나 거절될 위험이 높습니다. 변리사는 전문 지식으로 최적의 권리 범위를 설정하고 심사 대응을 돕습니다. PatentAI는 AI 초안으로 셀프 출원의 품질을 높이거나 변리사 비용을 절감하는 데 활용할 수 있습니다.', ref:null },
  { cat:'filing', q:'특허 등록 결정을 받은 후 절차는?', a:'등록 결정 후 30일 이내에 등록료(1~3년분)를 납부해야 특허권이 발생합니다. 납부 후 특허 등록원부에 등록되고 특허증이 발급됩니다. 이후 매년 연차료를 납부하여 권리를 유지해야 합니다. 등록료 미납 시 등록 결정이 취소될 수 있습니다.', ref:'특허법 제79조' },

  // ────────────────────────────────────────────────────────────────────
  // PatentAI 서비스 추가 (service)
  // ────────────────────────────────────────────────────────────────────
  { cat:'service', q:'PatentAI와 일반 변리사 사무소의 차이점은?', a:'일반 변리사 사무소는 전문가의 경험과 판단을 바탕으로 맞춤형 서비스를 제공하며, 복잡한 분쟁 대응에 강점이 있습니다. PatentAI는 AI로 초안 작성·선행기술 조사·도면 생성을 자동화하여 비용과 시간을 절감합니다. 두 방식을 병행하면 AI가 초안을 작성하고 변리사가 검토·보완하는 최적의 시너지를 낼 수 있습니다.', ref:null },
  { cat:'service', q:'PatentAI 이용 시 데이터는 어느 서버에 저장되나요?', a:'모든 데이터는 Supabase(PostgreSQL) 클라우드 DB에 AES-256 암호화하여 저장됩니다. 서버는 국내외 데이터센터를 이용하며, 개인정보보호법 및 정보통신망법을 준수합니다. 사용자 요청 시 데이터 삭제가 가능합니다.', ref:'개인정보보호법 제24조' },
  { cat:'service', q:'특허 출원 후 등록까지 PatentAI가 계속 지원하나요?', a:'현재 PatentAI는 출원 전 단계(상담·조사·명세서·도면·심사 대응 초안)를 지원합니다. 실제 출원 및 특허청 대리는 변리사가 수행해야 합니다. 향후 심사 대응 자동화 기능이 고도화되면 더 넓은 범위를 지원할 예정입니다.', ref:null },
  { cat:'service', q:'PatentAI의 AI 모델은 어떤 것을 사용하나요?', a:'자연어 분석·상담·명세서 초안에는 GPT-4o 및 GPT-4o-mini를 사용합니다. 청구항 생성에는 특허 데이터로 파인튜닝한 EXAONE(LGAI) sLLM을 사용합니다. 선행기술 조사에는 임베딩 벡터 모델과 BM25 하이브리드 검색을 활용합니다.', ref:null },
  { cat:'service', q:'생성된 명세서 초안의 품질은 어느 정도인가요?', a:'PatentAI가 생성하는 초안은 실제 특허 데이터로 학습된 모델을 기반으로 하여 특허법 형식 요건을 충족합니다. 다만 기술적 정확성과 권리 범위 최적화는 전문 변리사의 검토가 필요합니다. 실제 이용 고객의 평가에서 초안 완성도가 평균 75% 이상으로 나타났습니다.', ref:null },
  { cat:'service', q:'무료로 사용할 수 있나요?', a:'현재 PatentAI는 SKN25 프로젝트로 운영 중이며, 이용 요금 정책은 상담 신청 후 안내받으실 수 있습니다. 데모 체험이나 구체적인 요금 안내를 원하시면 상담 신청 페이지를 이용해 주세요.', ref:null },
  { cat:'service', q:'특허 분야별로 이용 가능한가요?', a:'소프트웨어·AI·반도체·바이오·기계·화학 등 다양한 기술 분야에 적용 가능합니다. 다만 생명공학·의약·화학 분야는 실험 데이터 등 특수한 기재 요건이 있으므로 전문 변리사의 검토가 더욱 중요합니다.', ref:null },
  { cat:'service', q:'여러 발명을 동시에 처리할 수 있나요?', a:'네, 여러 발명에 대해 각각 독립적인 상담·분석 프로젝트를 생성하여 관리할 수 있습니다. 기업 계정에서는 다수의 발명 프로젝트를 한 번에 관리하는 기능을 제공할 예정입니다.', ref:null },
  { cat:'service', q:'영어 특허 명세서도 작성할 수 있나요?', a:'현재 PatentAI는 한국어 명세서 초안 작성을 주력으로 하며, 영어 번역 기능도 제공합니다. 미국·유럽·일본·중국 출원을 위한 각국어 명세서 지원은 단계적으로 확대할 예정입니다.', ref:null },
  { cat:'service', q:'API로 연동하여 사용할 수 있나요?', a:'기업 고객을 위한 API 연동 서비스를 준비 중입니다. 특허 관리 시스템(IPS)이나 사내 업무 시스템과 연동하여 PatentAI 기능을 활용할 수 있습니다. 문의는 contact@patentai.kr로 해주세요.', ref:null },
  { cat:'service', q:'PatentAI 사용 중 문제가 생기면 어디에 문의하나요?', a:'contact@patentai.kr 이메일 또는 상담 신청 페이지를 통해 문의하실 수 있습니다. 영업일 기준 1~2일 내 답변드립니다. 긴급 문의는 전화(02-0000-0000)로 연락 주세요.', ref:null },
  { cat:'service', q:'개인정보는 어떻게 처리되나요?', a:'수집된 개인정보(이름·이메일·연락처)는 서비스 제공 목적으로만 이용하며, 제3자에게 제공하지 않습니다. 상담 종료 후 원하시면 데이터 삭제를 요청할 수 있습니다. 자세한 내용은 개인정보처리방침을 확인해 주세요.', ref:'개인정보보호법 제15조' },
  { cat:'service', q:'발명 내용이 유출될 위험은 없나요?', a:'PatentAI에 입력된 발명 내용은 암호화되어 저장되며, 담당자 외 접근이 제한됩니다. AI 모델 학습에 고객 데이터를 사용하지 않습니다. 영업비밀 보호를 위해 내부 접근 통제 및 보안 정책을 엄격히 운영합니다.', ref:'영업비밀보호법 제2조' },
  { cat:'service', q:'PatentAI로 해외 특허 출원도 준비할 수 있나요?', a:'네. 한국 명세서 초안을 기반으로 PCT 출원 및 각국 출원을 위한 번역·변환 기능을 지원할 예정입니다. 현재는 한국어 명세서 초안 및 선행기술 조사(국내외 DB)를 제공하며, 해외 출원 전략 수립에 활용할 수 있습니다.', ref:null },
  { cat:'service', q:'PatentAI 서비스의 정확도는 어느 정도인가요?', a:'선행기술 조사의 경우 키워드 검색 대비 관련도가 30~50% 향상된 것으로 내부 검증되었습니다. 명세서 초안은 실제 특허 명세서와 유사도 75% 이상을 달성합니다. 도면 품질 점수는 평균 85점(A등급)을 기록합니다. 단, AI 결과물은 반드시 전문가 검토를 권장합니다.', ref:null },

  // ────────────────────────────────────────────────────────────────────
  // 선행기술 조사 추가 (priorart)
  // ────────────────────────────────────────────────────────────────────
  { cat:'priorart', q:'선행기술 조사는 언제 해야 하나요?', a:'출원 전 반드시 수행하는 것이 이상적입니다. 개발 초기 단계에서 조사하면 이미 특허가 있는 방향을 피해 발명을 차별화할 수 있습니다. 출원 직전에만 조사하면 이미 개발에 많은 비용이 투자된 후라 방향 수정이 어렵습니다.', ref:null },
  { cat:'priorart', q:'KIPRIS란 무엇인가요?', a:'KIPRIS(Korea Intellectual Property Rights Information Service)는 특허청이 운영하는 국내 특허 정보 검색 서비스입니다. 국내 특허·실용신안·디자인·상표 정보를 무료로 검색할 수 있으며, 출원 명세서·공보 원문도 열람 가능합니다. PatentAI는 KIPRIS API를 활용하여 자동 수집합니다.', ref:null },
  { cat:'priorart', q:'Google Patents와 KIPRIS의 차이는?', a:'KIPRIS는 국내 특허에 특화된 공식 DB로 상세한 법적 상태 정보를 제공합니다. Google Patents는 전 세계 특허를 통합 검색할 수 있고 자연어 검색이 강력합니다. PatentAI는 두 DB를 모두 활용하여 국내외 선행기술을 종합적으로 분석합니다.', ref:null },
  { cat:'priorart', q:'IPC 코드란 무엇인가요?', a:'IPC(International Patent Classification)는 WIPO가 관리하는 국제 특허 분류 체계입니다. 기술 분야를 섹션(A~H) → 클래스 → 서브클래스 → 그룹 → 서브그룹으로 세분화합니다. 같은 IPC 코드를 가진 특허들은 유사한 기술 분야에 속하므로 선행기술 조사 시 중요한 검색 기준입니다.', ref:'특허법 시행령 제2조' },
  { cat:'priorart', q:'벡터 유사도 검색이란 무엇인가요?', a:'발명 텍스트를 AI 임베딩 모델로 벡터(숫자 배열)로 변환한 후, 코사인 유사도로 유사한 특허를 찾는 기술입니다. 키워드가 달라도 의미적으로 유사한 특허를 탐색할 수 있어 키워드 검색의 한계를 보완합니다. PatentAI는 BM25 키워드 검색과 벡터 검색을 결합한 하이브리드 방식을 사용합니다.', ref:null },
  { cat:'priorart', q:'선행기술 조사 결과, 유사 특허가 발견되면 어떻게 하나요?', a:'유사 특허 발견 시 ① 해당 특허의 청구범위를 분석하여 회피 설계(우리 발명이 청구범위 밖에 있도록 수정) ② 차별점을 강조하는 방향으로 청구범위를 재설계 ③ 해당 특허가 만료되었다면 그대로 진행 가능 등의 전략을 수립합니다.', ref:null },
  { cat:'priorart', q:'유사도 점수는 어떻게 해석하나요?', a:'0.9 이상은 매우 높은 유사도로 신규성 위협 가능성이 높습니다. 0.7~0.9는 상당한 유사도로 청구범위 분석이 필요합니다. 0.5~0.7은 중간 수준으로 차별점 확보가 가능합니다. 0.5 미만은 낮은 유사도로 출원에 문제가 없을 가능성이 높습니다.', ref:null },
  { cat:'priorart', q:'무효 자료 조사와 선행기술 조사의 차이는?', a:'선행기술 조사는 출원 전에 신규성·진보성을 미리 확인하는 조사입니다. 무효 자료 조사는 타인의 등록 특허를 무효화하기 위해 해당 특허 출원 전에 공지된 선행기술을 찾는 조사입니다. 두 조사 모두 동일한 DB를 활용하지만 목적과 검색 기준일이 다릅니다.', ref:null },
  { cat:'priorart', q:'해외 특허도 국내 신규성 판단에 영향을 미치나요?', a:'네. 특허법상 신규성은 국내외를 불문하고 출원 전에 공지·공용된 발명을 모두 포함합니다. 따라서 미국·유럽·일본 등 해외에 이미 등록된 특허도 국내 출원의 신규성을 저해할 수 있습니다. PatentAI는 주요국 DB를 함께 조사합니다.', ref:'특허법 제29조 제1항' },
  { cat:'priorart', q:'논문도 선행기술이 되나요?', a:'네. 학술 논문, 기술 보고서, 인터넷 게시물 등 비특허 문헌(NPL)도 신규성·진보성 판단의 선행기술이 됩니다. 공개된 논문, 특히 발명자 본인이 출원 전에 게재한 논문도 출원일을 기준으로 12개월을 초과하면 선행기술이 됩니다.', ref:'특허법 제29조 제1항 제2호' },
  { cat:'priorart', q:'선행기술 조사 없이 출원하면 어떤 위험이 있나요?', a:'① 이미 동일한 특허가 있어 거절될 위험 ② 타인의 특허를 침해하여 사업화 시 법적 분쟁 위험 ③ 불필요한 출원 비용 낭비 ④ 등록 후 무효심판으로 특허가 취소될 위험 등이 있습니다. 선행기술 조사는 비용 대비 효과가 매우 높은 필수 단계입니다.', ref:null },
  { cat:'priorart', q:'침묵 특허(sleeping patent)란 무엇인가요?', a:'실제로 실시되지 않고 잠자고 있는 특허를 말합니다. 이러한 특허가 특정 기술 분야에 광범위하게 존재하여 사업화를 방해하는 경우 특허 지뢰밭(patent minefield)이라 합니다. 선행기술 조사 시 침묵 특허도 탐색하여 사업화 위험을 미리 파악해야 합니다.', ref:null },
  { cat:'priorart', q:'특허 패밀리란 무엇인가요?', a:'동일한 발명에 대해 여러 국가에 출원된 특허 그룹을 특허 패밀리라 합니다. 선행기술 조사 시 특허 패밀리를 파악하면 해당 발명이 어느 국가에서 보호받고 있는지 파악할 수 있어 해외 사업화 전략 수립에 도움이 됩니다.', ref:null },

  // ────────────────────────────────────────────────────────────────────
  // 명세서 · 청구항 추가 (spec)
  // ────────────────────────────────────────────────────────────────────
  { cat:'spec', q:'독립항과 종속항의 차이는?', a:'독립항은 다른 청구항을 인용하지 않고 발명의 핵심 기술적 특징을 독립적으로 기재한 항입니다. 종속항은 독립항이나 다른 종속항을 인용하여 추가 특징을 한정합니다. 권리범위는 독립항이 가장 넓고, 종속항으로 갈수록 좁아지지만 특허 받기는 쉬워집니다.', ref:'특허법 제42조 제4항' },
  { cat:'spec', q:'청구범위를 넓게 쓰는 것이 항상 좋은가요?', a:'반드시 그렇지는 않습니다. 너무 넓은 청구범위는 신규성·진보성 결여로 거절되거나, 등록 후 무효가 될 위험이 있습니다. 선행기술 조사 결과를 반영하여 등록 가능한 최대한 넓은 범위를 찾는 것이 중요합니다. 경험 많은 변리사와 PatentAI의 AI 분석이 이 균형 잡기에 도움을 줍니다.', ref:null },
  { cat:'spec', q:'기능식 청구항이란 무엇인가요?', a:'"~하도록 구성된 수단"처럼 특정 기능으로 청구항 구성요소를 표현하는 방식입니다. 소프트웨어 발명에서 많이 사용되지만, 명세서에 해당 기능을 수행하는 구체적인 구조·알고리즘이 충분히 기재되어 있어야 합니다. 기재가 불충분하면 기재불비로 거절될 수 있습니다.', ref:'특허법 제42조 제6항' },
  { cat:'spec', q:'발명의 설명(상세한 설명)에는 어떤 내용이 필요한가요?', a:'기술분야, 배경기술(종래 기술의 문제점), 발명의 내용(해결 과제·수단·효과), 도면의 간단한 설명, 발명의 실시를 위한 구체적인 내용, 부호의 설명이 필요합니다. 특히 발명을 실시할 수 있을 정도로 명확하고 상세하게 기재해야 합니다.', ref:'특허법 제42조 제3항' },
  { cat:'spec', q:'실시예(embodiment)는 왜 중요한가요?', a:'실시예는 발명이 실제로 작동하는 방식을 구체적으로 설명하는 부분입니다. 청구범위 해석 시 실시예가 중요한 기준이 되며, 실시예가 부족하면 기재불비로 거절될 수 있습니다. 또한 분쟁 시 청구범위를 뒷받침하는 근거로 활용됩니다.', ref:'특허법 제42조 제3항' },
  { cat:'spec', q:'특허 명세서 작성 시 가장 흔한 실수는?', a:'① 청구범위를 너무 좁게 작성 ② 발명의 핵심 특징 누락 ③ 실시예 부족으로 기재불비 ④ 선행기술과의 차별성 미기재 ⑤ 도면부호 불일치 등이 흔한 실수입니다. PatentAI는 AI 분석으로 이러한 누락을 사전에 체크합니다.', ref:null },
  { cat:'spec', q:'소프트웨어 발명은 특허를 받을 수 있나요?', a:'네. 소프트웨어(컴퓨터 프로그램)도 하드웨어와 결합하여 구체적인 기술적 수단으로 과제를 해결하는 경우 특허를 받을 수 있습니다. "~를 실행하는 프로그램을 기록한 컴퓨터 판독 가능 매체" 또는 "~방법을 수행하는 시스템"의 형태로 청구합니다.', ref:'특허청 컴퓨터 관련 발명 심사지침' },
  { cat:'spec', q:'AI·머신러닝 발명은 어떻게 특허 출원하나요?', a:'AI 발명은 학습 방법(데이터 전처리·학습 알고리즘·손실함수), 모델 구조(레이어 설계·어텐션 메커니즘), 추론 방법, 응용 시스템 등의 측면에서 특허 가능합니다. 발명의 기술적 특징을 명확히 하고, 종래 AI 모델과의 차별성을 구체적으로 기재해야 합니다.', ref:'특허청 AI 발명 심사지침' },
  { cat:'spec', q:'명세서 언어는 한국어만 가능한가요?', a:'국내 출원은 한국어 명세서가 원칙이지만, 영어로도 출원할 수 있습니다(다만 일정 기간 내 한국어 번역문 제출 필요). 해외 출원(PCT 등)은 해당 특허청에서 요구하는 언어로 작성해야 합니다.', ref:'특허법 제42조의3' },
  { cat:'spec', q:'청구항의 수에 제한이 있나요?', a:'청구항 수에는 제한이 없지만, 청구항 수가 많을수록 심사청구료와 등록료가 증가합니다. 10항을 초과하는 경우 초과 항당 추가 수수료가 부과됩니다. 권리 보호의 다양성과 비용을 고려하여 적정 수의 청구항을 작성하는 것이 중요합니다.', ref:'특허법 시행규칙 별표 3' },
  { cat:'spec', q:'명세서 기재불비란 무엇인가요?', a:'발명을 재현하거나 이해하기에 명세서 기재가 불충분한 경우를 말합니다. 구체적으로는 ① 발명을 실시할 수 없을 정도로 기재가 부족한 경우 ② 청구범위가 발명의 설명에 의해 뒷받침되지 않는 경우 등입니다. 기재불비는 거절 및 무효의 원인이 됩니다.', ref:'특허법 제42조 제3항·제4항' },

  // ────────────────────────────────────────────────────────────────────
  // 도면 생성 추가 (drawing)
  // ────────────────────────────────────────────────────────────────────
  { cat:'drawing', q:'특허 도면은 컬러로 작성할 수 있나요?', a:'원칙적으로 특허 도면은 흑백 선화로 작성해야 합니다. 다만 흑백으로 표현이 어려운 경우(생물학적 서열, 그래프 등) 특허청 허가를 받아 컬러 도면을 제출할 수 있습니다. PatentAI는 특허청 기준에 맞는 흑백 선화 도면을 자동 생성합니다.', ref:'특허법 시행규칙 별지 제15호' },
  { cat:'drawing', q:'도면부호(참조번호)는 어떻게 정하나요?', a:'도면부호는 일반적으로 10, 20, 30 또는 100, 200, 300 등 10단위나 100단위 간격으로 부여합니다. 동일 구성요소는 모든 도면에서 같은 번호를 사용해야 합니다. 번호 체계는 명세서의 "부호의 설명"에 모두 기재되어야 합니다.', ref:'특허법 시행규칙 제21조' },
  { cat:'drawing', q:'도면이 없어도 특허를 받을 수 있나요?', a:'도면이 발명의 이해에 반드시 필요한 경우에는 도면을 첨부해야 합니다. 방법 발명이나 화학 발명은 도면 없이 출원 가능한 경우도 있습니다. 그러나 일반적으로 도면이 있으면 발명 내용 이해와 권리 해석에 유리합니다.', ref:'특허법 제42조 제2항' },
  { cat:'drawing', q:'도면의 크기와 여백 기준은?', a:'A4 용지 기준, 여백은 상 2.5cm, 하 1.0cm, 좌 2.5cm, 우 1.5cm 이상을 유지해야 합니다. 선의 굵기는 0.2mm 이상이어야 하며, 도면 내 문자는 인쇄 시 최소 3.2mm 이상이어야 합니다. PatentAI가 이 기준을 자동으로 적용합니다.', ref:'특허법 시행규칙 제21조' },
  { cat:'drawing', q:'흐름도(플로우차트)에서 각 도형의 의미는?', a:'타원형: 시작/종료, 직사각형: 처리/작업, 마름모형: 조건 판단(분기), 평행사변형: 입력/출력을 나타냅니다. PatentAI의 도면 에이전트는 이 규칙을 자동으로 적용하여 도면을 생성합니다.', ref:'KS X ISO 5807 순서도 기호 표준' },
  { cat:'drawing', q:'블록도(block diagram)와 흐름도의 차이는?', a:'블록도는 시스템 구성요소 간의 관계와 구조를 나타내며, 각 블록은 하드웨어·소프트웨어 모듈을 의미합니다. 흐름도는 처리 절차나 알고리즘의 흐름을 순서대로 나타냅니다. 시스템 발명에는 블록도, 방법 발명에는 흐름도가 적합합니다.', ref:null },
  { cat:'drawing', q:'시퀀스 다이어그램은 어떤 경우에 사용하나요?', a:'통신 시스템, 분산 시스템, 소프트웨어 아키텍처처럼 여러 주체(클라이언트·서버·DB) 간의 메시지 교환 순서를 표현할 때 사용합니다. 각 주체의 생명선과 메시지 화살표로 상호작용 흐름을 시각적으로 명확하게 전달합니다.', ref:null },
  { cat:'drawing', q:'도면과 명세서의 내용이 불일치하면 어떻게 되나요?', a:'도면과 명세서(특히 부호의 설명)의 불일치는 기재불비로 거절 사유가 됩니다. 도면부호가 명세서에 기재되어 있지 않거나, 명세서에 언급된 구성요소가 도면에 없는 경우가 해당됩니다. PatentAI는 도면부호와 명세서 기재의 일치 여부를 자동 검증합니다.', ref:'특허법 제42조 제3항' },
  { cat:'drawing', q:'출원 후 도면을 수정할 수 있나요?', a:'보정은 출원 시 첨부된 도면의 범위를 벗어나지 않는 한도에서 가능합니다. 새로운 구성요소나 내용을 추가하는 것은 신규사항 추가로 인정되어 불허될 수 있습니다. 도면 내 기재불비를 수정하는 경미한 보정은 허용됩니다.', ref:'특허법 제47조 제2항' },
  { cat:'drawing', q:'도면 생성에 어느 정도 시간이 소요되나요?', a:'PatentAI 도면 에이전트는 명세서 텍스트 입력 후 30초~2분 내에 SVG 도면을 생성합니다. 복잡한 시스템이나 많은 구성요소가 있는 경우 최대 5분까지 소요될 수 있습니다. 생성 후 품질 점수가 75점 미만이면 자동 보정 과정이 추가로 진행됩니다.', ref:null },
  { cat:'drawing', q:'SVG 파일이란 무엇이고 왜 사용하나요?', a:'SVG(Scalable Vector Graphics)는 벡터 기반 이미지 형식으로 확대해도 품질이 저하되지 않습니다. 특허 도면처럼 정확한 선화가 필요한 경우 SVG가 PNG·JPG보다 유리합니다. 특허청 제출 시에는 SVG를 고해상도 PNG나 TIFF로 변환하여 사용합니다.', ref:null },
  { cat:'drawing', q:'특허 도면은 직접 그려도 되나요?', a:'네, 직접 그리는 것도 가능합니다. CAD 소프트웨어(AutoCAD), 다이어그램 도구(draw.io, Visio), 일러스트레이터 등을 활용할 수 있습니다. 다만 특허청 기준(흑백·선굵기·여백·도면부호)을 충족해야 합니다. PatentAI를 이용하면 이 과정을 자동화할 수 있습니다.', ref:null },

  // ────────────────────────────────────────────────────────────────────
  // 비용 · 기간 추가 (cost)
  // ────────────────────────────────────────────────────────────────────
  { cat:'cost', q:'특허 출원 시 발생하는 전체 비용 항목은?', a:'① 특허청 관납료(출원료·심사청구료·등록료·연차료) ② 변리사 수수료(명세서 작성·심사 대응·등록 절차) ③ 번역비(해외 출원의 경우) ④ PatentAI 서비스 이용료 등으로 구성됩니다. 특허청 관납료는 법정 금액이며, 변리사 수수료는 사무소별로 다릅니다.', ref:'특허법 시행규칙 별표 3' },
  { cat:'cost', q:'출원료는 얼마인가요?', a:'전자출원 기준 기본 출원료는 56,000원이며, 청구항 1항 초과 시 항당 44,000원이 추가됩니다(20항까지). 20항 초과 시 항당 22,000원 추가입니다. 소기업·개인은 60~70% 감면 혜택이 있습니다.', ref:'특허법 시행규칙 별표 3' },
  { cat:'cost', q:'심사청구료는 얼마인가요?', a:'기본 심사청구료는 143,000원이며, 청구항 1항 초과 시 항당 44,000원이 추가됩니다. 소기업·개인·국가유공자 등은 감면 혜택을 받을 수 있습니다. 심사청구는 출원일로부터 3년 이내에 해야 합니다.', ref:'특허법 시행규칙 별표 3' },
  { cat:'cost', q:'특허 등록료는 얼마인가요?', a:'1~3년분 등록료는 기본료 15,000원에 청구항당 13,000원을 합산하여 3년분을 한번에 납부합니다. 4년차부터는 연차료를 매년 납부하며, 연차가 경과할수록 금액이 증가합니다. 소기업·개인은 최대 70% 감면됩니다.', ref:'특허법 시행규칙 별표 3' },
  { cat:'cost', q:'해외 출원 비용은 어느 정도인가요?', a:'PCT 출원은 국제 수수료(약 150만원~)와 국내 수수료를 합쳐 200~300만원 수준입니다. 각국 진입 시 미국 30만원~, 유럽(EPO) 50만원~, 일본 30만원~, 중국 20만원~의 관납료가 추가됩니다. 번역비와 현지 변리사 수수료를 포함하면 국가당 100~300만원이 더 소요됩니다.', ref:'PCT 조약 수수료 규정' },
  { cat:'cost', q:'변리사 수수료를 줄이는 방법이 있나요?', a:'① PatentAI로 명세서 초안을 작성하여 변리사의 작성 시간 단축 ② 정부 지원 사업(특허 바우처, 중소기업 IP 지원) 활용 ③ 대학·연구소의 경우 TLO(기술이전전담조직)를 통한 지원 ④ 특허청 개인 발명가 지원 프로그램 활용 등이 있습니다.', ref:'발명진흥법 제2조' },
  { cat:'cost', q:'특허 유지 비용은 얼마인가요?', a:'연차료는 1~3년차 일괄 납부 후 4년차부터 매년 납부합니다. 4~6년차 약 4만원, 7~9년차 약 10만원, 10~12년차 약 24만원, 13~20년차 약 50만원 이상으로 증가합니다(청구항 수에 따라 달라짐). 상업적으로 활용하지 않는 특허는 포기하는 것도 전략입니다.', ref:'특허법 시행규칙 별표 3' },
  { cat:'cost', q:'특허 비용 감면 혜택을 받을 수 있는 경우는?', a:'① 소기업(종업원 300인 미만) 70% 감면 ② 개인 발명가 70% 감면 ③ 국가유공자 70% 감면 ④ 기초생활수급자 전액 면제 ⑤ 장애인 70% 감면 ⑥ 중견기업 50% 감면 등이 적용됩니다. 감면 신청 시 증빙서류를 함께 제출해야 합니다.', ref:'특허법 시행규칙 별표 3 비고' },
  { cat:'cost', q:'우선심사를 신청하면 비용이 더 드나요?', a:'우선심사 신청 시 우선심사 수수료(특허 200,000원, 실용신안 100,000원)가 추가로 발생합니다. 벤처기업·중소기업·녹색기술 인증 기업 등은 우선심사 수수료가 면제되는 경우도 있습니다.', ref:'특허법 시행규칙 별표 3' },
  { cat:'cost', q:'특허 출원에서 등록까지 총 비용은 얼마인가요?', a:'국내 특허 기준으로 출원부터 등록까지(출원료+심사청구료+등록료) 관납료만 약 30~50만원입니다. 변리사 수수료(150~350만원)를 포함하면 약 200~400만원이 소요됩니다. PatentAI 활용 시 변리사 수수료를 30~50% 절감할 수 있습니다.', ref:null },
  { cat:'cost', q:'정부 지원으로 특허 비용을 지원받을 수 있나요?', a:'특허청 "IP 바우처" 사업, 중소벤처기업부 스타트업 지원, 지역 지식재산센터 지원 등 다양한 정부 지원 프로그램이 있습니다. 특허청 홈페이지(kipo.go.kr) 또는 IP-NAVI(ipnavi.or.kr)에서 지원 사업을 확인할 수 있습니다.', ref:null },
  { cat:'cost', q:'특허권을 이전하거나 라이선스할 때 비용은?', a:'특허권 이전(양도) 시 등록원부에 등록해야 하며 등록 수수료가 발생합니다. 라이선스(실시권) 설정도 등록이 필요합니다. 양도 금액이나 라이선스 로열티는 당사자 간 협상으로 결정됩니다. PatentAI는 이 절차에 대한 법적 처리는 지원하지 않습니다.', ref:'특허법 제99조~제102조' },

  // ────────────────────────────────────────────────────────────────────
  // 이용 방법 추가 (usage)
  // ────────────────────────────────────────────────────────────────────
  { cat:'usage', q:'PatentAI 상담을 시작하려면 어떻게 해야 하나요?', a:'① 오른쪽 하단 AI 챗봇으로 즉시 질문 ② 상담 신청 페이지에서 발명 내용을 작성하여 접수하는 두 가지 방법이 있습니다. 접수 후 영업일 기준 1~2일 내에 전담 담당자가 연락드립니다.', ref:null },
  { cat:'usage', q:'상담 신청 시 어떤 정보를 준비해야 하나요?', a:'발명의 제목, 기술 분야, 해결하려는 문제, 해결 방법(아이디어), 기존 기술과의 차이점을 간략히 정리해두면 좋습니다. 관련 도면이나 기술 문서가 있다면 함께 첨부해 주세요. 완벽하게 정리되지 않아도 AI가 단계적 질문으로 도와드립니다.', ref:null },
  { cat:'usage', q:'모바일에서도 이용할 수 있나요?', a:'네, PatentAI 웹사이트는 모바일 반응형으로 설계되어 스마트폰·태블릿에서도 이용 가능합니다. AI 상담 챗봇과 상담 신청 기능도 모바일에서 동일하게 작동합니다.', ref:null },
  { cat:'usage', q:'상담 이력을 나중에 다시 확인할 수 있나요?', a:'고객 로그인 후 마이페이지에서 상담 이력, 생성된 명세서 초안, 선행기술 조사 결과, 도면 파일 등을 확인하고 다운로드할 수 있습니다.', ref:null },
  { cat:'usage', q:'생성된 명세서나 도면은 어떻게 다운로드하나요?', a:'마이페이지 또는 각 서비스 결과 페이지에서 PDF, SVG, PNG 형식으로 다운로드 가능합니다. 도면은 SVG(벡터)와 PNG(고해상도) 형식을 모두 제공합니다.', ref:null },
  { cat:'usage', q:'여러 명이 공동으로 이용할 수 있나요?', a:'팀 계정 기능을 통해 여러 구성원이 같은 프로젝트에 접근할 수 있습니다. 기업 계정에서는 관리자 권한을 설정하여 팀원별 접근 권한을 관리할 수 있습니다.', ref:null },
  { cat:'usage', q:'이미 출원된 특허의 명세서도 분석할 수 있나요?', a:'네, 기존 특허 명세서를 업로드하면 선행기술과의 비교, 청구범위 분석, 도면 품질 평가 등을 수행할 수 있습니다. 경쟁사 특허 분석이나 자사 포트폴리오 관리에도 활용할 수 있습니다.', ref:null },
  { cat:'usage', q:'영어로 된 특허 명세서를 한국어로 번역할 수 있나요?', a:'PatentAI는 영어 특허 명세서의 한국어 번역을 지원합니다. 번역된 내용을 기반으로 선행기술 조사나 명세서 초안 작성에 활용할 수 있습니다.', ref:null },
  { cat:'usage', q:'PatentAI를 사용하면 변리사가 필요 없나요?', a:'PatentAI는 변리사를 대체하는 것이 아니라 보조하는 도구입니다. 최종 출원 및 특허청 대리는 변리사가 수행해야 하며, 복잡한 분쟁 대응은 전문 변리사가 필수입니다. PatentAI로 초안을 준비하면 변리사의 시간과 비용을 절감할 수 있습니다.', ref:null },
  { cat:'usage', q:'특허 출원 후 PatentAI를 계속 이용할 수 있나요?', a:'출원 후에도 심사 대응(의견서·보정서 초안), 연차료 납부 알림, 경쟁사 특허 모니터링 등의 기능을 지속적으로 이용할 수 있습니다.', ref:null },
  { cat:'usage', q:'PatentAI 이용을 중단하면 데이터는 어떻게 되나요?', a:'서비스 해지 후 30일 이내에 개인정보 및 발명 데이터 삭제를 요청할 수 있습니다. 요청이 없는 경우 개인정보보호법에 따라 일정 기간 보관 후 파기합니다.', ref:'개인정보보호법 제21조' },
]

export default function FaqPage() {
  const { lang } = useLang()
  const fT = t.faq
  const searchParams = useSearchParams()
  const [activeTab, setActiveTab] = useState('all')
  const [openIdx, setOpenIdx]     = useState<number | null>(null)
  const [search, setSearch]       = useState('')

  useEffect(() => {
    const cat = searchParams.get('cat')
    if (cat) setActiveTab(cat)
  }, [searchParams])

  const filtered = useMemo(() => {
    return faqs.filter(f => {
      const matchCat    = activeTab === 'all' || f.cat === activeTab
      const matchSearch = !search || f.q.includes(search) || f.a.includes(search)
      return matchCat && matchSearch
    })
  }, [activeTab, search])

  const catLabel = (id: string) => {
    const key = id as keyof typeof fT.cats
    return fT.cats[key] ? tr(fT.cats[key], lang) : id
  }

  return (
    <div className="site">
      <style>{`
        /* 통계 바 */
        .faq-stats {
          background: #111128;
          display: flex; justify-content: center;
          gap: 0; border-bottom: 1px solid rgba(201,168,76,0.2);
        }
        .faq-stat-item {
          text-align: center; padding: 1.6rem 3.5rem;
          border-right: 1px solid rgba(201,168,76,0.12);
        }
        .faq-stat-item:last-child { border-right: none; }
        .faq-stat-num {
          color: #C9A84C; font-family: 'Noto Serif KR', serif;
          font-size: 1.6rem; font-weight: 300; letter-spacing: 0.05em;
        }
        .faq-stat-label { color: #7777A0; font-size: 0.72rem; margin-top: 4px; letter-spacing: 0.08em; }

        /* 검색 */
        .faq-search-wrap {
          background: #F5F4F1; padding: 2rem 5.5rem;
          border-bottom: 1px solid #E8E4DC;
        }
        .faq-search {
          max-width: 640px; margin: 0 auto;
          display: flex; align-items: center;
          background: white; border: 1px solid #C8C0B4;
          transition: border 0.2s, box-shadow 0.2s;
        }
        .faq-search:focus-within {
          border-color: #C9A84C;
          box-shadow: 0 0 0 2px rgba(201,168,76,0.15);
        }
        .faq-search-label {
          padding: 0 1rem; color: #999; font-size: 0.72rem;
          font-weight: 700; letter-spacing: 0.12em; border-right: 1px solid #E8E4DC;
          white-space: nowrap; height: 48px; display: flex; align-items: center;
        }
        .faq-search input {
          flex: 1; border: none; outline: none;
          padding: 0 1rem; height: 48px;
          font-size: 0.88rem; font-family: inherit; background: transparent; color: #222;
        }
        .faq-search input::placeholder { color: #BBB; }
        .faq-search-clear {
          background: none; border: none; color: #aaa; cursor: pointer;
          font-size: 1rem; padding: 0 1rem; height: 48px;
        }
        .faq-search-clear:hover { color: #C9A84C; }

        /* 2단 레이아웃 */
        .faq-layout {
          display: grid; grid-template-columns: 240px 1fr;
          min-height: 600px;
        }

        /* 사이드바 */
        .faq-sidebar {
          background: #F5F4F1; border-right: 1px solid #E8E4DC;
          padding: 2.5rem 0; position: sticky; top: 0;
          height: fit-content;
        }
        .faq-sidebar-heading {
          padding: 0 1.8rem 1rem;
          font-size: 0.68rem; font-weight: 700; letter-spacing: 0.2em;
          color: #C9A84C; border-bottom: 1px solid #E8E4DC; margin-bottom: 0.5rem;
        }
        .faq-tab {
          display: flex; align-items: center; justify-content: space-between;
          width: 100%; text-align: left; background: none; border: none;
          padding: 0.9rem 1.8rem; cursor: pointer; font-family: inherit;
          transition: 0.12s; border-left: 3px solid transparent; gap: 0.8rem;
        }
        .faq-tab:hover { background: rgba(0,0,0,0.03); }
        .faq-tab.active {
          border-left-color: #C9A84C; background: white;
        }
        .faq-tab-left { display: flex; flex-direction: column; gap: 0.18rem; }
        .faq-tab-label {
          font-size: 0.88rem; font-weight: 600; color: #333;
          line-height: 1.2; white-space: nowrap;
        }
        .faq-tab.active .faq-tab-label { color: #111128; }
        .faq-tab:hover .faq-tab-label { color: #111128; }
        .faq-tab-sub {
          font-size: 0.62rem; color: #B8A87A; letter-spacing: 0.1em;
          font-weight: 500; white-space: nowrap;
        }
        .faq-tab.active .faq-tab-sub { color: #C9A84C; }
        .faq-tab-count {
          background: #E8E4DC; color: #888; flex-shrink: 0;
          font-size: 0.72rem; font-weight: 600;
          padding: 2px 8px; border-radius: 10px; min-width: 28px; text-align: center;
        }
        .faq-tab.active .faq-tab-count { background: #C9A84C; color: #111128; }

        /* 콘텐츠 */
        .faq-content { padding: 2.5rem 3rem; }
        .faq-result-bar {
          display: flex; align-items: center; justify-content: space-between;
          margin-bottom: 1.5rem; padding-bottom: 1rem;
          border-bottom: 1px solid #E8E4DC;
        }
        .faq-result-label { font-size: 0.82rem; color: #888; }
        .faq-result-label strong { color: #111128; font-weight: 700; }
        .faq-result-cat {
          font-size: 0.72rem; color: #C9A84C; font-weight: 700;
          letter-spacing: 0.1em;
        }

        /* 아이템 */
        .faq-item {
          border: 1px solid #E8E4DC; margin-bottom: 4px;
          background: white; transition: border-color 0.15s;
        }
        .faq-item:hover { border-color: #C9A84C; }
        .faq-item.open { border-color: #C9A84C; }

        .faq-q {
          width: 100%; text-align: left; background: none; border: none;
          padding: 1.3rem 1.6rem; cursor: pointer;
          display: flex; align-items: flex-start; gap: 1.2rem;
          font-family: inherit;
        }
        .faq-q-num {
          font-family: 'Noto Serif KR', serif; color: #C9A84C;
          font-size: 0.8rem; font-weight: 300; flex-shrink: 0; margin-top: 1px;
          min-width: 24px;
        }
        .faq-q-text {
          flex: 1; font-size: 0.92rem; font-weight: 600;
          color: #111128; line-height: 1.5;
        }
        .faq-item.open .faq-q-text { color: #C9A84C; }
        .faq-q-arrow {
          flex-shrink: 0; width: 18px; height: 18px;
          border: 1px solid #D8D2C8; border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          color: #999; font-size: 0.7rem; margin-top: 2px;
          transition: transform 0.2s, background 0.15s, border-color 0.15s;
        }
        .faq-item.open .faq-q-arrow {
          transform: rotate(180deg);
          background: #C9A84C; border-color: #C9A84C; color: #111128;
        }

        .faq-a-wrap {
          padding: 0 1.6rem 1.6rem 3.8rem;
          animation: fadeIn 0.18s ease;
        }
        .faq-a-divider {
          height: 1px; background: #F0EDE8; margin-bottom: 1.2rem;
        }
        .faq-a-label {
          font-size: 0.68rem; font-weight: 700; letter-spacing: 0.2em;
          color: #C9A84C; margin-bottom: 0.7rem;
        }
        .faq-a {
          font-size: 0.9rem; line-height: 2; color: #333;
          word-break: keep-all;
        }
        .faq-ref {
          display: inline-block; margin-top: 1rem;
          color: #888; font-size: 0.74rem;
          border-bottom: 1px solid #E8E4DC;
          padding-bottom: 2px; letter-spacing: 0.03em;
        }
        .faq-ref::before { content: 'REF. '; color: #C9A84C; font-weight: 700; }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-4px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        .faq-empty {
          text-align: center; padding: 5rem 2rem; color: #aaa; font-size: 0.9rem;
        }

        /* CTA */
        .faq-cta {
          background: #111128; margin: 0;
          padding: 3.5rem 5.5rem;
          display: flex; align-items: center; justify-content: space-between;
          gap: 2rem; border-top: 2px solid rgba(201,168,76,0.2);
        }
        .faq-cta-left {}
        .faq-cta-kicker {
          color: #C9A84C; font-size: 0.7rem; font-weight: 700;
          letter-spacing: 0.25em; margin-bottom: 0.5rem;
        }
        .faq-cta-title {
          font-family: 'Noto Serif KR', serif; font-size: 1.6rem;
          font-weight: 300; color: #F0EDE6; margin-bottom: 0.4rem;
        }
        .faq-cta-sub { color: #7777A0; font-size: 0.86rem; }
        .faq-cta-btn {
          display: inline-block; padding: 1rem 2.8rem;
          border: 1px solid #C9A84C; color: #C9A84C;
          text-decoration: none; font-size: 0.84rem; font-weight: 700;
          letter-spacing: 0.1em; white-space: nowrap; flex-shrink: 0;
          transition: 0.2s;
        }
        .faq-cta-btn:hover { background: #C9A84C; color: #111128; }

        @media (max-width: 900px) {
          .faq-layout { grid-template-columns: 1fr; }
          .faq-sidebar { position: static; padding: 1.5rem; display: flex; flex-wrap: wrap; gap: 0.4rem; border-right: none; border-bottom: 1px solid #E8E4DC; }
          .faq-sidebar-heading { width: 100%; border-bottom: none; padding: 0; margin-bottom: 0; }
          .faq-tab { width: auto; border-left: none; border: 1px solid #E8E4DC; padding: 0.4rem 0.9rem; }
          .faq-tab.active { border-color: #C9A84C; background: #F5F4F1; }
          .faq-tab-sub { display: none; }
          .faq-content { padding: 1.5rem; }
          .faq-search-wrap, .faq-cta { padding: 1.5rem; }
          .faq-stats { flex-wrap: wrap; }
          .faq-stat-item { padding: 1.2rem 2rem; }
          .faq-cta { flex-direction: column; align-items: flex-start; }
        }
      `}</style>

      <Nav />

      <div className="hero">
        <div className="tag">{tr(fT.tag, lang)}</div>
        <h1>{tr(fT.h1, lang)}</h1>
        <p>{tr(fT.desc, lang)}</p>
      </div>

      {/* 통계 바 */}
      <div className="faq-stats">
        {[
          { num: `${faqs.length}`, label: 'TOTAL Q&A' },
          { num: `${categories.length - 1}`, label: 'CATEGORIES' },
          { num: '1 — 2일', label: 'AVG. RESPONSE' },
          { num: '98%', label: 'SATISFACTION' },
        ].map(s => (
          <div className="faq-stat-item" key={s.label}>
            <div className="faq-stat-num">{s.num}</div>
            <div className="faq-stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* 검색 */}
      <div className="faq-search-wrap">
        <div className="faq-search">
          <div className="faq-search-label">SEARCH</div>
          <input
            placeholder={tr(fT.search, lang)}
            value={search}
            onChange={e => { setSearch(e.target.value); setOpenIdx(null) }}
          />
          {search && (
            <button className="faq-search-clear" onClick={() => setSearch('')}>×</button>
          )}
        </div>
      </div>

      {/* 본문 2단 */}
      <div className="faq-layout">

        {/* 사이드바 */}
        <aside className="faq-sidebar">
          <div className="faq-sidebar-heading">CATEGORIES</div>
          {categories.map(cat => {
            const cnt = cat.id === 'all' ? faqs.length : faqs.filter(f => f.cat === cat.id).length
            return (
              <button
                key={cat.id}
                className={`faq-tab ${activeTab === cat.id ? 'active' : ''}`}
                onClick={() => { setActiveTab(cat.id); setOpenIdx(null) }}
              >
                <span className="faq-tab-left">
                  <span className="faq-tab-label">{catLabel(cat.id)}</span>
                  {cat.id !== 'all' && <span className="faq-tab-sub">{cat.sub}</span>}
                </span>
                <span className="faq-tab-count">{cnt}</span>
              </button>
            )
          })}
        </aside>

        {/* FAQ 목록 */}
        <div className="faq-content">
          <div className="faq-result-bar">
            <div className="faq-result-label">
              <strong>{filtered.length}</strong> {tr(fT.resultLabel, lang)}
            </div>
            <div className="faq-result-cat">
              {categories.find(c => c.id === activeTab)?.sub ?? 'ALL'}
            </div>
          </div>

          {filtered.length === 0 && (
            <div className="faq-empty">{tr(fT.noResult, lang)}</div>
          )}

          {filtered.map((item, i) => {
            const isOpen = openIdx === i
            return (
              <div key={i} className={`faq-item ${isOpen ? 'open' : ''}`}>
                <button className="faq-q" onClick={() => setOpenIdx(isOpen ? null : i)}>
                  <span className="faq-q-num">{String(i + 1).padStart(2, '0')}</span>
                  <span className="faq-q-text">{item.q}</span>
                  <span className="faq-q-arrow">
                    <svg width="8" height="8" viewBox="0 0 10 6" fill="none">
                      <path d="M1 1l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </span>
                </button>
                {isOpen && (
                  <div className="faq-a-wrap">
                    <div className="faq-a-divider" />
                    <div className="faq-a-label">ANSWER</div>
                    <div className="faq-a">{item.a}</div>
                    {item.ref && <div className="faq-ref">{item.ref}</div>}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* CTA */}
      <div className="faq-cta">
        <div className="faq-cta-left">
          <div className="faq-cta-kicker">NEED MORE HELP?</div>
          <div className="faq-cta-title">더 구체적인 상담이 필요하신가요?</div>
          <div className="faq-cta-sub">전문 상담팀이 영업일 1~2일 내 답변드립니다.</div>
        </div>
        <Link className="faq-cta-btn" href="/contact">상담 신청하기 →</Link>
      </div>

      <Footer />
    </div>
  )
}
