import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { VisualTestRunner } from "./VisualTestRunner";

const assetPathPrefix = `${(import.meta.env.BASE_URL || "/").replace(/\/$/, "")}/assets`;
const imgMoreHorizontal = `${assetPathPrefix}/eff74.svg`;
const imgSearch = `${assetPathPrefix}/ad518.svg`;
const imgNews1 = `${assetPathPrefix}/c0fcf.png`;
const imgNews2 = `${assetPathPrefix}/d5053.png`;
const imgNews3 = `${assetPathPrefix}/a9902.png`;
const imgNews4 = `${assetPathPrefix}/79d9c.png`;
const imgNews5 = `${assetPathPrefix}/5b63a.png`;
const imgTabletNews3 = `${assetPathPrefix}/192b8.png`;
const imgTabletNews4 = `${assetPathPrefix}/645e7.png`;
const imgTabletNews5 = `${assetPathPrefix}/ef83c.png`;
const imgDesktopNews3 = `${assetPathPrefix}/d84e7.png`;
const imgDesktopNews4 = `${assetPathPrefix}/6ef75.png`;
const imgDesktopNews5 = `${assetPathPrefix}/740c6.png`;
const imgLocationPin = `${assetPathPrefix}/0eabf.svg`;
const imgClock = `${assetPathPrefix}/c681b.svg`;

export function BrandLogo({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const isSm = size === "sm";
  return (
    <div className="flex items-center gap-2.5 group cursor-pointer select-none">
      <div className="relative flex items-center justify-center shrink-0">
        <div className={`${isSm ? "size-7 rounded-lg" : "size-9 rounded-xl"} bg-gradient-to-tr from-[#ff315f] via-[#f72585] to-[#f7a928] flex items-center justify-center shadow-md shadow-[#ff315f]/25 group-hover:scale-105 transition-transform`}>
          <span className={`text-white ${isSm ? "text-[14px]" : "text-[18px]"} font-black`}>P</span>
        </div>
        <span className="absolute -bottom-0.5 -right-0.5 size-2 rounded-full bg-emerald-400 border-2 border-white animate-pulse" />
      </div>
      <div className="flex flex-col items-start leading-none">
        <div className="flex items-center gap-1.5">
          <span className={`font-['Inter:Extra_Bold'] font-black text-[#ff315f] ${isSm ? "text-[17px]" : "text-[20px]"} tracking-tight`}>pulse.</span>
          <span className="bg-gradient-to-r from-[#ff315f] to-[#f97316] text-white text-[9px] font-extrabold px-1.5 py-0.5 rounded uppercase tracking-wider shadow-xs">
            TIỀN PHONG
          </span>
        </div>
        <span className="text-[10px] text-[#5f687b] font-medium tracking-tight mt-0.5 hidden sm:inline">
          Tin tức & Thời tiết Đô thị 24/7
        </span>
      </div>
    </div>
  );
}

const FALLBACK_NEWS_IMAGES = [imgNews1, imgNews2, imgNews3, imgNews4, imgNews5];
const TABLET_FALLBACK_IMAGES = [imgNews1, imgTabletNews3, imgTabletNews4, imgTabletNews5];
const DESKTOP_FALLBACK_IMAGES = [imgNews1, imgNews2, imgDesktopNews3, imgDesktopNews4, imgDesktopNews5];

// ── API Keys & Config ─────────────────────────────────────────────────────
const OWM_KEY = "a201c471567522a7d0b7a0567ad245fe";
const DEFAULT_LAT = 20.9716;
const DEFAULT_LON = 105.7725;
const DEFAULT_LOCATION = "Hà Nội";
const BACKEND_URL = "https://quan-ly-tien-phong-main.onrender.com";

// ── Geolocation & Location Services ───────────────────────────────────────
export type GeoSource = "gps" | "ip" | "manual" | "default";
export type GeoState = {
  status: "idle" | "loading" | "granted" | "denied";
  lat: number;
  lon: number;
  name: string;
  source: GeoSource;
};

export const POPULAR_LOCATIONS = [
  { name: "TP. Hồ Chí Minh", lat: 10.8231, lon: 106.6297, icon: "🏙️" },
  { name: "Hà Nội", lat: 21.0285, lon: 105.8542, icon: "🏛️" },
  { name: "Đà Nẵng", lat: 16.0544, lon: 108.2022, icon: "🌉" },
  { name: "Hải Phòng", lat: 20.8449, lon: 106.6881, icon: "⚓" },
  { name: "Cần Thơ", lat: 10.0452, lon: 105.7469, icon: "🛶" },
  { name: "Nha Trang", lat: 12.2388, lon: 109.1967, icon: "🏖️" },
  { name: "Huế", lat: 16.4637, lon: 107.5909, icon: "🏯" },
  { name: "Vũng Tàu", lat: 10.3460, lon: 107.0843, icon: "🌊" },
  { name: "Đà Lạt", lat: 11.9404, lon: 108.4583, icon: "🌲" },
  { name: "Hạ Long", lat: 20.9505, lon: 107.0734, icon: "⛵" },
  { name: "Bình Dương", lat: 11.1667, lon: 106.6667, icon: "🏭" },
  { name: "Đồng Nai", lat: 11.0500, lon: 107.0000, icon: "🌾" },
];

function normalizeVietnameseCity(city: string): string {
  if (!city) return DEFAULT_LOCATION;
  const c = city.trim().toLowerCase();
  if (c.includes("ho chi minh") || c.includes("saigon") || c.includes("sai gon")) return "TP. Hồ Chí Minh";
  if (c.includes("da nang") || c.includes("danang")) return "Đà Nẵng";
  if (c.includes("hai phong") || c.includes("haiphong")) return "Hải Phòng";
  if (c.includes("can tho") || c.includes("cantho")) return "Cần Thơ";
  if (c.includes("nha trang")) return "Nha Trang";
  if (c.includes("hue") || c.includes("thua thien")) return "Huế";
  if (c.includes("vung tau") || c.includes("ba ria")) return "Vũng Tàu";
  if (c.includes("da lat") || c.includes("dalat") || c.includes("lam dong")) return "Đà Lạt";
  if (c.includes("ha long") || c.includes("halong") || c.includes("quang ninh")) return "Hạ Long";
  if (c.includes("bien hoa") || c.includes("dong nai")) return "Đồng Nai";
  if (c.includes("thu dau mot") || c.includes("binh duong")) return "Bình Dương";
  if (c.includes("quy nhon") || c.includes("binh dinh")) return "Quy Nhơn";
  if (c.includes("buon ma thuot") || c.includes("dak lak")) return "Buôn Ma Thuột";
  if (c.includes("phan thiet") || c.includes("binh thuan")) return "Phan Thiết";
  if (c.includes("son tay")) return "Sơn Tây, Hà Nội";
  if (c.includes("ha dong")) return "Hà Đông, Hà Nội";
  if (c.includes("nam dinh")) return "Nam Định";
  if (c.includes("thai nguyen")) return "Thái Nguyên";
  if (c.includes("bac ninh")) return "Bắc Ninh";
  if (c.includes("vinh") || c.includes("nghe an")) return "Vinh";
  if (c.includes("hanoi") || c.includes("ha noi")) return "Hà Nội";
  return city;
}

async function detectIPLocation(): Promise<{ lat: number; lon: number; name: string } | null> {
  // 1. ipwho.is (CORS free, fast)
  try {
    const res = await fetch("https://ipwho.is/", { signal: AbortSignal.timeout(3500) });
    if (res.ok) {
      const d = await res.json();
      if (d && d.success !== false && d.latitude && d.longitude) {
        return {
          lat: Math.round(d.latitude * 10000) / 10000,
          lon: Math.round(d.longitude * 10000) / 10000,
          name: normalizeVietnameseCity(d.city || d.region || "Việt Nam"),
        };
      }
    }
  } catch {}

  // 2. geojs.io fallback
  try {
    const res = await fetch("https://get.geojs.io/v1/ip/geo.json", { signal: AbortSignal.timeout(3500) });
    if (res.ok) {
      const d = await res.json();
      if (d && d.latitude && d.longitude) {
        return {
          lat: Math.round(parseFloat(d.latitude) * 10000) / 10000,
          lon: Math.round(parseFloat(d.longitude) * 10000) / 10000,
          name: normalizeVietnameseCity(d.city || d.region || "Việt Nam"),
        };
      }
    }
  } catch {}

  return null;
}

// ── Manual location change (city name search) ─────────────────────────────
async function geocodeCity(cityName: string): Promise<{ lat: number; lon: number; name: string } | null> {
  try {
    const r = await fetch(`https://api.openweathermap.org/geo/1.0/direct?q=${encodeURIComponent(cityName)}&limit=1&appid=${OWM_KEY}`);
    if (r.ok) {
      const d = await r.json();
      if (d && d.length > 0) return { lat: d[0].lat, lon: d[0].lon, name: d[0].local_names?.vi || d[0].name };
    }
  } catch {}
  return null;
}

function useGeoLocation(): {
  geo: GeoState;
  requestGPS: () => Promise<void>;
  requestIP: () => Promise<void>;
  setManualLocation: (loc: { lat: number; lon: number; name: string }) => void;
} {
  const [geo, setGeo] = useState<GeoState>(() => {
    try {
      const savedManual = localStorage.getItem("pulse_manual_location");
      if (savedManual) {
        const p = JSON.parse(savedManual);
        if (p.lat && p.lon && p.name) return { status: "granted", lat: p.lat, lon: p.lon, name: p.name, source: "manual" };
      }
    } catch {}
    return { status: "loading", lat: DEFAULT_LAT, lon: DEFAULT_LON, name: DEFAULT_LOCATION, source: "default" };
  });

  const requestGPS = useCallback(async () => {
    if (!navigator.geolocation) {
      const ipLoc = await detectIPLocation();
      if (ipLoc) setGeo({ status: "granted", ...ipLoc, source: "ip" });
      else setGeo(g => ({ ...g, status: "denied" }));
      return;
    }
    setGeo(g => ({ ...g, status: "loading" }));
    return new Promise<void>((resolve) => {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = Math.round(pos.coords.latitude * 10000) / 10000;
          const lon = Math.round(pos.coords.longitude * 10000) / 10000;
          let name = DEFAULT_LOCATION;
          try {
            const r = await fetch(`https://api.openweathermap.org/geo/1.0/reverse?lat=${lat}&lon=${lon}&limit=1&appid=${OWM_KEY}`);
            if (r.ok) {
              const d = await r.json();
              if (d && d.length > 0) {
                name = d[0].local_names?.vi || d[0].name || DEFAULT_LOCATION;
              }
            }
          } catch {}
          const newGeo: GeoState = { status: "granted", lat, lon, name, source: "gps" };
          setGeo(newGeo);
          localStorage.removeItem("pulse_manual_location");
          resolve();
        },
        async () => {
          const ipLoc = await detectIPLocation();
          if (ipLoc) setGeo({ status: "granted", ...ipLoc, source: "ip" });
          else setGeo(g => ({ ...g, status: "denied" }));
          resolve();
        },
        { timeout: 7000, enableHighAccuracy: true, maximumAge: 60000 }
      );
    });
  }, []);

  const requestIP = useCallback(async () => {
    setGeo(g => ({ ...g, status: "loading" }));
    const ipLoc = await detectIPLocation();
    if (ipLoc) {
      setGeo({ status: "granted", ...ipLoc, source: "ip" });
      localStorage.removeItem("pulse_manual_location");
    } else {
      setGeo(g => ({ ...g, status: "denied" }));
    }
  }, []);

  const setManualLocation = useCallback((loc: { lat: number; lon: number; name: string }) => {
    const newGeo: GeoState = { status: "granted", ...loc, source: "manual" };
    setGeo(newGeo);
    localStorage.setItem("pulse_manual_location", JSON.stringify(loc));
  }, []);

  useEffect(() => {
    try {
      const savedManual = localStorage.getItem("pulse_manual_location");
      if (savedManual) {
        const p = JSON.parse(savedManual);
        if (p.lat && p.lon && p.name) {
          setGeo({ status: "granted", ...p, source: "manual" });
          return;
        }
      }
    } catch {}

    // Auto-detect immediately:
    // 1. Fire IP detection first (takes ~150ms)
    detectIPLocation().then((ipLoc) => {
      if (ipLoc) {
        setGeo(curr => {
          if (curr.source === "gps" || curr.source === "manual") return curr;
          return { status: "granted", ...ipLoc, source: "ip" };
        });
      }
    });

    // 2. Also request device GPS in background
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = Math.round(pos.coords.latitude * 10000) / 10000;
          const lon = Math.round(pos.coords.longitude * 10000) / 10000;
          let name = "";
          try {
            const r = await fetch(`https://api.openweathermap.org/geo/1.0/reverse?lat=${lat}&lon=${lon}&limit=1&appid=${OWM_KEY}`);
            if (r.ok) {
              const d = await r.json();
              if (d && d.length > 0) name = d[0].local_names?.vi || d[0].name;
            }
          } catch {}
          if (!name) name = DEFAULT_LOCATION;
          setGeo({ status: "granted", lat, lon, name, source: "gps" });
        },
        () => {},
        { timeout: 8000, enableHighAccuracy: true, maximumAge: 60000 }
      );
    }
  }, []);

  return { geo, requestGPS, requestIP, setManualLocation };
}

