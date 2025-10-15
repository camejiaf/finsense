/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable service worker to prevent fetch errors
  experimental: {
    esmExternals: false,
  },
  // Disable PWA features that might cause service worker issues
  pwa: {
    disable: true,
  },
}

module.exports = nextConfig


