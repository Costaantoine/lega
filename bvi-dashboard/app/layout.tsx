export const metadata = {
  title: 'LEGA Admin — Antoine',
  description: 'Dashboard de supervision LEGA/BVI',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body style={{ margin: 0, padding: 0, background: '#0f172a', color: '#e2e8f0', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
        {children}
      </body>
    </html>
  )
}
