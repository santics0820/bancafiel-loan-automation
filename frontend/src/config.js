export const API_URL = import.meta.env.DEV
  ? ''  // use Vite proxy — avoids Safari cross-origin block on localhost
  : 'https://nfgxyb0os2.execute-api.us-east-1.amazonaws.com/dev'
