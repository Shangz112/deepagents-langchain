
const http = require('http');

function request(options, data) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(body) });
        } catch (e) {
          resolve({ status: res.statusCode, body: body });
        }
      });
    });
    req.on('error', reject);
    if (data) req.write(JSON.stringify(data));
    req.end();
  });
}

async function run() {
  const baseUrl = 'http://localhost:8005/api/v1/chat';
  
  console.log('1. Creating session...');
  const createRes = await request({
    hostname: 'localhost',
    port: 8005,
    path: '/api/v1/chat/sessions',
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  console.log('Create Response:', createRes.body);
  const sid = createRes.body.id;
  if (!sid) throw new Error('No session ID returned');

  console.log('2. Sending message...');
  await request({
    hostname: 'localhost',
    port: 8005,
    path: `/api/v1/chat/sessions/${sid}/messages`,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }, { content: 'Hello, this is a test message.', tools: true });

  // Wait a bit for async processing (though for simple message it might be fast, 
  // but context update usually happens after stream or explicit save. 
  // In our app.py, post_message appends to list but stream_session processes it. 
  // We are NOT calling stream here, so the message is just in 'messages' list as user message.)
  // Ideally we should call stream to get the assistant response, but for now let's check if the user message is there.
  
  console.log('3. Getting context...');
  const contextRes = await request({
    hostname: 'localhost',
    port: 8005,
    path: `/api/v1/chat/sessions/${sid}/context`,
    method: 'GET'
  });
  console.log('Context Response:', JSON.stringify(contextRes.body, null, 2));

  console.log('4. Exporting session...');
  const exportRes = await request({
    hostname: 'localhost',
    port: 8005,
    path: `/api/v1/chat/sessions/${sid}/export`,
    method: 'GET'
  });
  console.log('Export Response:', JSON.stringify(exportRes.body, null, 2));
}

run().catch(console.error);
