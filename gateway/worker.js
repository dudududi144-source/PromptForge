// PromptForge Gateway Worker
// Handles API requests and connects to NVIDIA Build API

const NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1";

// NVIDIA API key - read from Cloudflare Worker environment variable
// Set via: wrangler secret put NVIDIA_API_KEY
// The key is NOT hardcoded - it is stored securely as a Cloudflare Worker secret

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  'Content-Type': 'application/json',
};

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS });
    }

    const url = new URL(request.url);

    try {
      if (url.pathname === '/api/health') {
        return await handleHealth(env);
      } else if (url.pathname === '/api/generate' && request.method === 'POST') {
        return await handleGenerate(request, env);
      } else if (url.pathname === '/api/models') {
        return await handleModels(env);
      } else if (url.pathname === '/api/connect-key' && request.method === 'POST') {
        return await handleConnectKey(request, env);
      } else if (url.pathname === '/api/check-connection' && request.method === 'GET') {
        return await handleCheckConnection(env);
      } else {
        return new Response(JSON.stringify({ error: 'Not found' }), { status: 404, headers: CORS });
      }
    } catch (e) {
      return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: CORS });
    }
  }
};

// Get NVIDIA API key from environment variable
function getNvidiaApiKey(env) {
  return env.NVIDIA_API_KEY || "";
}

async function handleHealth(env) {
  const apiKey = getNvidiaApiKey(env);
  return new Response(JSON.stringify({
    status: 'healthy',
    nvidia_configured: !!apiKey,
    timestamp: Date.now()
  }), { headers: CORS });
}

async function handleCheckConnection(env) {
  const apiKey = getNvidiaApiKey(env);
  if (!apiKey) {
    return new Response(JSON.stringify({
      connected: false,
      message: 'NVIDIA API key not configured. Please add your key.'
    }), { headers: CORS });
  }

  // Test the connection
  try {
    const resp = await fetch(NVIDIA_API_URL + "/models", {
      headers: { 'Authorization': 'Bearer ' + apiKey },
      signal: AbortSignal.timeout(10000)
    });

    if (resp.ok) {
      const data = await resp.json();
      const modelCount = (data.data || []).length;
      return new Response(JSON.stringify({
        connected: true,
        message: 'Connected to NVIDIA Build API',
        models_available: modelCount
      }), { headers: CORS });
    } else {
      return new Response(JSON.stringify({
        connected: false,
        message: 'API key invalid or expired'
      }), { status: 401, headers: CORS });
    }
  } catch (e) {
    return new Response(JSON.stringify({
      connected: false,
      message: 'Connection failed: ' + e.message
    }), { status: 500, headers: CORS });
  }
}

async function handleConnectKey(request, env) {
  // This endpoint is for testing the connection with a provided key
  // The actual key storage is done via Cloudflare Worker secrets
  try {
    const body = await request.json();
    const apiKey = body.apiKey || "";

    if (!apiKey) {
      return new Response(JSON.stringify({ error: 'apiKey is required' }), { status: 400, headers: CORS });
    }

    // Test the key
    const resp = await fetch(NVIDIA_API_URL + "/models", {
      headers: { 'Authorization': 'Bearer ' + apiKey },
      signal: AbortSignal.timeout(10000)
    });

    if (resp.ok) {
      const data = await resp.json();
      const modelCount = (data.data || []).length;
      return new Response(JSON.stringify({
        success: true,
        message: 'Key is valid and connected',
        models_available: modelCount
      }), { headers: CORS });
    } else {
      return new Response(JSON.stringify({
        success: false,
        message: 'Key is invalid or expired'
      }), { status: 401, headers: CORS });
    }
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: CORS });
  }
}

async function handleModels(env) {
  const apiKey = getNvidiaApiKey(env);
  if (!apiKey) {
    return new Response(JSON.stringify({ error: 'NVIDIA API key not configured' }), { status: 503, headers: CORS });
  }

  try {
    const resp = await fetch(NVIDIA_API_URL + "/models", {
      headers: { 'Authorization': 'Bearer ' + apiKey }
    });

    if (!resp.ok) {
      return new Response(JSON.stringify({ error: 'NVIDIA API error: ' + resp.status }), { status: resp.status, headers: CORS });
    }

    const data = await resp.json();
    const models = (data.data || []).map(m => m.id);

    return new Response(JSON.stringify({ models, total: models.length }), { headers: CORS });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: CORS });
  }
}

async function handleGenerate(request, env) {
  const apiKey = getNvidiaApiKey(env);
  if (!apiKey) {
    return new Response(JSON.stringify({ error: 'NVIDIA API key not configured. Please add your key via the Connect API option.' }), { status: 503, headers: CORS });
  }

  try {
    const body = await request.json();
    const goal = body.goal || "";
    const model = body.model || "meta/llama-3.1-8b-instruct";

    if (!goal) {
      return new Response(JSON.stringify({ error: 'goal is required' }), { status: 400, headers: CORS });
    }

    const resp = await fetch(NVIDIA_API_URL + "/chat/completions", {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + apiKey,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: model,
        messages: [
          { role: 'system', content: 'You are a senior software engineer. Write complete, production-quality code. Include type annotations, docstrings, error handling. Write ONLY code, no explanation.' },
          { role: 'user', content: goal }
        ],
        max_tokens: 4096,
        temperature: 0.1
      })
    });

    if (!resp.ok) {
      const errText = await resp.text();
      return new Response(JSON.stringify({ error: 'NVIDIA API error: ' + resp.status + ' - ' + errText.substring(0, 200) }), { status: resp.status, headers: CORS });
    }

    const data = await resp.json();
    let code = (data.choices && data.choices[0]) ? data.choices[0].message.content : "";
    const tokens = (data.usage && data.usage.total_tokens) ? data.usage.total_tokens : 0;

    // Remove markdown fences
    const fence = '```';
    if (code.includes(fence)) {
      const parts = code.split(fence);
      if (parts.length >= 3) {
        code = parts[1];
        const lines = code.split('\n');
        if (['python', 'py', 'javascript', 'js', 'typescript', 'ts', ''].includes(lines[0].trim().toLowerCase())) {
          code = lines.slice(1).join("\n");
        }
      }
    }

    return new Response(JSON.stringify({
      success: true,
      code: code.trim(),
      model: model,
      total_tokens: tokens,
      outputs: { code: code.trim() }
    }), { headers: CORS });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: CORS });
  }
}