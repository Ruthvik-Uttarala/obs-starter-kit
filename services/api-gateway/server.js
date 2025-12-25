import "./otel.js";
import express from "express";
import fetch from "node-fetch";

const app = express();

app.get("/reco", async (req, res) => {
  try {
    const userId = req.query.user_id;
    if (!userId) return res.status(400).json({ error: "user_id is required" });

    const r = await fetch(`http://reco-worker:9091/reco?user_id=${encodeURIComponent(userId)}`);
    const body = await r.text();

    res.status(r.status);
    res.set("content-type", r.headers.get("content-type") || "application/json");
    res.send(body);
  } catch (e) {
    res.status(500).json({ error: "gateway error", details: String(e) });
  }
});



const port = Number(process.env.PORT || 8080);
const recoUrl = process.env.RECO_URL || "http://localhost:9091";

app.get("/health", (req, res) => res.json({ ok: true }));

app.get("/recommend", async (req, res) => {
  const userId = req.query.user_id || "anon";

  try {
    const r = await fetch(`${recoUrl}/reco?user_id=${encodeURIComponent(userId)}`, {
      headers: { "x-request-source": "api-gateway" }
    });

    if (!r.ok) {
      res.status(502).json({ error: "reco-worker bad response", status: r.status });
      return;
    }

    const data = await r.json();
    res.json({ user_id: userId, recommendations: data.recommendations });
  } catch (e) {
    res.status(500).json({ error: "api-gateway failed", detail: String(e) });
  }
});

app.listen(port, () => {
  console.log(`api-gateway listening on :${port}`);
});
