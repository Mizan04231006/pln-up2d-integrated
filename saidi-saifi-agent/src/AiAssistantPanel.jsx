import { useState, useRef, useEffect } from "react";
import { Sparkles, Send, Wrench, AlertTriangle, Bot, User, RotateCcw } from "lucide-react";
import { runConversationTurn } from "./aiAgent.js";

const SARAN = [
  "Bagaimana ringkasan SAIDI/SAIFI tahun ini dibanding standar IEEE?",
  "Penyulang mana yang paling buruk keandalannya?",
  "Bulan apa saja kontribusi gangguannya paling tinggi?",
  "Bandingkan kecepatan pemulihan SCADA vs manual",
];

const HAS_KEY = Boolean(
  import.meta.env.VITE_GEMINI_API_KEY && !import.meta.env.VITE_GEMINI_API_KEY.includes("tempel_api_key")
);

export default function AiAssistantPanel() {
  const [display, setDisplay] = useState([
    {
      role: "assistant",
      text:
        'Halo! Saya asisten AI untuk dashboard keandalan jaringan ini. Tanyakan apa saja tentang SAIDI/SAIFI/CAIDI, penyulang tertentu, tren bulanan, atau penyebab gangguan — saya akan memanggil fungsi perhitungan yang sama dengan yang dipakai dashboard, bukan menebak.',
    },
  ]);
  const [apiHistory, setApiHistory] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [display, loading]);

  async function ask(text) {
    if (!text.trim() || loading) return;
    setDisplay((d) => [...d, { role: "user", text }]);
    setInput("");
    setLoading(true);
    try {
      const result = await runConversationTurn(apiHistory, text);
      setApiHistory(result.history);
      const traceMsgs = result.toolTrace.map((t) => ({ role: "tool", ...t }));
      setDisplay((d) => [...d, ...traceMsgs, { role: "assistant", text: result.text }]);
    } catch (err) {
      setDisplay((d) => [...d, { role: "assistant", text: `Maaf, terjadi kendala: ${err.message}`, isError: true }]);
    } finally {
      setLoading(false);
    }
  }

  function resetChat() {
    setDisplay([{ role: "assistant", text: "Percakapan direset. Silakan ajukan pertanyaan baru." }]);
    setApiHistory([]);
  }

  return (
    <div className="space-y-4">
      {!HAS_KEY && (
        <div className="bg-amber-500/10 border border-amber-500/25 rounded-xl px-4 py-3 flex gap-2.5 items-start">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p className="text-xs text-amber-200/90 leading-relaxed">
            <span className="font-semibold">API key Gemini belum diatur.</span> Salin{" "}
            <code className="font-mono bg-slate-900/60 px-1 rounded">.env.example</code> menjadi{" "}
            <code className="font-mono bg-slate-900/60 px-1 rounded">.env</code>, isi{" "}
            <code className="font-mono bg-slate-900/60 px-1 rounded">VITE_GEMINI_API_KEY</code> dengan API key gratis
            dari{" "}
            <a
              href="https://aistudio.google.com/apikey"
              target="_blank"
              rel="noreferrer"
              className="underline text-amber-300 hover:text-amber-200"
            >
              aistudio.google.com/apikey
            </a>
            , lalu jalankan ulang <code className="font-mono bg-slate-900/60 px-1 rounded">npm run dev</code>.
            Langkah lengkap ada di README.md.
          </p>
        </div>
      )}

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden flex flex-col" style={{ height: 460 }}>
        <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <p className="text-xs font-medium text-slate-300">Asisten AI — Tanya Jawab Keandalan Jaringan (Gemini)</p>
          </div>
          <button onClick={resetChat} className="text-slate-500 hover:text-slate-300 flex items-center gap-1 text-[11px]">
            <RotateCcw className="w-3 h-3" /> Reset
          </button>
        </div>

        <div ref={scrollRef} className="flex-1 overflow-y-auto p-3.5 space-y-2.5">
          {display.map((m, i) => {
            if (m.role === "tool") {
              return (
                <div
                  key={i}
                  className="mx-auto max-w-md rounded-md border border-violet-500/30 bg-violet-500/5 px-3 py-2 font-mono text-[10.5px]"
                >
                  <div className="flex items-center gap-1.5 mb-1 text-violet-300">
                    <Wrench className="w-3 h-3" />
                    {m.name}({JSON.stringify(m.args)})
                  </div>
                  <div className="text-slate-500 break-words">{"\u2192 " + JSON.stringify(m.result)}</div>
                </div>
              );
            }
            const isUser = m.role === "user";
            return (
              <div key={i} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                <div className={`flex items-start gap-2 max-w-[85%] ${isUser ? "flex-row-reverse" : ""}`}>
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                      isUser ? "bg-cyan-500" : "bg-slate-800 border border-slate-700"
                    }`}
                  >
                    {isUser ? <User className="w-3 h-3 text-slate-950" /> : <Bot className="w-3 h-3 text-cyan-400" />}
                  </div>
                  <div
                    className={`rounded-lg px-3 py-2 text-xs leading-relaxed ${
                      isUser
                        ? "bg-cyan-500/15 text-cyan-50 ring-1 ring-cyan-500/30"
                        : m.isError
                        ? "bg-rose-500/10 text-rose-200 ring-1 ring-rose-500/30"
                        : "bg-slate-800/60 text-slate-200 ring-1 ring-slate-700/60"
                    }`}
                  >
                    {m.text}
                  </div>
                </div>
              </div>
            );
          })}
          {loading && (
            <div className="flex justify-start">
              <div className="rounded-lg px-3 py-2 text-xs text-slate-500 ring-1 ring-slate-800">Agent sedang berpikir…</div>
            </div>
          )}
        </div>

        <div className="border-t border-slate-800 p-2.5">
          {display.length <= 1 && (
            <div className="flex flex-wrap gap-1.5 mb-2">
              {SARAN.map((s, i) => (
                <button
                  key={i}
                  onClick={() => ask(s)}
                  className="text-[10.5px] px-2.5 py-1.5 rounded-full bg-slate-800/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800 ring-1 ring-slate-700/60"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && ask(input)}
              disabled={loading}
              placeholder="Tanyakan sesuatu tentang keandalan jaringan…"
              className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-3 py-2 text-xs text-slate-200 placeholder:text-slate-600 outline-none focus:border-cyan-500/50"
            />
            <button
              onClick={() => ask(input)}
              disabled={loading || !input.trim()}
              className="bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 disabled:hover:bg-cyan-500 text-slate-950 rounded-md px-3 flex items-center justify-center"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
