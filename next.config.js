/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['cdn.facelessreels.com', 'cdn.prod.website-files.com'],
  },
}

module.exports = nextConfig
