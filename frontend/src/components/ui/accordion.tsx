import * as React from 'react'

export interface AccordionProps extends React.HTMLAttributes<HTMLDivElement> {
  type?: 'single' | 'multiple'
  collapsible?: boolean
}

export function Accordion({ children, ...props }: AccordionProps) {
  return <div {...props}>{children}</div>
}

export function AccordionItem({ children, className }: { children: React.ReactNode; value: string; className?: string }) {
  return <div className={className}>{children}</div>
}

export function AccordionTrigger({ children, className }: { children: React.ReactNode; className?: string }) {
  const [open, setOpen] = React.useState(false)
  return (
    <button onClick={() => setOpen(!open)} className={className} aria-expanded={open}>
      {children}
    </button>
  )
}

export function AccordionContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={className}>{children}</div>
}
