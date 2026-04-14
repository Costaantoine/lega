export const metadata = {
  title: 'LEGA — Assistant TP',
  description: 'Votre assistant machines de Travaux Publics',
  appleWebApp: { capable: true, statusBarStyle: 'black-translucent', title: 'LEGA' },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <head>
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="theme-color" content="#0f172a" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
      </head>
      <body style={{ margin: 0, padding: 0, background: '#0f172a', color: '#e2e8f0', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
        {children}
      </body>
    </html>
  )
}
