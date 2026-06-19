import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { workspaceApi } from '../api/workspace';
import MarkdownContent from '../components/MarkdownContent';

export default function ReportPage() {
  //const { id } = useParams<{ id: string }>();
  const { projectId } = useParams<{ projectId: string }>();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // 페이지가 열리면 프로젝트 ID로 데이터를 불러옵니다.
  useEffect(() => {
    if (projectId) {
      workspaceApi.getReport(projectId)
        .then(res => {
          setData(res);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          alert('리포트 데이터를 불러오는데 실패했습니다.');
          setLoading(false);
        });
    }
  }, [projectId]); 

  if (loading) {
    return <div style={{ padding: 100, textAlign: 'center', fontSize: 18 }}>리포트 데이터를 불러오는 중입니다...</div>;
  }

  if (!data || !data.project) {
    return <div style={{ padding: 100, textAlign: 'center', fontSize: 18, color: 'red' }}>데이터를 찾을 수 없습니다.</div>;
  }

  const { project, state, claims, drawings, specification } = data;

  return (
    <div style={{ backgroundColor: '#f8f9fa', minHeight: '100vh', padding: '40px 20px', color: '#12100e', fontFamily: "'Times New Roman', 'Pretendard', serif" }}>
      {/* 🎯 인쇄 시 버튼 숨기기용 CSS */}
      <style>
        {`
          @media print {
            body { background: white; }
            .no-print { display: none !important; }
            .report-container { box-shadow: none !important; padding: 0 !important; margin: 0 !important; border: none !important; max-width: 100% !important; }
          }
        `}
      </style>

      {/* 우측 하단 둥둥 떠있는 인쇄 버튼 */}
      <button 
        className="no-print" 
        onClick={() => window.print()} 
        style={{
          position: 'fixed', bottom: 40, right: 40, background: '#12100e', color: 'white', 
          border: 'none', padding: '16px 30px', borderRadius: 4, fontWeight: 600, 
          cursor: 'pointer', boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
        }}
      >
        🖨️ 인쇄 / PDF 저장
      </button>

      {/* 📄 실제 문서 영역 */}
      <div className="report-container" style={{
        maxWidth: 800, margin: '0 auto', background: 'white', padding: 80,
        boxShadow: '0 4px 20px rgba(0,0,0,0.08)', borderTop: '6px solid #9a7840'
      }}>
        <div style={{ textAlign: 'center', borderBottom: '2px solid #12100e', paddingBottom: 30, marginBottom: 50 }}>
          <h1 style={{ fontFamily: "'Georgia', serif", fontSize: 32, margin: 0 }}>{project.title}</h1>
          <p style={{ color: '#9a7840', fontSize: 13, marginTop: 15, letterSpacing: 1, textTransform: 'uppercase' }}>
            특허 출원 요약 및 청구범위 리포트 | {new Date(project.created_at).toLocaleDateString('ko-KR')}
          </p>
        </div>

        <h3 style={sectionTitleStyle}>I. 발명 요약 (AI 분석)</h3>
        <ContentBox title="해결하고자 하는 과제" content={state?.ext_problem || "입력된 데이터가 없습니다."} />
        <ContentBox title="핵심 해결 방법" content={state?.ext_solution || "입력된 데이터가 없습니다."} />
        <ContentBox title="발명의 차별성" content={state?.ext_differentiation || "입력된 데이터가 없습니다."} />
        <ContentBox title="기대 효과" content={state?.ext_effect || "입력된 데이터가 없습니다."} />

        <h3 style={sectionTitleStyle}>II. 특허 청구범위</h3>
        {claims && claims.length > 0 ? (
          claims.map((c: any) => (
            <div key={c.id} style={{ 
              marginBottom: 25, paddingLeft: 15, 
              borderLeft: `2px solid ${c.is_dependent ? '#e2e8f0' : '#12100e'}`,
              marginLeft: c.is_dependent ? 30 : 0
            }}>
              <h4 style={{ margin: '0 0 8px 0', fontSize: 15 }}>
                【청구항 {c.claim_no}】 {c.is_dependent ? '[종속항]' : '[독립항]'}
              </h4>
              <p style={{ margin: 0, lineHeight: 1.7, fontSize: 15 }}>{c.content}</p>
            </div>
          ))
        ) : (
          <p style={{ textAlign: 'center', color: '#94a3b8', padding: 30 }}>아직 작성된 청구항이 없습니다.</p>
        )}

        {drawings && drawings.length > 0 && (
          <>
            <h3 style={sectionTitleStyle}>III. 첨부 도면</h3>
            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
              {drawings.map((drawing: any, idx: number) => (
                <div key={idx} style={{ background: '#f8f9fa', padding: 15, border: '1px solid #e2e8f0', textAlign: 'center', width: 220 }}>
                  <img src={drawing.image_url} alt={drawing.title} style={{ maxWidth: '100%', border: '1px solid #e2e8f0' }} />
                  <p style={{ fontSize: 12, fontWeight: 'bold', marginTop: 10 }}>{drawing.title}</p>
                </div>
              ))}
            </div>
          </>
        )}

        {specification && specification.markdown_content && (
          <>
            <h3 style={sectionTitleStyle}>IV. 발명의 설명</h3>
            <div style={{ background: '#fff', border: '1px solid #e2e8f0', padding: 40, borderRadius: 2 }}>
              <MarkdownContent content={specification.markdown_content} variant="report" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

const sectionTitleStyle: React.CSSProperties = {
  fontFamily: "'Georgia', serif", fontSize: 20, fontWeight: 'bold', color: '#12100e',
  borderBottom: '1px solid #e2e8f0', paddingBottom: 10, marginTop: 50, marginBottom: 25, display: 'flex', alignItems: 'center', gap: 10
};

const ContentBox = ({ title, content }: { title: string, content: string }) => (
  <div style={{ background: '#fff', border: '1px solid #e2e8f0', padding: 24, borderRadius: 2, marginBottom: 20 }}>
    <h4 style={{ margin: '0 0 12px 0', color: '#9a7840', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 }}>{title}</h4>
    <p style={{ margin: 0, lineHeight: 1.8, fontSize: 14.5, color: '#334155', whiteSpace: 'pre-wrap' }}>{content}</p>
  </div>
);
