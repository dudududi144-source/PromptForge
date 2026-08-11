// PromptForge Gateway Worker
// Handles API requests and connects to NVIDIA Build API

const NVIDIA_API_URL = "https://integrate.api.nvidia.com/v1";

// NVIDIA API key - stored as Cloudflare Worker secret
// Set via: wrangler secret put NVIDIA_API_KEY
const NVIDIA_API_KEY = "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";

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
      } else {
        return new Response(JSON.stringify({ error: 'Not found' }), { status: 404, headers: CORS });
      }
    } catch (e) {
      return new Response(JSON.stringify({ error: e.message }), { status: 500, headers: CORS });
    }
  }
};

async function handleHealth(env) {
  const apiKey = env.NVIDIA_API_KEY || NVIDIA_API_KEY;
  return new Response(JSON.stringify({
    status: 'healthy',
    nvidia_configured: !!apiKey,
    timestamp: Date.now()
  }), { headers: CORS });
}

async function handleModels(env) {
  const apiKey = env.NVIDIA_API_KEY || NVIDIA_API_KEY;
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
  const apiKey = env.NVIDIA_API_KEY || NVIDIA_API_KEY;
  if (!apiKey) {
    return new Response(JSON.stringify({ error: 'NVIDIA API key not configured' }), { status: 503, headers: CORS });
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
        // Remove language identifier
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