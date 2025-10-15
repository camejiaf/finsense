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
  // Disable service worker completely and prevent caching issues
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
      };
      
      // Remove service worker registration
      config.plugins = config.plugins.filter(plugin => {
        return plugin.constructor.name !== 'GenerateSW';
      });
    }
    return config;
  },
  // Disable static optimization for API routes
  trailingSlash: false,
  // Disable service worker caching
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 2,
  },
}

module.exports = nextConfig


