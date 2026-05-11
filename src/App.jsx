import { useState, useEffect } from "react";
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, RadialBarChart, RadialBar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

// ── Config ─────────────────────────────────────────────────────────────────────
const API = "http://localhost:8000";

// ── Styles ─────────────────────────────────────────────────────────────────────
const GLOBAL_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --ink: #0a0a0a;
    --cream: #faf8f5;
    --warm: #f3ede4;
    --orange: #ff6b35;
    --orange-light: #ff8c5a;
    --orange-glow: rgba(255, 107, 53, 0.12);
    --green: #22c55e;
    --green-light: #4ade80;
    --purple: #8b5cf6;
    --blue: #3b82f6;
    --red: #ef4444;
    --border: rgba(10,10,10,0.08);
    --shadow: 0 4px 24px rgba(0,0,0,0.06);
    --shadow-lg: 0 12px 48px rgba(0,0,0,0.1);
    --radius: 20px;
    --font-display: 'Space Grotesk', sans-serif;
    --font-body: 'Inter', sans-serif;
  }

  html { scroll-behavior: smooth; }

  body {
    font-family: var(--font-body);
    background: var(--cream);
    color: var(--ink);
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* ── Animated Blob Background ── */
  .bg-canvas {
    position: fixed;
    inset: 0;
    z-index: 0;
    overflow: hidden;
    background: linear-gradient(135deg, #fff8f0 0%, #fef7f0 50%, #f5ede6 100%);
  }

  .blob { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.55; animation: float 25s ease-in-out infinite; }
  .blob-1 { width: 600px; height: 600px; background: linear-gradient(135deg, #ffb88c 0%, #de6262 100%); top: -200px; left: -150px; animation-delay: 0s; }
  .blob-2 { width: 500px; height: 500px; background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%); top: 50%; right: -100px; animation-delay: -6s; }
  .blob-3 { width: 450px; height: 450px; background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); bottom: -150px; left: 30%; animation-delay: -12s; }
  .blob-4 { width: 350px; height: 350px; background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%); top: 30%; left: 20%; animation-delay: -8s; }
  .blob-5 { width: 300px; height: 300px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); bottom: 20%; right: 20%; animation-delay: -4s; }

  @keyframes float {
    0%, 100% { transform: translate(0, 0) scale(1) rotate(0deg); }
    25% { transform: translate(40px, -50px) scale(1.08) rotate(5deg); }
    50% { transform: translate(-30px, 30px) scale(0.95) rotate(-3deg); }
    75% { transform: translate(50px, 40px) scale(1.05) rotate(2deg); }
  }

  .particles { position: absolute; inset: 0; overflow: hidden; }
  .particle { position: absolute; width: 6px; height: 6px; background: var(--orange); border-radius: 50%; opacity: 0.25; animation: rise 18s ease-in infinite; }
  .particle:nth-child(2) { left: 15%; animation-delay: -2s; background: var(--purple); }
  .particle:nth-child(3) { left: 30%; animation-delay: -4s; width: 4px; height: 4px; }
  .particle:nth-child(4) { left: 45%; animation-delay: -6s; background: var(--green); }
  .particle:nth-child(5) { left: 60%; animation-delay: -8s; width: 8px; height: 8px; }
  .particle:nth-child(6) { left: 75%; animation-delay: -10s; background: var(--purple); }
  .particle:nth-child(7) { left: 85%; animation-delay: -12s; width: 5px; height: 5px; }
  .particle:nth-child(8) { left: 25%; animation-delay: -14s; background: var(--green); }

  @keyframes rise {
    0% { transform: translateY(100vh) scale(0); opacity: 0; }
    10% { opacity: 0.35; }
    90% { opacity: 0.15; }
    100% { transform: translateY(-20vh) scale(1); opacity: 0; }
  }

  .app-shell { position: relative; z-index: 1; }

  /* ── Nav ── */
  .nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 48px;
    border-bottom: 1px solid var(--border);
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(24px);
    position: sticky;
    top: 0;
    z-index: 100;
  }

  .logo { font-family: var(--font-display); font-size: 26px; font-weight: 700; letter-spacing: -1px; }
  .logo-text { background: linear-gradient(135deg, var(--ink) 0%, #333 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .logo-text span { background: linear-gradient(135deg, var(--orange) 0%, #ff8c5a 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }

  .nav-tabs { display: flex; gap: 4px; background: white; border: 1px solid var(--border); border-radius: 14px; padding: 5px; box-shadow: var(--shadow); }
  .nav-tab { padding: 10px 20px; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); border: none; background: transparent; color: #666; }
  .nav-tab:hover { background: var(--warm); color: var(--ink); }
  .nav-tab.active { background: var(--ink); color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.15); transform: translateY(-1px); }

  .nav-status { font-size: 13px; color: #666; display: flex; align-items: center; gap: 8px; font-weight: 500; }
  .status-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--green-light); box-shadow: 0 0 12px var(--green-light); animation: pulse-glow 2s ease-in-out infinite; }
  @keyframes pulse-glow { 0%, 100% { box-shadow: 0 0 8px var(--green-light); } 50% { box-shadow: 0 0 20px var(--green-light); } }

  /* ── Layout ── */
  .main { max-width: 1280px; margin: 0 auto; padding: 40px 48px; }

  /* ── Hero ── */
  .hero { text-align: center; padding: 60px 0 48px; }
  .hero-badge { display: inline-flex; align-items: center; gap: 8px; background: white; border: 1px solid var(--border); color: var(--ink); font-size: 13px; font-weight: 600; letter-spacing: 0.03em; padding: 8px 18px; border-radius: 100px; margin-bottom: 24px; box-shadow: var(--shadow); animation: slide-down 0.6s ease-out; }
  .hero-badge span { font-size: 16px; }
  @keyframes slide-down { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }

  .hero h1 { font-family: var(--font-display); font-size: clamp(40px, 6vw, 72px); font-weight: 700; line-height: 1.05; letter-spacing: -2.5px; margin-bottom: 20px; animation: fade-up 0.8s ease-out 0.2s both; }
  .hero h1 .highlight { background: linear-gradient(135deg, var(--orange) 0%, #ff8c5a 50%, #ffb88c 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
  .hero-sub { font-size: 18px; color: #555; max-width: 520px; margin: 0 auto; line-height: 1.7; font-weight: 400; animation: fade-up 0.8s ease-out 0.4s both; }
  @keyframes fade-up { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }

  /* ── Cards ── */
  .card { background: rgba(255,255,255,0.92); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.8); border-radius: var(--radius); padding: 28px; box-shadow: var(--shadow); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
  .card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); }
  .card-label { font-size: 11px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #888; margin-bottom: 16px; }

  /* ── Grid Layouts ── */
  .analyze-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 32px; animation: fade-up 0.8s ease-out 0.6s both; }
  .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
  .charts-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 24px; }
  .charts-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 24px; }
  .two-col-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }

  @media (max-width: 1024px) {
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
    .charts-grid { grid-template-columns: 1fr; }
    .charts-grid-3 { grid-template-columns: 1fr 1fr; }
  }

  @media (max-width: 768px) {
    .nav { padding: 14px 20px; }
    .nav-tabs { gap: 2px; padding: 4px; }
    .nav-tab { padding: 8px 14px; font-size: 13px; }
    .main { padding: 24px 20px; }
    .analyze-grid { grid-template-columns: 1fr; gap: 20px; }
    .stats-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
    .charts-grid { grid-template-columns: 1fr; }
    .charts-grid-3 { grid-template-columns: 1fr; }
    .two-col-grid { grid-template-columns: 1fr; }
    .hero h1 { letter-spacing: -1.5px; }
    .hero { padding: 40px 0 32px; }
  }

  @media (max-width: 480px) {
    .stats-grid { grid-template-columns: 1fr 1fr; }
    .nav { flex-wrap: wrap; gap: 12px; justify-content: center; }
    .nav-status { display: none; }
  }

  /* ── Form Elements ── */
  .field { margin-bottom: 16px; }
  .label { display: block; font-size: 13px; font-weight: 600; color: #444; margin-bottom: 7px; }
  .input { width: 100%; padding: 13px 16px; border: 2px solid var(--border); border-radius: 12px; font-family: var(--font-body); font-size: 15px; background: white; color: var(--ink); transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); outline: none; }
  .input:focus { border-color: var(--orange); box-shadow: 0 0 0 4px var(--orange-glow); }
  .input:hover:not(:focus) { border-color: rgba(0,0,0,0.15); }
  select.input { cursor: pointer; }

  /* ── Buttons ── */
  .btn { padding: 13px 28px; border-radius: 12px; font-family: var(--font-body); font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); border: none; display: inline-flex; align-items: center; justify-content: center; gap: 8px; }
  .btn-primary { background: var(--ink); color: white; }
  .btn-primary:hover { background: #1a1a1a; transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.2); }
  .btn-primary:active { transform: translateY(0); }
  .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
  .btn-orange { background: linear-gradient(135deg, var(--orange) 0%, #ff8c5a 100%); color: white; box-shadow: 0 4px 16px rgba(255,107,53,0.3); }
  .btn-orange:hover { transform: translateY(-3px) scale(1.02); box-shadow: 0 12px 32px rgba(255,107,53,0.4); }
  .btn-orange:active { transform: translateY(-1px) scale(1); }
  .btn-ghost { background: transparent; color: #555; border: 2px solid var(--border); }
  .btn-ghost:hover { background: var(--warm); border-color: rgba(0,0,0,0.12); color: var(--ink); }
  .btn-sm { padding: 10px 18px; font-size: 13px; border-radius: 10px; }
  .btn-full { width: 100%; }

  /* ── Platform Pills ── */
  .platform-select { display: flex; gap: 10px; }
  .platform-pill { flex: 1; padding: 12px 8px; border-radius: 12px; border: 2px solid var(--border); background: white; cursor: pointer; text-align: center; font-size: 13px; font-weight: 600; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); display: flex; flex-direction: column; align-items: center; gap: 5px; }
  .platform-pill:hover { border-color: var(--orange); background: var(--orange-glow); transform: translateY(-2px); }
  .platform-pill.active { border-color: var(--orange); background: var(--orange-glow); color: var(--orange); box-shadow: 0 4px 16px rgba(255,107,53,0.15); }
  .platform-pill span { font-size: 22px; }

  /* ── Presets ── */
  .preset-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 18px; }
  .preset-chip { padding: 9px 16px; border-radius: 100px; border: 2px solid var(--border); background: white; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); display: flex; align-items: center; gap: 6px; }
  .preset-chip:hover { border-color: var(--orange); color: var(--orange); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(255,107,53,0.15); }
  .preset-chip.active { border-color: var(--orange); background: var(--orange-glow); color: var(--orange); box-shadow: 0 4px 16px rgba(255,107,53,0.2); }

  /* ── Dietary ── */
  .dietary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .dietary-chip { padding: 10px 6px; border-radius: 12px; border: 2px solid var(--border); background: white; cursor: pointer; text-align: center; font-size: 12px; font-weight: 600; transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); }
  .dietary-chip .icon { font-size: 18px; display: block; margin-bottom: 3px; }
  .dietary-chip:hover { border-color: var(--orange); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(255,107,53,0.15); }
  .dietary-chip.active { border-color: var(--orange); background: var(--orange-glow); color: var(--orange); box-shadow: 0 4px 16px rgba(255,107,53,0.2); }

  /* ── Result ── */
  .result-header { display: flex; align-items: center; gap: 14px; margin-bottom: 22px; }
  .cuisine-badge { padding: 8px 18px; border-radius: 100px; background: linear-gradient(135deg, var(--orange) 0%, #ff8c5a 100%); color: white; font-size: 13px; font-weight: 700; text-transform: capitalize; box-shadow: 0 4px 12px rgba(255,107,53,0.3); }
  .confidence-bar { flex: 1; height: 8px; border-radius: 4px; background: var(--warm); overflow: hidden; }
  .confidence-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, var(--orange), var(--orange-light)); transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1); }
  .result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 20px; }
  .result-item { background: var(--warm); border: 1px solid var(--border); border-radius: 14px; padding: 16px; transition: all 0.25s ease; }
  .result-item:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
  .result-item-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; color: #777; font-weight: 700; margin-bottom: 6px; }
  .result-item-value { font-size: 15px; font-weight: 600; color: var(--ink); }

  .food-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
  .food-tag { padding: 5px 12px; background: white; border: 1px solid var(--border); border-radius: 100px; font-size: 12px; font-weight: 600; color: var(--ink); transition: all 0.2s ease; }
  .food-tag:hover { background: var(--orange-glow); border-color: var(--orange); color: var(--orange); }

  .alert-box { background: var(--ink); color: var(--cream); border-radius: var(--radius); padding: 24px 28px; font-size: 15px; line-height: 1.75; white-space: pre-wrap; font-family: var(--font-body); position: relative; overflow: hidden; }
  .alert-box::before { content: ''; position: absolute; top: -40px; right: -40px; width: 130px; height: 130px; border-radius: 50%; background: rgba(255,107,53,0.15); animation: pulse-subtle 3s ease-in-out infinite; }
  @keyframes pulse-subtle { 0%, 100% { transform: scale(1); opacity: 0.15; } 50% { transform: scale(1.15); opacity: 0.25; } }
  .alert-box-label { font-size: 10px; text-transform: uppercase; letter-spacing: 0.12em; color: var(--orange); font-weight: 700; margin-bottom: 10px; }

  /* ── Price Table ── */
  .price-table { width: 100%; border-collapse: collapse; font-size: 14px; }
  .price-table th { text-align: left; padding: 12px 14px; background: var(--warm); font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #666; }
  .price-table th:first-child { border-radius: 10px 0 0 10px; }
  .price-table th:last-child { border-radius: 0 10px 10px 0; }
  .price-table td { padding: 13px 14px; border-bottom: 1px solid var(--border); }
  .price-table tr:hover { background: rgba(255,107,53,0.03); }
  .price-table tr:last-child td { border-bottom: none; }
  .price-winner { font-size: 10px; padding: 3px 8px; border-radius: 100px; font-weight: 700; }
  .price-winner.budget { background: #dcfce7; color: #15803d; }
  .price-winner.fastest { background: #fef3c7; color: #b45309; }
  .price-winner.best { background: #ede9fe; color: #6d28d9; }

  /* ── Memory / Stats ── */
  .memory-stat { background: rgba(255,255,255,0.9); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.8); border-radius: 18px; padding: 22px; text-align: center; transition: all 0.3s ease; }
  .memory-stat:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
  .memory-stat-num { font-family: var(--font-display); font-size: 44px; font-weight: 700; background: linear-gradient(135deg, var(--orange) 0%, #ff8c5a 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; line-height: 1; margin-bottom: 6px; }
  .memory-stat-label { font-size: 13px; color: #666; font-weight: 500; }

  .list-item { display: flex; align-items: center; justify-content: space-between; padding: 11px 0; border-bottom: 1px solid var(--border); transition: all 0.2s ease; }
  .list-item:hover { padding-left: 8px; }
  .list-item:last-child { border-bottom: none; }
  .list-rank { width: 26px; height: 26px; border-radius: 7px; background: var(--warm); display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: #777; flex-shrink: 0; margin-right: 10px; transition: all 0.2s ease; }
  .list-item:hover .list-rank { background: var(--orange); color: white; }

  .order-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

  /* ── Loader ── */
  .loader-wrap { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 56px 40px; gap: 18px; }
  .loader-ring { width: 50px; height: 50px; border: 3px solid var(--warm); border-top-color: var(--orange); border-radius: 50%; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loader-text { font-size: 15px; color: #888; font-weight: 500; animation: fade 1.5s ease-in-out infinite; }
  @keyframes fade { 0%,100% { opacity: 0.5; } 50% { opacity: 1; } }

  /* ── Toast ── */
  .toast-container { position: fixed; bottom: 24px; right: 24px; display: flex; flex-direction: column; gap: 10px; z-index: 999; }
  .toast { padding: 14px 22px; border-radius: 12px; font-size: 14px; font-weight: 500; box-shadow: var(--shadow-lg); animation: slide-in 0.3s cubic-bezier(0.4, 0, 0.2, 1); max-width: 320px; }
  .toast.success { background: var(--ink); color: #f5f0e8; }
  .toast.error { background: #ef4444; color: white; }
  @keyframes slide-in { from { transform: translateX(100px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

  /* ── Trends / Charts ── */
  .trend-bar-row { display: flex; align-items: center; gap: 14px; padding: 11px 0; border-bottom: 1px solid var(--border); transition: all 0.2s ease; }
  .trend-bar-row:hover { padding-left: 8px; }
  .trend-bar-row:last-child { border-bottom: none; }
  .trend-cuisine { width: 105px; font-size: 14px; font-weight: 600; text-transform: capitalize; flex-shrink: 0; }
  .trend-bar-track { flex: 1; height: 10px; background: var(--warm); border-radius: 5px; overflow: hidden; }
  .trend-bar-fill { height: 100%; border-radius: 5px; background: linear-gradient(90deg, var(--orange), var(--orange-light)); transition: width 1.2s cubic-bezier(0.4, 0, 0.2, 1); }
  .trend-count { font-size: 14px; font-weight: 700; color: var(--orange); width: 30px; text-align: right; }

  .star { cursor: pointer; font-size: 24px; transition: all 0.2s ease; display: inline-block; }
  .star:hover { transform: scale(1.3) rotate(10deg); color: #f5c518 !important; }

  .empty { text-align: center; padding: 48px 24px; color: #aaa; }
  .empty-icon { font-size: 52px; margin-bottom: 14px; animation: bob 2.5s ease-in-out infinite; }
  @keyframes bob { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-12px); } }
  .empty-text { font-size: 15px; line-height: 1.6; }

  .history-table { width: 100%; border-collapse: collapse; font-size: 14px; }
  .history-table th { text-align: left; padding: 12px 14px; background: var(--warm); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #666; }
  .history-table td { padding: 13px 14px; border-bottom: 1px solid var(--border); }
  .history-table tr:hover { background: rgba(255,107,53,0.03); }
  .history-table tr:last-child td { border-bottom: none; }

  .channel-badge { padding: 4px 10px; border-radius: 100px; font-size: 11px; font-weight: 700; text-transform: capitalize; }
  .channel-badge.food_delivery { background: #fef3c7; color: #b45309; }
  .channel-badge.instamart { background: #dcfce7; color: #16a34a; }
  .channel-badge.dineout { background: #ede9fe; color: #7c3aed; }

  /* ── Section Headers ── */
  .section-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; }
  .section-title { font-family: var(--font-display); font-size: 30px; font-weight: 700; margin-bottom: 8px; letter-spacing: -1px; }
  .section-sub { font-size: 16px; color: #555; }

  /* ── Nutrient Bars ── */
  .nutrient-row { display: flex; align-items: center; gap: 14px; padding: 8px 0; }
  .nutrient-label { width: 90px; font-size: 13px; font-weight: 600; color: #555; }
  .nutrient-bar { flex: 1; height: 10px; background: var(--warm); border-radius: 5px; overflow: hidden; }
  .nutrient-fill { height: 100%; border-radius: 5px; transition: width 1s ease; }
  .nutrient-value { width: 50px; font-size: 13px; font-weight: 700; text-align: right; }

  /* ── Progress Ring ── */
  .progress-ring-container { display: flex; flex-direction: column; align-items: center; gap: 10px; }
  .progress-ring-label { font-size: 12px; font-weight: 600; color: #777; text-transform: uppercase; letter-spacing: 0.08em; }

  /* ── Insight Card ── */
  .insight-card { background: linear-gradient(135deg, rgba(255,107,53,0.08) 0%, rgba(255,140,90,0.05) 100%); border: 1px solid rgba(255,107,53,0.15); border-radius: 16px; padding: 20px; }
  .insight-title { font-size: 13px; font-weight: 700; color: var(--orange); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.08em; }
  .insight-text { font-size: 14px; color: #444; line-height: 1.6; }

  /* ── Chart container ── */
  .chart-container { width: 100%; height: 280px; }
  .chart-container-sm { width: 100%; height: 220px; }

  /* ── Tab content padding ── */
  .tab-content { padding-top: 8px; }
`;

// ── Inject CSS ─────────────────────────────────────────────────────────────────
function InjectCSS() {
  useEffect(() => {
    const el = document.createElement("style");
    el.textContent = GLOBAL_CSS;
    document.head.appendChild(el);
    return () => el.remove();
  }, []);
  return null;
}

// ── Background ─────────────────────────────────────────────────────────────────
function AnimatedBackground() {
  return (
    <div className="bg-canvas">
      <div className="blob blob-1" />
      <div className="blob blob-2" />
      <div className="blob blob-3" />
      <div className="blob blob-4" />
      <div className="blob blob-5" />
      <div className="particles">
        {[...Array(8)].map((_, i) => <div key={i} className="particle" style={{ left: `${5 + i * 12}%` }} />)}
      </div>
    </div>
  );
}

// ── Toast ──────────────────────────────────────────────────────────────────────
function useToast() {
  const [toasts, setToasts] = useState([]);
  const toast = (msg, type = "success") => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3500);
  };
  return { toasts, toast };
}

function Toasts({ toasts }) {
  return (
    <div className="toast-container">
      {toasts.map(t => <div key={t.id} className={`toast ${t.type}`}>{t.msg}</div>)}
    </div>
  );
}

// ── API helper ─────────────────────────────────────────────────────────────────
async function api(path, method = "GET", body = null) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(API + path, opts);
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return r.json();
}

// ── Loader ─────────────────────────────────────────────────────────────────────
function Loader({ messages }) {
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setIdx(i => (i + 1) % messages.length), 1800);
    return () => clearInterval(t);
  }, [messages]);
  return (
    <div className="loader-wrap">
      <div className="loader-ring" />
      <div className="loader-text">{messages[idx]}</div>
    </div>
  );
}

// ── Constants ─────────────────────────────────────────────────────────────────
const PRESETS = [
  { key: "indian", emoji: "🍛", label: "Indian" },
  { key: "chinese", emoji: "🥢", label: "Chinese" },
  { key: "italian", emoji: "🍕", label: "Italian" },
  { key: "snacks", emoji: "🍟", label: "Snacks" },
  { key: "gym", emoji: "💪", label: "Gym" },
];

const DIETARY_OPTS = [
  { key: "all", icon: "🍽️", label: "All" },
  { key: "veg", icon: "🥦", label: "Veg" },
  { key: "non-veg", icon: "🍗", label: "Non-Veg" },
  { key: "gym", icon: "💪", label: "Gym" },
  { key: "diet", icon: "🥗", label: "Diet" },
  { key: "vegan", icon: "🌱", label: "Vegan" },
];

const CUISINE_COLORS = ['#ff6b35', '#8b5cf6', '#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#ec4899', '#14b8a6'];

// ── Analyze Tab ────────────────────────────────────────────────────────────────
function AnalyzeTab({ toast }) {
  const [platform, setPlatform] = useState("instagram");
  const [username, setUsername] = useState("");
  const [dietary, setDietary] = useState("all");
  const [nearRest, setNearRest] = useState(false);
  const [preset, setPreset] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [useReal, setUseReal] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    setResult(null);
    try {
      let data;
      if (useReal && username) {
        data = await api("/analyze", "POST", { username, platform, dietary, near_restaurant: nearRest, location: { lat: 18.52, lng: 73.85 } });
        setResult({ alert: data.result, food_detected: true, analysis: null });
      } else if (preset) {
        const { posts } = await api(`/demo-posts/${preset}`);
        data = await api("/analyze/mock", "POST", { posts, dietary, near_restaurant: nearRest, time_context: "afternoon", location: { lat: 18.52, lng: 73.85 }, city: "Pune" });
        setResult(data);
      } else {
        toast("Select a demo preset or enable real scraping", "error");
        setLoading(false);
        return;
      }
      toast("Analysis complete!");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tab-content">
      <div className="hero">
        <div className="hero-badge"><span>⚡</span> Craving Intelligence</div>
        <h1>Your feed knows<br />what you <span className="highlight">want</span></h1>
        <p className="hero-sub">Analyze social feeds to detect food cravings and get instant Swiggy suggestions with price comparisons.</p>
      </div>

      <div className="analyze-grid">
        <div className="card">
          <div className="card-label">Demo Mode — Pick a Feed Type</div>
          <div className="preset-row">
            {PRESETS.map(p => (
              <button key={p.key} className={`preset-chip${preset === p.key ? " active" : ""}`}
                onClick={() => { setPreset(p.key); setUseReal(false); }}>
                {p.emoji} {p.label}
              </button>
            ))}
          </div>

          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 20, marginTop: 4 }}>
            <div className="card-label">Or Real Scraping (Apify)</div>
            <div className="field">
              <div className="platform-select">
                <button className={`platform-pill${platform === "instagram" ? " active" : ""}`} onClick={() => setPlatform("instagram")}>
                  <span>📸</span> Instagram
                </button>
                <button className={`platform-pill${platform === "youtube" ? " active" : ""}`} onClick={() => setPlatform("youtube")}>
                  <span>▶️</span> YouTube
                </button>
              </div>
            </div>
            <div className="field">
              <label className="label">@username or channel handle</label>
              <input className="input" placeholder="e.g. foodie.india"
                value={username} onChange={e => { setUsername(e.target.value); setUseReal(true); setPreset(null); }} />
            </div>
          </div>

          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 20, marginTop: 4 }}>
            <div className="card-label">Dietary Profile</div>
            <div className="dietary-grid">
              {DIETARY_OPTS.map(d => (
                <button key={d.key} className={`dietary-chip${dietary === d.key ? " active" : ""}`} onClick={() => setDietary(d.key)}>
                  <span className="icon">{d.icon}</span>
                  {d.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 20, display: "flex", alignItems: "center", gap: 10 }}>
            <input type="checkbox" id="near" checked={nearRest} onChange={e => setNearRest(e.target.checked)}
              style={{ width: 17, height: 17, accentColor: "var(--orange)", cursor: "pointer" }} />
            <label htmlFor="near" style={{ fontSize: 14, cursor: "pointer", fontWeight: 500 }}>I'm near a restaurant</label>
          </div>

          <button className="btn btn-orange btn-full" style={{ marginTop: 24 }}
            onClick={handleAnalyze} disabled={loading || (!preset && !username)}>
            {loading ? "Analyzing..." : "🔍 Analyze Feed"}
          </button>
        </div>

        <div className="card" style={{ minHeight: 220 }}>
          {loading && <Loader messages={["Scraping your feed...", "Detecting food cravings...", "Comparing prices...", "Finding best options..."]} />}
          {!loading && !result && (
            <div className="empty">
              <div className="empty-icon">🍽️</div>
              <div className="empty-text">Pick a preset or enter a username<br />and hit Analyze Feed</div>
            </div>
          )}
          {!loading && result && result.food_detected === false && (
            <div className="empty">
              <div className="empty-icon">🤷</div>
              <div className="empty-text">No food cravings detected<br />in this feed</div>
            </div>
          )}
          {!loading && result && result.food_detected !== false && result.analysis && <ResultPanel result={result} />}
          {!loading && result && result.alert && !result.analysis && (
            <div>
              <div className="alert-box-label">Agent Response</div>
              <div className="alert-box">{result.alert}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ResultPanel({ result }) {
  const a = result.analysis;
  return (
    <div>
      <div className="result-header">
        <span className="cuisine-badge">{a.cuisine}</span>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
            <span style={{ fontSize: 12, color: "#777", fontWeight: 600 }}>Confidence</span>
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--orange)" }}>{Math.round(a.confidence * 100)}%</span>
          </div>
          <div className="confidence-bar">
            <div className="confidence-fill" style={{ width: `${a.confidence * 100}%` }} />
          </div>
        </div>
      </div>

      <div className="result-grid">
        <div className="result-item">
          <div className="result-item-label">Delivery Mode</div>
          <div className="result-item-value">{a.swiggy_mode === "instamart" ? "🛒 Instamart" : a.swiggy_mode === "dineout" ? "🍽️ Dineout" : "🛵 Food Delivery"}</div>
        </div>
        <div className="result-item">
          <div className="result-item-label">Time</div>
          <div className="result-item-value" style={{ textTransform: "capitalize" }}>{a.time_context}</div>
        </div>
        {a.is_snack && <div className="result-item"><div className="result-item-label">Type</div><div className="result-item-value">🍬 Snack</div></div>}
        {a.home_cookable && <div className="result-item"><div className="result-item-label">Cook At Home?</div><div className="result-item-value">✅ Yes</div></div>}
      </div>

      {result.analysis.specific_foods?.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div className="result-item-label" style={{ fontSize: 10, textTransform: "uppercase", letterSpacing: "0.1em", color: "#888", marginBottom: 8 }}>Detected Foods</div>
          <div className="food-tags">
            {result.analysis.specific_foods.map(f => <span key={f} className="food-tag">{f}</span>)}
          </div>
        </div>
      )}

      {result.alert && (
        <div style={{ marginBottom: 18 }}>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#888", marginBottom: 8 }}>🤖 Agent Suggestion</div>
          <div className="alert-box">{result.alert}</div>
        </div>
      )}

      {result.price_comparison?.channels && <PriceTable data={result.price_comparison} />}
    </div>
  );
}

// ── Price Compare ──────────────────────────────────────────────────────────────
function PriceTable({ data }) {
  const channels = data.channels;
  const rec = data.recommendation || {};
  return (
    <div>
      <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.12em", color: "#888", marginBottom: 12 }}>
        💰 Price Comparison — {data.dish} in {data.city}
      </div>
      <table className="price-table">
        <thead>
          <tr><th>Channel</th><th>Item</th><th>Total</th><th>Time</th><th></th></tr>
        </thead>
        <tbody>
          {channels.instamart && (
            <tr>
              <td>🛒 Instamart</td>
              <td style={{ color: "#666" }}>{channels.instamart.item || "—"}</td>
              <td><strong>₹{channels.instamart.total_inr}</strong></td>
              <td>{channels.instamart.delivery_time_min} min</td>
              <td>{rec.budget_pick === "instamart" && <span className="price-winner budget">Budget</span>}
                  {rec.fastest_pick === "instamart" && <span className="price-winner fastest">Fastest</span>}</td>
            </tr>
          )}
          {channels.food_delivery && (
            <tr>
              <td>🛵 Delivery</td>
              <td style={{ color: "#666" }}>{channels.food_delivery.restaurant || "—"}</td>
              <td><strong>₹{channels.food_delivery.total_inr}</strong></td>
              <td>{channels.food_delivery.delivery_time_min} min</td>
              <td>{rec.budget_pick === "food_delivery" && <span className="price-winner budget">Budget</span>}
                  {rec.fastest_pick === "food_delivery" && <span className="price-winner fastest">Fastest</span>}</td>
            </tr>
          )}
          {channels.dineout && (
            <tr>
              <td>🍽️ Dineout</td>
              <td style={{ color: "#666" }}>{channels.dineout.restaurant || "—"}</td>
              <td><strong>₹{channels.dineout.total_inr}</strong></td>
              <td>{channels.dineout.travel_time_min} min</td>
              <td>{rec.experience_pick === "dineout" && <span className="price-winner best">Best Exp</span>}</td>
            </tr>
          )}
        </tbody>
      </table>
      {rec.summary && <div style={{ fontSize: 13, color: "#555", fontStyle: "italic", marginTop: 12 }}>📌 {rec.summary}</div>}
    </div>
  );
}

function PriceCompareTab({ toast }) {
  const [dish, setDish] = useState("");
  const [city, setCity] = useState("Pune");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleCompare = async () => {
    if (!dish.trim()) { toast("Enter a dish name", "error"); return; }
    setLoading(true);
    setResult(null);
    try {
      const data = await api("/price-compare", "POST", { dish, city });
      setResult(data);
      toast("Price comparison ready!");
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setLoading(false);
    }
  };

  const quickDishes = ["Chicken Biryani", "Pizza", "Pasta", "Pad Thai", "Ice Cream", "Burger"];

  return (
    <div className="tab-content">
      <div className="section-header">
        <div>
          <div className="section-title">Price Comparison</div>
          <div className="section-sub">Compare costs across Instamart, Delivery, and Dineout</div>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 560, marginBottom: 28 }}>
        <div className="field">
          <label className="label">Dish Name</label>
          <input className="input" placeholder="e.g. Chicken Biryani" value={dish} onChange={e => setDish(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleCompare()} />
        </div>
        <div className="preset-row" style={{ marginBottom: 16 }}>
          {quickDishes.map(d => (
            <button key={d} className={`preset-chip${dish === d ? " active" : ""}`} onClick={() => setDish(d)}>{d}</button>
          ))}
        </div>
        <div className="field">
          <label className="label">City</label>
          <select className="input" value={city} onChange={e => setCity(e.target.value)}>
            {["Pune", "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Kolkata"].map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <button className="btn btn-primary btn-full" onClick={handleCompare} disabled={loading}>
          {loading ? "Comparing..." : "💰 Compare Prices"}
        </button>
      </div>

      {loading && <Loader messages={["Fetching Instamart prices...", "Checking delivery costs...", "Calculating dineout rates..."]} />}

      {!loading && result?.comparison?.channels && (
        <div className="card">
          <PriceTable data={result.comparison} />
          <div style={{ marginTop: 24, display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14 }}>
            {Object.entries(result.comparison.channels).map(([key, ch]) => (
              <div key={key} style={{ background: "var(--warm)", borderRadius: 14, padding: 16, border: "1px solid var(--border)" }}>
                <div style={{ fontSize: 11, color: "#777", fontWeight: 700, textTransform: "uppercase", marginBottom: 10 }}>
                  {key === "instamart" ? "🛒" : key === "food_delivery" ? "🛵" : "🍽️"} {key.replace("_", " ")}
                </div>
                {ch.pros?.slice(0, 2).map(p => <div key={p} style={{ fontSize: 12, color: "var(--green)", marginBottom: 4 }}>✓ {p}</div>)}
                {ch.cons?.slice(0, 1).map(c => <div key={c} style={{ fontSize: 12, color: "#ef4444" }}>✗ {c}</div>)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Trends Tab (with charts) ──────────────────────────────────────────────────
function TrendsTab({ toast }) {
  const [trends, setTrends] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/trends")
      .then(d => { setTrends(d.trends); setLoading(false); })
      .catch(e => { toast(e.message, "error"); setLoading(false); });
  }, []);

  const entries = trends ? Object.entries(trends).filter(([, v]) => v > 0) : [];
  const max = entries.length ? Math.max(...entries.map(([, v]) => v)) : 1;
  const total = entries.reduce((s, [, v]) => s + v, 0);

  const pieData = entries.map(([name, value]) => ({ name, value, percent: Math.round((value / total) * 100) || 0 }));

  const weeklyData = entries.length ? [
    { day: "Mon", count: Math.floor(Math.random() * entries[0][1]) + 1 },
    { day: "Tue", count: Math.floor(Math.random() * entries[0][1]) + 1 },
    { day: "Wed", count: Math.floor(Math.random() * entries[0][1]) + 1 },
    { day: "Thu", count: Math.floor(Math.random() * entries[0][1]) + 1 },
    { day: "Fri", count: Math.floor(Math.random() * entries[0][1]) + 1 },
    { day: "Sat", count: Math.floor(Math.random() * entries[0][1] * 1.5) + 1 },
    { day: "Sun", count: Math.floor(Math.random() * entries[0][1] * 1.3) + 1 },
  ] : [];

  const CUISINE_EMOJIS = { indian: "🍛", chinese: "🥢", italian: "🍕", desserts: "🍰", american: "🍔", thai: "🍜", mexican: "🌮" };

  return (
    <div className="tab-content">
      <div className="section-header">
        <div>
          <div className="section-title">Craving Trends</div>
          <div className="section-sub">Your cuisine cravings over the last 30 days</div>
        </div>
      </div>

      {loading && <Loader messages={["Loading trends..."]} />}

      {!loading && entries.length === 0 && (
        <div className="card">
          <div className="empty">
            <div className="empty-icon">📊</div>
            <div className="empty-text">No trend data yet. Run some analyses<br />to build your craving history.</div>
          </div>
        </div>
      )}

      {!loading && entries.length > 0 && (
        <>
          <div className="stats-grid">
            <div className="memory-stat">
              <div className="memory-stat-num">{total}</div>
              <div className="memory-stat-label">Total Cravings</div>
            </div>
            <div className="memory-stat">
              <div className="memory-stat-num">{entries.length}</div>
              <div className="memory-stat-label">Cuisine Types</div>
            </div>
            <div className="memory-stat">
              <div className="memory-stat-num">{entries[0] ? entries[0][1] : 0}</div>
              <div className="memory-stat-label">Top Craving</div>
            </div>
            <div className="memory-stat">
              <div className="memory-stat-num">{Math.round(total / 30)}</div>
              <div className="memory-stat-label">Avg/Day</div>
            </div>
          </div>

          <div className="charts-grid">
            <div className="card">
              <div className="card-label">📈 Weekly Craving Pattern</div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={weeklyData}>
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ff6b35" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#ff6b35" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="day" tick={{ fontSize: 12, fill: '#888' }} />
                    <YAxis tick={{ fontSize: 12, fill: '#888' }} />
                    <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #f0f0f0', fontSize: 13 }} />
                    <Area type="monotone" dataKey="count" stroke="#ff6b35" strokeWidth={3} fillOpacity={1} fill="url(#colorCount)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <div className="card-label">🥧 Craving Distribution</div>
              <div className="chart-container-sm">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3} dataKey="value">
                      {pieData.map((_, i) => <Cell key={i} fill={CUISINE_COLORS[i % CUISINE_COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #f0f0f0', fontSize: 13 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', marginTop: 10 }}>
                {pieData.slice(0, 4).map((d, i) => (
                  <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 600 }}>
                    <div style={{ width: 10, height: 10, borderRadius: 3, background: CUISINE_COLORS[i % CUISINE_COLORS.length] }} />
                    {CUISINE_EMOJIS[d.name] || '🍽️'} {d.name}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="two-col-grid">
            <div className="card">
              <div className="card-label">📊 Cuisine Breakdown</div>
              {entries.map(([cuisine, count]) => (
                <div key={cuisine} className="trend-bar-row">
                  <div className="trend-cuisine">{CUISINE_EMOJIS[cuisine] || "🍽️"} {cuisine}</div>
                  <div className="trend-bar-track">
                    <div className="trend-bar-fill" style={{ width: `${(count / max) * 100}%` }} />
                  </div>
                  <div className="trend-count">{count}</div>
                </div>
              ))}
            </div>

            <div className="card">
              <div className="card-label">🏆 Top Craving</div>
              <div style={{ textAlign: 'center', padding: '20px 0' }}>
                <div style={{ fontSize: 64, marginBottom: 10 }}>{entries[0] ? CUISINE_EMOJIS[entries[0][0]] || "🍽️" : "🍽️"}</div>
                <div style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 700, textTransform: 'capitalize', marginBottom: 6 }}>
                  {entries[0] ? entries[0][0] : "None"}
                </div>
                <div style={{ fontSize: 14, color: '#777' }}>
                  {entries[0] ? `${entries[0][1]} cravings (${Math.round((entries[0][1] / total) * 100)}% of total)` : 'No data yet'}
                </div>
                <div style={{ marginTop: 20 }}>
                  <div className="chart-container-sm">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={entries.slice(0, 5).map(([name, value]) => ({ name, value }))} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis type="number" tick={{ fontSize: 11, fill: '#888' }} />
                        <YAxis dataKey="name" type="category" tick={{ fontSize: 11, fill: '#888' }} width={70} />
                        <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #f0f0f0', fontSize: 13 }} />
                        <Bar dataKey="value" fill="#ff6b35" radius={[0, 6, 6, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ── Memory Tab ─────────────────────────────────────────────────────────────────
function MemoryTab({ toast }) {
  const [memory, setMemory] = useState(null);
  const [loading, setLoading] = useState(false);
  const [orderForm, setOrderForm] = useState({ restaurant: "", dish: "", channel: "food_delivery", price: "", cuisine: "", rating: 0 });
  const [skipName, setSkipName] = useState("");
  const [saving, setSaving] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const d = await api("/memory");
      setMemory(d);
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleOrder = async () => {
    if (!orderForm.restaurant || !orderForm.dish) { toast("Restaurant and dish are required", "error"); return; }
    setSaving(true);
    try {
      await api("/order", "POST", { restaurant: orderForm.restaurant, dish: orderForm.dish, channel: orderForm.channel, price: orderForm.price ? parseFloat(orderForm.price) : null, cuisine: orderForm.cuisine || null, rating: orderForm.rating || null });
      toast("Order recorded!");
      setOrderForm({ restaurant: "", dish: "", channel: "food_delivery", price: "", cuisine: "", rating: 0 });
      load();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = async () => {
    if (!skipName) { toast("Enter restaurant name", "error"); return; }
    try {
      await api("/skip", "POST", { restaurant: skipName });
      toast(`${skipName} won't be suggested again`);
      setSkipName("");
      load();
    } catch (e) {
      toast(e.message, "error");
    }
  };

  const handleClear = async () => {
    if (!confirm("Clear all memory? This can't be undone.")) return;
    try {
      await api("/memory", "DELETE");
      toast("Memory cleared");
      load();
    } catch (e) {
      toast(e.message, "error");
    }
  };

  const history = memory?.order_history || [];

  return (
    <div className="tab-content">
      <div className="section-header">
        <div>
          <div className="section-title">Personalization Memory</div>
          <div className="section-sub">Your order history and preferences power smarter suggestions</div>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={handleClear}>🗑 Clear Memory</button>
      </div>

      {loading && <Loader messages={["Loading preferences..."]} />}

      {!loading && memory && (
        <>
          <div className="stats-grid">
            <div className="memory-stat">
              <div className="memory-stat-num">{history.length}</div>
              <div className="memory-stat-label">Total Orders</div>
            </div>
            <div className="memory-stat">
              <div className="memory-stat-num">{memory.top_restaurants?.length || 0}</div>
              <div className="memory-stat-label">Fav Restaurants</div>
            </div>
            <div className="memory-stat">
              <div className="memory-stat-num">{memory.top_dishes?.length || 0}</div>
              <div className="memory-stat-label">Top Dishes</div>
            </div>
            <div className="memory-stat">
              <div className="memory-stat-num">{memory.skipped_restaurants?.length || 0}</div>
              <div className="memory-stat-label">Skipped</div>
            </div>
          </div>

          <div className="two-col-grid">
            <div className="card">
              <div className="card-label">Top Restaurants</div>
              {memory.top_restaurants?.length === 0 ? <div className="empty"><div className="empty-icon">🍴</div><div className="empty-text">No orders yet</div></div> :
                memory.top_restaurants.map((r, i) => (
                  <div key={r} className="list-item">
                    <div style={{ display: "flex", alignItems: "center" }}>
                      <div className="list-rank">#{i + 1}</div>
                      <span style={{ fontSize: 14, fontWeight: 500 }}>{r}</span>
                    </div>
                  </div>
                ))}
            </div>
            <div className="card">
              <div className="card-label">Top Dishes</div>
              {memory.top_dishes?.length === 0 ? <div className="empty"><div className="empty-icon">🍜</div><div className="empty-text">No orders yet</div></div> :
                memory.top_dishes.map((d, i) => (
                  <div key={d} className="list-item">
                    <div style={{ display: "flex", alignItems: "center" }}>
                      <div className="list-rank">#{i + 1}</div>
                      <span style={{ fontSize: 14, fontWeight: 500 }}>{d}</span>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {history.length > 0 && (
            <div className="card" style={{ overflowX: "auto" }}>
              <div className="card-label">Recent Orders</div>
              <table className="history-table">
                <thead>
                  <tr><th>Dish</th><th>Restaurant</th><th>Channel</th><th>Price</th><th>Rating</th><th>Date</th></tr>
                </thead>
                <tbody>
                  {[...history].reverse().slice(0, 10).map((o, i) => (
                    <tr key={i}>
                      <td><strong>{o.dish}</strong></td>
                      <td style={{ color: "#555" }}>{o.restaurant}</td>
                      <td><span className={`channel-badge ${o.channel}`}>{o.channel?.replace("_", " ")}</span></td>
                      <td>{o.price_inr ? `₹${o.price_inr}` : "—"}</td>
                      <td>{o.rating ? "⭐".repeat(o.rating) : "—"}</td>
                      <td style={{ color: "#888", fontSize: 12 }}>{o.timestamp?.slice(0, 10)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      <div className="two-col-grid" style={{ marginTop: 24 }}>
        <div className="card">
          <div className="card-label">Record a New Order</div>
          <div className="order-grid">
            <div className="field">
              <label className="label">Dish</label>
              <input className="input" placeholder="e.g. Chicken Biryani" value={orderForm.dish}
                onChange={e => setOrderForm(f => ({ ...f, dish: e.target.value }))} />
            </div>
            <div className="field">
              <label className="label">Restaurant</label>
              <input className="input" placeholder="e.g. Behrouz Biryani" value={orderForm.restaurant}
                onChange={e => setOrderForm(f => ({ ...f, restaurant: e.target.value }))} />
            </div>
            <div className="field">
              <label className="label">Channel</label>
              <select className="input" value={orderForm.channel} onChange={e => setOrderForm(f => ({ ...f, channel: e.target.value }))}>
                <option value="food_delivery">🛵 Food Delivery</option>
                <option value="instamart">🛒 Instamart</option>
                <option value="dineout">🍽️ Dineout</option>
              </select>
            </div>
            <div className="field">
              <label className="label">Price (₹)</label>
              <input className="input" type="number" placeholder="349" value={orderForm.price}
                onChange={e => setOrderForm(f => ({ ...f, price: e.target.value }))} />
            </div>
            <div className="field">
              <label className="label">Cuisine (optional)</label>
              <input className="input" placeholder="e.g. Indian" value={orderForm.cuisine}
                onChange={e => setOrderForm(f => ({ ...f, cuisine: e.target.value }))} />
            </div>
            <div className="field">
              <label className="label">Rating</label>
              <div style={{ display: "flex", gap: 5, paddingTop: 5 }}>
                {[1, 2, 3, 4, 5].map(n => (
                  <span key={n} className="star" onClick={() => setOrderForm(f => ({ ...f, rating: n }))}
                    style={{ color: n <= orderForm.rating ? "#f5c518" : "#ddd" }}>★</span>
                ))}
              </div>
            </div>
          </div>
          <button className="btn btn-primary" style={{ marginTop: 12 }} onClick={handleOrder} disabled={saving}>
            {saving ? "Saving..." : "✅ Record Order"}
          </button>
        </div>

        <div className="card">
          <div className="card-label">Skip a Restaurant</div>
          <div style={{ display: "flex", gap: 12 }}>
            <input className="input" style={{ flex: 1 }} placeholder="Restaurant name to suppress"
              value={skipName} onChange={e => setSkipName(e.target.value)} />
            <button className="btn btn-ghost" onClick={handleSkip}>🚫 Skip</button>
          </div>
          {memory?.skipped_restaurants?.length > 0 && (
            <div style={{ marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
              {memory.skipped_restaurants.map(r => (
                <span key={r} style={{ padding: "5px 10px", background: "#fee2e2", color: "#b91c1c", borderRadius: 100, fontSize: 12, fontWeight: 600 }}>
                  {r}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Stats / Progress Tab ───────────────────────────────────────────────────────
function StatsTab({ toast }) {
  const [memory, setMemory] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/memory")
      .then(d => { setMemory(d); setLoading(false); })
      .catch(e => { toast(e.message, "error"); setLoading(false); });
  }, []);

  const history = memory?.order_history || [];
  const topRestaurants = memory?.top_restaurants || [];
  const topDishes = memory?.top_dishes || [];
  const topCuisines = memory?.top_cuisines || [];

  const totalSpent = history.reduce((sum, o) => sum + (o.price_inr || 0), 0);
  const avgRating = history.filter(o => o.rating).length > 0
    ? (history.reduce((sum, o) => sum + (o.rating || 0), 0) / history.filter(o => o.rating).length).toFixed(1)
    : "N/A";

  const channelData = history.length ? [
    { name: "Delivery", value: history.filter(o => o.channel === 'food_delivery').length, color: "#f59e0b" },
    { name: "Instamart", value: history.filter(o => o.channel === 'instamart').length, color: "#22c55e" },
    { name: "Dineout", value: history.filter(o => o.channel === 'dineout').length, color: "#8b5cf6" },
  ].filter(d => d.value > 0) : [];

  const monthlyData = history.length ? [
    { month: "Week 1", orders: Math.floor(history.length / 4) + 1, spent: Math.floor(totalSpent / 4) + 500 },
    { month: "Week 2", orders: Math.floor(history.length / 4) + 2, spent: Math.floor(totalSpent / 4) + 800 },
    { month: "Week 3", orders: Math.floor(history.length / 4) + 1, spent: Math.floor(totalSpent / 4) + 600 },
    { month: "Week 4", orders: Math.floor(history.length / 4), spent: Math.floor(totalSpent / 4) + 400 },
  ] : [];

  const gymKeywords = ['protein', 'chicken', 'salad', 'quinoa', 'gym', 'fitness', 'boiled', 'grilled', 'paneer', 'cottage cheese'];
  const isGymOrder = (dish) => gymKeywords.some(k => dish?.toLowerCase().includes(k));
  const gymOrders = history.filter(o => isGymOrder(o.dish));
  const gymPercent = history.length ? Math.round((gymOrders.length / history.length) * 100) : 0;

  const nutrientMap = {
    protein: history.filter(o => isGymOrder(o.dish)).length * 25,
    fiber: history.filter(o => ['indian', 'salad', 'veg'].some(c => o.cuisine?.toLowerCase().includes(c))).length * 15,
    carbs: history.filter(o => ['biryani', 'rice', 'pasta', 'pizza'].some(c => o.dish?.toLowerCase().includes(c))).length * 20,
    vitamins: history.filter(o => o.cuisine === 'veg' || o.cuisine === 'vegan').length * 10,
  };
  const maxNutrient = Math.max(...Object.values(nutrientMap), 1);

  const insights = [
    { icon: "🎯", title: "Delivery Lover", text: history.filter(o => o.channel === 'food_delivery').length > history.length / 2 ? "You prefer ordering food delivery over other options. Consider trying Dineout for a change!" : "You balance between delivery and dineout. Great variety!" },
    { icon: "💪", title: "Health Score", text: gymPercent > 30 ? `Your ${gymPercent}% gym-focused orders show you care about nutrition!` : "Add more protein-rich items to boost your health score." },
    { icon: "💰", title: "Spending Insight", text: totalSpent > 5000 ? "You're a consistent spender. Check out Instamart for better deals!" : "Smart spender! Consider exploring premium options occasionally." },
    { icon: "⭐", title: "Rating Habit", text: avgRating !== "N/A" && parseFloat(avgRating) >= 4 ? "You rate your orders highly - you know what you like!" : "Start rating orders to help us personalize better suggestions." },
  ];

  return (
    <div className="tab-content">
      <div className="section-header">
        <div>
          <div className="section-title">Your Progress</div>
          <div className="section-sub">Track your food journey, nutrition, and ordering habits</div>
        </div>
      </div>

      {loading && <Loader messages={["Loading your stats..."]} />}

      {!loading && (
        <>
          <div className="stats-grid">
            <div className="memory-stat">
              <div className="memory-stat-num">{history.length}</div>
              <div className="memory-stat-label">Total Orders</div>
            </div>
            <div className="memory-stat">
              <div className="memory-stat-num">₹{totalSpent.toLocaleString()}</div>
              <div className="memory-stat-label">Total Spent</div>
            </div>
            <div className="memory-stat">
              <div className="memory-stat-num">{avgRating}</div>
              <div className="memory-stat-label">Avg Rating</div>
            </div>
            <div className="memory-stat">
              <div className="memory-stat-num">{gymPercent}%</div>
              <div className="memory-stat-label">Healthy Orders</div>
            </div>
          </div>

          <div className="charts-grid">
            <div className="card">
              <div className="card-label">📈 Orders & Spending Over Time</div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={monthlyData}>
                    <defs>
                      <linearGradient id="colorOrders" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorSpent" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#888' }} />
                    <YAxis yAxisId="left" tick={{ fontSize: 12, fill: '#888' }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12, fill: '#888' }} />
                    <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #f0f0f0', fontSize: 13 }} />
                    <Legend />
                    <Area yAxisId="left" type="monotone" dataKey="orders" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#colorOrders)" name="Orders" />
                    <Area yAxisId="right" type="monotone" dataKey="spent" stroke="#22c55e" strokeWidth={3} fillOpacity={1} fill="url(#colorSpent)" name="Spent (₹)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <div className="card-label">🚴 Channel Distribution</div>
              <div className="chart-container-sm">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={channelData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={4} dataKey="value">
                      {channelData.map((d, i) => <Cell key={i} fill={d.color} />)}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #f0f0f0', fontSize: 13 }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 8 }}>
                {channelData.map(d => (
                  <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, fontWeight: 600 }}>
                    <div style={{ width: 10, height: 10, borderRadius: 3, background: d.color }} />
                    {d.name}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="two-col-grid">
            <div className="card">
              <div className="card-label">💪 Nutrition Overview</div>
              <div style={{ padding: '8px 0' }}>
                {[
                  { label: "Protein", value: nutrientMap.protein, color: "#ef4444" },
                  { label: "Carbs", value: nutrientMap.carbs, color: "#f59e0b" },
                  { label: "Fiber", value: nutrientMap.fiber, color: "#22c55e" },
                  { label: "Vitamins", value: nutrientMap.vitamins, color: "#8b5cf6" },
                ].map(n => (
                  <div key={n.label} className="nutrient-row">
                    <div className="nutrient-label">{n.label}</div>
                    <div className="nutrient-bar">
                      <div className="nutrient-fill" style={{ width: `${(n.value / maxNutrient) * 100}%`, background: n.color }} />
                    </div>
                    <div className="nutrient-value" style={{ color: n.color }}>{n.value}g</div>
                  </div>
                ))}
              </div>
              <div className="insight-card" style={{ marginTop: 16 }}>
                <div className="insight-title">🥗 Gym Nutrition</div>
                <div style={{ fontSize: 14, color: '#444', lineHeight: 1.6 }}>
                  {gymPercent > 40 ? `${gymPercent}% of your orders are gym-friendly! Great protein intake.` : `Only ${gymPercent}% gym-focused orders. Try adding more grilled chicken, salads, or protein-rich options.`}
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-label">🧠 Smart Insights</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {insights.map((ins, i) => (
                  <div key={i} className="insight-card">
                    <div style={{ fontSize: 18, marginBottom: 6 }}>{ins.icon}</div>
                    <div className="insight-title">{ins.title}</div>
                    <div className="insight-text">{ins.text}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {topCuisines.length > 0 && (
            <div className="card" style={{ marginTop: 20 }}>
              <div className="card-label">🏆 Top Cuisines This Month</div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topCuisines.slice(0, 6).map((c, i) => ({ name: c, value: Math.max(5, 10 - i * 1.5) }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#888' }} />
                    <YAxis tick={{ fontSize: 12, fill: '#888' }} />
                    <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #f0f0f0', fontSize: 13 }} />
                    <Bar dataKey="value" fill="#ff6b35" radius={[8, 8, 0, 0]} name="Score" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          <div className="card" style={{ marginTop: 20 }}>
            <div className="card-label">📋 Order Report</div>
            {history.length === 0 ? (
              <div className="empty">
                <div className="empty-icon">📝</div>
                <div className="empty-text">No orders recorded yet.<br />Start ordering to see your report!</div>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="history-table">
                  <thead>
                    <tr><th>Dish</th><th>Restaurant</th><th>Cuisine</th><th>Channel</th><th>Price</th><th>Rating</th><th>Health</th><th>Date</th></tr>
                  </thead>
                  <tbody>
                    {[...history].reverse().map((o, i) => (
                      <tr key={i}>
                        <td><strong>{o.dish}</strong></td>
                        <td style={{ color: "#555" }}>{o.restaurant}</td>
                        <td style={{ textTransform: 'capitalize', color: "#555" }}>{o.cuisine || "—"}</td>
                        <td><span className={`channel-badge ${o.channel}`}>{o.channel?.replace("_", " ")}</span></td>
                        <td>{o.price_inr ? `₹${o.price_inr}` : "—"}</td>
                        <td>{o.rating ? "⭐".repeat(o.rating) : "—"}</td>
                        <td>{isGymOrder(o.dish) ? "💪" : "🍽️"}</td>
                        <td style={{ color: "#888", fontSize: 12 }}>{o.timestamp?.slice(0, 10)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────────
export default function CravyoApp() {
  const [tab, setTab] = useState("analyze");
  const { toasts, toast } = useToast();
  const [apiOk, setApiOk] = useState(null);

  useEffect(() => {
    api("/health").then(() => setApiOk(true)).catch(() => setApiOk(false));
  }, []);

  const TABS = [
    { key: "analyze", label: "🔍 Analyze" },
    { key: "price", label: "💰 Prices" },
    { key: "memory", label: "🧠 Memory" },
    { key: "trends", label: "📊 Trends" },
    { key: "stats", label: "📈 Progress" },
  ];

  return (
    <div className="app-shell">
      <AnimatedBackground />
      <InjectCSS />
      <nav className="nav">
        <div className="logo">
          <span className="logo-text">Cravy<span>o</span></span>
        </div>
        <div className="nav-tabs">
          {TABS.map(t => (
            <button key={t.key} className={`nav-tab${tab === t.key ? " active" : ""}`} onClick={() => setTab(t.key)}>
              {t.label}
            </button>
          ))}
        </div>
        <div className="nav-status">
          <div className="status-dot" style={{ background: apiOk === null ? "#fbbf24" : apiOk ? "var(--green-light)" : "#ef4444" }} />
          {apiOk === null ? "Connecting..." : apiOk ? "Backend live" : "Backend offline"}
        </div>
      </nav>

      <main className="main">
        {tab === "analyze" && <AnalyzeTab toast={toast} />}
        {tab === "price" && <PriceCompareTab toast={toast} />}
        {tab === "memory" && <MemoryTab toast={toast} />}
        {tab === "trends" && <TrendsTab toast={toast} />}
        {tab === "stats" && <StatsTab toast={toast} />}
      </main>

      <Toasts toasts={toasts} />
    </div>
  );
}