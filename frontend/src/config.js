export const API_URL = import.meta.env.DEV
  ? ''  // use Vite proxy — avoids Safari cross-origin block on localhost
  : ''  // production: CloudFront handles /api/* → API Gateway (same origin)
