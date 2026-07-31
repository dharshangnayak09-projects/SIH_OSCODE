import { useState, useEffect, useContext, createContext, useCallback, useRef } from "react";
import {
  Shield, LayoutDashboard, Activity, Search, RefreshCw, Bell,
  ChevronRight, Sun, Moon, ShieldCheck, ShieldAlert, Network,
  BarChart3, AlertTriangle, Settings, FileText, Cpu, Zap,
  TrendingUp, TrendingDown, CheckCircle, XCircle, Clock,
  Eye, Download, Filter, User, CreditCard, Send, ArrowRight,
  IndianRupee, Loader2, Radio, Lock, Unlock, Flag, Info, Menu, X,
} from "lucide-react";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from "recharts";

// ─── THEME CONTEXT ────────────────────────────────────────────────────────────
const ThemeCtx = createContext<{ isDark: boolean; toggle: () => void }>({ isDark: false, toggle: () => {} });
const useDark = () => useContext(ThemeCtx);

// ─── DATA ─────────────────────────────────────────────────────────────────────
const RECEIVERS = [
  { id: "r1", name: "Vikram Singh",   upi: "vsingh@ybl" },
  { id: "r2", name: "QuickMart",      upi: "quickmart@upi" },
  { id: "r3", name: "FoodHub",        upi: "foodhub@paytm" },
  { id: "r4", name: "TechStore",      upi: "techstore@hdfc" },
  { id: "r5", name: "Unknown Merch.", upi: "merch8821@upi" },
  { id: "r6", name: "Sanjay Mehta",   upi: "smehta@okaxis" },
];

const TRANSACTIONS = [
  { id: "TXN-847291", sender: "Rahul Sharma",  sUPI: "rahul@okaxis",   receiver: "QuickMart",       rUPI: "quickmart@upi",  amount: 4250,    time: "14:32:01", score: 92, status: "Blocked",  type: "Phishing" },
  { id: "TXN-847290", sender: "Priya Patel",   sUPI: "priya.p@ybl",    receiver: "FoodHub",         rUPI: "foodhub@paytm",  amount: 180,     time: "14:31:44", score: 8,  status: "Allowed",  type: "Normal" },
  { id: "TXN-847289", sender: "Amit Kumar",    sUPI: "amitk@okicici",  receiver: "TechStore",       rUPI: "techstore@hdfc", amount: 18500,   time: "14:31:22", score: 67, status: "Flagged",  type: "Velocity" },
  { id: "TXN-847288", sender: "Sunita Devi",   sUPI: "sunita@okaxis",  receiver: "GasStation",      rUPI: "gaspump@sbi",    amount: 1200,    time: "14:31:05", score: 6,  status: "Allowed",  type: "Normal" },
  { id: "TXN-847287", sender: "Vikram Singh",  sUPI: "vsingh@ybl",     receiver: "Unknown Merchant",rUPI: "merch8821@upi",  amount: 85000,   time: "14:30:48", score: 97, status: "Blocked",  type: "Mule Transfer" },
  { id: "TXN-847286", sender: "Deepa Nair",    sUPI: "deepan@paytm",   receiver: "BigBazaar",       rUPI: "bigbazaar@rbl",  amount: 3680,    time: "14:30:31", score: 11, status: "Allowed",  type: "Normal" },
  { id: "TXN-847285", sender: "Rajesh Gupta",  sUPI: "rgupta@okhdfc",  receiver: "P2P Transfer",    rUPI: "unknown@9872",   amount: 45000,   time: "14:30:14", score: 78, status: "Flagged",  type: "Amount Breach" },
  { id: "TXN-847284", sender: "Meena Kumari",  sUPI: "meena.k@sbi",    receiver: "AmazonPay",       rUPI: "amazon@apl",     amount: 999,     time: "14:29:57", score: 4,  status: "Allowed",  type: "Normal" },
  { id: "TXN-847283", sender: "Sanjay Mehta",  sUPI: "smehta@okaxis",  receiver: "Foreign IP Acc",  rUPI: "forex9912@upi",  amount: 120000,  time: "14:29:40", score: 99, status: "Blocked",  type: "Cross-Border Mule" },
  { id: "TXN-847282", sender: "Kavitha Reddy", sUPI: "kavitha@ybl",    receiver: "Swiggy",          rUPI: "swiggy@icici",   amount: 450,     time: "14:29:23", score: 7,  status: "Allowed",  type: "Normal" },
];

const ALERTS = [
  { id: "ALT-0091", type: "High-Value Anomaly",  amount: 85000,  sender: "Vikram Singh",  sUPI: "vsingh@ybl",    receiver: "Unknown Merchant", rUPI: "merch8821@upi",  score: 97, time: "14:30:48", action: "Blocked" },
  { id: "ALT-0090", type: "Cross-Border Mule",   amount: 120000, sender: "Sanjay Mehta",  sUPI: "smehta@okaxis", receiver: "Foreign IP Acc",   rUPI: "forex9912@upi",  score: 99, time: "14:29:40", action: "Blocked" },
  { id: "ALT-0089", type: "Phishing Pattern",    amount: 4250,   sender: "Rahul Sharma",  sUPI: "rahul@okaxis",  receiver: "QuickMart",        rUPI: "quickmart@upi",  score: 92, time: "14:32:01", action: "Blocked" },
  { id: "ALT-0088", type: "Velocity Breach",     amount: 45000,  sender: "Rajesh Gupta",  sUPI: "rgupta@okhdfc", receiver: "P2P Transfer",     rUPI: "unknown@9872",   score: 78, time: "14:30:14", action: "Flagged" },
  { id: "ALT-0087", type: "Unusual Behaviour",   amount: 18500,  sender: "Amit Kumar",    sUPI: "amitk@okicici", receiver: "TechStore",        rUPI: "techstore@hdfc", score: 67, time: "14:31:22", action: "Flagged" },
];

const fraudTrendData = [
  { time: "00:00", fraud: 12, safe: 340 }, { time: "03:00", fraud: 6,  safe: 180 },
  { time: "06:00", fraud: 18, safe: 420 }, { time: "09:00", fraud: 42, safe: 1240 },
  { time: "12:00", fraud: 51, safe: 1560 },{ time: "15:00", fraud: 38, safe: 1200 },
  { time: "18:00", fraud: 56, safe: 980 }, { time: "21:00", fraud: 22, safe: 520 },
];
const hourlyData = [
  { h: "6AM",  v: 420 },{ h: "8AM",  v: 890 },{ h: "10AM", v: 1240 },
  { h: "12PM", v: 1560},{ h: "2PM",  v: 1380},{ h: "4PM",  v: 1200 },
  { h: "6PM",  v: 980 },{ h: "8PM",  v: 760 },{ h: "10PM", v: 520 },
];
const fraudTypesData = [
  { name: "Phishing",         value: 34, fill: "#dc2626" },
  { name: "Acct. Takeover",  value: 28, fill: "#ea580c" },
  { name: "Mule Transfer",   value: 22, fill: "#d97706" },
  { name: "SIM Swap",        value: 10, fill: "#7c3aed" },
  { name: "Others",          value: 6,  fill: "#64748b" },
];
const highRiskReceivers = [
  { name: "merch8821@upi", count: 14, amount: 340000 },
  { name: "forex9912@upi", count: 9,  amount: 890000 },
  { name: "unknown@9872",  count: 7,  amount: 210000 },
  { name: "quickmart@upi", count: 5,  amount: 85000  },
  { name: "p2p@anon",      count: 4,  amount: 120000 },
];

const MULE_NODES = [
  { id: "M1", x: 220, y: 150, label: "9912@upi",   risk: 99, type: "mule" },
  { id: "M2", x: 120, y: 80,  label: "vsingh@ybl", risk: 97, type: "mule" },
  { id: "M3", x: 320, y: 90,  label: "forex9912",  risk: 95, type: "mule" },
  { id: "M4", x: 80,  y: 200, label: "smehta@ok",  risk: 91, type: "mule" },
  { id: "S1", x: 360, y: 210, label: "rgupta@hd",  risk: 78, type: "suspect" },
  { id: "S2", x: 250, y: 250, label: "merch8821",  risk: 85, type: "suspect" },
  { id: "N1", x: 50,  y: 120, label: "rahul@ok",   risk: 22, type: "normal" },
  { id: "N2", x: 400, y: 130, label: "priya.p@y",  risk: 12, type: "normal" },
];
const MULE_EDGES = [
  ["M1","M2"],["M1","M3"],["M1","M4"],["M2","S1"],["M3","S2"],
  ["M4","S2"],["N1","M2"],["N2","M3"],["S1","M1"],["S2","M1"],
];

// ─── SHARED HELPERS ───────────────────────────────────────────────────────────
function fmtAmount(n: number) {
  return "₹" + n.toLocaleString("en-IN");
}

type TxStatus = "Allowed" | "Flagged" | "Blocked";

