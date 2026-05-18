/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: '*.supabase.co' },
      { protocol: 'https', hostname: 'images.unsplash.com' },
      { protocol: 'http', hostname: '76.13.141.221' },
    ],
  },
  async rewrites() {
    return [
      {
        source: '/api/site/:path*',
        destination: `${process.env.SITE_API_URL || 'http://lega-backend:8000'}/api/site/:path*`,
      },
      {
        source: '/uploads/:path*',
        destination: `${process.env.SITE_API_URL || 'http://lega-backend:8000'}/uploads/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
