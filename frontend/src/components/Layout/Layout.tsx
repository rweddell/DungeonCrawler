import React, { ReactNode } from 'react'
import './Layout.css'

interface LayoutProps {
  children: ReactNode
  sidebarContent?: ReactNode
  showSidebar?: boolean
  headerExtra?: ReactNode
}

export function Layout({ children, sidebarContent, showSidebar, headerExtra }: LayoutProps) {
  return (
    <div className="layout">
      <header className="layout-header parchment medieval-border">
        <h1 className="layout-title">DungeonCrawler</h1>
        <div className="layout-header-extra">{headerExtra}</div>
      </header>
      <div className="layout-body">
        <main className="layout-main">{children}</main>
        {showSidebar && sidebarContent && (
          <aside className="layout-sidebar parchment medieval-border">
            {sidebarContent}
          </aside>
        )}
      </div>
    </div>
  )
}