function StatusBadge({ status }: { status: TxStatus | string }) {
  const cfg: Record<string, string> = {
    Allowed: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800",
    Flagged: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800",
    Blocked: "bg-red-50 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800",
  };
  const icons: Record<string, JSX.Element> = {
    Allowed: <CheckCircle size={10} />,
    Flagged: <Clock size={10} />,
    Blocked: <XCircle size={10} />,
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${cfg[status] || ""}`}>
      {icons[status]} {status}
    </span>
  );
}

function RiskBar({ score }: { score: number }) {
  const color = score >= 75 ? "#dc2626" : score >= 45 ? "#f59e0b" : "#16a34a";
  return (
    <div className="flex items-center gap-2">
      <div className="w-14 h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
        <div style={{ width: `${score}%`, background: color }} className="h-full rounded-full" />
      </div>
      <span className="text-[11px] font-mono font-bold" style={{ color }}>{score}</span>
    </div>
  );
}

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`bg-white dark:bg-[#1e293b] border border-slate-200/60 dark:border-white/[0.06] shadow-sm rounded-2xl transition-colors duration-200 ${className}`}>
      {children}
    </div>
  );
}

function useChartTheme() {
  const { isDark } = useDark();
  return {
    grid: isDark ? "#1e293b" : "#f1f5f9",
    tick: isDark ? "#64748b" : "#94a3b8",
    tooltip: {
      fontSize: 11, borderRadius: 8,
      border: isDark ? "1px solid #334155" : "1px solid #e2e8f0",
      background: isDark ? "#1e293b" : "#fff",
      color: isDark ? "#f8fafc" : "#0f172a",
    },
    blue: isDark ? "#3b82f6" : "#2563eb",
  };
}

function ScoreGauge({ score, size = 120 }: { score: number; size?: number }) {
  const r = (size / 2) * 0.75;
  const cx = size / 2;
  const cy = size / 2;
  const arc = Math.PI * r;
  const offset = arc * (1 - score / 100);
  const color = score >= 75 ? "#dc2626" : score >= 45 ? "#f59e0b" : "#16a34a";
  const { isDark } = useDark();
  return (
    <svg width={size} height={size * 0.6} viewBox={`0 0 ${size} ${size * 0.6}`}>
      <path
        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
        fill="none" stroke={isDark ? "#1e3a5f" : "#f1f5f9"} strokeWidth={size * 0.08} strokeLinecap="round"
      />
      <path
        d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
        fill="none" stroke={color} strokeWidth={size * 0.08} strokeLinecap="round"
        strokeDasharray={arc} strokeDashoffset={offset}
      />
      <text x={cx} y={cy - 4} textAnchor="middle" fill={color}
        style={{ fontSize: size * 0.2, fontWeight: 800, fontFamily: "Inter" }}>{score}</text>
      <text x={cx} y={cy + 12} textAnchor="middle" fill={isDark ? "#64748b" : "#94a3b8"}
        style={{ fontSize: size * 0.1, fontFamily: "Inter" }}>FRAUD SCORE</text>
    </svg>
  );
}

// ─── SIDEBAR ──────────────────────────────────────────────────────────────────
const NAV = [
  { id: "dashboard",  label: "Dashboard",            icon: LayoutDashboard, badge: null },
  { id: "payment",    label: "UPI Payment",           icon: Send,            badge: null },
  { id: "live",       label: "Live Transactions",     icon: Activity,        badge: "LIVE" },
  { id: "analysis",   label: "Transaction Analysis",  icon: Eye,             badge: null },
  { id: "mule",       label: "Mule Detection",        icon: Network,         badge: null },
  { id: "analytics",  label: "Analytics",             icon: BarChart3,       badge: null },
  { id: "alerts",     label: "Fraud Alerts",          icon: AlertTriangle,   badge: "5" },
  { id: "settings",   label: "Settings",              icon: Settings,        badge: null },
];

function Sidebar({ active, setActive, mobileOpen, setMobileOpen }: {
  active: string;
  setActive: (id: string) => void;
  mobileOpen: boolean;
  setMobileOpen: (v: boolean) => void;
}) {
  const handleNav = (id: string) => { setActive(id); setMobileOpen(false); };

  const sidebarContent = (
    <aside className="w-60 shrink-0 bg-[#0c1829] flex flex-col h-full transition-colors duration-300">
      <div className="px-5 py-5 border-b border-white/[0.08]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-600/40">
            <Shield size={17} className="text-white" />
          </div>
          <div className="flex-1">
            <p className="text-white font-bold text-[15px] leading-none tracking-tight">SentinelAI</p>
            <p className="text-blue-400/60 text-[9px] mt-0.5 font-semibold tracking-widest uppercase">UPI Fraud Detection</p>
          </div>
          <button onClick={() => setMobileOpen(false)} className="md:hidden p-1 rounded-lg text-slate-500 hover:text-white transition-colors">
            <X size={16} />
          </button>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <p className="px-2 pb-2 pt-1 text-[9px] font-bold text-slate-600 tracking-widest uppercase">Navigation</p>
        {NAV.map(({ id, label, icon: Icon, badge }) => (
          <button key={id} onClick={() => handleNav(id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-[13px] font-medium transition-all duration-150 group ${
              active === id
                ? "bg-blue-600 text-white shadow-lg shadow-blue-600/25"
                : "text-slate-400 hover:text-white hover:bg-white/[0.07]"
            }`}>
            <Icon size={15} className={active === id ? "text-white" : "text-slate-500 group-hover:text-blue-300"} />
            <span className="flex-1 text-left">{label}</span>
            {badge === "LIVE" && (
              <span className="flex items-center gap-1 text-[9px] font-bold text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />LIVE
              </span>
            )}
            {badge && badge !== "LIVE" && (
              <span className="bg-red-500 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full leading-none">{badge}</span>
            )}
          </button>
        ))}
      </nav>

      <div className="mx-3 mb-4 p-3 rounded-xl bg-white/[0.04] border border-white/[0.07]">
        <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-2">System</p>
        {[["AI Engine","online"],["UPI Gateway","online"],["Rule Engine","online"]].map(([l,s]) => (
          <div key={l} className="flex items-center justify-between py-0.5">
            <span className="text-[11px] text-slate-500">{l}</span>
            <div className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span className="text-[10px] font-semibold text-emerald-400 capitalize">{s}</span>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop sidebar — always visible */}
      <div className="hidden md:flex">{sidebarContent}</div>

      {/* Mobile overlay drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="relative z-10 flex">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}

// ─── TOP NAV ──────────────────────────────────────────────────────────────────
function TopNav({ page, onRefresh, onMenuToggle }: { page: string; onRefresh: () => void; onMenuToggle: () => void }) {
  const { isDark, toggle } = useDark();
  const [spin, setSpin] = useState(false);
  const refresh = () => { setSpin(true); onRefresh(); setTimeout(() => setSpin(false), 800); };
  const titles: Record<string,string> = {
    dashboard: "Overview Dashboard", payment: "UPI Payment Simulator",
    live: "Live Transactions", analysis: "Transaction Analysis",
    mule: "Mule Detection", analytics: "Analytics",
    alerts: "Fraud Alerts", settings: "Settings",
  };
  return (
    <header className="h-14 bg-white dark:bg-[#1e293b] border-b border-slate-200 dark:border-white/[0.07] flex items-center px-4 md:px-6 gap-3 shrink-0 transition-colors duration-200">
      {/* Hamburger — mobile only */}
      <button onClick={onMenuToggle}
        className="md:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors shrink-0">
        <Menu size={18} />
      </button>

      <div className="flex items-center gap-1.5 text-sm min-w-0">
        <span className="text-slate-400 dark:text-slate-500 text-xs hidden sm:inline">SentinelAI</span>
        <ChevronRight size={12} className="text-slate-300 dark:text-slate-600 hidden sm:inline" />
        <span className="font-semibold text-slate-700 dark:text-slate-100 truncate text-xs sm:text-sm">{titles[page]}</span>
      </div>

      {/* Search — hidden on mobile, visible on sm+ */}
      <div className="hidden sm:flex flex-1 max-w-xs ml-2">
        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-white/[0.07] rounded-lg w-full">
          <Search size={13} className="text-slate-400 shrink-0" />
          <input placeholder="Search transactions, UPI IDs..."
            className="bg-transparent text-xs text-slate-600 dark:text-slate-300 placeholder-slate-400 dark:placeholder-slate-600 outline-none flex-1" />
        </div>
      </div>

      <div className="ml-auto flex items-center gap-1.5">
        {/* Search icon on mobile */}
        <button className="sm:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors">
          <Search size={15} />
        </button>
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 bg-emerald-50 dark:bg-emerald-900/25 border border-emerald-200 dark:border-emerald-800 rounded-lg">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-[11px] font-semibold text-emerald-700 dark:text-emerald-400">Live</span>
        </div>
        <button onClick={refresh} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors">
          <RefreshCw size={15} className={spin ? "animate-spin" : ""} />
        </button>
        <button className="relative p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors">
          <Bell size={15} />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-red-500" />
        </button>
        <button onClick={toggle}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-white/[0.08] hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
          {isDark
            ? <Sun size={14} className="text-amber-400" />
            : <Moon size={14} className="text-slate-500" />}
          <span className="text-[11px] font-medium text-slate-600 dark:text-slate-300 hidden lg:block">{isDark ? "Light" : "Dark"}</span>
        </button>
        <div className="flex items-center gap-2 pl-3 border-l border-slate-200 dark:border-white/[0.07] ml-1">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-[11px] font-bold">AK</div>
          <div className="hidden lg:block">
            <p className="text-[11px] font-semibold text-slate-700 dark:text-slate-100 leading-none">Arjun Kumar</p>
            <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">Analyst</p>
          </div>
        </div>
      </div>
    </header>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 1 — DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════════
function DashboardPage() {
  const ct = useChartTheme();
  const { isDark } = useDark();
  const blocked = TRANSACTIONS.filter(t => t.status === "Blocked").length;
  const flagged = TRANSACTIONS.filter(t => t.status === "Flagged").length;
  const safe    = TRANSACTIONS.filter(t => t.status === "Allowed").length;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Transactions",   value: "2,84,391", sub: "Last 24h",       icon: Activity,    color: "bg-blue-600",    change: "+12.4%", up: true  },
          { label: "Fraud Detected",        value: "1,247",    sub: "₹3.8Cr blocked", icon: ShieldAlert, color: "bg-red-500",     change: "+3.2%",  up: false },
          { label: "Safe Transactions",     value: "2,83,144", sub: "99.56% of total",icon: ShieldCheck, color: "bg-emerald-500", change: "+12.1%", up: true  },
          { label: "Avg Detection Latency", value: "~1 ms",    sub: "Real-time AI",   icon: Zap,         color: "bg-violet-600",  change: "-0.2ms", up: true  },
        ].map(({ label, value, sub, icon: Icon, color, change, up }) => (
          <Card key={label} className="p-5">
            <div className="flex items-start justify-between mb-4">
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
                <Icon size={18} className="text-white" />
              </div>
              <span className={`flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full ${up ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" : "bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400"}`}>
                {up ? <TrendingUp size={10}/> : <TrendingDown size={10}/>} {change}
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-800 dark:text-slate-100 leading-none">{value}</p>
            <p className="text-[11px] text-slate-400 dark:text-slate-500 font-mono mt-0.5">{sub}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{label}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Card className="xl:col-span-2 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-white/[0.06]">
            <div>
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">Recent Transactions</h3>
              <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">Live UPI feed</p>
            </div>
            <span className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />STREAMING
            </span>
          </div>
          {/* Desktop table */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-xs">
              <thead><tr className="bg-slate-50/80 dark:bg-slate-800/50">
                {["Txn ID","Sender","Receiver","Amount","Score","Status","Time"].map(h => (
                  <th key={h} className="text-left px-4 py-2.5 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr></thead>
              <tbody className="divide-y divide-slate-50 dark:divide-white/[0.04]">
                {TRANSACTIONS.slice(0,8).map(t => (
                  <tr key={t.id} className="hover:bg-blue-50/20 dark:hover:bg-blue-900/10 transition-colors">
                    <td className="px-4 py-2.5"><span className="font-mono text-blue-600 dark:text-blue-400 font-semibold text-[11px]">{t.id}</span></td>
                    <td className="px-4 py-2.5">
                      <p className="font-semibold text-slate-700 dark:text-slate-200 text-[11px]">{t.sender}</p>
                      <p className="text-[10px] text-slate-400 dark:text-slate-500">{t.sUPI}</p>
                    </td>
                    <td className="px-4 py-2.5">
                      <p className="font-semibold text-slate-700 dark:text-slate-200 text-[11px]">{t.receiver}</p>
                      <p className="text-[10px] text-slate-400 dark:text-slate-500">{t.rUPI}</p>
                    </td>
                    <td className="px-4 py-2.5 font-bold text-slate-800 dark:text-slate-100">{fmtAmount(t.amount)}</td>
                    <td className="px-4 py-2.5"><RiskBar score={t.score} /></td>
                    <td className="px-4 py-2.5"><StatusBadge status={t.status} /></td>
                    <td className="px-4 py-2.5 font-mono text-slate-400 dark:text-slate-500 text-[11px]">{t.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile transaction cards */}
          <div className="md:hidden divide-y divide-slate-100 dark:divide-white/[0.05]">
            {TRANSACTIONS.slice(0,8).map(t => (
              <div key={t.id} className="px-4 py-3.5">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <span className="font-mono text-blue-600 dark:text-blue-400 font-semibold text-[11px]">{t.id}</span>
                    <p className="text-xs font-semibold text-slate-700 dark:text-slate-200 mt-0.5">{t.sender} → {t.receiver}</p>
                    <p className="text-[10px] text-slate-400 dark:text-slate-500 font-mono mt-0.5">{t.sUPI}</p>
                  </div>
                  <StatusBadge status={t.status} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-800 dark:text-slate-100">{fmtAmount(t.amount)}</span>
                  <div className="flex items-center gap-3">
                    <RiskBar score={t.score} />
                    <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500">{t.time}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <div className="space-y-4">
          <Card className="p-5">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-3">Detection Summary</h3>
            <div className="space-y-2.5">
              {[
                { label: "Blocked",  val: blocked, color: "bg-red-500",     pct: (blocked/TRANSACTIONS.length)*100 },
                { label: "Flagged",  val: flagged, color: "bg-amber-400",   pct: (flagged/TRANSACTIONS.length)*100 },
                { label: "Allowed",  val: safe,    color: "bg-emerald-500", pct: (safe/TRANSACTIONS.length)*100 },
              ].map(({ label, val, color, pct }) => (
                <div key={label}>
                  <div className="flex justify-between mb-1">
                    <span className="text-xs text-slate-500 dark:text-slate-400">{label}</span>
                    <span className="text-xs font-bold text-slate-700 dark:text-slate-200">{val} <span className="font-normal text-slate-400">({pct.toFixed(0)}%)</span></span>
                  </div>
                  <div className="h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-3">Fraud Types</h3>
            <PieChart width={180} height={130}>
              <Pie key="dash-pie" data={fraudTypesData} cx={90} cy={65} innerRadius={38} outerRadius={58} paddingAngle={3} dataKey="value">
                {fraudTypesData.map((e,i) => <Cell key={`dash-pie-cell-${i}`} fill={e.fill} />)}
              </Pie>
              <Tooltip key="dash-pie-tt" contentStyle={ct.tooltip} />
            </PieChart>
            <div className="space-y-1 mt-1">
              {fraudTypesData.map(({ name, value, fill }) => (
                <div key={name} className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: fill }} />
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 flex-1">{name}</span>
                  <span className="text-[10px] font-bold text-slate-700 dark:text-slate-200">{value}%</span>
                </div>
              ))}
            </div>
          </Card>

          <Card className="p-5">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-3">Fraud Trend</h3>
            <ResponsiveContainer width="100%" height={100}>
              <AreaChart data={fraudTrendData} margin={{ top: 0, right: 0, left: -30, bottom: 0 }}>
                <XAxis key="dash-trend-x" dataKey="time" tick={{ fontSize: 9, fill: ct.tick }} tickLine={false} axisLine={false} />
                <YAxis key="dash-trend-y" tick={{ fontSize: 9, fill: ct.tick }} tickLine={false} axisLine={false} />
                <Tooltip key="dash-trend-tt" contentStyle={ct.tooltip} />
                <Area key="dash-trend-area" type="monotone" dataKey="fraud" stroke="#dc2626" strokeWidth={2} fill="#dc2626" fillOpacity={isDark ? 0.12 : 0.08} name="Fraud" />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 2 — UPI PAYMENT SIMULATOR
// ═══════════════════════════════════════════════════════════════════════════════
type PayState = "idle" | "scanning" | "result";
type PayResult = { status: TxStatus; score: number; latency: string; txnId: string } | null;

function PaymentPage({ onGoAnalysis }: { onGoAnalysis: (txn: typeof TRANSACTIONS[0]) => void }) {
  const [sender] = useState("Arjun Kumar  •  arjun.k@okaxis  •  HDFC xxxx-4821");
  const [receiver, setReceiver] = useState("");
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [payState, setPayState] = useState<PayState>("idle");
  const [result, setResult] = useState<PayResult>(null);
  const [scanStep, setScanStep] = useState(0);
  const [timestamp] = useState(new Date().toLocaleString("en-IN"));

  const scanSteps = [
    "Connecting to fraud detection engine...",
    "Evaluating rule engine conditions...",
    "Running AI fraud prediction model...",
    "Checking mule network connections...",
    "Generating final decision...",
  ];

  const handlePay = () => {
    if (!receiver || !amount) return;
    setPayState("scanning");
    setScanStep(0);
    let step = 0;
    const iv = setInterval(() => {
      step++;
      setScanStep(step);
      if (step >= scanSteps.length - 1) {
        clearInterval(iv);
        setTimeout(() => {
          const amt = parseFloat(amount);
          const score = amt > 50000 ? 94 : amt > 10000 ? 67 : 12;
          const status: TxStatus = score >= 75 ? "Blocked" : score >= 45 ? "Flagged" : "Allowed";
          const txnId = "TXN-" + Math.floor(800000 + Math.random() * 99999);
          setResult({ status, score, latency: "0.9ms", txnId });
          setPayState("result");
        }, 600);
      }
    }, 650);
  };

  const reset = () => { setPayState("idle"); setResult(null); setAmount(""); setNote(""); setReceiver(""); };

  if (payState === "scanning") {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <Card className="w-full max-w-md p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center mx-auto mb-5">
            <Loader2 size={32} className="text-blue-600 dark:text-blue-400 animate-spin" />
          </div>
          <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-1">Analysing Transaction</h3>
          <p className="text-sm text-slate-400 dark:text-slate-500 mb-6">Scanning transaction for fraud...</p>
          <div className="space-y-2.5 text-left">
            {scanSteps.map((step, i) => (
              <div key={i} className={`flex items-center gap-3 transition-all duration-300 ${i <= scanStep ? "opacity-100" : "opacity-25"}`}>
                <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
                  i < scanStep ? "bg-emerald-500" : i === scanStep ? "bg-blue-600 animate-pulse" : "bg-slate-200 dark:bg-slate-700"
                }`}>
                  {i < scanStep
                    ? <CheckCircle size={12} className="text-white" />
                    : <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                </div>
                <span className={`text-xs font-medium ${i <= scanStep ? "text-slate-700 dark:text-slate-200" : "text-slate-400 dark:text-slate-600"}`}>{step}</span>
              </div>
            ))}
          </div>
          <div className="mt-6 h-1 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
            <div className="h-full bg-blue-600 rounded-full transition-all duration-500"
              style={{ width: `${((scanStep + 1) / scanSteps.length) * 100}%` }} />
          </div>
          <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-2 font-mono">avg latency ~1ms</p>
        </Card>
      </div>
    );
  }

  if (payState === "result" && result) {
    const cfg = {
      Allowed: { bg: "bg-emerald-50 dark:bg-emerald-900/20", border: "border-emerald-300 dark:border-emerald-700", icon: <CheckCircle size={32} className="text-emerald-600 dark:text-emerald-400" />, text: "text-emerald-700 dark:text-emerald-300", label: "Transaction Approved", sub: "No fraud indicators detected. Payment processed." },
      Flagged: { bg: "bg-amber-50 dark:bg-amber-900/20",     border: "border-amber-300 dark:border-amber-700",     icon: <Flag size={32} className="text-amber-600 dark:text-amber-400" />,          text: "text-amber-700 dark:text-amber-300",   label: "Flagged for Review",    sub: "Suspicious activity detected. Pending manual review." },
      Blocked: { bg: "bg-red-50 dark:bg-red-900/20",         border: "border-red-300 dark:border-red-700",         icon: <Lock size={32} className="text-red-600 dark:text-red-400" />,              text: "text-red-700 dark:text-red-300",       label: "Transaction Blocked",   sub: "High fraud risk. Payment has been blocked automatically." },
    }[result.status];

    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <Card className="w-full max-w-md p-8">
          <div className={`rounded-2xl border-2 p-6 text-center mb-5 ${cfg.bg} ${cfg.border}`}>
            <div className="flex justify-center mb-3">{cfg.icon}</div>
            <p className={`text-xl font-black ${cfg.text}`}>{result.status.toUpperCase()}</p>
            <p className={`text-sm font-semibold mt-0.5 ${cfg.text}`}>{cfg.label}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{cfg.sub}</p>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-5">
            {[
              { label: "Transaction ID", value: result.txnId },
              { label: "Amount",         value: fmtAmount(parseFloat(amount)) },
              { label: "Fraud Score",    value: `${result.score}/100` },
              { label: "Latency",        value: result.latency },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-50 dark:bg-slate-800/60 rounded-xl p-3">
                <p className="text-[10px] text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-0.5">{label}</p>
                <p className="text-sm font-bold text-slate-800 dark:text-slate-100">{value}</p>
              </div>
            ))}
          </div>

          <p className="text-[11px] text-center text-slate-400 dark:text-slate-500 mb-4">
            Decision generated using <span className="font-semibold text-blue-600 dark:text-blue-400">Rule Engine + AI Fraud Model + Mule Detection</span>
          </p>

          <div className="flex gap-3">
            <button onClick={reset}
              className="flex-1 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 text-sm font-semibold hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors">
              New Payment
            </button>
            <button
              onClick={() => {
                const synth = { ...TRANSACTIONS[0], id: result.txnId, amount: parseFloat(amount), status: result.status, score: result.score };
                onGoAnalysis(synth as any);
              }}
              className="flex-1 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold transition-colors">
              View Analysis
            </button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex items-start justify-center gap-5 pb-20 md:pb-0">
      <Card className="w-full max-w-md p-6">
        <div className="flex items-center gap-2 mb-6">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
            <Send size={15} className="text-white" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-800 dark:text-slate-100">UPI Payment</h2>
            <p className="text-[11px] text-slate-400 dark:text-slate-500">Protected by SentinelAI fraud detection</p>
          </div>
        </div>

        {/* Sender */}
        <div className="mb-4">
          <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5 block">From</label>
          <div className="flex items-center gap-3 p-3.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-white/[0.07] rounded-xl">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shrink-0">AK</div>
            <div>
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">Arjun Kumar</p>
              <p className="text-[11px] text-slate-400 dark:text-slate-500 font-mono">arjun.k@okaxis  •  HDFC xxxx-4821</p>
            </div>
          </div>
        </div>

        {/* Receiver */}
        <div className="mb-4">
          <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5 block">To</label>
          <select value={receiver} onChange={e => setReceiver(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/[0.07] rounded-xl text-sm text-slate-700 dark:text-slate-200 outline-none focus:border-blue-400 dark:focus:border-blue-500 transition-colors">
            <option value="">Select recipient...</option>
            {RECEIVERS.map(r => <option key={r.id} value={r.upi}>{r.name} ({r.upi})</option>)}
          </select>
        </div>

        {/* Amount */}
        <div className="mb-4">
          <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5 block">Amount</label>
          <div className="relative">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 font-semibold text-sm">₹</span>
            <input type="number" value={amount} onChange={e => setAmount(e.target.value)}
              placeholder="0.00"
              className="w-full pl-8 pr-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/[0.07] rounded-xl text-sm text-slate-700 dark:text-slate-200 outline-none focus:border-blue-400 dark:focus:border-blue-500 transition-colors" />
          </div>
          <div className="flex gap-2 mt-2">
            {["500","1000","5000","10000"].map(v => (
              <button key={v} onClick={() => setAmount(v)}
                className="flex-1 py-1 text-[11px] font-semibold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/25 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors">
                ₹{v}
              </button>
            ))}
          </div>
        </div>

        {/* Note */}
        <div className="mb-5">
          <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5 block">Note (optional)</label>
          <input type="text" value={note} onChange={e => setNote(e.target.value)}
            placeholder="Add a note..."
            className="w-full px-3.5 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/[0.07] rounded-xl text-sm text-slate-700 dark:text-slate-200 outline-none focus:border-blue-400 dark:focus:border-blue-500 transition-colors" />
        </div>

        {/* Desktop Pay button */}
        <button onClick={handlePay} disabled={!receiver || !amount}
          className="hidden md:flex w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-sm transition-all items-center justify-center gap-2 shadow-lg shadow-blue-600/25">
          <Shield size={16} /> Pay Securely with SentinelAI
        </button>

        {/* Mobile sticky Pay button */}
        <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 p-4 bg-white/95 dark:bg-[#1e293b]/95 backdrop-blur border-t border-slate-200 dark:border-white/[0.07]">
          <button onClick={handlePay} disabled={!receiver || !amount}
            className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-sm transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-600/25">
            <Shield size={16} /> Pay Securely with SentinelAI
          </button>
        </div>

        <p className="text-[10px] text-center text-slate-400 dark:text-slate-500 mt-3 font-mono">{timestamp}</p>

        <div className="mt-4 flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl">
          <Info size={13} className="text-blue-600 dark:text-blue-400 shrink-0" />
          <p className="text-[11px] text-blue-700 dark:text-blue-300">
            Every payment is scanned in <span className="font-bold">~1ms</span> using AI + Rule Engine + Mule Detection before processing.
          </p>
        </div>
      </Card>

      {/* How it works panel */}
      <div className="hidden lg:block w-72 space-y-3">
        <Card className="p-4">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-3">How SentinelAI Works</h3>
          <div className="space-y-3">
            {[
              { step: "1", title: "Rule Engine",    desc: "Checks velocity, limits, and thresholds in real time.", color: "bg-blue-600" },
              { step: "2", title: "AI Model",       desc: "XGBoost + LSTM ensemble predicts fraud probability.",   color: "bg-violet-600" },
              { step: "3", title: "Mule Detection", desc: "GNN graph analysis detects linked mule accounts.",      color: "bg-teal-600" },
              { step: "4", title: "Final Decision", desc: "Aggregated verdict: Allow, Flag, or Block.",            color: "bg-slate-700 dark:bg-slate-600" },
            ].map(({ step, title, desc, color }) => (
              <div key={step} className="flex items-start gap-3">
                <div className={`w-6 h-6 rounded-lg ${color} text-white text-[11px] font-bold flex items-center justify-center shrink-0 mt-0.5`}>{step}</div>
                <div>
                  <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">{title}</p>
                  <p className="text-[11px] text-slate-400 dark:text-slate-500 leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
        <Card className="p-4">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-2">Risk Thresholds</h3>
          {[
            { label: "Allowed",  range: "Score 0–44",  color: "bg-emerald-500" },
            { label: "Flagged",  range: "Score 45–74", color: "bg-amber-400" },
            { label: "Blocked",  range: "Score 75–100",color: "bg-red-500" },
          ].map(({ label, range, color }) => (
            <div key={label} className="flex items-center justify-between py-1.5 border-b border-slate-100 dark:border-white/[0.05] last:border-0">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${color}`} />
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">{label}</span>
              </div>
              <span className="text-[11px] font-mono text-slate-400 dark:text-slate-500">{range}</span>
            </div>
          ))}
        </Card>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 3 — LIVE TRANSACTIONS
// ═══════════════════════════════════════════════════════════════════════════════
function LivePage({ onSelect }: { onSelect: (t: typeof TRANSACTIONS[0]) => void }) {
  const [filter, setFilter] = useState("All");
  const [tick, setTick] = useState(0);
  useEffect(() => { const iv = setInterval(() => setTick(v => v + 1), 3000); return () => clearInterval(iv); }, []);
  const filtered = filter === "All" ? TRANSACTIONS : TRANSACTIONS.filter(t => t.status === filter);

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-base md:text-lg font-bold text-slate-800 dark:text-slate-100">Live Transaction Feed</h2>
          <p className="text-xs text-slate-400 dark:text-slate-500 hidden sm:block">Click any row to open Transaction Analysis</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="flex items-center gap-1.5 bg-emerald-50 dark:bg-emerald-900/25 border border-emerald-200 dark:border-emerald-800 px-2 md:px-2.5 py-1.5 rounded-lg text-[11px] font-semibold text-emerald-700 dark:text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="hidden sm:inline">{284391 + tick} processed</span>
            <span className="sm:hidden">LIVE</span>
          </span>
          <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-white/[0.08] text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors">
            <Download size={12} /><span className="hidden sm:inline">Export</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 md:gap-3">
        {[
          { label: "TPS", value: "847",  cls: "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/25 border-blue-200 dark:border-blue-800", icon: Zap },
          { label: "Fraud Rate", value: "0.44%", cls: "text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/25 border-red-200 dark:border-red-800", icon: AlertTriangle },
          { label: "Avg Latency", value: "~1ms", cls: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/25 border-emerald-200 dark:border-emerald-800", icon: Activity },
        ].map(({ label, value, cls, icon: Icon }) => (
          <div key={label} className={`flex items-center gap-2 md:gap-3 px-3 md:px-4 py-3 rounded-xl border ${cls}`}>
            <Icon size={14} className="shrink-0" />
            <div className="min-w-0">
              <p className="text-[10px] md:text-[11px] text-slate-500 dark:text-slate-400 truncate">{label}</p>
              <p className="font-bold text-slate-800 dark:text-slate-100 text-sm">{value}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
        {["All","Allowed","Flagged","Blocked"].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`shrink-0 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-colors ${
              filter === f ? "bg-blue-600 text-white" : "bg-white dark:bg-slate-800 border border-slate-200 dark:border-white/[0.08] text-slate-500 dark:text-slate-400 hover:border-blue-300 hover:text-blue-600"
            }`}>
            {f}{f !== "All" && ` (${TRANSACTIONS.filter(t => t.status === f).length})`}
          </button>
        ))}
      </div>

      <Card className="overflow-hidden">
        {/* Desktop table */}
        <div className="hidden md:block">
          <table className="w-full text-xs">
            <thead><tr className="bg-slate-50/80 dark:bg-slate-800/50">
              {["Txn ID","Sender","Receiver","Amount","Fraud Score","Status","Timestamp",""].map(h => (
                <th key={h} className="text-left px-4 py-3 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr></thead>
            <tbody className="divide-y divide-slate-50 dark:divide-white/[0.04]">
              {filtered.map(t => (
                <tr key={t.id}
                  onClick={() => onSelect(t)}
                  className="hover:bg-blue-50/30 dark:hover:bg-blue-900/10 cursor-pointer transition-colors group">
                  <td className="px-4 py-3"><span className="font-mono font-semibold text-blue-600 dark:text-blue-400">{t.id}</span></td>
                  <td className="px-4 py-3">
                    <p className="font-semibold text-slate-700 dark:text-slate-200">{t.sender}</p>
                    <p className="text-[10px] text-slate-400 dark:text-slate-500">{t.sUPI}</p>
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-semibold text-slate-700 dark:text-slate-200">{t.receiver}</p>
                    <p className="text-[10px] text-slate-400 dark:text-slate-500">{t.rUPI}</p>
                  </td>
                  <td className="px-4 py-3 font-bold text-slate-800 dark:text-slate-100">{fmtAmount(t.amount)}</td>
                  <td className="px-4 py-3"><RiskBar score={t.score} /></td>
                  <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                  <td className="px-4 py-3 font-mono text-slate-500 dark:text-slate-400 text-[11px]">{t.time}</td>
                  <td className="px-4 py-3">
                    <span className="text-[10px] font-semibold text-blue-600 dark:text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">Analyse →</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Mobile transaction cards */}
        <div className="md:hidden divide-y divide-slate-100 dark:divide-white/[0.05]">
          {filtered.map(t => (
            <button key={t.id} onClick={() => onSelect(t)}
              className="w-full text-left px-4 py-3.5 hover:bg-blue-50/30 dark:hover:bg-blue-900/10 transition-colors active:bg-blue-50/50 dark:active:bg-blue-900/20">
              <div className="flex items-start justify-between mb-2">
                <div className="min-w-0 flex-1">
                  <span className="font-mono text-blue-600 dark:text-blue-400 font-semibold text-[11px]">{t.id}</span>
                  <p className="text-xs font-semibold text-slate-700 dark:text-slate-200 mt-0.5 truncate">{t.sender} → {t.receiver}</p>
                  <p className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">{t.sUPI}</p>
                </div>
                <StatusBadge status={t.status} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-bold text-slate-800 dark:text-slate-100">{fmtAmount(t.amount)}</span>
                <div className="flex items-center gap-3">
                  <RiskBar score={t.score} />
                  <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500">{t.time}</span>
                </div>
              </div>
            </button>
          ))}
        </div>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 4 — TRANSACTION ANALYSIS
// ═══════════════════════════════════════════════════════════════════════════════
function AnalysisPage({ selected: ext }: { selected: typeof TRANSACTIONS[0] | null }) {
  const [selected, setSelected] = useState<typeof TRANSACTIONS[0]>(ext ?? TRANSACTIONS[0]);
  useEffect(() => { if (ext) setSelected(ext); }, [ext]);

  const { isDark } = useDark();
  const t = selected;

  const rules = [
    { name: "Velocity Check",          result: t.score > 80 ? "Failed" : t.score > 50 ? "Warning" : "Passed", detail: t.score > 80 ? "7 txns in 10 min (limit: 3)" : "Within normal range" },
    { name: "Daily Txn Limit",         result: t.amount > 50000 ? "Failed" : t.amount > 20000 ? "Warning" : "Passed", detail: t.amount > 50000 ? `₹${(t.amount/1000).toFixed(0)}K exceeds ₹50K limit` : "Under daily limit" },
    { name: "Amount Threshold",        result: t.amount > 100000 ? "Failed" : t.amount > 40000 ? "Warning" : "Passed", detail: t.amount > 100000 ? "Exceeds single txn threshold" : "Within threshold" },
  ];

  const muleScore   = t.status === "Blocked" ? 88 : t.status === "Flagged" ? 54 : 9;
  const muleConn    = t.status === "Blocked" ? 4  : t.status === "Flagged" ? 2  : 0;
  const networkRisk = t.status === "Blocked" ? "Critical" : t.status === "Flagged" ? "Medium" : "Low";

  const ruleStyle = (r: string) => ({
    Passed:  "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400",
    Warning: "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400",
    Failed:  "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400",
  })[r] ?? "";

  const decisionCfg = {
    Allowed: { bg: "bg-emerald-500", icon: <CheckCircle size={28} className="text-white" />, label: "ALLOW TRANSACTION" },
    Flagged: { bg: "bg-amber-500",   icon: <Flag size={28} className="text-white" />,        label: "FLAG FOR REVIEW" },
    Blocked: { bg: "bg-red-600",     icon: <Lock size={28} className="text-white" />,         label: "BLOCK TRANSACTION" },
  }[t.status];

  const miniMuleNodes = MULE_NODES.slice(0, 6);
  const miniMuleEdges = MULE_EDGES.slice(0, 7);

  return (
    <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
      {/* Left: transaction list — horizontal scroll on mobile, vertical list on desktop */}
      <div className="xl:col-span-1">
        <Card className="overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 dark:border-white/[0.06]">
            <p className="text-sm font-bold text-slate-800 dark:text-slate-100">Select Transaction</p>
            <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5 hidden sm:block">Click to analyse</p>
          </div>
          {/* Mobile: horizontal scrolling chips */}
          <div className="xl:hidden flex gap-2 overflow-x-auto p-3 scrollbar-none">
            {TRANSACTIONS.map(tx => (
              <button key={tx.id} onClick={() => setSelected(tx)}
                className={`shrink-0 px-3 py-2 rounded-xl text-left transition-colors ${selected.id === tx.id ? "bg-blue-600 text-white" : "bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 hover:bg-blue-50 dark:hover:bg-blue-900/20"}`}>
                <p className="font-mono text-[10px] font-bold">{tx.id}</p>
                <p className="text-[10px] font-semibold mt-0.5 whitespace-nowrap">{fmtAmount(tx.amount)}</p>
                <StatusBadge status={tx.status} />
              </button>
            ))}
          </div>
          {/* Desktop: vertical list */}
          <div className="hidden xl:block divide-y divide-slate-50 dark:divide-white/[0.04] max-h-[600px] overflow-y-auto">
            {TRANSACTIONS.map(tx => (
              <button key={tx.id} onClick={() => setSelected(tx)}
                className={`w-full text-left px-4 py-3 hover:bg-blue-50/30 dark:hover:bg-blue-900/10 transition-colors ${selected.id === tx.id ? "bg-blue-50 dark:bg-blue-900/15 border-l-2 border-blue-600" : ""}`}>
                <p className="font-mono text-[11px] font-bold text-blue-600 dark:text-blue-400">{tx.id}</p>
                <p className="text-[11px] font-semibold text-slate-600 dark:text-slate-300 mt-0.5">{tx.sender}</p>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-[11px] font-bold text-slate-700 dark:text-slate-200">{fmtAmount(tx.amount)}</span>
                  <StatusBadge status={tx.status} />
                </div>
              </button>
            ))}
          </div>
        </Card>
      </div>

      {/* Right: analysis */}
      <div className="xl:col-span-3 space-y-4">
        {/* Transaction Details */}
        <Card className="p-5">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-3">Transaction Details</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {[
              { label: "Txn ID",    value: t.id },
              { label: "Sender",    value: t.sender },
              { label: "Receiver",  value: t.receiver },
              { label: "Amount",    value: fmtAmount(t.amount) },
              { label: "Time",      value: t.time },
            ].map(({ label, value }) => (
              <div key={label} className="bg-slate-50 dark:bg-slate-800/60 rounded-xl p-3">
                <p className="text-[9px] text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-0.5">{label}</p>
                <p className="text-xs font-bold text-slate-700 dark:text-slate-200 truncate">{value}</p>
              </div>
            ))}
          </div>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Rule Engine */}
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
                <Filter size={13} className="text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">Rule Engine</h3>
            </div>
            <div className="space-y-3">
              {rules.map(({ name, result, detail }) => (
                <div key={name} className={`p-3 rounded-xl border ${ruleStyle(result)}`}>
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-xs font-bold">{name}</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider">{result}</span>
                  </div>
                  <p className="text-[11px] opacity-80">{detail}</p>
                </div>
              ))}
            </div>
          </Card>

          {/* AI Prediction */}
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 rounded-lg bg-violet-50 dark:bg-violet-900/30 flex items-center justify-center">
                <Cpu size={13} className="text-violet-600 dark:text-violet-400" />
              </div>
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">AI Prediction</h3>
            </div>
            <div className="flex justify-center mb-3">
              <ScoreGauge score={t.score} size={150} />
            </div>
            <div className="space-y-2">
              {[
                { label: "AI Confidence", value: `${Math.max(85, 99 - (100 - t.score) / 10).toFixed(1)}%`, bar: Math.max(85, 99 - (100 - t.score) / 10), barColor: "#7c3aed" },
                { label: "Detection Latency", value: "~1 ms", bar: 95, barColor: "#0891b2" },
              ].map(({ label, value, bar, barColor }) => (
                <div key={label}>
                  <div className="flex justify-between mb-0.5">
                    <span className="text-[11px] text-slate-500 dark:text-slate-400">{label}</span>
                    <span className="text-[11px] font-bold text-slate-700 dark:text-slate-200">{value}</span>
                  </div>
                  <div className="h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${bar}%`, background: barColor }} />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Mule Detection */}
          <Card className="p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 rounded-lg bg-teal-50 dark:bg-teal-900/30 flex items-center justify-center">
                <Network size={13} className="text-teal-600 dark:text-teal-400" />
              </div>
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">Mule Detection</h3>
            </div>
            <div className="grid grid-cols-3 gap-2 mb-4">
              {[
                { label: "Network Risk",        value: networkRisk,        color: networkRisk === "Critical" ? "text-red-600 dark:text-red-400" : networkRisk === "Medium" ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400" },
                { label: "Suspicious Conns.",   value: String(muleConn),   color: muleConn > 2 ? "text-red-600 dark:text-red-400" : muleConn > 0 ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400" },
                { label: "Mule Score",          value: String(muleScore),  color: muleScore > 75 ? "text-red-600 dark:text-red-400" : muleScore > 45 ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400" },
              ].map(({ label, value, color }) => (
                <div key={label} className="bg-slate-50 dark:bg-slate-800/60 rounded-xl p-2.5 text-center">
                  <p className={`text-sm font-black ${color}`}>{value}</p>
                  <p className="text-[9px] text-slate-400 dark:text-slate-500 mt-0.5 leading-snug">{label}</p>
                </div>
              ))}
            </div>
            {/* Mini network graph */}
            <div className={`rounded-xl overflow-hidden ${isDark ? "bg-slate-800/50" : "bg-slate-50"}`}>
              <svg viewBox="0 0 420 200" width="100%" height={140}>
                {miniMuleEdges.map(([f,t],i) => {
                  const fn = miniMuleNodes.find(n => n.id === f);
                  const tn = miniMuleNodes.find(n => n.id === t);
                  if (!fn || !tn) return null;
                  const crit = fn.type === "mule" && tn.type === "mule";
                  return <line key={i} x1={fn.x} y1={fn.y} x2={tn.x} y2={tn.y}
                    stroke={crit ? (isDark ? "#7f1d1d" : "#fca5a5") : (isDark ? "#334155" : "#cbd5e1")}
                    strokeWidth={crit ? 1.5 : 1} strokeDasharray={crit ? "" : "3 2"} />;
                })}
                {miniMuleNodes.map(node => {
                  const c = node.type === "mule" ? "#dc2626" : node.type === "suspect" ? "#f59e0b" : "#22c55e";
                  const r = node.type === "mule" ? 16 : node.type === "suspect" ? 13 : 10;
                  return (
                    <g key={node.id}>
                      {node.type === "mule" && <circle cx={node.x} cy={node.y} r={r+6} fill={c} opacity={isDark?0.18:0.1} />}
                      <circle cx={node.x} cy={node.y} r={r} fill={isDark?"#1e293b":"white"} stroke={c} strokeWidth={2} />
                      <text x={node.x} y={node.y} textAnchor="middle" dominantBaseline="middle" fontSize={7} fontWeight="bold" fill={c}>{node.risk}</text>
                      <text x={node.x} y={node.y+r+8} textAnchor="middle" fontSize={7} fill={isDark?"#64748b":"#94a3b8"} fontFamily="monospace">{node.label}</text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </Card>

          {/* Final Decision */}
          <Card className="p-5 flex flex-col">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-7 h-7 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center">
                <ShieldCheck size={13} className="text-slate-600 dark:text-slate-400" />
              </div>
              <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">Final Decision</h3>
            </div>

            <div className={`flex-1 rounded-2xl ${decisionCfg.bg} flex flex-col items-center justify-center p-6 mb-4`}>
              <div className="w-14 h-14 rounded-full bg-white/20 flex items-center justify-center mb-3">
                {decisionCfg.icon}
              </div>
              <p className="text-2xl font-black text-white tracking-wide">{decisionCfg.label}</p>
              <p className="text-white/80 text-xs mt-1 font-semibold">Fraud Score: {t.score}/100</p>
            </div>

            <p className="text-[11px] text-slate-400 dark:text-slate-500 text-center leading-relaxed">
              Decision generated using{" "}
              <span className="font-semibold text-slate-600 dark:text-slate-300">Rule Engine</span> +{" "}
              <span className="font-semibold text-slate-600 dark:text-slate-300">AI Fraud Model</span> +{" "}
              <span className="font-semibold text-slate-600 dark:text-slate-300">Mule Detection</span>
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 5 — MULE NETWORK
// ═══════════════════════════════════════════════════════════════════════════════
function MulePage() {
  const { isDark } = useDark();
  const nc = (t: string) => t === "mule" ? "#dc2626" : t === "suspect" ? "#f59e0b" : "#22c55e";

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-base md:text-lg font-bold text-slate-800 dark:text-slate-100">Mule Network Analysis</h2>
          <p className="text-xs text-slate-400 dark:text-slate-500">GNN-based detection of money mule clusters</p>
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          {[["bg-red-500","Confirmed Mule"],["bg-amber-400","Suspect"],["bg-emerald-500","Normal"]].map(([c,l]) => (
            <div key={l} className="flex items-center gap-1.5"><span className={`w-2.5 h-2.5 rounded-full ${c}`} /><span className="text-xs text-slate-500 dark:text-slate-400">{l}</span></div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2 p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">Network Graph — Cluster #A-147</h3>
            <span className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 text-[10px] font-bold px-2 py-1 rounded-lg">HIGH RISK</span>
          </div>
          <div className={`rounded-xl overflow-hidden ${isDark ? "bg-slate-800/50" : "bg-slate-50"}`}>
            <svg viewBox="0 0 450 320" width="100%" height={300}>
              {MULE_EDGES.map(([f,t],i) => {
                const fn = MULE_NODES.find(n => n.id === f)!;
                const tn = MULE_NODES.find(n => n.id === t)!;
                const crit = fn?.type === "mule" && tn?.type === "mule";
                if (!fn || !tn) return null;
                return <line key={i} x1={fn.x} y1={fn.y} x2={tn.x} y2={tn.y}
                  stroke={crit ? (isDark?"#7f1d1d":"#fca5a5") : (isDark?"#334155":"#cbd5e1")}
                  strokeWidth={crit?2:1} strokeDasharray={crit?"":"4 2"} opacity={0.9} />;
              })}
              {MULE_NODES.map(node => {
                const c = nc(node.type);
                const r = node.type==="mule"?20:node.type==="suspect"?15:11;
                return (
                  <g key={node.id}>
                    {node.type==="mule" && <circle cx={node.x} cy={node.y} r={r+7} fill={c} opacity={isDark?0.18:0.1} />}
                    <circle cx={node.x} cy={node.y} r={r} fill={isDark?"#1e293b":"white"} stroke={c} strokeWidth={node.type==="mule"?3:2} />
                    <text x={node.x} y={node.y} textAnchor="middle" dominantBaseline="middle" fontSize={8} fontWeight="bold" fill={c}>{node.risk}</text>
                    <text x={node.x} y={node.y+r+10} textAnchor="middle" fontSize={8} fill={isDark?"#64748b":"#64748b"} fontFamily="monospace">{node.label}</text>
                  </g>
                );
              })}
            </svg>
          </div>
        </Card>

        <div className="space-y-3">
          <Card className="p-5">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-3">Flagged Accounts</h3>
            <div className="space-y-2">
              {MULE_NODES.filter(n => n.type!=="normal").sort((a,b)=>b.risk-a.risk).map(node => (
                <div key={node.id} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full" style={{ background: nc(node.type) }} />
                    <span className="text-xs font-mono font-semibold text-slate-600 dark:text-slate-300">{node.label}</span>
                  </div>
                  <span className="text-xs font-bold" style={{ color: nc(node.type) }}>{node.risk}</span>
                </div>
              ))}
            </div>
          </Card>
          <Card className="p-5">
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-3">Cluster Stats</h3>
            <div className="space-y-2">
              {[
                ["Total Nodes","8"],["Mule Accounts","4"],["Suspects","2"],["Edges","10"],["Cluster Risk","CRITICAL"],["Laundered","₹2.3 Cr"],
              ].map(([l,v]) => (
                <div key={l} className="flex justify-between items-center">
                  <span className="text-xs text-slate-500 dark:text-slate-400">{l}</span>
                  <span className={`text-xs font-bold ${v==="CRITICAL"?"text-red-600 dark:text-red-400":"text-slate-700 dark:text-slate-200"}`}>{v}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 6 — ANALYTICS
// ═══════════════════════════════════════════════════════════════════════════════
function AnalyticsPage() {
  const ct = useChartTheme();
  const { isDark } = useDark();

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Analytics & Insights</h2>
        <p className="text-xs text-slate-400 dark:text-slate-500">AI-driven fraud intelligence and pattern analysis</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Blocked Value",    value: "₹3.8 Cr",  color: "bg-red-500",    up: false },
          { label: "Avg Risk Score",   value: "41.2",      color: "bg-blue-600",   up: true  },
          { label: "False Positives",  value: "0.8%",      color: "bg-violet-600", up: true  },
          { label: "Models Active",    value: "7",         color: "bg-teal-600",   up: true  },
        ].map(({ label, value, color, up }) => (
          <Card key={label} className="p-4">
            <div className={`w-7 h-7 rounded-lg ${color} mb-3`} />
            <p className="text-xl font-bold text-slate-800 dark:text-slate-100">{value}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{label}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="p-5">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-0.5">Fraud Trends (24h)</h3>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mb-4">Fraud vs safe volume over time</p>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={fraudTrendData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid key="an-trend-grid" strokeDasharray="3 3" stroke={ct.grid} />
              <XAxis key="an-trend-x" dataKey="time" tick={{ fontSize: 10, fill: ct.tick }} tickLine={false} axisLine={false} />
              <YAxis key="an-trend-y" tick={{ fontSize: 10, fill: ct.tick }} tickLine={false} axisLine={false} />
              <Tooltip key="an-trend-tt" contentStyle={ct.tooltip} />
              <Area key="an-trend-safe"  type="monotone" dataKey="safe"  stroke={ct.blue} strokeWidth={2} fill={ct.blue}  fillOpacity={isDark ? 0.12 : 0.08} name="Safe" />
              <Area key="an-trend-fraud" type="monotone" dataKey="fraud" stroke="#dc2626" strokeWidth={2} fill="#dc2626" fillOpacity={isDark ? 0.14 : 0.10} name="Fraud" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card className="p-5">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-0.5">Hourly Transaction Volume</h3>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mb-4">Transaction load per hour</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={hourlyData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <CartesianGrid key="an-bar-grid" strokeDasharray="3 3" stroke={ct.grid} vertical={false} />
              <XAxis key="an-bar-x" dataKey="h" tick={{ fontSize: 10, fill: ct.tick }} tickLine={false} axisLine={false} />
              <YAxis key="an-bar-y" tick={{ fontSize: 10, fill: ct.tick }} tickLine={false} axisLine={false} />
              <Tooltip key="an-bar-tt" contentStyle={ct.tooltip} />
              <Bar key="an-bar-v" dataKey="v" fill={ct.blue} radius={[4,4,0,0]} name="Transactions" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card className="p-5">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-0.5">Top Fraud Types</h3>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mb-4">Distribution this month</p>
          <div className="flex items-center gap-6">
            <PieChart width={150} height={150}>
              <Pie key="an-ft-pie" data={fraudTypesData} cx={75} cy={75} innerRadius={42} outerRadius={68} paddingAngle={3} dataKey="value">
                {fraudTypesData.map((e,i) => <Cell key={`an-ft-cell-${i}`} fill={e.fill} />)}
              </Pie>
              <Tooltip key="an-ft-tt" contentStyle={ct.tooltip} />
            </PieChart>
            <div className="space-y-2 flex-1">
              {fraudTypesData.map(({ name, value, fill }) => (
                <div key={name}>
                  <div className="flex justify-between mb-0.5">
                    <span className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full" style={{ background: fill }} />{name}
                    </span>
                    <span className="text-[11px] font-bold text-slate-700 dark:text-slate-200">{value}%</span>
                  </div>
                  <div className="h-1 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div className="h-full rounded-full" style={{ width: `${value}%`, background: fill }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        <Card className="p-5">
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100 mb-0.5">High-Risk Receivers</h3>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 mb-4">Top flagged UPI receivers</p>
          <div className="space-y-3">
            {highRiskReceivers.map(({ name, count, amount }, i) => (
              <div key={name}>
                <div className="flex justify-between mb-0.5">
                  <span className="text-xs font-mono font-semibold text-slate-600 dark:text-slate-300">{name}</span>
                  <div className="flex gap-3 text-[11px]">
                    <span className="text-red-600 dark:text-red-400 font-bold">{count} txns</span>
                    <span className="text-slate-500 dark:text-slate-400">{fmtAmount(amount)}</span>
                  </div>
                </div>
                <div className="h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full rounded-full bg-red-500"
                    style={{ width: `${(count / highRiskReceivers[0].count) * 100}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 7 — FRAUD ALERTS
// ═══════════════════════════════════════════════════════════════════════════════
function AlertsPage({ onAnalyse }: { onAnalyse: (t: typeof TRANSACTIONS[0]) => void }) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Fraud Alerts</h2>
          <p className="text-xs text-slate-400 dark:text-slate-500">Active incidents requiring review</p>
        </div>
        <span className="bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400 text-xs font-bold px-3 py-1.5 rounded-full border border-red-200 dark:border-red-800">
          {ALERTS.length} Active
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {ALERTS.map(a => {
          const isBlocked = a.action === "Blocked";
          return (
            <Card key={a.id} className={`p-5 border-l-4 ${isBlocked ? "border-l-red-500" : "border-l-amber-400"}`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-start gap-3">
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 mt-0.5 ${isBlocked ? "bg-red-100 dark:bg-red-900/30" : "bg-amber-100 dark:bg-amber-900/30"}`}>
                    <AlertTriangle size={16} className={isBlocked ? "text-red-600 dark:text-red-400" : "text-amber-600 dark:text-amber-400"} />
                  </div>
                  <div>
                    <p className="text-xs font-mono text-slate-400 dark:text-slate-500">{a.id}</p>
                    <p className="text-sm font-bold text-slate-800 dark:text-slate-100">{a.type}</p>
                  </div>
                </div>
                <StatusBadge status={a.action} />
              </div>

              <div className="grid grid-cols-2 gap-2.5 mb-4">
                {[
                  { label: "Sender",      value: a.sender },
                  { label: "Receiver",    value: a.receiver },
                  { label: "Amount",      value: fmtAmount(a.amount) },
                  { label: "Fraud Score", value: `${a.score}/100` },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-slate-50 dark:bg-slate-800/60 rounded-xl p-2.5">
                    <p className="text-[9px] text-slate-400 dark:text-slate-500 uppercase tracking-wider">{label}</p>
                    <p className="text-xs font-bold text-slate-700 dark:text-slate-200 mt-0.5 truncate">{value}</p>
                  </div>
                ))}
              </div>

              <div className="mb-3">
                <div className="flex justify-between mb-0.5">
                  <span className="text-[11px] text-slate-400 dark:text-slate-500">Fraud Score</span>
                  <span className="text-[11px] font-bold text-red-600 dark:text-red-400">{a.score}%</span>
                </div>
                <div className="h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                  <div className="h-full rounded-full bg-red-500" style={{ width: `${a.score}%` }} />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <p className="text-[11px] font-mono text-slate-400 dark:text-slate-500">{a.time}</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      const match = TRANSACTIONS.find(t => t.sUPI === a.sUPI) ?? TRANSACTIONS[0];
                      onAnalyse(match);
                    }}
                    className="px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-900/25 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-400 text-xs font-semibold hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors">
                    Analyse
                  </button>
                  {!isBlocked && (
                    <button className="px-3 py-1.5 rounded-lg bg-red-600 text-white text-xs font-semibold hover:bg-red-700 transition-colors">
                      Block Now
                    </button>
                  )}
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREEN 8 — SETTINGS
// ═══════════════════════════════════════════════════════════════════════════════
function SettingsPage() {
  const [threshold, setThreshold] = useState(75);
  const [toggles, setToggles] = useState({
    autoBlock: true, velocity: true, mule: true,
    email: true, sms: false, realtime: true,
  });
  const flip = (k: keyof typeof toggles) => setToggles(p => ({ ...p, [k]: !p[k] }));

  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100">Settings</h2>
        <p className="text-xs text-slate-400 dark:text-slate-500">Configure fraud detection parameters</p>
      </div>

      {[
        { title: "Detection", icon: Cpu, color: "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400", items: [
          { key: "autoBlock" as const, label: "Auto-Block High Risk", desc: "Block transactions exceeding the risk threshold automatically" },
          { key: "velocity"  as const, label: "Velocity Detection",   desc: "Flag accounts with unusual transaction velocity" },
          { key: "mule"      as const, label: "Mule Network Detection",desc: "GNN-based mule account identification" },
          { key: "realtime"  as const, label: "Real-time Monitoring",  desc: "Stream live transaction data to the dashboard" },
        ]},
        { title: "Notifications", icon: Bell, color: "bg-violet-50 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400", items: [
          { key: "email" as const, label: "Email Alerts",  desc: "Send fraud alerts to registered analyst emails" },
          { key: "sms"   as const, label: "SMS Alerts",    desc: "Send critical alerts via SMS" },
        ]},
      ].map(({ title, icon: Icon, color, items }) => (
        <Card key={title} className="overflow-hidden">
          <div className="flex items-center gap-2 px-5 py-4 border-b border-slate-100 dark:border-white/[0.06]">
            <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${color}`}><Icon size={13} /></div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">{title}</h3>
          </div>
          <div className="divide-y divide-slate-50 dark:divide-white/[0.04]">
            {items.map(({ key, label, desc }) => (
              <div key={key} className="flex items-center justify-between px-5 py-4">
                <div>
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">{label}</p>
                  <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">{desc}</p>
                </div>
                <button onClick={() => flip(key)}
                  className={`relative w-11 h-6 rounded-full transition-colors duration-200 ${toggles[key] ? "bg-blue-600" : "bg-slate-200 dark:bg-slate-600"}`}>
                  <span className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow-sm transition-all duration-200 ${toggles[key] ? "left-6" : "left-1"}`} />
                </button>
              </div>
            ))}
          </div>
        </Card>
      ))}

      <Card className="p-5">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-7 h-7 rounded-lg bg-red-50 dark:bg-red-900/30 flex items-center justify-center text-red-600 dark:text-red-400"><AlertTriangle size={13} /></div>
          <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">Risk Threshold</h3>
        </div>
        <div className="flex justify-between mb-2">
          <span className="text-xs font-medium text-slate-600 dark:text-slate-300">
            Auto-block at score ≥ <span className="text-blue-600 dark:text-blue-400 font-bold">{threshold}</span>
          </span>
          <span className="text-[11px] text-slate-400 dark:text-slate-500">Higher = more permissive</span>
        </div>
        <input type="range" min={50} max={99} value={threshold} onChange={e => setThreshold(+e.target.value)} className="w-full accent-blue-600" />
        <div className="flex justify-between text-[10px] text-slate-400 dark:text-slate-500 mt-1">
          <span>50 — Aggressive</span><span>99 — Conservative</span>
        </div>
      </Card>

      <button className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold transition-colors shadow-lg shadow-blue-600/20">
        Save Configuration
      </button>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// ROOT APP
// ═══════════════════════════════════════════════════════════════════════════════
export default function App() {
  const [page, setPage] = useState("dashboard");
  const [isDark, setIsDark] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [selectedTxn, setSelectedTxn] = useState<typeof TRANSACTIONS[0] | null>(null);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  const toggle = useCallback(() => setIsDark(d => !d), []);

  const navigateToAnalysis = (txn: typeof TRANSACTIONS[0]) => {
    setSelectedTxn(txn);
    setPage("analysis");
  };

  const pages: Record<string, JSX.Element> = {
    dashboard: <DashboardPage key={refresh} />,
    payment:   <PaymentPage onGoAnalysis={navigateToAnalysis} />,
    live:      <LivePage onSelect={navigateToAnalysis} />,
    analysis:  <AnalysisPage selected={selectedTxn} />,
    mule:      <MulePage />,
    analytics: <AnalyticsPage />,
    alerts:    <AlertsPage onAnalyse={t => { setSelectedTxn(t); setPage("analysis"); }} />,
    settings:  <SettingsPage />,
  };

  return (
    <ThemeCtx.Provider value={{ isDark, toggle }}>
      <div className={`${isDark ? "dark" : ""} flex h-screen w-full overflow-hidden`}
        style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
        <div className="flex h-full w-full bg-[#f0f4fa] dark:bg-[#0f172a] transition-colors duration-200">
          <Sidebar active={page} setActive={setPage} mobileOpen={mobileSidebarOpen} setMobileOpen={setMobileSidebarOpen} />
          <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
            <TopNav page={page} onRefresh={() => setRefresh(r => r + 1)} onMenuToggle={() => setMobileSidebarOpen(v => !v)} />
            <main className="flex-1 overflow-y-auto p-4 md:p-5 sentinel-scroll">
              {pages[page]}
            </main>
          </div>
        </div>
      </div>
      <style>{`
        .sentinel-scroll::-webkit-scrollbar { width: 5px; }
        .sentinel-scroll::-webkit-scrollbar-track { background: transparent; }
        .sentinel-scroll::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.3); border-radius: 10px; }
        .sentinel-scroll::-webkit-scrollbar-thumb:hover { background: rgba(148,163,184,0.5); }
        .dark .sentinel-scroll::-webkit-scrollbar-thumb { background: rgba(51,65,85,0.6); }
        .scrollbar-none { -ms-overflow-style: none; scrollbar-width: none; }
        .scrollbar-none::-webkit-scrollbar { display: none; }
      `}</style>
    </ThemeCtx.Provider>
  );
}
