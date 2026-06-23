export type ProjectLoadingVariant = 'paper' | 'manual' | 'workspace'

const LOADING_COPY: Record<ProjectLoadingVariant, { title: string; description: string }> = {
  paper: {
    title: '에이전트가 논문을 파악 중입니다',
    description: '논문의 기술 내용을 특허 프로젝트 입력값으로 구조화하고 있습니다.',
  },
  manual: {
    title: '에이전트가 입력 내용을 파악 중입니다',
    description: '입력한 기술 내용을 특허 프로젝트 데이터로 구조화하고 있습니다.',
  },
  workspace: {
    title: '프로젝트 데이터를 불러오는 중입니다',
    description: '특허 프로젝트 워크스테이션을 준비하고 있습니다.',
  },
}

export default function ProjectLoadingOverlay({ variant }: { variant: ProjectLoadingVariant }) {
  const copy = LOADING_COPY[variant]

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={copy.title}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 2000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(18,16,14,.42)',
        backdropFilter: 'blur(7px)',
        WebkitBackdropFilter: 'blur(7px)',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', color: '#fff', textAlign: 'center', padding: '0 24px' }}>
        <div
          aria-hidden="true"
          style={{
            width: 56,
            height: 56,
            borderRadius: '50%',
            border: '4px solid rgba(255,255,255,.32)',
            borderTopColor: 'var(--lf-gold)',
            animation: 'paper-spin 1s linear infinite',
            willChange: 'transform',
            marginBottom: 24,
          }}
        />
        <h2 style={{ fontFamily: 'var(--lf-serif)', fontSize: 26, fontWeight: 300, marginBottom: 10 }}>
          {copy.title}
        </h2>
        <p style={{ fontSize: 13, color: 'rgba(255,255,255,.76)', letterSpacing: 0 }}>
          {copy.description}
        </p>
      </div>
    </div>
  )
}
