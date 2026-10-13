import { useState, useRef, useEffect, useCallback } from "react";

const assetPathPrefix = "/assets";
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

const FALLBACK_NEWS_IMAGES = [imgNews1, imgNews2, imgNews3, imgNews4, imgNews5];
const TABLET_FALLBACK_IMAGES = [imgNews1, imgTabletNews3, imgTabletNews4, imgTabletNews5];
const DESKTOP_FALLBACK_IMAGES = [imgNews1, imgNews2, imgDesktopNews3, imgDesktopNews4, imgDesktopNews5];

// ── API Keys & Config ─────────────────────────────────────────────────────
const OWM_KEY = "a201c471567522a7d0b7a0567ad245fe";
const DEFAULT_LAT = 20.9716;
const DEFAULT_LON = 105.7725;
const DEFAULT_LOCATION = "Hà Nội";
const BACKEND_URL = "https://quan-ly-tien-phong-main.onrender.com";

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

const WEATHER_THEMES: Record<ConditionKey, WeatherTheme> = {
  "binh-thuong": {
    key: "binh-thuong",
    gradient: "linear-gradient(135deg, #506477 0%, #73879a 50%, #9aa9b5 100%)",
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
    gradient: "linear-gradient(135deg, #1e73be 0%, #58a8dc 50%, #f7a928 100%)",
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
    gradient: "linear-gradient(135deg, #b93815 0%, #ef6c20 50%, #f7a928 100%)",
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
    gradient: "linear-gradient(135deg, #34495e 0%, #52697e 50%, #75889a 100%)",
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
    gradient: "linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 50%, #4c93c3 100%)",
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
    gradient: "linear-gradient(135deg, #111827 0%, #293a55 50%, #475569 100%)",
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

function detectCondition(temp: number, feelsLike: number, desc: string, pop: number, humidity: number): ConditionKey {
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
  description: string;
  icon: string;
  pm25: number;
  aqiLevel: number;
  condKey: ConditionKey;
}

interface ForecastItem {
  time: string;
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

interface AppData {
  weather: LiveWeather;
  forecast: ForecastItem[];
  news: NewsArticle[];
  videos: VideoItem[];
  updateTime: string;
  location: string;
}

// ── Verified Rich Video Catalog (Fallback & Instant Display) ──────────────

const FALLBACK_VIDEOS: VideoItem[] = [
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
    published: "Vừa phát sóng",
    duration: "14:20",
  },
  {
    id: "oOB-MNGwlYQ",
    title: "Cảnh báo mưa lớn diện rộng kết hợp triều cường, nguy cơ ngập úng đô thị",
    link: "https://www.youtube.com/watch?v=oOB-MNGwlYQ",
    embedUrl: "https://www.youtube-nocookie.com/embed/oOB-MNGwlYQ",
    thumbnail: "https://img.youtube.com/vi/oOB-MNGwlYQ/hqdefault.jpg",
    channel: "VTV24",
    category: "weather",
    categoryLabel: "Thời tiết & Bão lũ",
    badge: "CẢNH BÁO",
    published: "Hôm nay",
    duration: "08:45",
  },
  {
    id: "Na5uByDy8Sw",
    title: "Dự báo thời tiết và diễn biến thiên tai: Mô phỏng vùng ngập lụt ven sông",
    link: "https://www.youtube.com/watch?v=Na5uByDy8Sw",
    embedUrl: "https://www.youtube-nocookie.com/embed/Na5uByDy8Sw",
    thumbnail: "https://img.youtube.com/vi/Na5uByDy8Sw/hqdefault.jpg",
    channel: "VTC Now",
    category: "weather",
    categoryLabel: "Thời tiết & Bão lũ",
    badge: "THỜI TIẾT",
    published: "Hôm nay",
    duration: "06:12",
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
    published: "Hôm nay",
    duration: "11:30",
  },
  {
    id: "6bfwopT5zUA",
    title: "Chiến dịch hạ tầng giao thông trọng điểm: Hành trình bứt phá tiến độ",
    link: "https://www.youtube.com/watch?v=6bfwopT5zUA",
    embedUrl: "https://www.youtube-nocookie.com/embed/6bfwopT5zUA",
    thumbnail: "https://img.youtube.com/vi/6bfwopT5zUA/hqdefault.jpg",
    channel: "VTV24",
    category: "traffic",
    categoryLabel: "Giao thông & Đô thị",
    badge: "HẠ TẦNG",
    published: "Hôm nay",
    duration: "18:05",
  },
  {
    id: "utYT3v_KTyo",
    title: "Phim tài liệu công nghệ số: Cuộc sống người dân ven đô thích ứng biến đổi khí hậu",
    link: "https://www.youtube.com/watch?v=utYT3v_KTyo",
    embedUrl: "https://www.youtube-nocookie.com/embed/utYT3v_KTyo",
    thumbnail: "https://img.youtube.com/vi/utYT3v_KTyo/hqdefault.jpg",
    channel: "VTC Now",
    category: "life",
    categoryLabel: "Đời sống & Xã hội",
    badge: "ĐỜI SỐNG",
    published: "Hôm qua",
    duration: "24:15",
  },
  {
    id: "V1BlfJPgmjk",
    title: "Ghi nhận y tế và cứu hộ khẩn cấp: Nỗ lực kịp thời trong mưa dông phức tạp",
    link: "https://www.youtube.com/watch?v=V1BlfJPgmjk",
    embedUrl: "https://www.youtube-nocookie.com/embed/V1BlfJPgmjk",
    thumbnail: "https://img.youtube.com/vi/V1BlfJPgmjk/hqdefault.jpg",
    channel: "VTV24",
    category: "life",
    categoryLabel: "Đời sống & Xã hội",
    badge: "XÃ HỘI",
    published: "Hôm nay",
    duration: "09:50",
  },
  {
    id: "U0e7Cq0aMZc",
    title: "Bản tin công nghệ và khoa học khí tượng: Ứng dụng cảm biến viễn thám cảnh báo sớm",
    link: "https://www.youtube.com/watch?v=U0e7Cq0aMZc",
    embedUrl: "https://www.youtube-nocookie.com/embed/U0e7Cq0aMZc",
    thumbnail: "https://img.youtube.com/vi/U0e7Cq0aMZc/hqdefault.jpg",
    channel: "VTV24",
    category: "news",
    categoryLabel: "Tiêu điểm 24h",
    badge: "KHOA HỌC",
    published: "Hôm nay",
    duration: "07:35",
  },
];

// ── Fetch weather directly from OpenWeatherMap ────────────────────────────

async function fetchWeatherDirect(): Promise<{ weather: LiveWeather; forecast: ForecastItem[] }> {
  const [currRes, foreRes, aqiRes] = await Promise.all([
    fetch(`https://api.openweathermap.org/data/2.5/weather?lat=${DEFAULT_LAT}&lon=${DEFAULT_LON}&appid=${OWM_KEY}&units=metric&lang=vi`),
    fetch(`https://api.openweathermap.org/data/2.5/forecast?lat=${DEFAULT_LAT}&lon=${DEFAULT_LON}&appid=${OWM_KEY}&units=metric&lang=vi`),
    fetch(`https://api.openweathermap.org/data/2.5/air_pollution?lat=${DEFAULT_LAT}&lon=${DEFAULT_LON}&appid=${OWM_KEY}`),
  ]);

  const curr = await currRes.json();
  const fore = await foreRes.json();
  const aqi = await aqiRes.json();

  const desc = curr.weather?.[0]?.description?.charAt(0).toUpperCase() + curr.weather?.[0]?.description?.slice(1) || "N/A";
  const temp = Math.round(curr.main.temp * 10) / 10;
  const feelsLike = Math.round(curr.main.feels_like * 10) / 10;
  const humidity = curr.main.humidity;
  const windSpeed = Math.round((curr.wind?.speed || 0) * 3.6); // m/s -> km/h
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
    temp, feelsLike, humidity, windSpeed, description: desc,
    icon: iconMap[curr.weather?.[0]?.icon] || "🌤️",
    pm25: Math.round(pm25 * 100) / 100,
    aqiLevel, condKey,
  };

  const forecast: ForecastItem[] = forecastList.map((item: any) => {
    const dt = new Date(item.dt * 1000);
    return {
      time: dt.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" }),
      temp: Math.round(item.main.temp),
      pop: Math.round((item.pop || 0) * 100),
      icon: iconMap[item.weather?.[0]?.icon] || "🌤️",
      desc: item.weather?.[0]?.description || "",
    };
  });

  return { weather, forecast };
}

// ── Fetch news from backend or fallback ───────────────────────────────────

async function fetchNews(): Promise<NewsArticle[]> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/daily-news`, { signal: AbortSignal.timeout(8000) });
    if (res.ok) {
      const data = await res.json();
      if (data.news && data.news.length > 0) {
        return data.news.slice(0, 10).map((n: any) => ({
          title: n.title || "", description: n.description || "",
          link: n.link || "#", image: n.image || null, source: n.source || n.author || "",
        }));
      }
    }
  } catch { /* backend unavailable, use fallback */ }

  try {
    const rssUrl = encodeURIComponent("https://news.google.com/rss?hl=vi&gl=VN&ceid=VN:vi");
    const proxyUrl = `https://api.allorigins.win/raw?url=${rssUrl}`;
    const res = await fetch(proxyUrl, { signal: AbortSignal.timeout(10000) });
    if (res.ok) {
      const text = await res.text();
      const parser = new DOMParser();
      const xml = parser.parseFromString(text, "text/xml");
      const items = xml.querySelectorAll("item");
      const articles: NewsArticle[] = [];
      items.forEach((item, i) => {
        if (i >= 10) return;
        const title = item.querySelector("title")?.textContent || "";
        const link = item.querySelector("link")?.textContent || "#";
        const rawDesc = item.querySelector("description")?.textContent || "";
        const descDoc = parser.parseFromString(rawDesc, "text/html");
        const description = descDoc.body?.textContent?.trim().slice(0, 200) || "";
        const imgTag = descDoc.querySelector("img");
        const image = imgTag?.getAttribute("src") || null;
        const sourceEl = item.querySelector("source");
        const source = sourceEl?.textContent || "Google News";
        articles.push({ title, description, link, image, source });
      });
      return articles;
    }
  } catch { /* RSS also failed */ }

  return [
    { title: "Hà Nội: Dự báo thời tiết ngày hôm nay", description: "Cập nhật tình hình thời tiết mới nhất tại khu vực Hà Nội và các vùng lân cận.", link: "#", image: null, source: "VnExpress" },
    { title: "Tin tức kinh tế Việt Nam mới nhất", description: "Tổng hợp tin tức kinh tế nổi bật trong ngày.", link: "#", image: null, source: "Dân Trí" },
    { title: "Chuyển đổi số trong giáo dục và y tế", description: "Bộ TT&TT công bố lộ trình chuyển đổi số với trọng tâm y tế số.", link: "#", image: null, source: "ICTNews" },
    { title: "Đội tuyển Việt Nam chuẩn bị cho giải châu Á", description: "HLV công bố danh sách 25 cầu thủ tập trung.", link: "#", image: null, source: "Tuổi Trẻ" },
    { title: "Top 10 quán ăn nổi tiếng tại Hà Đông", description: "Khám phá những địa điểm ẩm thực được yêu thích nhất.", link: "#", image: null, source: "Zing News" },
  ];
}