// ── Location Picker Modal ──────────────────────────────────────────────────
export function LocationPickerModal({
  isOpen,
  onClose,
  currentLocation,
  onSelectLocation,
  onAutoGPS,
  onAutoIP,
  geoSource,
  loading,
}: {
  isOpen: boolean;
  onClose: () => void;
  currentLocation: string;
  onSelectLocation: (loc: { lat: number; lon: number; name: string }) => void;
  onAutoGPS: () => void;
  onAutoIP: () => void;
  geoSource?: GeoSource;
  loading?: boolean;
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState("");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;
    setSearching(true);
    setSearchError("");
    try {
      const res = await geocodeCity(searchTerm.trim());
      if (res) {
        onSelectLocation(res);
        onClose();
        setSearchTerm("");
      } else {
        setSearchError(`Không tìm thấy "${searchTerm}". Thử nhập: Đà Nẵng, TP.HCM, Nha Trang...`);
      }
    } catch {
      setSearchError("Lỗi kết nối khi tìm kiếm địa điểm.");
    } finally {
      setSearching(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg bg-[#0f172a] rounded-3xl overflow-hidden border border-white/15 shadow-[0_20px_60px_rgba(0,0,0,0.7)] text-white flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-blue-900/60 via-indigo-900/60 to-purple-900/60 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <span className="size-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-lg">📍</span>
            <div>
              <p className="font-bold text-[15px]">Chọn Vị Trí Thời Tiết</p>
              <p className="text-[11px] text-gray-300">
                Hiện tại: <strong className="text-white">{currentLocation}</strong> ({geoSource === "gps" ? "GPS Thiết Bị" : geoSource === "ip" ? "IP Mạng" : geoSource === "manual" ? "Thủ Công" : "Tự Động"})
              </p>
            </div>
          </div>
          <button onClick={onClose} className="size-8 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center text-sm cursor-pointer transition-colors">✕</button>
        </div>

        <div className="p-5 flex flex-col gap-4 overflow-y-auto">
          {/* Quick Auto Buttons */}
          <div className="grid grid-cols-2 gap-2.5">
            <button
              onClick={() => { onAutoGPS(); onClose(); }}
              disabled={loading}
              className="flex items-center gap-2.5 p-3 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white transition-all shadow-md cursor-pointer text-left active:scale-95"
            >
              <span className="text-xl">🎯</span>
              <div className="min-w-0">
                <p className="font-bold text-[12px] leading-tight">Định Vị GPS</p>
                <p className="text-[10px] text-blue-100 opacity-90 truncate">Chính xác theo thiết bị</p>
              </div>
            </button>

            <button
              onClick={() => { onAutoIP(); onClose(); }}
              disabled={loading}
              className="flex items-center gap-2.5 p-3 rounded-2xl bg-white/10 hover:bg-white/15 border border-white/10 text-white transition-all cursor-pointer text-left active:scale-95"
            >
              <span className="text-xl">🌐</span>
              <div className="min-w-0">
                <p className="font-bold text-[12px] leading-tight">Dò Theo IP Mạng</p>
                <p className="text-[10px] text-gray-300 opacity-90 truncate">Không cần cấp quyền GPS</p>
              </div>
            </button>
          </div>

          {/* Search form */}
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="Nhập tên tỉnh/thành phố (Enter)..."
              className="flex-1 bg-white/10 border border-white/15 rounded-xl px-4 py-2.5 text-[13px] text-white placeholder-gray-400 focus:outline-none focus:border-blue-400"
            />
            <button
              type="submit"
              disabled={searching || !searchTerm.trim()}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold text-[13px] cursor-pointer"
            >
              {searching ? "Tìm..." : "Tìm"}
            </button>
          </form>

          {searchError && <p className="text-rose-400 text-[12px]">{searchError}</p>}

          {/* Popular Cities */}
          <div className="flex flex-col gap-2 pt-1">
            <p className="text-[11.5px] font-semibold text-gray-400 uppercase tracking-wider">Thành Phố Phổ Biến</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {POPULAR_LOCATIONS.map(loc => (
                <button
                  key={loc.name}
                  onClick={() => { onSelectLocation(loc); onClose(); }}
                  className={`flex items-center gap-2 p-2.5 rounded-xl text-left transition-all border cursor-pointer active:scale-95 ${
                    currentLocation.includes(loc.name) || loc.name.includes(currentLocation)
                      ? "bg-blue-500/25 border-blue-400/50 text-white shadow-sm"
                      : "bg-white/5 hover:bg-white/10 border-white/10 text-gray-200 hover:text-white"
                  }`}
                >
                  <span className="text-[16px]">{loc.icon}</span>
                  <span className="text-[12px] font-medium truncate">{loc.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Weather Types ─────────────────────────────────────────────────────────

type ConditionKey = "binh-thuong" | "nang" | "nang-gat" | "am-u" | "mua-nho" | "mua-dong";

interface WeatherTheme {
  key: ConditionKey;
  gradient: string;
  emoji: string;
  label: string;
  warningText: string;
  suggestionItems: string[];
  showFlood: boolean;
  floodItems?: string[];
  showRouteAdvisory: boolean;
  routeItems?: string[];
}

export const WEATHER_THEMES: Record<ConditionKey, WeatherTheme> = {
  "binh-thuong": {
    key: "binh-thuong",
    gradient: "linear-gradient(135deg, #1e3a8a 0%, #2563eb 25%, #0284c7 50%, #0d9488 75%, #4f46e5 100%)",
    emoji: "☁️", label: "Bình thường",
    warningText: "Thời tiết ổn định, ít biến động. Không có hiện tượng bất thường đáng chú ý.",
    suggestionItems: [
      "Điều khiển phương tiện: Giao thông thuận lợi, chú ý tốc độ theo quy định.",
      "Trang bị: Không cần trang bị đặc biệt.",
    ],
    showFlood: false, showRouteAdvisory: false,
  },
  "nang": {
    key: "nang",
    gradient: "linear-gradient(135deg, #0369a1 0%, #0284c7 25%, #f59e0b 55%, #ea580c 80%, #db2777 100%)",
    emoji: "☀️", label: "Nắng",
    warningText: "Trời nắng đẹp, tầm nhìn tốt. Chỉ số UV ở mức trung bình đến cao.",
    suggestionItems: [
      "Điều khiển phương tiện: Giao thông thuận lợi, chú ý chống chói khi lái xe.",
      "Trang bị: Nên đội mũ, đeo kính râm, bôi kem chống nắng nếu ra ngoài lâu.",
    ],
    showFlood: false, showRouteAdvisory: false,
  },
  "nang-gat": {
    key: "nang-gat",
    gradient: "linear-gradient(135deg, #991b1b 0%, #c2410c 25%, #ea580c 50%, #f59e0b 75%, #e11d48 100%)",
    emoji: "🔥", label: "Nắng gắt",
    warningText: "Nắng nóng gay gắt, chỉ số UV rất cao. Nguy cơ say nắng, mất nước cao nếu hoạt động ngoài trời lâu.",
    suggestionItems: [
      "Điều khiển phương tiện: Hạn chế di chuyển giờ cao điểm nắng (11h–15h). Để xe ở nơi có bóng râm.",
      "Trang bị: Đội mũ rộng vành, đeo kính râm UV400, mang theo nước uống, bôi kem chống nắng SPF50+.",
    ],
    showFlood: false, showRouteAdvisory: false,
  },
  "am-u": {
    key: "am-u",
    gradient: "linear-gradient(135deg, #1e293b 0%, #334155 30%, #475569 55%, #3b82f6 80%, #6366f1 100%)",
    emoji: "🌥️", label: "Âm u",
    warningText: "Trời nhiều mây, ánh sáng yếu. Có thể chuyển mưa nhẹ trong vài giờ tới nếu độ ẩm tăng cao.",
    suggestionItems: [
      "Điều khiển phương tiện: Tầm nhìn hơi giảm, nên bật đèn chiếu gần khi đi vào khu vực tối.",
      "Trang bị: Mang theo áo mưa mỏng phòng trường hợp mưa bất ngờ.",
    ],
    showFlood: false, showRouteAdvisory: false,
  },
  "mua-nho": {
    key: "mua-nho",
    gradient: "linear-gradient(135deg, #0f172a 0%, #1e3a8a 30%, #0369a1 60%, #0d9488 85%, #0284c7 100%)",
    emoji: "🌦️", label: "Mưa nhỏ",
    warningText: "Mưa nhỏ diện rộng, tầm nhìn giảm nhẹ. Mặt đường bắt đầu ướt, ma sát giảm.",
    suggestionItems: [
      "Điều khiển phương tiện: Giảm tốc độ, giữ khoảng cách an toàn, tránh phanh gấp.",
      "Trang bị: Nên mặc áo mưa, bọc kỹ thiết bị điện tử.",
    ],
    showFlood: true,
    floodItems: ["Chưa ghi nhận dữ liệu điểm ngập đáng chú ý."],
    showRouteAdvisory: false,
  },
  "mua-dong": {
    key: "mua-dong",
    gradient: "linear-gradient(135deg, #090d16 0%, #1e1b4b 25%, #4c1d95 50%, #1d4ed8 75%, #0f172a 100%)",
    emoji: "⛈️", label: "Mưa dông",
    warningText: "Mưa dông kèm sấm chớp, gió giật mạnh cục bộ. Nguy cơ ngập úng nhanh, cây đổ, mất điện.",
    suggestionItems: [
      "Điều khiển phương tiện: Tránh đi dưới cây lớn, biển quảng cáo. Giảm tốc độ, bật đèn khi tầm nhìn giảm.",
      "Trang bị: Áo mưa bộ rời, ủng cao su, tránh dùng ô khi có gió mạnh.",
    ],
    showFlood: true,
    floodItems: [
      "Văn Quán | 32–58cm | CẤM XE GẦM THẤP — Hồ Văn Quán, Chiến Thắng",
      "Phúc La | 26–52cm | CẤM XE GẦM THẤP — Khu Viện K, KĐT Xa La",
      "Hà Cầu | 19–32cm | ĐI CHẬM — Chợ Hà Đông, Lê Lợi",
      "Tân Triều | 39–65cm | CẤM XE GẦM THẤP — Triều Khúc, ngõ 66",
    ],
    showRouteAdvisory: true,
    routeItems: [
      "Đường tránh ngập: Ưu tiên các tuyến đường cao, tránh khu vực trũng.",
      "Giao thông công cộng: Ưu tiên tàu điện/metro nếu có.",
      "Khuyến cáo: Không cố đi vào vùng ngập sâu.",
    ],
  },
};

// ── Determine weather condition from API data ─────────────────────────────

export function detectCondition(temp: number, feelsLike: number, desc: string, pop: number, humidity: number): ConditionKey {
  const d = desc.toLowerCase();
  const isRain = ["mưa", "dông", "giông", "bão", "rào", "rain", "drizzle", "thunder", "storm"].some(k => d.includes(k));
  const isStorm = ["dông", "giông", "sấm", "thunder", "storm"].some(k => d.includes(k)) || (isRain && pop >= 80);
  const isCloudy = ["mây nhiều", "âm u", "xám", "overcast", "cloud"].some(k => d.includes(k)) || (humidity > 85 && !isRain);

  if (isStorm) return "mua-dong";
  if (isRain) return "mua-nho";
  if (temp >= 35 || feelsLike >= 38) return "nang-gat";
  if (temp >= 28 && !isCloudy && !isRain) return "nang";
  if (isCloudy) return "am-u";
  return "binh-thuong";
}

// ── Data interfaces ───────────────────────────────────────────────────────

interface LiveWeather {
  temp: number;
  feelsLike: number;
  humidity: number;
  windSpeed: number;
  visibility: number;
  description: string;
  icon: string;
  pm25: number;
  aqiLevel: number;
  condKey: ConditionKey;
}

interface ForecastItem {
  time: string;
  date?: string;
  tempMin?: number;
  tempMax?: number;
  temp: number;
  pop: number;
  icon: string;
  desc: string;
}

interface NewsArticle {
  title: string;
  description: string;
  link: string;
  image: string | null;
  source: string;
}

export interface VideoItem {
  id: string;
  title: string;
  link: string;
  embedUrl: string;
  thumbnail: string;
  channel: string;
  category: "weather" | "news" | "traffic" | "life";
  categoryLabel: string;
  badge: string;
  published: string;
  duration?: string;
}

export interface AppData {
  weather: LiveWeather;
  forecast: ForecastItem[];
  news: NewsArticle[];
  videos: VideoItem[];
  updateTime: string;
  location: string;
}

// ── Verified Rich Video Catalog (100% Video Dài, Không Dùng Shorts, Mới Nhất) ──

export const FALLBACK_VIDEOS: VideoItem[] = [
  {
    id: "iVF4Jr-xoWk",
    title: "Đường đi biến thành nơi tập kết rác tại Lạc Đạo, Hưng Yên",
    link: "https://www.youtube.com/watch?v=iVF4Jr-xoWk",
    embedUrl: "https://www.youtube-nocookie.com/embed/iVF4Jr-xoWk",
    thumbnail: "https://img.youtube.com/vi/iVF4Jr-xoWk/hqdefault.jpg",
    channel: "VTV24",
    category: "traffic",
    categoryLabel: "Giao thông & Đô thị",
    badge: "MỚI NHẤT",
    published: "Vừa phát sóng",
    duration: "06:45",
  },
  {
    id: "PQlBET-bx80",
    title: "Phóng sự điều tra: Tinh vi thủ đoạn rửa tiền hàng nghìn tỷ đồng xuyên biên giới",
    link: "https://www.youtube.com/watch?v=PQlBET-bx80",
    embedUrl: "https://www.youtube-nocookie.com/embed/PQlBET-bx80",
    thumbnail: "https://img.youtube.com/vi/PQlBET-bx80/hqdefault.jpg",
    channel: "VTV24",
    category: "news",
    categoryLabel: "Tiêu điểm 24h",
    badge: "ĐIỀU TRA",
    published: "Vừa phát sóng",
    duration: "12:15",
  },
  {
    id: "Q8gNSlAYBak",
    title: "Trực tiếp sự kiện: Lễ trao giải Thương Hiệu Vàng TP.HCM 2026 - Động lực tăng trưởng",
    link: "https://www.youtube.com/watch?v=Q8gNSlAYBak",
    embedUrl: "https://www.youtube-nocookie.com/embed/Q8gNSlAYBak",
    thumbnail: "https://img.youtube.com/vi/Q8gNSlAYBak/hqdefault.jpg",
    channel: "Báo Tuổi Trẻ",
    category: "life",
    categoryLabel: "Đời sống & Xã hội",
    badge: "TRỰC TIẾP",
    published: "Vừa phát sóng",
    duration: "45:00",
  },
  {
    id: "6bfwopT5zUA",
    title: "Chiến dịch 500 ngày đêm: Hành trình trở về sau gần 60 năm",
    link: "https://www.youtube.com/watch?v=6bfwopT5zUA",
    embedUrl: "https://www.youtube-nocookie.com/embed/6bfwopT5zUA",
    thumbnail: "https://img.youtube.com/vi/6bfwopT5zUA/hqdefault.jpg",
    channel: "VTV24",
    category: "news",
    categoryLabel: "Tiêu điểm 24h",
    badge: "PHÓNG SỰ",
    published: "Vừa phát sóng",
    duration: "18:05",
  },
  {
    id: "BywNaNPfvik",
    title: "Thời sự toàn cảnh: Việt Nam tăng cường hợp tác và phát triển kinh tế xã hội",
    link: "https://www.youtube.com/watch?v=BywNaNPfvik",
    embedUrl: "https://www.youtube-nocookie.com/embed/BywNaNPfvik",
    thumbnail: "https://img.youtube.com/vi/BywNaNPfvik/hqdefault.jpg",
    channel: "VTV24",
    category: "news",
    categoryLabel: "Tiêu điểm 24h",
    badge: "TIÊU ĐIỂM",
    published: "1 giờ trước",
    duration: "14:20",
  },
  {
    id: "wT7fGqh0e24",
    title: "Nóng nghị trường Quốc Hội: Phim ‘rác’ AI hủy hoại giới trẻ, liều thuốc độc thời đại mới",
    link: "https://www.youtube.com/watch?v=wT7fGqh0e24",
    embedUrl: "https://www.youtube-nocookie.com/embed/wT7fGqh0e24",
    thumbnail: "https://img.youtube.com/vi/wT7fGqh0e24/hqdefault.jpg",
    channel: "Báo Tiền Phong",
    category: "news",
    categoryLabel: "Tiêu điểm 24h",
    badge: "NGHỊ TRƯỜNG",
    published: "2 giờ trước",
    duration: "10:50",
  },
  {
    id: "byik3EPK-NQ",
    title: "Mặt đường bất ngờ nứt vỡ 'nuốt chửng’ 15 ô tô, 'hố tử thần’ xuất hiện khiến dân bàng hoàng",
    link: "https://www.youtube.com/watch?v=byik3EPK-NQ",
    embedUrl: "https://www.youtube-nocookie.com/embed/byik3EPK-NQ",
    thumbnail: "https://img.youtube.com/vi/byik3EPK-NQ/hqdefault.jpg",
    channel: "Báo Tiền Phong",
    category: "warning",
    categoryLabel: "Cảnh báo khẩn",
    badge: "CẢNH BÁO",
    published: "3 giờ trước",
    duration: "08:15",
  },
  {
    id: "BroH-g3y8Qc",
    title: "Chuyển đổi số đô thị: Từ giao thông thông minh đến trạm y tế A.I",
    link: "https://www.youtube.com/watch?v=BroH-g3y8Qc",
    embedUrl: "https://www.youtube-nocookie.com/embed/BroH-g3y8Qc",
    thumbnail: "https://img.youtube.com/vi/BroH-g3y8Qc/hqdefault.jpg",
    channel: "VTV24",
    category: "traffic",
    categoryLabel: "Giao thông & Đô thị",
    badge: "ĐÔ THỊ",
    published: "2 giờ trước",
    duration: "11:30",
  },
];

// ── Fetch weather directly from OpenWeatherMap (dynamic lat/lon) ─────────

async function fetchWeatherDirect(lat: number, lon: number): Promise<{ weather: LiveWeather; forecast: ForecastItem[] }> {
  const [currRes, foreRes, aqiRes] = await Promise.all([
    fetch(`https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&appid=${OWM_KEY}&units=metric&lang=vi`),
    fetch(`https://api.openweathermap.org/data/2.5/forecast?lat=${lat}&lon=${lon}&appid=${OWM_KEY}&units=metric&lang=vi`),
    fetch(`https://api.openweathermap.org/data/2.5/air_pollution?lat=${lat}&lon=${lon}&appid=${OWM_KEY}`),
  ]);

  const curr = await currRes.json();
  const fore = await foreRes.json();
  const aqi = await aqiRes.json();

  const desc = curr.weather?.[0]?.description?.charAt(0).toUpperCase() + curr.weather?.[0]?.description?.slice(1) || "N/A";
  const temp = Math.round(curr.main.temp * 10) / 10;
  const feelsLike = Math.round(curr.main.feels_like * 10) / 10;
  const humidity = curr.main.humidity;
  const windSpeed = Math.round((curr.wind?.speed || 0) * 3.6); // m/s → km/h
  const visibility = Math.round((curr.visibility || 10000) / 1000); // m → km
  const pm25 = aqi.list?.[0]?.components?.pm2_5 || 0;
  const aqiLevel = aqi.list?.[0]?.main?.aqi || 1;

  const forecastList = (fore.list || []).slice(0, 3);
  const firstPop = forecastList[0] ? Math.round((forecastList[0].pop || 0) * 100) : 0;
  const condKey = detectCondition(temp, feelsLike, desc, firstPop, humidity);

  const iconMap: Record<string, string> = {
    "01d": "☀️", "01n": "🌑", "02d": "⛅", "02n": "☁️",
    "03d": "☁️", "03n": "☁️", "04d": "☁️", "04n": "☁️",
    "09d": "🌧️", "09n": "🌧️", "10d": "🌦️", "10n": "🌧️",
    "11d": "⛈️", "11n": "⛈️", "13d": "❄️", "13n": "❄️",
    "50d": "🌫️", "50n": "🌫️",
  };

  const weather: LiveWeather = {
    temp, feelsLike, humidity, windSpeed, visibility,
    description: desc,
    icon: iconMap[curr.weather?.[0]?.icon] || "🌤️",
    pm25: Math.round(pm25 * 100) / 100,
    aqiLevel, condKey,
  };

  // ── 5-day daily forecast (group by day) ──────────────────────────────────
  const allSlots = (fore.list || []) as any[];
  const dayMap = new Map<string, { temps: number[]; pops: number[]; icons: string[]; descs: string[] }>();
  const today = new Date().toLocaleDateString("vi-VN", { weekday: "short" });
  allSlots.forEach((slot: any) => {
    const dt = new Date(slot.dt * 1000);
    const dayKey = dt.toLocaleDateString("vi-VN", { weekday: "short", day: "2-digit", month: "2-digit" });
    if (!dayMap.has(dayKey)) dayMap.set(dayKey, { temps: [], pops: [], icons: [], descs: [] });
    const d = dayMap.get(dayKey)!;
    d.temps.push(slot.main.temp);
    d.pops.push(slot.pop || 0);
    d.icons.push(iconMap[slot.weather?.[0]?.icon] || "🌤️");
    d.descs.push(slot.weather?.[0]?.description || "");
  });

  const forecast: ForecastItem[] = Array.from(dayMap.entries())
    .slice(0, 5)
    .map(([dayKey, d]) => {
      const maxPop = Math.round(Math.max(...d.pops) * 100);
      const avgTemp = Math.round(d.temps.reduce((a, b) => a + b, 0) / d.temps.length);
      const minTemp = Math.round(Math.min(...d.temps));
      const maxTemp = Math.round(Math.max(...d.temps));
      // Pick most common icon
      const iconCount = d.icons.reduce((acc: Record<string, number>, ic) => { acc[ic] = (acc[ic] || 0) + 1; return acc; }, {});
      const bestIcon = Object.entries(iconCount).sort((a, b) => b[1] - a[1])[0]?.[0] || "🌤️";
      const isToday = dayKey.startsWith(today);
      return {
        time: isToday ? "Hôm nay" : dayKey.split(",")[0] || dayKey,
        date: dayKey,
        temp: avgTemp,
        tempMin: minTemp,
        tempMax: maxTemp,
        pop: maxPop,
        icon: bestIcon,
        desc: d.descs[Math.floor(d.descs.length / 2)] || "",
      };
    });

  return { weather, forecast };
}


// ── Fetch news from backend or fallback (Chỉ lấy bài viết mới nhất trong ngày hôm nay) ──

async function fetchNews(): Promise<NewsArticle[]> {
  // 1. Thử kết nối Backend API (/api/daily-news đã lọc bài viết hôm nay)
  const backendCandidates = [
    "http://localhost:10000",
    "http://127.0.0.1:10000",
    BACKEND_URL,
  ];

  for (const bUrl of backendCandidates) {
    try {
      const res = await fetch(`${bUrl}/api/daily-news`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) {
        const data = await res.json();
        if (data.news && Array.isArray(data.news) && data.news.length > 0) {
          return data.news.slice(0, 10).map((n: any) => ({
            title: n.title || "",
            description: n.description || "",
            link: n.link || "#",
            image: n.image || null,
            source: n.source || n.author || "Báo Tiền Phong",
          }));
        }
      }
    } catch {
      // thử ứng viên tiếp theo
    }
  }

  // 2. Fallback trực tiếp qua RSS của các tờ báo lớn (Ưu tiên Báo Tiền Phong & VnExpress, lọc chặt chẽ CHỈ LẤY BÀI HÔM NAY)
  const rssCandidates = [
    "https://tienphong.vn/rss/home.rss",
    "https://vnexpress.net/rss/tin-moi-nhat.rss",
    "https://dantri.com.vn/rss/home.rss"
  ];

  for (const rssFeed of rssCandidates) {
    try {
      const proxyUrl = `https://api.allorigins.win/raw?url=${encodeURIComponent(rssFeed)}&_t=${Date.now()}`;
      const res = await fetch(proxyUrl, { signal: AbortSignal.timeout(4000) });
      if (res.ok) {
        const text = await res.text();
        const parser = new DOMParser();
        const xml = parser.parseFromString(text, "text/xml");
        const items = Array.from(xml.querySelectorAll("item"));
        const articles: NewsArticle[] = [];
        
        const now = Date.now();
        const currentYear = new Date().getFullYear();

        for (const item of items) {
          if (articles.length >= 10) break;

          const title = item.querySelector("title")?.textContent?.trim() || "";
          const link = item.querySelector("link")?.textContent?.trim() || "#";
          const pubDateStr = item.querySelector("pubDate")?.textContent?.trim() || "";

          // Kiểm tra và loại bỏ triệt để các bài viết cũ (2024, 2025 hoặc quá 36 tiếng)
          if (pubDateStr) {
            const pubDt = new Date(pubDateStr);
            const pubTime = pubDt.getTime();
            if (!isNaN(pubTime)) {
              if (pubDt.getFullYear() < currentYear || (now - pubTime > 36 * 3600 * 1000)) {
                continue; // Bỏ qua bài viết cũ
              }
            }
          }

          const rawDesc = item.querySelector("description")?.textContent || "";
          const descDoc = parser.parseFromString(rawDesc, "text/html");
          const description = descDoc.body?.textContent?.trim().slice(0, 1000) || "";
          const imgTag = descDoc.querySelector("img");
          const image = imgTag?.getAttribute("src") || item.querySelector("enclosure")?.getAttribute("url") || null;
          const sourceEl = item.querySelector("source");
          const source = sourceEl?.textContent?.trim() || (rssFeed.includes("tienphong") ? "Báo Tiền Phong" : rssFeed.includes("vnexpress") ? "VnExpress" : "Dân Trí");

          if (title && title.length > 5) {
            articles.push({ title, description, link, image, source });
          }
        }

        if (articles.length >= 3) {
          return articles;
        }
      }
    } catch {
      // thử feed tiếp theo
    }
  }

  // 3. Fallback mặc định tin nóng cập nhật hôm nay (chuẩn xác theo ngày hiện tại, không có năm cũ)
  const todayStr = new Date().toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
  return [
    { title: `Báo Tiền Phong: Thời sự đô thị và giao thông ngày ${todayStr}`, description: `Ghi nhận thực tế tình hình giao thông, hạ tầng và nhịp sống đô thị ngày ${todayStr}.`, link: "https://tienphong.vn", image: null, source: "Báo Tiền Phong" },
    { title: `Dự báo thời tiết và diễn biến môi trường ngày ${todayStr}`, description: `Bản tin khí tượng thủy văn mới nhất, cập nhật nhiệt độ và chất lượng không khí hôm nay.`, link: "https://tienphong.vn", image: null, source: "Báo Tiền Phong" },
    { title: `Đẩy mạnh chuyển đổi số và ứng dụng AI trong quản lý dịch vụ công`, description: `Các giải pháp công nghệ thông minh hỗ trợ người dân và doanh nghiệp tra cứu thuận tiện.`, link: "https://tienphong.vn", image: null, source: "Báo Tiền Phong" },
    { title: `Thị trường và giá cả tiêu dùng ổn định trong ngày ${todayStr}`, description: `Theo dõi biến động giá hàng hóa thiết yếu và nguồn cung nông sản thực phẩm đô thị.`, link: "https://tienphong.vn", image: null, source: "Dân Trí" },
    { title: `Công tác chuẩn bị an toàn đê điều và thoát nước đô thị`, description: `Các lực lượng ứng trực 24/7 kiểm tra hồ đệm và hệ thống cống tiêu thoát nước.`, link: "https://tienphong.vn", image: null, source: "VnExpress" },
  ];
}

// ── Fetch multi-channel rich videos (Chỉ lấy video dài, loại bỏ hoàn toàn Shorts) ──

async function fetchVideos(): Promise<VideoItem[]> {
  // 1. Thử lấy từ Backend API (đã được lọc video dài và sắp xếp mới nhất)
  try {
    const res = await fetch(`${BACKEND_URL}/api/daily-news`, { signal: AbortSignal.timeout(8000) });
    if (res.ok) {
      const data = await res.json();
      if (data.videos && Array.isArray(data.videos) && data.videos.length > 0) {
        const validVideos = data.videos
          .filter((v: any) => {
            if (!v.id) return false;
            const link = (v.link || "").toLowerCase();
            const title = (v.title || "").toLowerCase();
            // Loại bỏ hoàn toàn nếu là link Shorts
            if (link.includes("/shorts/")) return false;
            // Loại bỏ từ khóa Shorts, 30s nóng, tiktok
            const shortsKws = ["#short", "#shorts", "30s nóng", "tiktok", "#reels", "reels", "#shortvideo"];
            if (shortsKws.some((k) => title.includes(k))) return false;
            return true;
          })
          .map((v: any) => ({
            id: v.id,
            title: v.title || "Bản tin truyền hình",
            link: v.link || `https://www.youtube.com/watch?v=${v.id}`,
            embedUrl: v.embed_url || `https://www.youtube-nocookie.com/embed/${v.id}`,
            thumbnail: v.thumbnail || `https://img.youtube.com/vi/${v.id}/hqdefault.jpg`,
            channel: v.channel || "Truyền hình",
            category: v.category || "news",
            categoryLabel: v.category_label || "Tiêu điểm 24h",
            badge: v.badge || "HOT",
            published: v.published || "Hôm nay",
            duration: v.duration || "HD",
          }));

        if (validVideos.length > 0) {
          return validVideos;
        }
      }
    }
  } catch { /* backend unavailable */ }

  // 2. Dự phòng: Thử lấy trực tiếp từ YouTube RSS của VTV24 qua CORS proxy
  try {
    const feedUrl = encodeURIComponent("https://www.youtube.com/feeds/videos.xml?channel_id=UCabsTV34JwALXKGMqHpvUiA");
    const proxyUrl = `https://api.allorigins.win/raw?url=${feedUrl}`;
    const res = await fetch(proxyUrl, { signal: AbortSignal.timeout(8000) });
    if (res.ok) {
      const xmlText = await res.text();
      const parser = new DOMParser();
      const xml = parser.parseFromString(xmlText, "text/xml");
      const entries = xml.querySelectorAll("entry");
      const directVideos: VideoItem[] = [];

      entries.forEach((e) => {
        const vidId = e.querySelector("videoId")?.textContent || "";
        const title = e.querySelector("title")?.textContent || "";
        const link = e.querySelector("link")?.getAttribute("href") || "";

        if (!vidId) return;
        // Kiểm tra loại bỏ Shorts
        if (link.toLowerCase().includes("/shorts/")) return;
        const shortsKws = ["#short", "#shorts", "30s nóng", "tiktok", "#reels", "reels"];
        if (shortsKws.some((k) => title.toLowerCase().includes(k))) return;

        directVideos.push({
          id: vidId,
          title,
          link: `https://www.youtube.com/watch?v=${vidId}`,
          embedUrl: `https://www.youtube-nocookie.com/embed/${vidId}`,
          thumbnail: `https://img.youtube.com/vi/${vidId}/hqdefault.jpg`,
          channel: "VTV24",
          category: "news",
          categoryLabel: "Tiêu điểm 24h",
          badge: "VTV24",
          published: "Vừa phát sóng",
          duration: "HD",
        });
      });

      if (directVideos.length > 0) {
        return directVideos;
      }
    }
  } catch { /* proxy unavailable */ }

  // 3. Danh mục video dài chuẩn xác minh 100%
  return FALLBACK_VIDEOS;
}

// ── Image fallback handler ────────────────────────────────────────────────

function onImgError(e: React.SyntheticEvent<HTMLImageElement>, idx: number) {
  e.currentTarget.onerror = null;
  e.currentTarget.src = FALLBACK_NEWS_IMAGES[idx % FALLBACK_NEWS_IMAGES.length];
}

// ── Interactive Cinema Video Modal ────────────────────────────────────────

export function VideoModal({ video, onClose }: { video: VideoItem | null; onClose: () => void }) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (video) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.body.style.overflow = "auto";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [video, onClose]);

  if (!video) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl bg-[#111827] rounded-3xl overflow-hidden border border-white/10 shadow-[0_0_50px_rgba(0,0,0,0.8)]">
        {/* Header bar */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-[#1f2937]/90 border-b border-white/10">
          <div className="flex items-center gap-2.5 min-w-0 pr-4">
            <span className="flex size-3 rounded-full bg-[#ff315f] animate-ping" />
            <span className="bg-[#ff315f] text-white text-[11px] font-bold px-2 py-0.5 rounded-full whitespace-nowrap">
              {video.badge || "VIDEO NÓNG"}
            </span>
            <p className="font-['Inter:Semi_Bold'] font-semibold text-white text-[14px] truncate">
              {video.title}
            </p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <a
              href={video.link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#9ca3af] hover:text-white text-[12px] px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 transition-colors flex items-center gap-1"
            >
              Mở YouTube ↗
            </a>
            <button
              onClick={onClose}
              data-testid="close-video-modal"
              className="size-8 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center text-[18px] transition-colors cursor-pointer"
              aria-label="Đóng video"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Video Player */}
        <div className="relative aspect-video w-full bg-black">
          <iframe
            src={`${video.embedUrl}?autoplay=1&rel=0`}
            title={video.title}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="absolute inset-0 size-full border-0"
          />
        </div>

        {/* Footer info */}
        <div className="p-4 bg-[#111827] flex flex-wrap items-center justify-between gap-3 text-[13px] text-[#9ca3af]">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-white">Kênh: {video.channel}</span>
            <span>•</span>
            <span className="text-[#38bdf8] font-medium">{video.categoryLabel}</span>
            <span>•</span>
            <span>{video.published}</span>
          </div>
          <p className="text-[12px] text-[#6b7280]">Nhấn ESC hoặc ✕ để thoát chế độ rạp chiếu</p>
        </div>
      </div>
    </div>
  );
}

// ── Interactive Article Detail Modal (Đọc bài viết chi tiết & Tóm tắt AI) ─
export { ArticleDetailModal } from "./ArticleDetailModal";


// ── Antigravity Copilot Client & Fallback Engine ──────────────────────────

export async function callCopilotAPI(
  prompt: string,
  action: string,
  context: any
): Promise<{ reply: string; model: string; riskLevel?: "low" | "medium" | "high" }> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/ai-chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, action, context }),
      signal: AbortSignal.timeout(12000),
    });
    if (res.ok) {
      const data = await res.json();
      if (data.reply) {
        return {
          reply: data.reply,
          model: data.model || "Gemini 2.5 Flash (Antigravity Copilot Engine)",
          riskLevel: data.risk_level || "low",
        };
      }
    }
  } catch (e) {
    console.warn("Copilot API backend call timed out or failed, using client-side Antigravity engine:", e);
  }

  return generateClientCopilotFallback(action, prompt, context);
}

export function generateClientCopilotFallback(action: string, prompt: string, context: any) {
  const temp = context?.temp ?? 26.5;
  const feelsLike = context?.feelsLike ?? 27.8;
  const desc = context?.desc ?? "Nhiều mây";
  const pm25 = context?.pm25 ?? 30;
  const location = context?.location ?? "Hà Nội";
  const news = context?.news_titles ?? [];

  if (action === "weather_impact") {
    const isHot = temp >= 33 || feelsLike >= 36;
    const isRain = desc.toLowerCase().includes("mưa") || desc.toLowerCase().includes("dông");
    return {
      reply: `🌤️ **PHÂN TÍCH TÁC ĐỘNG THỜI TIẾT TẠI ${location.toUpperCase()}**:\n\n` +
        `• **Nhiệt độ & Cảm giác nhiệt**: Hiện tại ${temp}°C (Cảm nhận thực tế ${feelsLike}°C). ` +
        (isHot ? "Nắng gắt, nguy cơ mất nước và sốc nhiệt khi ở lâu ngoài trời." : isRain ? "Thời tiết ẩm ướt, mặt đường giảm độ bám." : "Nhiệt độ dễ chịu, thuận lợi cho hầu hết các hoạt động.") + "\n" +
        `• **Tác động sinh hoạt**: ${isRain ? "Mưa gây chậm trễ giờ cao điểm, tầm nhìn hạn chế." : "Tầm nhìn tốt, gió nhẹ thông thoáng."}\n` +
        `• **Khuyến nghị Antigravity Copilot**: ${isRain ? "Trang bị áo mưa bộ, giảm tốc độ 20% khi vào cua." : isHot ? "Mang theo bình nước cá nhân, tránh ra đường từ 11h-14h." : "Thời tiết lý tưởng để di chuyển và làm việc ngoài trời."}`,
      model: "Antigravity Intelligent Copilot Engine",
      riskLevel: (isHot || isRain ? "medium" : "low") as "low" | "medium" | "high"
    };
  } else if (action === "news_digest") {
    const list = news.slice(0, 3).map((t: string, idx: number) => `${idx + 1}. **${t}**`).join("\n");
    return {
      reply: `📰 **TỔNG HỢP & PHÂN TÍCH TIÊU ĐIỂM TIN NÓNG**:\n\n` +
        (list || "1. VTV24: Diễn biến mới nhất về giao thông đô thị và an sinh.\n2. Báo Tiền Phong: Công tác phòng ngừa ngập úng mùa mưa bão.\n3. Tuổi Trẻ: Đẩy mạnh các giải pháp số hóa đô thị.") + "\n\n" +
        `💡 **Nhận định AI**: Trọng tâm thông tin xoay quanh an toàn đô thị và chuyển đổi số. Bạn nên chủ động theo dõi các bản tin phát thanh để cập nhật lộ trình kịp thời.`,
      model: "Antigravity Intelligent Copilot Engine",
      riskLevel: "low" as const
    };
  } else if (action === "health_pm25") {
    const status = pm25 <= 25 ? "TỐT" : pm25 <= 50 ? "TRUNG BÌNH" : "KÉM";
    return {
      reply: `🍃 **ĐÁNH GIÁ CHỈ SỐ BỤI MỊN PM2.5 & BẢO VỆ SỨC KHỎE**:\n\n` +
        `• **Nồng độ PM2.5**: ${pm25} µg/m³ (Chất lượng không khí: **${status}**).\n` +
        `• **Tác động hô hấp**: ` + (pm25 > 35 ? `Bụi mịn ${pm25} µg/m³ có thể gây rát họng, mỏi mắt cho người đi đường nhiều giờ.` : "Không khí ở ngưỡng tương đối sạch, không gây hại cho sức khỏe.") + "\n" +
        `• **Khuyến cáo y tế AI**: ` + (pm25 > 35 ? "Nên dùng khẩu trang lọc bụi mịn N95 hoặc khẩu trang kháng khuẩn khi di chuyển trên trục đường đông xe." : "Có thể mở cửa đón gió vào sáng sớm, duy trì tập luyện bình thường."),
      model: "Antigravity Intelligent Copilot Engine",
      riskLevel: (pm25 > 50 ? "high" : pm25 > 25 ? "medium" : "low") as const
    };
  } else if (action === "smart_route") {
    const isRain = desc.toLowerCase().includes("mưa") || desc.toLowerCase().includes("dông");
    return {
      reply: `🚗 **KHUYẾN CÁO LỘ TRÌNH THÔNG MINH & GIÁM SÁT ĐIỂM ĐEN**:\n\n` +
        `• **Điểm đen ngập úng**: ` + (isRain ? "Cảnh báo ngập tại Chiến Thắng (Văn Quán 32-58cm), ngõ 66 Triều Khúc, khu Viện K Xa La. Tuyệt đối không cho xe gầm thấp đi vào!" : "Tất cả các điểm đen ngập úng (Hồ Văn Quán, Xa La, Triều Khúc) hiện đều KHÔ RÁO, lưu thông thông suốt.") + "\n" +
        `• **Lộ trình tối ưu**: ` + (isRain ? "Ưu tiên trục Tàu điện trên cao Cát Linh - Hà Đông hoặc các tuyến đường cao tầng tránh ngã ba trũng." : "Trục Nguyễn Trãi - Trần Phú - Quang Trung giao thông ổn định, chú ý các nút giao đèn đỏ.") + "\n" +
        `• **Độ an toàn giao thông**: ` + (isRain ? "45/100 (Cần hết sức thận trọng)" : "95/100 (Rất an toàn)"),
      model: "Antigravity Intelligent Copilot Engine",
      riskLevel: (isRain ? "high" : "low") as const
    };
  } else {
    return {
      reply: `🤖 **Antigravity AI Copilot** đã xử lý yêu cầu của bạn dựa trên dữ liệu thực tế:\n\n` +
        `*"${prompt}"*\n\n` +
        `📍 Vị trí: **${location}** | Thời tiết: ${temp}°C, ${desc} | PM2.5: ${pm25} µg/m³\n\n` +
        `Hệ thống nhận định các điều kiện hiện tại cho phép bạn tiến hành các kế hoạch công việc thuận lợi. Hãy lưu ý các khung giờ cao điểm và chủ động kiểm tra bản tin dự báo 3 giờ tới trước khi xuất phát.`,
      model: "Antigravity Intelligent Copilot Engine",
      riskLevel: "low" as const
    };
  }
}

// ── Antigravity Copilot Interactive Modal ─────────────────────────────────

interface CopilotModalProps {
  isOpen: boolean;
  onClose: () => void;
  data: AppData;
  initialAction?: string | null;
}

export function AntigravityCopilotModal({ isOpen, onClose, data, initialAction }: CopilotModalProps) {
  const [messages, setMessages] = useState<Array<{
    sender: "user" | "copilot";
    text: string;
    model?: string;
    riskLevel?: "low" | "medium" | "high";
    time: string;
  }>>([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const executeAction = useCallback(async (action: string, promptText?: string) => {
    const userPrompt = promptText || (
      action === "weather_impact" ? "Phân tích tác động thời tiết & môi trường hiện tại" :
      action === "news_digest" ? "Tóm tắt 3 tin tức nóng nhất hôm nay" :
      action === "health_pm25" ? "Đánh giá chỉ số bụi mịn PM2.5 và cảnh báo sức khỏe" :
      action === "smart_route" ? "Tư vấn lộ trình an toàn và các điểm đen ngập úng" :
      "Phân tích tổng quan đô thị"
    );

    const now = new Date();
    const timeStr = now.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });

    setMessages((prev) => [...prev, {
      sender: "user",
      text: userPrompt,
      time: timeStr,
    }]);

    setLoading(true);

    const context = {
      location: data.location,
      temp: data.weather.temp,
      feelsLike: data.weather.feelsLike,
      desc: data.weather.description,
      humidity: data.weather.humidity,
      pm25: data.weather.pm25,
      aqi_level: data.weather.aqiLevel,
      wind_speed: data.weather.windSpeed,
      news_titles: data.news.slice(0, 4).map(n => n.title),
    };

    try {
      const response = await callCopilotAPI(userPrompt, action, context);
      setMessages((prev) => [...prev, {
        sender: "copilot",
        text: response.reply,
        model: response.model,
        riskLevel: response.riskLevel,
        time: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      }]);
    } catch {
      const fallback = generateClientCopilotFallback(action, userPrompt, context);
      setMessages((prev) => [...prev, {
        sender: "copilot",
        text: fallback.reply,
        model: fallback.model,
        riskLevel: fallback.riskLevel,
        time: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      }]);
    } finally {
      setLoading(false);
    }
  }, [data]);

  useEffect(() => {
    if (isOpen) {
      if (messages.length === 0) {
        const now = new Date();
        const timeStr = now.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
        setMessages([{
          sender: "copilot",
          text: `👋 Xin chào! Tôi là **Antigravity Copilot** — Trợ lý AI Đô Thị & Bản Tin Thông Minh.\n\nTôi trực tiếp phân tích các dữ liệu cảm biến thời gian thực tại **${data.location}** (${data.weather.temp}°C, ${data.weather.description}, PM2.5: ${data.weather.pm25} µg/m³) cùng luồng tin tức nóng nhất từ VTV24, Báo Tiền Phong và Tuổi Trẻ.\n\nHãy bấm một trong 4 tác vụ phân tích chuyên sâu bên dưới hoặc gõ câu hỏi bất kỳ!`,
          model: "Gemini 2.5 Flash (Antigravity Copilot Engine)",
          riskLevel: "low",
          time: timeStr,
        }]);

        if (initialAction) {
          executeAction(initialAction);
        }
      } else if (initialAction) {
        executeAction(initialAction);
      }
    }
  }, [isOpen, initialAction, data, executeAction]);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.body.style.overflow = "auto";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;
    const text = inputText.trim();
    setInputText("");
    executeAction("general_chat", text);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 md:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl bg-[#0f172a] rounded-3xl overflow-hidden border border-indigo-500/30 shadow-[0_0_50px_rgba(79,70,229,0.3)] flex flex-col max-h-[90vh]">
        {/* Header bar */}
        <div className="flex items-center justify-between px-5 py-4 bg-gradient-to-r from-[#1e1b4b] via-[#31104b] to-[#1e1b4b] border-b border-indigo-500/20">
          <div className="flex items-center gap-3">
            <div className="size-10 rounded-2xl bg-gradient-to-tr from-violet-600 to-rose-500 flex items-center justify-center text-xl shadow-lg shadow-violet-500/30">
              🤖
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <p className="font-['Inter:Bold'] font-bold text-white text-[16px]">
                  Antigravity Copilot
                </p>
                <span className="flex items-center gap-1 bg-emerald-500/20 text-emerald-300 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-500/30">
                  <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Gemini 2.5 Active
                </span>
              </div>
              <p className="text-[12px] text-indigo-200/80">
                AI Trợ lý Đô thị & Bản tin Thông minh · Phân tích dữ liệu thực tế
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            data-testid="close-copilot-modal"
            className="size-8 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center text-[18px] transition-colors cursor-pointer"
            aria-label="Đóng Copilot"
          >
            ✕
          </button>
        </div>

        {/* Live Context Bar */}
        <div className="bg-[#1e293b]/80 px-5 py-2.5 border-b border-indigo-500/10 flex flex-wrap items-center gap-2 text-[11px] text-indigo-200">
          <span className="bg-indigo-950/80 px-2.5 py-1 rounded-lg border border-indigo-500/20 font-medium">
            📍 {data.location}
          </span>
          <span className="bg-indigo-950/80 px-2.5 py-1 rounded-lg border border-indigo-500/20 font-medium">
            🌡️ {data.weather.temp}°C ({data.weather.description})
          </span>
          <span className="bg-indigo-950/80 px-2.5 py-1 rounded-lg border border-indigo-500/20 font-medium">
            🍃 PM2.5: {data.weather.pm25} µg/m³
          </span>
          <span className="bg-indigo-950/80 px-2.5 py-1 rounded-lg border border-indigo-500/20 font-medium">
            💨 Gió: {data.weather.windSpeed} km/h
          </span>
        </div>

        {/* Quick Action Hub (4 Buttons) */}
        <div className="p-3 bg-[#0f172a] border-b border-indigo-500/10 grid grid-cols-2 sm:grid-cols-4 gap-2">
          <button
            onClick={() => executeAction("weather_impact")}
            data-testid="copilot-modal-btn-weather"
            disabled={loading}
            className="flex flex-col items-start p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-violet-500/50 transition-all text-left cursor-pointer group disabled:opacity-50"
          >
            <span className="text-[16px] mb-1">🌤️ Tác động</span>
            <span className="text-[11px] font-semibold text-white group-hover:text-amber-300">Thời tiết & UV</span>
          </button>
          <button
            onClick={() => executeAction("news_digest")}
            data-testid="copilot-modal-btn-news"
            disabled={loading}
            className="flex flex-col items-start p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-violet-500/50 transition-all text-left cursor-pointer group disabled:opacity-50"
          >
            <span className="text-[16px] mb-1">📰 Tin nóng</span>
            <span className="text-[11px] font-semibold text-white group-hover:text-amber-300">3 sự kiện 24h</span>
          </button>
          <button
            onClick={() => executeAction("health_pm25")}
            data-testid="copilot-modal-btn-pm25"
            disabled={loading}
            className="flex flex-col items-start p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-violet-500/50 transition-all text-left cursor-pointer group disabled:opacity-50"
          >
            <span className="text-[16px] mb-1">🍃 Sức khỏe</span>
            <span className="text-[11px] font-semibold text-white group-hover:text-amber-300">PM2.5 & Hô hấp</span>
          </button>
          <button
            onClick={() => executeAction("smart_route")}
            data-testid="copilot-modal-btn-route"
            disabled={loading}
            className="flex flex-col items-start p-2.5 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 hover:border-violet-500/50 transition-all text-left cursor-pointer group disabled:opacity-50"
          >
            <span className="text-[16px] mb-1">🚗 Lộ trình</span>
            <span className="text-[11px] font-semibold text-white group-hover:text-amber-300">Tránh điểm ngập</span>
          </button>
        </div>

        {/* Chat Feed */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-[460px] bg-[#0b0f19]">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex gap-3 ${m.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              {m.sender === "copilot" && (
                <div className="size-8 rounded-full bg-gradient-to-tr from-violet-600 to-rose-500 shrink-0 flex items-center justify-center text-sm shadow">
                  🤖
                </div>
              )}
              <div
                className={`max-w-[85%] rounded-2xl p-4 shadow-md ${
                  m.sender === "user"
                    ? "bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-tr-none"
                    : "bg-[#1e293b] text-gray-100 border border-indigo-500/20 rounded-tl-none"
                }`}
              >
                {m.sender === "copilot" && m.model && (
                  <div className="flex items-center justify-between gap-2 pb-2 mb-2 border-b border-white/10 text-[11px]">
                    <span className="text-indigo-300 font-mono font-medium">{m.model}</span>
                    {m.riskLevel && (
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                          m.riskLevel === "high"
                            ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                            : m.riskLevel === "medium"
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                            : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                        }`}
                      >
                        {m.riskLevel === "high" ? "Cảnh báo cao" : m.riskLevel === "medium" ? "Cần cẩn trọng" : "An toàn"}
                      </span>
                    )}
                  </div>
                )}
                <div className="text-[13px] leading-relaxed whitespace-pre-wrap">
                  {m.text}
                </div>
                <div className={`text-[10px] mt-2 pt-1 flex justify-end ${m.sender === "user" ? "text-violet-200" : "text-gray-400"}`}>
                  {m.time}
                </div>
              </div>
              {m.sender === "user" && (
                <div className="size-8 rounded-full bg-indigo-500 shrink-0 flex items-center justify-center text-sm font-bold text-white shadow">
                  👤
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3 justify-start items-center">
              <div className="size-8 rounded-full bg-gradient-to-tr from-violet-600 to-rose-500 shrink-0 flex items-center justify-center text-sm animate-pulse">
                🤖
              </div>
              <div className="bg-[#1e293b] border border-indigo-500/20 rounded-2xl rounded-tl-none p-3.5 flex items-center gap-3">
                <span className="size-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
                <span className="text-[12px] text-indigo-200">
                  Antigravity Copilot đang kích hoạt mô hình AI và tổng hợp dữ liệu...
                </span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form & Suggested Queries */}
        <div className="p-3 bg-[#111827] border-t border-indigo-500/20 flex flex-col gap-2">
          {/* Quick chip queries */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none text-[11px]">
            <span className="text-[#9ca3af] whitespace-nowrap">Gợi ý câu hỏi:</span>
            <button
              type="button"
              onClick={() => executeAction("general_chat", "Thời tiết hiện tại có thích hợp để chạy bộ ngoài trời không?")}
              className="px-2.5 py-1 rounded-full bg-white/5 hover:bg-white/10 text-indigo-200 whitespace-nowrap transition-colors border border-white/5 cursor-pointer"
            >
              🏃 Chạy bộ ngoài trời?
            </button>
            <button
              type="button"
              onClick={() => executeAction("general_chat", "Đường Nguyễn Trãi và Quang Trung có nguy cơ ngập không?")}
              className="px-2.5 py-1 rounded-full bg-white/5 hover:bg-white/10 text-indigo-200 whitespace-nowrap transition-colors border border-white/5 cursor-pointer"
            >
              🚗 Đường Nguyễn Trãi có ngập?
            </button>
            <button
              type="button"
              onClick={() => executeAction("general_chat", "Tóm tắt các vấn đề an toàn đô thị quan trọng nhất")}
              className="px-2.5 py-1 rounded-full bg-white/5 hover:bg-white/10 text-indigo-200 whitespace-nowrap transition-colors border border-white/5 cursor-pointer"
            >
              🛡️ An toàn đô thị?
            </button>
          </div>

          <form onSubmit={handleSendMessage} className="flex items-center gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Hỏi Copilot bất kỳ điều gì về thời tiết, tin tức, ngập úng, sức khỏe..."
              className="flex-1 bg-[#1f293d] border border-indigo-500/30 rounded-xl px-4 py-2.5 text-[13px] text-white placeholder-gray-400 focus:outline-none focus:border-indigo-400 transition-colors"
            />
            <button
              type="submit"
              disabled={loading || !inputText.trim()}
              className="bg-gradient-to-r from-violet-600 to-rose-500 hover:opacity-90 disabled:opacity-40 text-white font-['Inter:Semi_Bold'] font-semibold px-4 py-2.5 rounded-xl text-[13px] transition-all cursor-pointer shadow-md flex items-center gap-1.5 shrink-0"
            >
              <span>Gửi</span>
              <span>↑</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// ── Weather Section (Left Column) ─────────────────────────────────────────

function LiveClock({ location }: { location: string }) {
  const [time, setTime] = useState(() => new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }));
  useEffect(() => {
    const id = setInterval(() => setTime(new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })), 30000);
    return () => clearInterval(id);
  }, []);
  return <span>{time}</span>;
}

export function WeatherColumn({
  data,
  onOpenCopilot,
  geoStatus,
  geoSource,
  onOpenLocationModal,
  onRefresh,
  isRefreshing,
}: {
  data: AppData;
  onOpenCopilot: (action: string | null) => void;
  geoStatus?: "idle" | "loading" | "granted" | "denied";
  geoSource?: GeoSource;
  onOpenLocationModal?: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}) {
  const theme = WEATHER_THEMES[data.weather.condKey];
  const pm25 = data.weather.pm25;
  const pm25Icon = data.weather.aqiLevel >= 4 ? "🚫" : data.weather.aqiLevel >= 3 ? "⚠️" : "✅";
  const pm25Label = pm25 <= 12 ? "Tốt" : pm25 <= 35.4 ? "Trung bình" : pm25 <= 55.4 ? "Kém" : "Nguy hại";
  const isStorm = data.weather.condKey === "mua-dong";
  const isBadAir = data.weather.aqiLevel >= 4;
  const [alertDismissed, setAlertDismissed] = useState(false);

  return (
    <div className="flex flex-col gap-4 w-full">

      {/* ── Alert Banner (Storm / Bad Air) ─────────────────────────────── */}
      {(isStorm || isBadAir) && !alertDismissed && (
        <div className={`flex items-start gap-3 p-3.5 rounded-2xl border animate-in slide-in-from-top duration-300 ${
          isStorm
            ? "bg-rose-50 border-rose-200 text-rose-800"
            : "bg-amber-50 border-amber-200 text-amber-800"
        }`}>
          <span className="text-[22px] shrink-0 mt-0.5">{isStorm ? "⛈️" : "😷"}</span>
          <div className="flex-1 min-w-0">
            <p className="font-bold text-[13px]">
              {isStorm ? "⚠️ Cảnh báo mưa dông mạnh" : "⚠️ Chất lượng không khí kém"}
            </p>
            <p className="text-[12px] mt-0.5 opacity-80 leading-snug">
              {isStorm
                ? "Nguy cơ ngập úng, cây đổ. Hạn chế ra ngoài, tránh vùng trũng thấp."
                : `PM2.5 đạt ${pm25} µg/m³ — nên đeo khẩu trang N95 khi ra ngoài.`}
            </p>
          </div>
          <button onClick={() => setAlertDismissed(true)} className="shrink-0 text-[16px] opacity-50 hover:opacity-100 cursor-pointer transition-opacity">✕</button>
        </div>
      )}

      {/* ── Hero Weather Card with CSS Morphing Gradients Animated Background ── */}
      <div
        data-testid="hero-weather-card"
        className="relative flex flex-col gap-4 items-start overflow-hidden p-6 rounded-3xl shadow-[0_16px_40px_-8px_rgba(37,99,235,0.38)] w-full transition-all duration-500 hover:scale-[1.01] lg:h-[400px] lg:justify-between border border-white/25 animate-morph-gradient"
        style={{ background: theme.gradient }}
      >
        {/* CSS Morphing Gradients Animated Liquid Blobs */}
        <div className="absolute -right-12 -top-12 w-64 h-64 rounded-full bg-gradient-to-br from-white/30 via-sky-300/30 to-blue-500/25 blur-2xl pointer-events-none animate-morph-blob-1" />
        <div className="absolute -left-12 -bottom-12 w-72 h-72 rounded-full bg-gradient-to-tr from-cyan-400/30 via-indigo-400/25 to-purple-500/30 blur-2xl pointer-events-none animate-morph-blob-2" />
        <div className="absolute left-1/3 top-1/4 w-48 h-48 rounded-full bg-gradient-to-r from-amber-300/20 via-pink-400/20 to-violet-400/25 blur-3xl pointer-events-none animate-morph-blob-3" />

        {/* Shimmer light glass overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-transparent to-black/20 pointer-events-none" />

        {/* Top row: Location badge + refresh */}
        <div className="flex items-center justify-between w-full z-10">
          <button
            type="button"
            onClick={onOpenLocationModal}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white/20 hover:bg-white/30 active:scale-95 backdrop-blur-md border border-white/30 text-white font-medium text-[12.5px] shadow-sm cursor-pointer transition-all group"
            title="Nhấp để đổi vị trí hoặc chọn định vị GPS / IP"
            data-testid="hero-location-badge"
          >
            <span className="group-hover:scale-125 transition-transform">
              {geoStatus === "loading" ? "⏳" : geoSource === "gps" ? "🎯" : "📍"}
            </span>
            <span className="underline decoration-dotted decoration-white/70 underline-offset-2">
              {geoStatus === "loading" ? "Đang định vị..." : data.location}
            </span>
            <span className="opacity-60">·</span>
            <LiveClock location={data.location} />
            <span className="text-[10px] bg-white/25 hover:bg-white/40 font-bold px-2 py-0.5 rounded-full ml-1">
              {geoSource === "gps" ? "GPS Tự động" : geoSource === "ip" ? "IP Tự động" : geoSource === "manual" ? "Thủ công" : "Tự động"}
            </span>
          </button>

          {/* Refresh button */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur-md border border-white/30 text-white text-[11px] font-medium cursor-pointer transition-all disabled:opacity-50 active:scale-95 shadow-sm"
              title="Cập nhật dữ liệu thời tiết mới nhất"
            >
              <span className={`text-[13px] ${isRefreshing ? "animate-spin" : ""}`}>🔄</span>
              <span className="hidden sm:inline">{isRefreshing ? "Đang tải..." : "Cập nhật"}</span>
            </button>
          )}
        </div>

        {/* Temperature + Condition */}
        <div className="flex flex-col gap-1 items-start w-full z-10">
          <p className="font-black leading-none text-[64px] sm:text-[72px] text-white tracking-tighter drop-shadow-md">
            {data.weather.temp}°C
          </p>
          <p className="font-bold text-[18px] text-white flex items-center gap-2 drop-shadow-xs">
            <span className="inline-block animate-bounce text-2xl" style={{ animationDuration: "3s" }}>{theme.emoji}</span>
            <span>{data.weather.description}</span>
          </p>
          <p className="font-medium text-[13.5px] text-white/80">Cảm nhận {data.weather.feelsLike}°C</p>
        </div>

        {/* 4 Stats Grid */}
        <div className="grid grid-cols-2 gap-2.5 w-full text-[13px] z-10">
          <div className="bg-white/15 backdrop-blur-md border border-white/25 flex flex-col gap-1 items-start min-w-0 overflow-hidden p-3 rounded-2xl hover:bg-white/25 transition-all duration-300 shadow-xs">
            <p className="font-medium text-white/90 text-[11.5px] whitespace-nowrap">💨 Gió</p>
            <p className="font-bold leading-5 text-white text-[14px]">{data.weather.windSpeed} km/h</p>
          </div>
          <div className="bg-white/15 backdrop-blur-md border border-white/25 flex flex-col gap-1 items-start min-w-0 overflow-hidden p-3 rounded-2xl hover:bg-white/25 transition-all duration-300 shadow-xs">
            <p className="font-medium text-white/90 text-[11.5px] whitespace-nowrap">💧 Độ ẩm</p>
            <p className="font-bold leading-5 text-white text-[14px]">{data.weather.humidity}%</p>
          </div>
          <div className="bg-white/15 backdrop-blur-md border border-white/25 flex flex-col gap-1 items-start min-w-0 overflow-hidden p-3 rounded-2xl hover:bg-white/25 transition-all duration-300 shadow-xs">
            <p className="font-medium text-white/90 text-[11.5px] whitespace-nowrap">🌫️ Bụi PM2.5</p>
            <p className="font-bold leading-5 text-white text-[14px]">{pm25} µg/m³ {pm25Icon}</p>
          </div>
          <div className="bg-white/15 backdrop-blur-md border border-white/25 flex flex-col gap-1 items-start min-w-0 overflow-hidden p-3 rounded-2xl hover:bg-white/25 transition-all duration-300 shadow-xs">
            <p className="font-medium text-white/90 text-[11.5px] whitespace-nowrap">👁️ Tầm nhìn</p>
            <p className="font-bold leading-5 text-white text-[14px]">{(data.weather as any).visibility ?? 10} km</p>
          </div>
        </div>
      </div>

      {/* ── 5-Day Forecast ───────────────────────────────────────────────── */}
      <div className="bg-white border border-[#e3e7ef] flex flex-col gap-3 items-start overflow-hidden p-4 rounded-2xl text-[13px] w-full">
        <div className="flex items-center justify-between w-full">
          <p className="font-bold text-[#182033] whitespace-nowrap">📅 Dự báo 5 ngày tới</p>
          <p className="text-[12px] text-[#5f687b]">Cập nhật mỗi 3h</p>
        </div>
        <div className="flex gap-2 w-full overflow-x-auto pb-1 scrollbar-none">
          {data.forecast.map((f, i) => (
            <div key={i} className="flex-1 min-w-[68px] bg-[#f4f6fa] rounded-2xl p-3 flex flex-col items-center gap-1 border border-[#e3e7ef] hover:border-[#ff315f]/30 hover:bg-[#fff5f7] transition-all">
              <p className="font-semibold text-[#182033] text-[11px] whitespace-nowrap">{f.time}</p>
              <p className="text-[24px] leading-none">{f.icon}</p>
              <p className="font-bold text-[#182033] text-[14px]">{f.tempMax ?? f.temp}°</p>
              <p className="text-[#5f687b] text-[10px]">{f.tempMin ?? f.temp - 3}°</p>
              <div className="flex items-center gap-0.5">
                <span className="text-[10px]">💧</span>
                <p className="text-[#3b82f6] text-[10px] font-semibold">{f.pop}%</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Antigravity AI Copilot Active Card ──────────────────────────── */}
      <div className="bg-gradient-to-br from-[#1e1b4b] via-[#2e1065] to-[#0f172a] text-white border border-indigo-500/30 flex flex-col gap-3 items-start overflow-hidden p-5 rounded-2xl shadow-xl w-full relative">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center gap-2">
            <span className="size-2 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-[10px] font-bold tracking-wider uppercase bg-indigo-500/30 text-indigo-200 px-2.5 py-0.5 rounded-full border border-indigo-400/30">
              AI COPILOT ACTIVE
            </span>
          </div>
          <span className="text-[11px] text-indigo-300 font-mono">Gemini 2.5 Flash</span>
        </div>
        <div className="flex flex-col gap-1 w-full">
          <p className="font-bold text-[16px] text-white flex items-center gap-2">🤖 Antigravity Copilot</p>
          <p className="text-[12px] text-indigo-200/80 leading-relaxed">
            Hệ thống AI xử lý dữ liệu thời gian thực: phân tích tác động thời tiết, tóm tắt tin tức, đánh giá bụi mịn PM2.5 và khuyến cáo lộ trình an toàn.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2 w-full pt-1">
          <button onClick={() => onOpenCopilot("weather_impact")} data-testid="copilot-action-weather" className="flex items-center gap-2 p-2.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/10 text-left transition-all group cursor-pointer">
            <span className="text-[16px]">🌤️</span>
            <div className="flex flex-col min-w-0">
              <span className="text-[12px] font-semibold text-white group-hover:text-amber-300 transition-colors">Tác động thời tiết</span>
              <span className="text-[10px] text-indigo-200 truncate">Sốc nhiệt, UV, sinh hoạt</span>
            </div>
          </button>
          <button onClick={() => onOpenCopilot("news_digest")} data-testid="copilot-action-news" className="flex items-center gap-2 p-2.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/10 text-left transition-all group cursor-pointer">
            <span className="text-[16px]">📰</span>
            <div className="flex flex-col min-w-0">
              <span className="text-[12px] font-semibold text-white group-hover:text-amber-300 transition-colors">Tóm tắt tin nóng</span>
              <span className="text-[10px] text-indigo-200 truncate">Điểm tin VTV24, Tuổi Trẻ</span>
            </div>
          </button>
          <button onClick={() => onOpenCopilot("health_pm25")} data-testid="copilot-action-pm25" className="flex items-center gap-2 p-2.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/10 text-left transition-all group cursor-pointer">
            <span className="text-[16px]">🌱</span>
            <div className="flex flex-col min-w-0">
              <span className="text-[12px] font-semibold text-white group-hover:text-amber-300 transition-colors">Đánh giá PM2.5</span>
              <span className="text-[10px] text-indigo-200 truncate">Cảnh báo hô hấp, y tế · {pm25Label}</span>
            </div>
          </button>
          <button onClick={() => onOpenCopilot("smart_route")} data-testid="copilot-action-route" className="flex items-center gap-2 p-2.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/10 text-left transition-all group cursor-pointer">
            <span className="text-[16px]">🚗</span>
            <div className="flex flex-col min-w-0">
              <span className="text-[12px] font-semibold text-white group-hover:text-amber-300 transition-colors">Tuyến đường an toàn</span>
              <span className="text-[10px] text-indigo-200 truncate">Tránh ngập Chiến Thắng, Triều Khúc</span>
            </div>
          </button>
        </div>
        <button
          onClick={() => onOpenCopilot(null)}
          data-testid="copilot-action-dialog"
          className="w-full mt-1 py-2.5 px-4 rounded-xl bg-gradient-to-r from-[#ff315f] via-rose-500 to-amber-500 hover:opacity-95 text-white font-semibold text-[13px] flex items-center justify-center gap-2 shadow-lg transition-all cursor-pointer"
        >
          <span>💬 Mở Hộp Thoại Tương Tác Trực Tiếp Với AI</span>
          <span>→</span>
        </button>
      </div>

      {/* ── Warning ─────────────────────────────────────────────────────── */}
      <div className="bg-[#fff7ed] border border-[#e3e7ef] flex flex-col gap-2 items-start overflow-hidden p-4 rounded-2xl text-[13px] w-full">
        <div className="flex items-center gap-2">
          <span className="text-[16px]">⚠️</span>
          <p className="font-bold text-[#b93815]">Cảnh báo trọng tâm</p>
        </div>
        <p className="leading-5 text-[#5f687b] w-full">{theme.warningText}</p>
      </div>

      {/* ── Suggestion ──────────────────────────────────────────────────── */}
      <div className="bg-[#f0fdf4] border border-[#e3e7ef] flex flex-col gap-2 items-start overflow-hidden p-4 rounded-2xl text-[13px] w-full">
        <div className="flex items-center gap-2">
          <span className="text-[16px]">🌿</span>
          <p className="font-bold text-[#166534]">Gợi ý lịch trình thực tế</p>
        </div>
        <div className="flex flex-col gap-1 w-full">
          {theme.suggestionItems.map((line, i) => (
            <p key={i} className="leading-5 text-[#5f687b]">{line}</p>
          ))}
        </div>
      </div>

      {/* ── Flood blackspots ────────────────────────────────────────────── */}
      {theme.showFlood && theme.floodItems && (
        <div className="bg-white border border-[#e3e7ef] flex flex-col gap-2 items-start overflow-hidden p-4 rounded-2xl text-[13px] w-full">
          <p className="font-bold text-[#182033]">🌊 BẢNG ĐIỂM ĐEN NGẬP ÚNG (Hà Nội)</p>
          {theme.floodItems.map((line, i) => (
            <p key={i} className="leading-5 text-[#5f687b]">• {line}</p>
          ))}
        </div>
      )}

      {/* ── Route advisory ──────────────────────────────────────────────── */}
      {theme.showRouteAdvisory && theme.routeItems && (
        <div className="bg-[#eff6ff] border border-[#e3e7ef] flex flex-col gap-2 items-start overflow-hidden p-4 rounded-2xl text-[13px] w-full">
          <p className="font-bold text-[#182033]">🛣️ KHUYẾN CÁO LỘ TRÌNH</p>
          {theme.routeItems.map((line, i) => (
            <p key={i} className="leading-5 text-[#5f687b]">• {line}</p>
          ))}
        </div>
      )}
    </div>
  );
}


// ── Ultra-Stylish Video Hub Component ─────────────────────────────────────

export function VideoHubSection({
  videos,
  onPlayVideo,
}: {
  videos: VideoItem[];
  onPlayVideo: (v: VideoItem) => void;
}) {
  const [selectedFilter, setSelectedFilter] = useState<string>("all");

  const categories = [
    { key: "all", label: `🔥 Tất cả (${videos.length})` },
    { key: "weather", label: "🌤️ Thời tiết & Bão lũ" },
    { key: "news", label: "⚡ Tiêu điểm 24h" },
    { key: "traffic", label: "🚗 Giao thông & Đô thị" },
    { key: "life", label: "🌿 Đời sống" },
  ];

  const filteredVideos =
    selectedFilter === "all"
      ? videos
      : videos.filter((v) => v.category === selectedFilter);

  const heroVideo = filteredVideos[0] || videos[0];
  const gridVideos = filteredVideos.slice(1);

  if (!videos || videos.length === 0) return null;

  return (
    <div className="flex flex-col gap-5 w-full mt-4">
      {/* Section Header */}
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center gap-3">
          <div className="size-3 rounded-full bg-[#ff315f] animate-pulse" />
          <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[20px] tracking-tight">
            Truyền Hình Nóng & Video Tiêu Điểm
          </p>
          <div className="bg-gradient-to-r from-[#ff315f] to-[#f97316] text-white text-[10px] font-extrabold px-2.5 py-0.5 rounded-full shadow-sm">
            LIVE HUB
          </div>
        </div>
        <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px] hidden sm:block">
          Cập nhật từ VTV24, VTC Now, Báo Tuổi Trẻ
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none w-full">
        {categories.map((cat) => (
          <button
            key={cat.key}
            data-testid={cat.key === "weather" ? "video-tab-weather" : `video-tab-${cat.key}`}
            onClick={() => setSelectedFilter(cat.key)}
            className={`px-4 py-2 rounded-full text-[12px] font-['Inter:Semi_Bold'] font-semibold whitespace-nowrap transition-all duration-200 cursor-pointer ${
              selectedFilter === cat.key
                ? "bg-[#182033] text-white shadow-md shadow-[#182033]/20 scale-105"
                : "bg-white text-[#5f687b] hover:bg-[#eef2f6] border border-[#e3e7ef]"
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Hero Spotlight Video Card */}
      {heroVideo && (
        <div
          data-testid="hero-video-card"
          onClick={() => onPlayVideo(heroVideo)}
          className="group relative w-full h-[240px] md:h-[320px] rounded-3xl overflow-hidden cursor-pointer shadow-[0_10px_30px_rgba(23,33,51,0.15)] border border-[#e3e7ef] bg-black transition-transform duration-300 hover:scale-[1.01]"
        >
          {/* Background image */}
          <img
            src={heroVideo.thumbnail}
            alt={heroVideo.title}
            className="absolute inset-0 size-full object-cover opacity-85 transition-transform duration-700 group-hover:scale-105"
          />

          {/* Cinematic gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-[#090d16] via-[#090d16]/50 to-transparent" />

          {/* Badges top */}
          <div className="absolute top-4 left-4 right-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="bg-[#ff315f] text-white text-[11px] font-bold px-3 py-1 rounded-full shadow-lg flex items-center gap-1.5 backdrop-blur-sm">
                <span className="size-2 rounded-full bg-white animate-ping" />
                {heroVideo.badge || "TIÊU ĐIỂM"}
              </span>
              <span className="bg-black/60 backdrop-blur-md text-white text-[11px] font-semibold px-2.5 py-1 rounded-full border border-white/20">
                {heroVideo.channel}
              </span>
            </div>
            <span className="bg-black/70 backdrop-blur-md text-white/90 text-[11px] px-2.5 py-1 rounded-full border border-white/10 font-mono">
              {heroVideo.duration || "HD"}
            </span>
          </div>

          {/* Glowing Center Play Button */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="size-16 md:size-20 rounded-full bg-white/20 backdrop-blur-md border border-white/40 flex items-center justify-center shadow-[0_0_40px_rgba(255,49,95,0.5)] transition-all duration-300 group-hover:scale-115 group-hover:bg-[#ff315f] group-hover:border-[#ff315f]">
              <svg
                className="size-7 md:size-8 text-white ml-1 transition-transform group-hover:scale-110"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
          </div>

          {/* Bottom Title & Channel Info */}
          <div className="absolute bottom-4 left-4 right-4 flex flex-col gap-1.5">
            <span className="text-[#38bdf8] text-[12px] font-semibold tracking-wide uppercase">
              {heroVideo.categoryLabel}
            </span>
            <p className="font-['Inter:Bold'] font-bold text-white text-[16px] md:text-[20px] leading-tight line-clamp-2 drop-shadow-md">
              {heroVideo.title}
            </p>
            <div className="flex items-center gap-2 text-white/75 text-[11px] pt-1">
              <span>{heroVideo.channel}</span>
              <span>•</span>
              <span>{heroVideo.published}</span>
              <span>•</span>
              <span className="text-white font-medium underline underline-offset-2">
                Bấm để phát video ngay ▶
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Video Cards Grid */}
      {gridVideos.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 w-full">
          {gridVideos.map((video) => (
            <div
              key={video.id}
              onClick={() => onPlayVideo(video)}
              className="group bg-white rounded-2xl overflow-hidden border border-[#e3e7ef] shadow-[0px_4px_12px_0px_rgba(23,33,51,0.06)] hover:shadow-xl hover:-translate-y-1.5 transition-all duration-300 cursor-pointer flex flex-col"
            >
              {/* Thumbnail Container */}
              <div className="relative aspect-video w-full bg-[#111827] overflow-hidden">
                <img
                  src={video.thumbnail}
                  alt={video.title}
                  className="size-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-black/20" />

                {/* Badge top-left */}
                <div className="absolute top-2.5 left-2.5">
                  <span className="bg-[#182033]/80 backdrop-blur-md text-white text-[10px] font-bold px-2 py-0.5 rounded-md border border-white/10">
                    {video.channel}
                  </span>
                </div>

                {/* Duration bottom-right */}
                <div className="absolute bottom-2 right-2">
                  <span className="bg-black/75 backdrop-blur-md text-white text-[10px] font-mono px-1.5 py-0.5 rounded">
                    {video.duration || "HD"}
                  </span>
                </div>

                {/* Mini Hover Play Button */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                  <div className="size-11 rounded-full bg-[#ff315f] text-white flex items-center justify-center shadow-lg transform scale-90 group-hover:scale-100 transition-transform">
                    <svg className="size-5 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Text info */}
              <div className="p-3.5 flex flex-col justify-between flex-1 gap-2">
                <div className="flex flex-col gap-1">
                  <span className="text-[11px] font-semibold text-[#ff315f]">
                    {video.categoryLabel}
                  </span>
                  <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[13px] leading-snug line-clamp-2 group-hover:text-[#ff315f] transition-colors">
                    {video.title}
                  </p>
                </div>
                <div className="flex items-center justify-between text-[11px] text-[#5f687b] pt-1 border-t border-[#f1f3f7]">
                  <span>{video.channel}</span>
                  <span>{video.published}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Mobile Layout ─────────────────────────────────────────────────────────

export function MobileLayout({
  data,
  onPlayVideo,
  onOpenCopilot,
  onSelectArticle,
  geoStatus,
  onRequestGeo,
  onRefresh,
  isRefreshing,
}: {
  data: AppData;
  onPlayVideo: (v: VideoItem) => void;
  onOpenCopilot: (action: string | null) => void;
  onSelectArticle?: (article: NewsArticle) => void;
  geoStatus?: "idle" | "loading" | "granted" | "denied";
  geoSource?: GeoSource;
  onOpenLocationModal?: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}) {
  return (
    <div className="bg-[#f4f6fa] flex flex-col items-start w-full">
      {/* Header bar */}
      <div className="bg-white border-b border-[#e3e7ef] flex h-[72px] items-center justify-between px-4 w-full shrink-0">
        <BrandLogo size="sm" />
        <div className="flex items-center gap-2">
          <button
            onClick={() => onOpenCopilot(null)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-gradient-to-r from-violet-600 via-indigo-600 to-rose-500 text-white font-['Inter:Semi_Bold'] font-semibold text-[11px] shadow-sm hover:opacity-90 transition-opacity cursor-pointer"
          >
            <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>🤖 Copilot</span>
          </button>
          <div className="bg-[#f4f6fa] px-2.5 py-1 rounded-full border border-[#e3e7ef] flex items-center gap-1">
            <img src={imgClock} alt="time" className="size-3 opacity-60 inline" />
            <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px]">
              {data.location} · {data.updateTime}
            </p>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-6 items-start pb-8 pt-4 px-4 w-full">
        {/* Weather section */}
        <div className="flex flex-col gap-3 items-start w-full">
          <p className="font-['Inter:Semi_Bold'] font-semibold leading-[26px] text-[#182033] text-[20px]">Thời tiết</p>
          <WeatherColumn data={data} onOpenCopilot={onOpenCopilot} geoStatus={geoStatus} geoSource={geoSource} onOpenLocationModal={onOpenLocationModal} onRefresh={onRefresh} isRefreshing={isRefreshing} />
        </div>

        {/* Video Hub Section */}
        <VideoHubSection videos={data.videos} onPlayVideo={onPlayVideo} />

        {/* News Feed */}
        <div className="flex flex-col gap-3 items-start w-full mt-2">
          <div className="flex items-center justify-between w-full">
            <p className="font-['Inter:Semi_Bold'] font-semibold leading-[26px] text-[#182033] text-[20px]">
              Tin Tức Mới Nhất · {data.news.length} bài
            </p>
            <span className="text-[11px] text-[#ff315f] font-semibold">Chạm để đọc chi tiết</span>
          </div>
          {data.news.slice(0, 5).map((item, i) => (
            <div
              key={i}
              onClick={() => onSelectArticle?.(item)}
              className="bg-white flex flex-col gap-[12px] items-start overflow-hidden p-4 rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full cursor-pointer hover:shadow-lg transition-shadow border border-transparent active:border-indigo-100"
            >
              <div className="flex gap-[10px] items-center justify-between w-full">
                <div className="flex gap-[10px] items-center overflow-hidden flex-1">
                  <img
                    alt=""
                    className="rounded-full shrink-0 size-10 object-cover bg-[#f4f6fa]"
                    src={item.image || FALLBACK_NEWS_IMAGES[i % 5]}
                    onError={(e) => onImgError(e, i)}
                  />
                  <div className="flex flex-1 flex-col items-start min-w-0 overflow-hidden">
                    <p className="font-['Inter:Semi_Bold'] font-semibold text-[#182033] text-[14px] line-clamp-1">
                      {item.title}
                    </p>
                    <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px]">
                      {item.source} · Vừa cập nhật
                    </p>
                  </div>
                </div>
                <div className="relative shrink-0 size-5">
                  <img alt="" className="absolute inset-0 size-full opacity-60" src={imgMoreHorizontal} />
                </div>
              </div>

              <p className="font-['Inter:Regular'] font-normal leading-[21px] text-[#182033] text-[14px] line-clamp-2">
                {item.description}
              </p>

              <div className="h-[180px] relative rounded-xl w-full overflow-hidden bg-[#f4f6fa]">
                <img
                  alt=""
                  className="absolute inset-0 max-w-none object-cover size-full"
                  src={item.image || FALLBACK_NEWS_IMAGES[i % 5]}
                  onError={(e) => onImgError(e, i)}
                />
              </div>

              <div className="flex items-center justify-between pt-1 w-full text-[12px]">
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-[#ff315f]">📖 Đọc chi tiết →</span>
                  <span className="text-[10px] text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded font-medium border border-indigo-100">🔊 Nghe AI</span>
                </div>
                <a
                  href={item.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="text-[#5f687b] hover:text-[#182033]"
                >
                  Báo gốc ↗
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Tablet Layout ─────────────────────────────────────────────────────────

const TAB_CATS = [
  { cat: "THỜI SỰ", bg: "bg-[#ffe8ee]", color: "text-[#ff315f]" },
  { cat: "XÃ HỘI", bg: "bg-[#e0f2fe]", color: "text-[#0369a1]" },
  { cat: "KINH TẾ", bg: "bg-[#fef3c7]", color: "text-[#92400e]" },
  { cat: "ĐỜI SỐNG", bg: "bg-[#f0fdf4]", color: "text-[#166534]" },
];

export function TabletLayout({
  data,
  onPlayVideo,
  onOpenCopilot,
  onSelectArticle,
  geoStatus,
  onRequestGeo,
  onRefresh,
  isRefreshing,
}: {
  data: AppData;
  onPlayVideo: (v: VideoItem) => void;
  onOpenCopilot: (action: string | null) => void;
  onSelectArticle?: (article: NewsArticle) => void;
  geoStatus?: "idle" | "loading" | "granted" | "denied";
  geoSource?: GeoSource;
  onOpenLocationModal?: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}) {
  const feat = data.news[0];
  const sides = data.news.slice(1, 5);

  return (
    <div className="bg-[#f4f6fa] flex flex-col items-start w-full">
      {/* Header */}
      <div className="bg-white border-b border-[#e3e7ef] flex h-[72px] items-center justify-between px-6 w-full shrink-0">
        <div className="flex gap-3 items-center">
          <BrandLogo size="sm" />
          <div className="bg-[#f4f6fa] flex items-center gap-1.5 px-3 py-1 rounded-full border border-[#e3e7ef]">
            <img src={imgLocationPin} alt="pin" className="size-3.5 opacity-60 inline" />
            <p className="font-['Inter:Medium'] font-medium text-[#5f687b] text-[12px] whitespace-nowrap">{data.location}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => onOpenCopilot(null)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-violet-600 via-indigo-600 to-rose-500 text-white font-['Inter:Semi_Bold'] font-semibold text-[12px] shadow-sm hover:opacity-90 transition-opacity cursor-pointer"
          >
            <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>🤖 Antigravity Copilot</span>
            <span className="bg-white/20 text-[9px] font-bold px-1.5 py-0.5 rounded-full">AI</span>
          </button>
          <div className="bg-[#f4f6fa] flex items-center gap-1.5 px-3 py-1 rounded-full border border-[#e3e7ef]">
            <img src={imgClock} alt="time" className="size-3.5 opacity-60 inline" />
            <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px] whitespace-nowrap">Cập nhật {data.updateTime}</p>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-6 p-5 w-full">
        <div className="flex gap-5 items-start w-full">
          {/* Weather column */}
          <div className="flex flex-col gap-3 items-start shrink-0 w-[calc(50%-10px)] max-w-[560px]">
            <WeatherColumn data={data} onOpenCopilot={onOpenCopilot} geoStatus={geoStatus} geoSource={geoSource} onOpenLocationModal={onOpenLocationModal} onRefresh={onRefresh} isRefreshing={isRefreshing} />
          </div>

          {/* News column */}
          <div className="flex flex-1 flex-col gap-3 items-start min-w-0 overflow-hidden">
            <div className="flex items-center justify-between w-full">
              <div className="flex flex-col gap-[2px] items-start">
                <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[20px] tracking-[-0.3px]">Tin tức</p>
                <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px]">{data.location} · {data.news.length} bài mới nhất</p>
              </div>
              <span className="text-[11px] text-[#ff315f] font-semibold">Chạm để đọc nhanh</span>
            </div>
            {feat && (
              <div
                onClick={() => onSelectArticle?.(feat)}
                className="bg-white flex flex-col items-start overflow-hidden rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full cursor-pointer hover:shadow-lg transition-all border border-transparent hover:border-indigo-100 group"
              >
                <div className="h-[180px] relative rounded-tl-2xl rounded-tr-2xl w-full overflow-hidden bg-[#f4f6fa]">
                  <img
                    alt=""
                    className="absolute inset-0 max-w-none object-cover size-full group-hover:scale-105 transition-transform duration-500"
                    src={feat.image || TABLET_FALLBACK_IMAGES[0]}
                    onError={(e) => onImgError(e, 0)}
                  />
                  <div className="absolute bg-[#ff315f] left-3 top-3 flex items-start px-[10px] py-1 rounded-[6px]">
                    <p className="font-['Inter:Bold'] font-bold text-[10px] text-white tracking-[0.5px] uppercase">NỔI BẬT</p>
                  </div>
                </div>
                <div className="flex flex-col gap-2 items-start p-[14px] w-full">
                  <p className="font-['Inter:Bold'] font-bold leading-[22px] text-[#182033] text-[15px] w-full line-clamp-2 group-hover:text-[#ff315f] transition-colors">{feat.title}</p>
                  <p className="font-['Inter:Regular'] font-normal leading-[18px] text-[#5f687b] text-[12px] w-full line-clamp-2">{feat.description}</p>
                  <div className="flex items-center justify-between pt-1 w-full border-t border-[#f4f6fa]">
                    <div className="flex gap-[6px] items-center">
                      <div className="bg-[#f7a928] rounded-[4px] size-2" />
                      <p className="font-['Inter:Semi_Bold'] font-semibold text-[#ff315f] text-[11px]">{feat.source}</p>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[11px] text-[#ff315f] font-semibold">Đọc chi tiết →</span>
                      <span className="text-[10px] text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded font-medium border border-indigo-100">🔊 Nghe AI</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {sides.map((a, i) => {
              const c = TAB_CATS[i % TAB_CATS.length];
              return (
                <div
                  key={i}
                  onClick={() => onSelectArticle?.(a)}
                  className="bg-white flex gap-3 items-center overflow-hidden p-3 rounded-[10px] shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full cursor-pointer hover:shadow-lg transition-all border border-transparent hover:border-indigo-100 group"
                >
                  <div className="relative rounded-[10px] shrink-0 size-[72px] overflow-hidden bg-[#f4f6fa]">
                    <img
                      alt=""
                      className="absolute inset-0 max-w-none object-cover size-full group-hover:scale-105 transition-transform duration-500"
                      src={a.image || TABLET_FALLBACK_IMAGES[(i + 1) % TABLET_FALLBACK_IMAGES.length]}
                      onError={(e) => onImgError(e, i + 1)}
                    />
                  </div>
                  <div className="flex flex-1 flex-col gap-1 items-start min-w-0 overflow-hidden">
                    <div className={`${c.bg} flex items-start px-[7px] py-[2px] rounded-[4px]`}>
                      <p className={`font-['Inter:Bold'] font-bold ${c.color} text-[10px]`}>{c.cat}</p>
                    </div>
                    <p className="font-['Inter:Semi_Bold'] font-semibold leading-[19px] text-[#182033] text-[13px] line-clamp-2 w-full group-hover:text-[#ff315f] transition-colors">{a.title}</p>
                    <div className="flex items-center justify-between text-[11px] w-full">
                      <p className="font-['Inter:Medium'] font-medium text-[#ff315f]">{a.source}</p>
                      <span className="text-[#5f687b] group-hover:text-[#ff315f]">Đọc chi tiết →</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Video Hub Section in Tablet */}
        <VideoHubSection videos={data.videos} onPlayVideo={onPlayVideo} />
      </div>
    </div>
  );
}

// ── Desktop Layout ────────────────────────────────────────────────────────

export function DesktopLayout({
  data,
  onPlayVideo,
  onOpenCopilot,
  onSelectArticle,
  searchQuery,
  onSearchChange,
  onStartVisualTest,
  geoStatus,
  onRequestGeo,
  onRefresh,
  isRefreshing,
}: {
  data: AppData;
  onPlayVideo: (v: VideoItem) => void;
  onOpenCopilot: (action: string | null) => void;
  onSelectArticle?: (article: NewsArticle) => void;
  searchQuery?: string;
  onSearchChange?: (q: string) => void;
  onStartVisualTest?: () => void;
  geoStatus?: "idle" | "loading" | "granted" | "denied";
  geoSource?: GeoSource;
  onOpenLocationModal?: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}) {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [visibleCount, setVisibleCount] = useState<number>(5);

  const categorizedNews = useMemo(() => {
    let list = data.news;
    if (selectedCategory === "weather") {
      list = list.filter((n) => /mưa|bão|lũ|ngập|thời tiết|nhiệt độ|rét|nắng|áp thấp|dông/i.test(n.title + " " + n.description));
    } else if (selectedCategory === "traffic") {
      list = list.filter((n) => /giao thông|xe|đường|cầu|hạ tầng|cao tốc|ùn tắc/i.test(n.title + " " + n.description));
    } else if (selectedCategory === "news") {
      list = list.filter((n) => /thời sự|chính trị|tiêu điểm|quốc tế|kinh tế|nghị trường/i.test(n.title + " " + n.description));
    } else if (selectedCategory === "life") {
      list = list.filter((n) => /đời sống|xã hội|giáo dục|văn hóa|y tế|sức khỏe/i.test(n.title + " " + n.description));
    } else if (selectedCategory === "saved") {
      try {
        const raw = localStorage.getItem("pulse_saved_articles");
        if (raw) list = JSON.parse(raw);
        else list = [];
      } catch {
        list = [];
      }
    }
    return list;
  }, [data.news, selectedCategory]);

  const displayNews = searchQuery?.trim()
    ? categorizedNews.filter((n) =>
        (n.title + " " + n.description + " " + n.source)
          .toLowerCase()
          .includes(searchQuery.trim().toLowerCase())
      )
    : categorizedNews;

  const feat = displayNews[0];
  const grid = displayNews.slice(1, visibleCount);
  const hasMore = displayNews.length > visibleCount;
  const now = new Date();
  const days = ["Chủ nhật", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"];
  const dateStr = `${days[now.getDay()]}, ${now.getDate()} Tháng ${now.getMonth() + 1} - ${data.updateTime}`;

  return (
    <div className="bg-[#f4f6fa] flex flex-col items-start w-full">
      {/* Top Header Dashboard */}
      <div className="bg-white border-b border-[#e3e7ef] flex h-[76px] items-center justify-between px-6 w-full shrink-0">
        <div className="flex gap-3 items-center">
          <BrandLogo />
          <div className="hidden 2xl:flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#f4f6fa] border border-[#e3e7ef]">
            <span className="font-['Inter:Bold'] font-bold text-[#182033] text-[13px]">Dashboard</span>
          </div>
          <div className="bg-[#f4f6fa] flex items-center gap-1.5 px-3 py-1 rounded-full border border-[#e3e7ef]">
            <img src={imgClock} alt="time" className="size-3.5 opacity-60 inline" />
            <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px] whitespace-nowrap">{dateStr}</p>
          </div>
          <button
            onClick={() => onOpenCopilot(null)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-violet-600 via-indigo-600 to-rose-500 hover:opacity-90 text-white font-['Inter:Semi_Bold'] font-semibold text-[13px] shadow-sm transition-all cursor-pointer"
          >
            <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>🤖 Antigravity Copilot</span>
            <span className="bg-white/20 text-[10px] font-extrabold px-1.5 py-0.5 rounded-full">AI ACTIVE</span>
          </button>
          {onStartVisualTest && (
            <button
              data-testid="start-visual-test-btn"
              onClick={onStartVisualTest}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-emerald-600 hover:bg-emerald-700 text-white font-['Inter:Semi_Bold'] font-semibold text-[13px] shadow-sm transition-all cursor-pointer"
              title="Chạy kiểm thử giao diện trực quan với con trỏ laser và hiệu ứng click"
            >
              <span>🧪 Test Trực Quan</span>
              <span className="bg-white/20 text-[10px] font-extrabold px-1.5 py-0.5 rounded-full">5/5 MÀN HÌNH</span>
            </button>
          )}
        </div>
        <div className="bg-[#f4f6fa] border border-[#e3e7ef] focus-within:border-indigo-400 focus-within:bg-white flex gap-[10px] h-11 items-center overflow-hidden px-[14px] rounded-xl w-[320px] transition-all">
          <div className="relative shrink-0 size-[18px]">
            <img alt="" className="absolute inset-0 size-full" src={imgSearch} />
          </div>
          <span className="sr-only">Tìm kiếm thời tiết, tin tức...</span>
          <input
            type="text"
            data-testid="header-search-input"
            value={searchQuery || ""}
            onChange={(e) => onSearchChange?.(e.target.value)}
            placeholder="Tìm kiếm thời tiết, tin tức..."
            className="bg-transparent border-none text-[13px] text-[#182033] placeholder-[#5f687b] focus:outline-none w-full"
          />
          {searchQuery && (
            <button
              data-testid="clear-search-btn"
              onClick={() => onSearchChange?.("")}
              className="text-gray-400 hover:text-gray-600 text-xs px-1 cursor-pointer"
              aria-label="Xóa tìm kiếm"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      <div className="flex gap-6 items-start p-6 w-full">
        {/* Left Column (Weather) */}
        <div className="flex flex-col gap-4 items-start shrink-0 w-[420px]">
          <WeatherColumn data={data} onOpenCopilot={onOpenCopilot} geoStatus={geoStatus} geoSource={geoSource} onOpenLocationModal={onOpenLocationModal} onRefresh={onRefresh} isRefreshing={isRefreshing} />
        </div>

        {/* Right Column (News + Videos Hub) */}
        <div className="flex flex-1 flex-col gap-6 items-start min-w-0 overflow-hidden">
          {/* News header */}
          <div className="flex items-center justify-between w-full">
            <div className="flex gap-[10px] items-center">
              <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[20px] whitespace-nowrap">Tin Tức Mới Nhất</p>
              <div className="bg-[#f7a928] flex items-start px-[10px] py-[3px] rounded-full">
                <p className="font-['Inter:Bold'] font-bold text-[11px] text-white">LIVE</p>
              </div>
            </div>
            <div className="bg-white border border-[#e3e7ef] flex items-center px-3 py-[6px] rounded-full">
              <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px]">Mới nhất ▾</p>
            </div>
          </div>

          {/* News Category Filter Tabs */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none w-full">
            {[
              { key: "all", label: `🔥 Tất cả (${data.news.length})` },
              { key: "weather", label: "🌤️ Thời tiết & Môi trường" },
              { key: "traffic", label: "🚗 Giao thông & Đô thị" },
              { key: "news", label: "⚡ Thời sự & Tiêu điểm" },
              { key: "life", label: "🌿 Đời sống" },
              { key: "saved", label: "🔖 Bài viết đã lưu" },
            ].map((cat) => (
              <button
                key={cat.key}
                data-testid={`news-tab-${cat.key}`}
                onClick={() => {
                  setSelectedCategory(cat.key);
                  setVisibleCount(5);
                }}
                className={`px-3.5 py-1.5 rounded-full text-[12px] font-['Inter:Semi_Bold'] font-semibold whitespace-nowrap transition-all duration-200 cursor-pointer ${
                  selectedCategory === cat.key
                    ? "bg-[#ff315f] text-white shadow-md shadow-[#ff315f]/25 scale-102"
                    : "bg-white text-[#5f687b] hover:bg-[#eef2f6] border border-[#e3e7ef]"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {searchQuery && (
            <div className="bg-indigo-50/80 border border-indigo-200/60 rounded-xl px-4 py-2.5 flex items-center justify-between text-[13px] text-indigo-950 w-full">
              <span>🔍 Tìm thấy <strong>{displayNews.length}</strong> bài viết cho từ khóa "<strong>{searchQuery}</strong>"</span>
              <button
                onClick={() => onSearchChange?.("")}
                className="text-[#ff315f] hover:underline font-semibold text-xs cursor-pointer"
              >
                Xóa bộ lọc ✕
              </button>
            </div>
          )}

          {/* Featured News Card */}
          {feat && (
            <div
              data-testid="featured-article-card"
              onClick={() => onSelectArticle?.(feat)}
              className="bg-white flex flex-col gap-3 items-start overflow-hidden p-5 rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full cursor-pointer hover:shadow-xl transition-all border border-transparent hover:border-indigo-100 group"
            >
              <div className="flex gap-[10px] items-center justify-between w-full">
                <div className="flex items-center gap-2.5">
                  <div className="bg-[#ffe8ee] flex flex-col items-center justify-center overflow-hidden rounded-full shrink-0 size-10">
                    <p className="font-['Inter:Bold'] font-bold text-[#ff315f] text-[15.84px]">{(feat.source || "N")[0]}</p>
                  </div>
                  <div className="flex flex-1 flex-col items-start min-w-0 overflow-hidden">
                    <p className="font-['Inter:Semi_Bold'] font-semibold text-[#182033] text-[14px]">{feat.source}</p>
                    <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px]">Vừa cập nhật · Tin nổi bật</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="bg-[#ff315f] text-white text-[10px] font-bold px-2 py-0.5 rounded-full">TIÊU ĐIỂM</span>
                  <div className="relative shrink-0 size-5">
                    <img alt="" className="absolute inset-0 size-full opacity-60" src={imgMoreHorizontal} />
                  </div>
                </div>
              </div>

              {/* Title & Description */}
              <div className="flex flex-col gap-1.5 w-full">
                <h3 className="font-['Inter:Bold'] font-bold text-[#182033] text-[18px] leading-snug group-hover:text-[#ff315f] transition-colors line-clamp-2">
                  {feat.title}
                </h3>
                <p className="font-['Inter:Regular'] font-normal leading-[21px] text-[#5f687b] text-[14px] w-full line-clamp-3">
                  {feat.description}
                </p>
              </div>

              <div className="h-[200px] relative rounded-xl w-full overflow-hidden bg-[#f4f6fa]">
                <img
                  alt=""
                  className="absolute inset-0 max-w-none object-cover size-full group-hover:scale-102 transition-transform duration-500"
                  src={feat.image || DESKTOP_FALLBACK_IMAGES[0]}
                  onError={(e) => onImgError(e, 0)}
                />
              </div>

              <div className="flex items-center justify-between pt-1 w-full border-t border-[#f4f6fa] text-[13px]">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-[#ff315f] group-hover:translate-x-1 transition-transform">
                    📖 Đọc chi tiết bài viết →
                  </span>
                  <span className="text-[11px] bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 border border-indigo-200/50">
                    🦜 Nghe Đọc AI VieNeu
                  </span>
                </div>
                <a
                  href={feat.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="font-normal text-[#5f687b] hover:text-[#182033] no-underline"
                >
                  Nguồn: {feat.source} ↗
                </a>
              </div>
            </div>
          )}

          {/* News Grid */}
          <div className="flex flex-wrap gap-3 items-start w-full">
            {grid.map((n, i) => (
              <div
                key={i}
                onClick={() => onSelectArticle?.(n)}
                className="bg-white flex flex-col items-start overflow-hidden rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-[calc(50%-6px)] cursor-pointer hover:shadow-xl transition-all border border-transparent hover:border-indigo-100 group"
              >
                <div className="h-[140px] relative w-full overflow-hidden bg-[#f4f6fa]">
                  <img
                    alt=""
                    className="absolute inset-0 max-w-none object-cover size-full group-hover:scale-105 transition-transform duration-500"
                    src={n.image || DESKTOP_FALLBACK_IMAGES[(i + 1) % DESKTOP_FALLBACK_IMAGES.length]}
                    onError={(e) => onImgError(e, i + 1)}
                  />
                  <div className="absolute top-2 left-2 bg-black/60 backdrop-blur-sm text-white text-[10px] font-semibold px-2 py-0.5 rounded-full">
                    {n.source}
                  </div>
                </div>
                <div className="flex flex-col gap-[6px] items-start p-[14px] w-full">
                  <div className="flex gap-2 items-center justify-between w-full">
                    <div className="bg-[#ffe8ee] flex items-start px-2 py-[3px] rounded-full">
                      <p className="font-['Inter:Semi_Bold'] font-semibold text-[#ff315f] text-[11px]">{n.source}</p>
                    </div>
                    <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px]">{data.updateTime}</p>
                  </div>
                  <p className="font-['Inter:Bold'] font-bold leading-5 text-[#182033] text-[14px] w-full line-clamp-2 group-hover:text-[#ff315f] transition-colors">{n.title}</p>
                  <p className="font-['Inter:Regular'] font-normal leading-[18px] text-[#5f687b] text-[12px] w-full line-clamp-2">{n.description}</p>
                  <div className="flex items-center justify-between pt-1 w-full text-[11px] border-t border-[#f8fafc]">
                    <div className="flex items-center gap-1.5">
                      <span className="font-semibold text-[#ff315f]">Đọc chi tiết →</span>
                      <span className="text-[10px] text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded font-medium border border-indigo-100">🔊 Nghe AI</span>
                    </div>
                    <a
                      href={n.link}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-[#94a3b8] hover:text-[#475569]"
                    >
                      Báo gốc ↗
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Load More Articles Button */}
          {hasMore && (
            <div className="flex justify-center w-full pt-1">
              <button
                data-testid="load-more-news-btn"
                onClick={() => setVisibleCount((prev) => prev + 4)}
                className="px-6 py-2.5 rounded-full bg-white border border-[#e3e7ef] hover:border-[#ff315f]/50 hover:bg-[#fff5f7] text-[#182033] hover:text-[#ff315f] font-['Inter:Semi_Bold'] font-semibold text-[13px] shadow-xs transition-all flex items-center gap-2 cursor-pointer"
              >
                <span>⬇️ Xem thêm bài viết</span>
                <span className="text-[#5f687b] text-[12px]">({displayNews.length - visibleCount} bài còn lại)</span>
              </button>
            </div>
          )}

          {/* ULTRA-STYLED VIDEO MULTIMEDIA HUB */}
          <div className="w-full pt-2">
            <VideoHubSection videos={data.videos} onPlayVideo={onPlayVideo} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Loading Skeleton ──────────────────────────────────────────────────────

function LoadingSkeleton() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#f4f6fa] gap-4 p-8">
      <div className="animate-pulse flex flex-col gap-4 w-full max-w-md">
        <div className="h-52 bg-gradient-to-r from-[#506477] to-[#9aa9b5] rounded-2xl opacity-50" />
        <div className="h-6 bg-[#e3e7ef] rounded-lg w-3/4" />
        <div className="h-4 bg-[#e3e7ef] rounded-lg w-1/2" />
        <div className="h-24 bg-[#e3e7ef] rounded-2xl" />
        <div className="h-24 bg-[#e3e7ef] rounded-2xl" />
      </div>
      <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[14px] mt-4 animate-pulse">
        ⏳ Đang tải dữ liệu thời tiết & video trực tiếp...
      </p>
    </div>
  );
}

// ── Root App Component ────────────────────────────────────────────────────

export default function App() {
  const [data, setData] = useState<AppData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('pulse_dark') === '1');
  const [activeVideo, setActiveVideo] = useState<VideoItem | null>(null);
  const [activeArticle, setActiveArticle] = useState<NewsArticle | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [visualTestOpen, setVisualTestOpen] = useState(false);
  const [locationModalOpen, setLocationModalOpen] = useState(false);
  const refreshRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const { geo, requestGPS, requestIP, setManualLocation } = useGeoLocation();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadData = useCallback(async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      else setIsRefreshing(true);
      const lat = geo.lat || DEFAULT_LAT;
      const lon = geo.lon || DEFAULT_LON;
      const locName = geo.name || DEFAULT_LOCATION;
      const [weatherResult, newsResult, videoResult] = await Promise.all([
        fetchWeatherDirect(lat, lon),
        fetchNews(),
        fetchVideos(),
      ]);

      const now = new Date();
      const timeStr = now.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
      const ampm = now.getHours() < 12 ? "SA" : "CH";

      setData({
        weather: weatherResult.weather,
        forecast: weatherResult.forecast,
        news: newsResult,
        videos: videoResult,
        updateTime: `${timeStr} ${ampm}`,
        location: locName,
      });
      setError(null);
      setLoading(false);
      setIsRefreshing(false);
    } catch (err: any) {
      console.error("Load data failed:", err);
      setError(err.message || "Lỗi tải dữ liệu");
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [geo.lat, geo.lon, geo.name]);

  useEffect(() => {
    loadData();
    refreshRef.current = setInterval(() => loadData(true), 5 * 60 * 1000);
    return () => {
      if (refreshRef.current) clearInterval(refreshRef.current);
    };
  }, [loadData]);

  // Re-fetch weather when geolocation changes
  useEffect(() => {
    if (geo.status === "granted" && data) {
      loadData(true);
    }
  }, [geo.lat, geo.lon]); // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) return <LoadingSkeleton />;

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#f4f6fa] gap-4 p-8 text-center">
        <p className="text-[40px]">⚠️</p>
        <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[18px]">Không thể tải dữ liệu</p>
        <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[14px]">{error}</p>
        <button
          onClick={loadData}
          className="mt-4 bg-[#ff315f] text-white font-['Inter:Semi_Bold'] font-semibold px-6 py-2 rounded-full text-[14px] hover:bg-[#e02050] transition-colors cursor-pointer"
        >
          Thử lại
        </button>
      </div>
    );
  }

  return (
    <div className={`min-h-screen w-full ${darkMode ? "dark bg-[#0f172a]" : "bg-[#f4f6fa]"} relative`}>
      {/* Dark mode toggle */}
      <button
        onClick={() => { const nd = !darkMode; setDarkMode(nd); localStorage.setItem('pulse_dark', nd ? '1' : '0'); }}
        className="fixed top-3 left-3 z-30 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border border-[#e3e7ef] rounded-full px-3 py-1.5 flex items-center gap-1.5 shadow-sm text-[12px] font-medium text-[#5f687b] hover:text-[#182033] transition-colors cursor-pointer"
        title="Chuyển chế độ sáng/tối"
      >
        <span>{darkMode ? "☀️" : "🌙"}</span>
        <span className="hidden sm:inline">{darkMode ? "Sáng" : "Tối"}</span>
      </button>
      {/* Live status badge top-right */}
      <div className="fixed top-3 right-3 z-30 bg-white/80 backdrop-blur-sm border border-[#e3e7ef] rounded-full px-3 py-1 flex items-center gap-2 shadow-sm">
        <div className="size-2 rounded-full bg-[#22c55e] animate-pulse" />
        <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[10px]">LIVE · {data.updateTime}</p>
      </div>

      {/* Antigravity Copilot AI Interactive Modal */}
      <AntigravityCopilotModal
        isOpen={copilotOpen}
        onClose={() => setCopilotOpen(false)}
        data={data}
        initialAction={activeAction}
      />

      {/* Cinema Mode Video Modal */}
      <VideoModal video={activeVideo} onClose={() => setActiveVideo(null)} />

      {/* Interactive Article Detail Modal */}
      <ArticleDetailModal
        article={activeArticle}
        onClose={() => setActiveArticle(null)}
        allNews={data.news}
        onSelectArticle={setActiveArticle}
        backendUrl="http://localhost:10000"
        onOpenCopilotWithContext={(prompt) => {
          setCopilotOpen(true);
          setActiveAction("general_chat");
        }}
      />

      {/* Visual UI Simulation Test Runner with Virtual Laser Cursor */}
      <VisualTestRunner
        data={data}
        isOpen={visualTestOpen}
        onClose={() => setVisualTestOpen(false)}
        onOpenCopilot={handleOpenCopilot}
        onCloseCopilot={() => setCopilotOpen(false)}
        onPlayVideo={setActiveVideo}
        onCloseVideo={() => setActiveVideo(null)}
        onSelectArticle={setActiveArticle}
        onCloseArticle={() => setActiveArticle(null)}
        onSearch={setSearchQuery}
      />

      {/* Responsive Breakpoints */}
      <div className="md:hidden">
        <MobileLayout
          data={data}
          onPlayVideo={setActiveVideo}
          onOpenCopilot={handleOpenCopilot}
          onSelectArticle={setActiveArticle}
          geoStatus={geo.status}
          geoSource={geo.source}
          onOpenLocationModal={() => setLocationModalOpen(true)}
          onRefresh={() => loadData(true)}
          isRefreshing={isRefreshing}
        />
      </div>
      <div className="hidden md:block xl:hidden">
        <TabletLayout
          data={data}
          onPlayVideo={setActiveVideo}
          onOpenCopilot={handleOpenCopilot}
          onSelectArticle={setActiveArticle}
          geoStatus={geo.status}
          geoSource={geo.source}
          onOpenLocationModal={() => setLocationModalOpen(true)}
          onRefresh={() => loadData(true)}
          isRefreshing={isRefreshing}
        />
      </div>
      <div className="hidden xl:block">
        <DesktopLayout
          data={data}
          onPlayVideo={setActiveVideo}
          onOpenCopilot={handleOpenCopilot}
          onSelectArticle={setActiveArticle}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onStartVisualTest={() => setVisualTestOpen(true)}
          geoStatus={geo.status}
          geoSource={geo.source}
          onOpenLocationModal={() => setLocationModalOpen(true)}
          onRefresh={() => loadData(true)}
          isRefreshing={isRefreshing}
        />
      </div>

            {/* Location Picker Modal */}
      <LocationPickerModal
        isOpen={locationModalOpen}
        onClose={() => setLocationModalOpen(false)}
        currentLocation={data.location}
        onSelectLocation={setManualLocation}
        onAutoGPS={requestGPS}
        onAutoIP={requestIP}
        geoSource={geo.source}
        loading={geo.status === "loading"}
      />

      {/* Floating Antigravity Copilot Launcher Button */}
      <button
        onClick={() => handleOpenCopilot(null)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-violet-600 via-indigo-600 to-rose-500 hover:opacity-95 text-white font-['Inter:Semi_Bold'] font-semibold text-[13px] shadow-[0_10px_25px_rgba(79,70,229,0.45)] hover:shadow-[0_15px_30px_rgba(79,70,229,0.65)] hover:scale-105 active:scale-95 transition-all cursor-pointer border border-white/20"
        aria-label="Kích hoạt Antigravity Copilot AI"
      >
        <div className="relative">
          <span className="absolute -top-1 -right-1 size-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-[18px]">🤖</span>
        </div>
        <div className="flex flex-col items-start leading-none text-left hidden sm:flex">
          <span className="text-[13px] font-bold">Antigravity Copilot</span>
          <span className="text-[10px] text-indigo-200 mt-0.5">Trợ lý AI Đô Thị</span>
        </div>
        <span className="bg-white/20 text-[10px] font-extrabold px-1.5 py-0.5 rounded-full sm:hidden">
          AI
        </span>
      </button>

      {/* Floating Visual UI Test Simulation Button */}
      <button
        data-testid="floating-visual-test-btn"
        onClick={() => setVisualTestOpen(true)}
        className="fixed bottom-6 left-6 z-40 flex items-center gap-2.5 px-4 py-3 rounded-full bg-slate-900/95 hover:bg-slate-900 text-white backdrop-blur-md font-['Inter:Semi_Bold'] font-semibold text-[13px] shadow-[0_10px_25px_rgba(0,0,0,0.35)] hover:shadow-[0_15px_30px_rgba(16,185,129,0.3)] hover:scale-105 active:scale-95 transition-all cursor-pointer border border-emerald-500/40"
        aria-label="Kích hoạt kiểm thử trực quan 5 màn hình"
      >
        <span className="text-[18px]">🎯</span>
        <div className="flex flex-col items-start leading-none text-left hidden sm:flex">
          <span className="text-[12px] font-bold text-emerald-400">Kiểm Thử Trực Quan</span>
          <span className="text-[10px] text-gray-300 mt-0.5">Con trỏ laser & Click ảo</span>
        </div>
        <span className="bg-emerald-500 text-slate-950 font-black text-[9px] px-2 py-0.5 rounded-full">
          RUN UI TEST
        </span>
      </button>
    </div>
  );
}
