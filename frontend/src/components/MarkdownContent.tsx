import React from 'react'

type MarkdownContentProps = {
  content: string
  variant?: 'chat' | 'report'
}

function renderInline(text: string) {
  return text
    .split(/(\*\*[^*]+\*\*)/g)
    .filter(Boolean)
    .map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index} style={{ fontWeight: 700, color: 'var(--lf-navy, #12100e)' }}>{part.slice(2, -2)}</strong>
      }
      return <React.Fragment key={index}>{part}</React.Fragment>
    })
}

export default function MarkdownContent({ content, variant = 'chat' }: MarkdownContentProps) {
  const lines = content.replace(/\r\n/g, '\n').split('\n')
  const blocks: React.ReactNode[] = []
  const isReport = variant === 'report'
  let i = 0

  while (i < lines.length) {
    const line = lines[i]
    const trimmed = line.trim()

    if (!trimmed) {
      i += 1
      continue
    }

    if (trimmed.startsWith('# ')) {
      blocks.push(
        <h2 key={blocks.length} style={{
          fontSize: isReport ? 24 : 20,
          lineHeight: 1.35,
          fontWeight: 700,
          color: '#12100e',
          margin: isReport ? '0 0 28px' : '0 0 18px',
          paddingBottom: isReport ? 14 : 10,
          borderBottom: '1px solid rgba(154,120,64,.25)',
        }}>
          {renderInline(trimmed.slice(2).trim())}
        </h2>
      )
      i += 1
      continue
    }

    if (trimmed.startsWith('## ')) {
      blocks.push(
        <h3 key={blocks.length} style={{
          fontSize: isReport ? 18 : 15,
          lineHeight: 1.45,
          fontWeight: 700,
          color: '#12100e',
          margin: isReport ? '30px 0 12px' : '22px 0 8px',
        }}>
          {renderInline(trimmed.slice(3).trim())}
        </h3>
      )
      i += 1
      continue
    }

    if (trimmed.startsWith('### ')) {
      blocks.push(
        <h4 key={blocks.length} style={{
          fontSize: isReport ? 16 : 14,
          lineHeight: 1.45,
          fontWeight: 700,
          color: '#9a7840',
          margin: isReport ? '24px 0 10px' : '18px 0 8px',
        }}>
          {renderInline(trimmed.slice(4).trim())}
        </h4>
      )
      i += 1
      continue
    }

    if (/^[-*]\s+/.test(trimmed)) {
      const items: string[] = []
      while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^[-*]\s+/, ''))
        i += 1
      }
      blocks.push(
        <ul key={blocks.length} style={{
          margin: isReport ? '10px 0 22px 22px' : '8px 0 16px 20px',
          padding: 0,
          lineHeight: isReport ? 1.85 : 1.75,
        }}>
          {items.map((item, index) => <li key={index}>{renderInline(item)}</li>)}
        </ul>
      )
      continue
    }

    if (/^\d+\.\s+/.test(trimmed)) {
      const items: string[] = []
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        items.push(lines[i].trim().replace(/^\d+\.\s+/, ''))
        i += 1
      }
      blocks.push(
        <ol key={blocks.length} style={{
          margin: isReport ? '10px 0 22px 22px' : '8px 0 16px 20px',
          padding: 0,
          lineHeight: isReport ? 1.85 : 1.75,
        }}>
          {items.map((item, index) => <li key={index}>{renderInline(item)}</li>)}
        </ol>
      )
      continue
    }

    const paragraphLines = [trimmed]
    i += 1
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].trim().startsWith('#') &&
      !/^[-*]\s+/.test(lines[i].trim()) &&
      !/^\d+\.\s+/.test(lines[i].trim())
    ) {
      paragraphLines.push(lines[i].trim())
      i += 1
    }

    blocks.push(
      <p key={blocks.length} style={{
        margin: isReport ? '0 0 18px' : '0 0 14px',
        lineHeight: isReport ? 1.9 : 1.8,
        fontSize: isReport ? 15 : 14,
        color: isReport ? '#334155' : 'var(--lf-navy)',
        whiteSpace: 'pre-line',
      }}>
        {renderInline(paragraphLines.join('\n'))}
      </p>
    )
  }

  return (
    <div style={{
      fontSize: isReport ? 15 : 14,
      lineHeight: isReport ? 1.9 : 1.8,
      color: isReport ? '#334155' : 'var(--lf-navy)',
    }}>
      {blocks}
    </div>
  )
}