// ── Fetch multi-channel rich videos ───────────────────────────────────────

async function fetchVideos(): Promise<VideoItem[]> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/daily-news`, { signal: AbortSignal.timeout(8000) });
    if (res.ok) {
      const data = await res.json();
      if (data.videos && Array.isArray(data.videos) && data.videos.length > 0) {
        return data.videos.map((v: any) => ({
          id: v.id || "",
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
      }
    }
  } catch { /* fallback to direct feeds / catalog */ }

  return FALLBACK_VIDEOS;
}

// ── Image fallback handler ────────────────────────────────────────────────

function onImgError(e: React.SyntheticEvent<HTMLImageElement>, idx: number) {
  e.currentTarget.onerror = null;
  e.currentTarget.src = FALLBACK_NEWS_IMAGES[idx % FALLBACK_NEWS_IMAGES.length];
}

// ── Interactive Cinema Video Modal ────────────────────────────────────────

function VideoModal({ video, onClose }: { video: VideoItem | null; onClose: () => void }) {
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
              className="size-8 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center text-[18px] transition-colors"
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

// ── Weather Section (Left Column) ─────────────────────────────────────────

function WeatherColumn({ data }: { data: AppData }) {
  const theme = WEATHER_THEMES[data.weather.condKey];
  const pm25Icon = data.weather.aqiLevel >= 4 ? "😷" : data.weather.aqiLevel >= 3 ? "⚠️" : "✅";

  return (
    <div className="flex flex-col gap-4 w-full">
      {/* Hero Card */}
      <div
        className="flex flex-col gap-4 items-start overflow-hidden p-6 rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full"
        style={{ background: theme.gradient }}
      >
        <p className="font-['Inter:Semi_Bold'] font-semibold text-[13px] text-white whitespace-nowrap">
          📍 {data.location} · Cập nhật {data.updateTime}
        </p>
        <div className="flex flex-col gap-1 items-start w-full">
          <p className="font-['Inter:Extra_Bold'] font-extrabold leading-none text-[60px] text-white whitespace-nowrap">
            {data.weather.temp}°C
          </p>
          <p className="font-['Inter:Semi_Bold'] font-semibold text-[18px] text-white whitespace-nowrap">
            {theme.emoji} {data.weather.description}
          </p>
          <p className="font-['Inter:Regular'] font-normal text-[14px] text-[rgba(255,255,255,0.8)] whitespace-nowrap">
            Cảm nhận {data.weather.feelsLike}°C
          </p>
        </div>
        {/* 3 Info Boxes */}
        <div className="flex gap-2 items-start w-full text-[13px]">
          <div className="bg-[rgba(255,255,255,0.09)] border border-[rgba(255,255,255,0.2)] flex flex-1 flex-col gap-2 items-start min-w-0 overflow-hidden p-4 rounded-2xl">
            <p className="font-['Inter:Bold'] font-bold text-white whitespace-nowrap">💧 Độ ẩm</p>
            <p className="font-['Inter:Regular'] font-normal leading-5 text-[rgba(255,255,255,0.75)]">{data.weather.humidity}%</p>
          </div>
          <div className="bg-[rgba(255,255,255,0.09)] border border-[rgba(255,255,255,0.2)] flex flex-1 flex-col gap-2 items-start min-w-0 overflow-hidden p-4 rounded-2xl">
            <p className="font-['Inter:Bold'] font-bold text-white whitespace-nowrap">PM2.5</p>
            <p className="font-['Inter:Regular'] font-normal leading-5 text-[rgba(255,255,255,0.75)]">{data.weather.pm25} µg/m³ {pm25Icon}</p>
          </div>
          <div className="bg-[rgba(255,255,255,0.09)] border border-[rgba(255,255,255,0.2)] flex flex-1 flex-col gap-2 items-start min-w-0 overflow-hidden p-4 rounded-2xl">
            <p className="font-['Inter:Bold'] font-bold text-white whitespace-nowrap">💨 Tốc độ gió</p>
            <p className="font-['Inter:Regular'] font-normal leading-5 text-[rgba(255,255,255,0.75)]">{data.weather.windSpeed} km/h</p>
          </div>
        </div>
      </div>

      {/* Forecast 3 hours */}
      <div className="bg-white border border-[#e3e7ef] flex flex-col gap-3 items-start overflow-hidden p-4 rounded-2xl text-[13px] w-full">
        <div className="flex items-center justify-between w-full">
          <p className="font-['Inter:Bold'] font-bold text-[#182033] whitespace-nowrap">Dự báo 3 giờ tới</p>
          <p className="font-['Inter:Regular'] font-normal text-[#ff315f] text-[12px] cursor-pointer">Xem chi tiết →</p>
        </div>
        <div className="flex gap-2 w-full">
          {data.forecast.map((f, i) => (
            <div key={i} className="flex-1 bg-[#f4f6fa] rounded-xl p-3 flex flex-col items-center gap-1">
              <p className="font-['Inter:Semi_Bold'] font-semibold text-[#182033] text-[12px]">{f.time}</p>
              <p className="text-[22px] leading-none">{f.icon}</p>
              <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[15px]">{f.temp}°</p>
              <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px]">{f.pop}%</p>
            </div>
          ))}
        </div>
      </div>

      {/* Warning */}
      <div className="bg-[#fff7ed] border border-[#e3e7ef] flex flex-col gap-2 items-start overflow-hidden p-4 rounded-2xl text-[13px] w-full">
        <div className="flex items-center gap-2">
          <span className="text-[16px]">⚠️</span>
          <p className="font-['Inter:Bold'] font-bold text-[#b93815]">Cảnh báo trọng tâm</p>
        </div>
        <p className="font-['Inter:Regular'] font-normal leading-5 text-[#5f687b] w-full">{theme.warningText}</p>
      </div>

      {/* Suggestion */}
      <div className="bg-[#f0fdf4] border border-[#e3e7ef] flex flex-col gap-2 items-start overflow-hidden p-4 rounded-2xl text-[13px] w-full">
        <div className="flex items-center gap-2">
          <span className="text-[16px]">💡</span>
          <p className="font-['Inter:Bold'] font-bold text-[#166534]">Gợi ý lịch trình thực tế</p>
        </div>
        <div className="flex flex-col gap-1 w-full">
          {theme.suggestionItems.map((line, i) => (
            <p key={i} className="font-['Inter:Regular'] font-normal leading-5 text-[#5f687b]">{line}</p>
          ))}
        </div>
      </div>

      {/* Flood blackspots */}
      {theme.showFlood && theme.floodItems && (
        <div className="bg-white border border-[#e3e7ef] flex flex-col gap-2 items-start overflow-hidden p-4 rounded-2xl text-[13px] w-full">
          <p className="font-['Inter:Bold'] font-bold text-[#182033]">🌊 BẢNG ĐIỂM ĐEN NGẬP ÚNG (Hà Nội)</p>
          {theme.floodItems.map((line, i) => (
            <p key={i} className="font-['Inter:Regular'] font-normal leading-5 text-[#5f687b]">• {line}</p>
          ))}
        </div>
      )}

      {/* Route advisory */}
      {theme.showRouteAdvisory && theme.routeItems && (
        <div className="bg-[#eff6ff] border border-[#e3e7ef] flex flex-col gap-2 items-start overflow-hidden p-4 rounded-2xl text-[13px] w-full">
          <p className="font-['Inter:Bold'] font-bold text-[#182033]">🛡️ KHUYẾN CÁO LỘ TRÌNH</p>
          {theme.routeItems.map((line, i) => (
            <p key={i} className="font-['Inter:Regular'] font-normal leading-5 text-[#5f687b]">• {line}</p>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Ultra-Stylish Video Hub Component ─────────────────────────────────────

function VideoHubSection({
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

function MobileLayout({
  data,
  onPlayVideo,
}: {
  data: AppData;
  onPlayVideo: (v: VideoItem) => void;
}) {
  return (
    <div className="bg-[#f4f6fa] flex flex-col items-start w-full">
      {/* Header bar */}
      <div className="bg-white border-b border-[#e3e7ef] flex h-[72px] items-center justify-between px-4 w-full shrink-0">
        <p className="font-['Inter:Bold'] font-bold text-[#ff315f] text-[20px]">pulse.</p>
        <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px]">
          {data.location} · Cập nhật {data.updateTime}
        </p>
      </div>

      <div className="flex flex-col gap-6 items-start pb-8 pt-4 px-4 w-full">
        {/* Weather section */}
        <div className="flex flex-col gap-3 items-start w-full">
          <p className="font-['Inter:Semi_Bold'] font-semibold leading-[26px] text-[#182033] text-[20px]">Thời tiết</p>
          <WeatherColumn data={data} />
        </div>

        {/* Video Hub Section */}
        <VideoHubSection videos={data.videos} onPlayVideo={onPlayVideo} />

        {/* News Feed */}
        <div className="flex flex-col gap-3 items-start w-full mt-2">
          <p className="font-['Inter:Semi_Bold'] font-semibold leading-[26px] text-[#182033] text-[20px]">
            Tin Tức Mới Nhất · {data.news.length} bài
          </p>
          {data.news.slice(0, 5).map((item, i) => (
            <a
              key={i}
              href={item.link}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white flex flex-col gap-[14px] items-start overflow-hidden p-4 rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full no-underline hover:shadow-lg transition-shadow"
            >
              <div className="flex gap-[10px] items-center overflow-hidden w-full">
                <img
                  alt=""
                  className="rounded-full shrink-0 size-11 object-cover bg-[#f4f6fa]"
                  src={item.image || FALLBACK_NEWS_IMAGES[i % 5]}
                  onError={(e) => onImgError(e, i)}
                />
                <div className="flex flex-1 flex-col items-start min-w-0 overflow-hidden">
                  <p className="font-['Inter:Semi_Bold'] font-semibold text-[#182033] text-[14px] line-clamp-1">
                    {item.title}
                  </p>
                  <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px]">
                    {item.source}
                  </p>
                </div>
                <div className="relative shrink-0 size-5">
                  <img alt="" className="absolute inset-0 size-full" src={imgMoreHorizontal} />
                </div>
              </div>
              <p className="font-['Inter:Regular'] font-normal leading-[21px] text-[#182033] text-[14px]">
                {item.description}
              </p>
              <div className="h-[180px] relative rounded-[10px] w-full overflow-hidden bg-[#f4f6fa]">
                <img
                  alt=""
                  className="absolute inset-0 max-w-none object-cover size-full"
                  src={item.image || FALLBACK_NEWS_IMAGES[i % 5]}
                  onError={(e) => onImgError(e, i)}
                />
              </div>
            </a>
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

function TabletLayout({
  data,
  onPlayVideo,
}: {
  data: AppData;
  onPlayVideo: (v: VideoItem) => void;
}) {
  const feat = data.news[0];
  const sides = data.news.slice(1, 5);

  return (
    <div className="bg-[#f4f6fa] flex flex-col items-start w-full">
      {/* Header */}
      <div className="bg-white border-b border-[#e3e7ef] flex h-[72px] items-center justify-between px-6 w-full shrink-0">
        <div className="flex gap-3 items-center">
          <p className="font-['Inter:Bold'] font-bold text-[#ff315f] text-[20px] whitespace-nowrap">pulse.</p>
          <p className="font-['Inter:Medium'] font-medium text-[#5f687b] text-[13px] whitespace-nowrap">📍 {data.location}</p>
        </div>
        <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px] whitespace-nowrap">Cập nhật {data.updateTime}</p>
      </div>

      <div className="flex flex-col gap-6 p-5 w-full">
        <div className="flex gap-5 items-start w-full">
          {/* Weather column */}
          <div className="flex flex-col gap-3 items-start shrink-0 w-[calc(50%-10px)] max-w-[560px]">
            <WeatherColumn data={data} />
          </div>

          {/* News column */}
          <div className="flex flex-1 flex-col gap-3 items-start min-w-0 overflow-hidden">
            <div className="flex flex-col gap-[2px] items-start">
              <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[20px] tracking-[-0.3px]">Tin tức</p>
              <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px]">{data.location} · {data.news.length} bài mới nhất</p>
            </div>
            {feat && (
              <a
                href={feat.link}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-white flex flex-col items-start overflow-hidden rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full no-underline hover:shadow-lg transition-shadow"
              >
                <div className="h-[180px] relative rounded-tl-2xl rounded-tr-2xl w-full overflow-hidden bg-[#f4f6fa]">
                  <img
                    alt=""
                    className="absolute inset-0 max-w-none object-cover size-full"
                    src={feat.image || TABLET_FALLBACK_IMAGES[0]}
                    onError={(e) => onImgError(e, 0)}
                  />
                  <div className="absolute bg-[#ff315f] left-3 top-3 flex items-start px-[10px] py-1 rounded-[6px]">
                    <p className="font-['Inter:Bold'] font-bold text-[10px] text-white tracking-[0.5px] uppercase">NỔI BẬT</p>
                  </div>
                </div>
                <div className="flex flex-col gap-2 items-start p-[14px] w-full">
                  <p className="font-['Inter:Bold'] font-bold leading-[22px] text-[#182033] text-[15px] w-full line-clamp-2">{feat.title}</p>
                  <p className="font-['Inter:Regular'] font-normal leading-[18px] text-[#5f687b] text-[12px] w-full line-clamp-2">{feat.description}</p>
                  <div className="flex items-center justify-between pt-1 w-full">
                    <div className="flex gap-[6px] items-center">
                      <div className="bg-[#f7a928] rounded-[4px] size-2" />
                      <p className="font-['Inter:Semi_Bold'] font-semibold text-[#ff315f] text-[11px]">{feat.source}</p>
                    </div>
                    <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px]">{data.updateTime}</p>
                  </div>
                </div>
              </a>
            )}
            {sides.map((a, i) => {
              const c = TAB_CATS[i % TAB_CATS.length];
              return (
                <a
                  key={i}
                  href={a.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="bg-white flex gap-3 items-center overflow-hidden p-3 rounded-[10px] shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full no-underline hover:shadow-lg transition-shadow"
                >
                  <div className="relative rounded-[10px] shrink-0 size-[72px] overflow-hidden bg-[#f4f6fa]">
                    <img
                      alt=""
                      className="absolute inset-0 max-w-none object-cover size-full"
                      src={a.image || TABLET_FALLBACK_IMAGES[(i + 1) % TABLET_FALLBACK_IMAGES.length]}
                      onError={(e) => onImgError(e, i + 1)}
                    />
                  </div>
                  <div className="flex flex-1 flex-col gap-1 items-start min-w-0 overflow-hidden">
                    <div className={`${c.bg} flex items-start px-[7px] py-[2px] rounded-[4px]`}>
                      <p className={`font-['Inter:Bold'] font-bold ${c.color} text-[10px]`}>{c.cat}</p>
                    </div>
                    <p className="font-['Inter:Semi_Bold'] font-semibold leading-[19px] text-[#182033] text-[13px] line-clamp-2 w-full">{a.title}</p>
                    <div className="flex items-center justify-between text-[11px] w-full">
                      <p className="font-['Inter:Medium'] font-medium text-[#ff315f]">{a.source}</p>
                      <p className="font-['Inter:Regular'] font-normal text-[#5f687b]">Vừa cập nhật</p>
                    </div>
                  </div>
                </a>
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

function DesktopLayout({
  data,
  onPlayVideo,
}: {
  data: AppData;
  onPlayVideo: (v: VideoItem) => void;
}) {
  const feat = data.news[0];
  const grid = data.news.slice(1, 5);
  const now = new Date();
  const days = ["Chủ nhật", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7"];
  const dateStr = `${days[now.getDay()]}, ${now.getDate()} Tháng ${now.getMonth() + 1} - ${data.updateTime}`;

  return (
    <div className="bg-[#f4f6fa] flex flex-col items-start w-full">
      {/* Top Header Dashboard */}
      <div className="bg-white border-b border-[#e3e7ef] flex h-[72px] items-center justify-between px-6 w-full shrink-0">
        <div className="flex gap-4 items-center">
          <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[18px] whitespace-nowrap">Dashboard</p>
          <div className="bg-[#f4f6fa] flex items-start px-3 py-1 rounded-full">
            <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px] whitespace-nowrap">{dateStr}</p>
          </div>
        </div>
        <div className="bg-[#f4f6fa] border border-[#e3e7ef] flex gap-[10px] h-12 items-center overflow-hidden px-[14px] rounded-[10px] w-[300px]">
          <div className="relative shrink-0 size-[18px]"><img alt="" className="absolute inset-0 size-full" src={imgSearch} /></div>
          <p className="font-['Inter:Regular'] font-normal leading-[21px] text-[#5f687b] text-[14px] whitespace-nowrap">Tìm kiếm thời tiết, tin tức...</p>
        </div>
      </div>

      <div className="flex gap-6 items-start p-6 w-full">
        {/* Left Column (Weather) */}
        <div className="flex flex-col gap-4 items-start shrink-0 w-[420px]">
          <WeatherColumn data={data} />
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

          {/* Featured News Card */}
          {feat && (
            <a
              href={feat.link}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white flex flex-col gap-[14px] items-start overflow-hidden p-4 rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full no-underline hover:shadow-lg transition-shadow"
            >
              <div className="flex gap-[10px] items-center overflow-hidden w-full">
                <div className="bg-[#ffe8ee] flex flex-col items-center justify-center overflow-hidden rounded-full shrink-0 size-11">
                  <p className="font-['Inter:Bold'] font-bold text-[#ff315f] text-[15.84px]">{(feat.source || "N")[0]}</p>
                </div>
                <div className="flex flex-1 flex-col items-start min-w-0 overflow-hidden">
                  <p className="font-['Inter:Semi_Bold'] font-semibold text-[#182033] text-[14px]">{feat.source}</p>
                  <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px]">Vừa cập nhật</p>
                </div>
                <div className="relative shrink-0 size-5"><img alt="" className="absolute inset-0 size-full" src={imgMoreHorizontal} /></div>
              </div>
              <p className="font-['Inter:Regular'] font-normal leading-[21px] text-[#182033] text-[14px] w-full line-clamp-3">{feat.description || feat.title}</p>
              <div className="h-[180px] relative rounded-[10px] w-full overflow-hidden bg-[#f4f6fa]">
                <img
                  alt=""
                  className="absolute inset-0 max-w-none object-cover size-full"
                  src={feat.image || DESKTOP_FALLBACK_IMAGES[0]}
                  onError={(e) => onImgError(e, 0)}
                />
              </div>
              <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[13px]">{feat.source}</p>
            </a>
          )}

          {/* News Grid */}
          <div className="flex flex-wrap gap-3 items-start w-full">
            {grid.map((n, i) => (
              <a
                key={i}
                href={n.link}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-white flex flex-col items-start overflow-hidden rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-[calc(50%-6px)] no-underline hover:shadow-lg transition-shadow"
              >
                <div className="h-[140px] relative w-full overflow-hidden bg-[#f4f6fa]">
                  <img
                    alt=""
                    className="absolute inset-0 max-w-none object-cover size-full"
                    src={n.image || DESKTOP_FALLBACK_IMAGES[(i + 1) % DESKTOP_FALLBACK_IMAGES.length]}
                    onError={(e) => onImgError(e, i + 1)}
                  />
                </div>
                <div className="flex flex-col gap-[6px] items-start p-[14px] w-full">
                  <div className="flex gap-2 items-center">
                    <div className="bg-[#ffe8ee] flex items-start px-2 py-[3px] rounded-full">
                      <p className="font-['Inter:Semi_Bold'] font-semibold text-[#ff315f] text-[11px]">{n.source}</p>
                    </div>
                    <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px]">{data.updateTime}</p>
                  </div>
                  <p className="font-['Inter:Bold'] font-bold leading-5 text-[#182033] text-[14px] w-full line-clamp-2">{n.title}</p>
                  <p className="font-['Inter:Regular'] font-normal leading-[18px] text-[#5f687b] text-[12px] w-full line-clamp-2">{n.description}</p>
                </div>
              </a>
            ))}
          </div>

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
  const [activeVideo, setActiveVideo] = useState<VideoItem | null>(null);
  const refreshRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [weatherResult, newsResult, videoResult] = await Promise.all([
        fetchWeatherDirect(),
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
        location: DEFAULT_LOCATION,
      });
      setError(null);
      setLoading(false);
    } catch (err: any) {
      console.error("Load data failed:", err);
      setError(err.message || "Lỗi tải dữ liệu");
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    refreshRef.current = setInterval(loadData, 5 * 60 * 1000);
    return () => {
      if (refreshRef.current) clearInterval(refreshRef.current);
    };
  }, [loadData]);

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
    <div className="min-h-screen w-full bg-[#f4f6fa]">
      {/* Live status badge top-right */}
      <div className="fixed top-3 right-3 z-30 bg-white/80 backdrop-blur-sm border border-[#e3e7ef] rounded-full px-3 py-1 flex items-center gap-2 shadow-sm">
        <div className="size-2 rounded-full bg-[#22c55e] animate-pulse" />
        <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[10px]">LIVE · {data.updateTime}</p>
      </div>

      {/* Cinema Mode Video Modal */}
      <VideoModal video={activeVideo} onClose={() => setActiveVideo(null)} />

      {/* Responsive Breakpoints */}
      <div className="md:hidden">
        <MobileLayout data={data} onPlayVideo={setActiveVideo} />
      </div>
      <div className="hidden md:block xl:hidden">
        <TabletLayout data={data} onPlayVideo={setActiveVideo} />
      </div>
      <div className="hidden xl:block">
        <DesktopLayout data={data} onPlayVideo={setActiveVideo} />
      </div>
    </div>
  );
}
