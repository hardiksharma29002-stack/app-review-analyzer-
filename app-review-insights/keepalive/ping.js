const https = require('https');

// Placeholder for Render URL. We will update this when deploying.
const RENDER_URL = process.env.RENDER_URL || 'https://pulse-dashboard-render.onrender.com';

function keepAlive() {
  console.log(`[${new Date().toISOString()}] Pinging ${RENDER_URL} to prevent sleep...`);
  
  https.get(RENDER_URL, (res) => {
    console.log(`[${new Date().toISOString()}] Keep-alive ping status: ${res.statusCode}`);
  }).on('error', (err) => {
    console.error(`[${new Date().toISOString()}] Keep-alive ping failed:`, err.message);
  });
}

// Ping every 5 minutes (300000 ms)
const PING_INTERVAL = 5 * 60 * 1000;
setInterval(keepAlive, PING_INTERVAL);

// Initial ping
keepAlive();

console.log(`Keep-alive service started. Pinging every ${PING_INTERVAL / 1000} seconds.`);
