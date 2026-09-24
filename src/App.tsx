import { createContext, useContext, useState, useEffect } from "react";
import LZString from "lz-string";

const defaultData = {
  weather: {
     temp: "30.4",
     condition: "Mây thưa ☁️",
     feels_like: "36.4",
     humidity: "71",
     pm25: "39.38",
     wind: "12",
     location: "Quận Hà Đông, Hà Nội",
  }
};
const DataContext = createContext(defaultData);
const useData = () => useContext(DataContext);

const assetPathPrefix = "/assets";

const imgMapPin = `${assetPathPrefix}/0eabf.svg`;
const imgClock = `${assetPathPrefix}/c681b.svg`;
const imgMoreHorizontal = `${assetPathPrefix}/eff74.svg`;
const imgSearch = `${assetPathPrefix}/ad518.svg`;

// News article images
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

// ── Shared sub-components ────────────────────────────────────────────────────

function WeatherWarning({ className = "" }: { className?: string }) {
  return (
    <div
      className={`bg-[#fff8e1] border-l-4 border-[#f7a928] flex gap-3 items-start overflow-hidden p-[14px] rounded-2xl ${className}`}
    >
      <p className="font-['Inter:Regular'] font-normal leading-normal shrink-0 text-[20px] text-black">⚠️</p>
      <div className="flex flex-col gap-1 items-start min-w-0">
        <p className="font-['Inter:Bold'] font-bold leading-normal text-[#e65100] text-[13px] whitespace-nowrap">
          Cảnh báo trọng tâm
        </p>
        <p className="font-['Inter:Regular'] font-normal leading-[18px] text-[#5d4037] text-[12px]">
          Trời đang tạnh ráo (Mây thưa), nhưng mây dông đang tích tụ. Dự báo vài giờ tới có khả năng đổ mưa (Xác suất: 100%).
        </p>
      </div>
    </div>
  );
}

function ActivitySuggestion({ className = "" }: { className?: string }) {
  return (
    <div
      className={`bg-white flex gap-3 items-start overflow-hidden p-[14px] rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] ${className}`}
    >
      <p className="font-['Inter:Regular'] font-normal leading-normal shrink-0 text-[20px] text-black">💡</p>
      <div className="flex flex-col gap-1 items-start min-w-0">
        <p className="font-['Inter:Bold'] font-bold leading-normal text-[#182033] text-[13px] whitespace-nowrap">
          Gợi ý lịch trình thực tế
        </p>
        <p className="font-['Inter:Regular'] font-normal leading-[18px] text-[#5f687b] text-[12px]">
          Lộ trình: Trời chưa mưa nhưng nên mang sẵn áo mưa dự phòng. Ra ngoài trước 11h để tránh cơn mưa buổi trưa.
        </p>
      </div>
    </div>
  );
}

// ── Mobile Layout ────────────────────────────────────────────────────────────

function MobileLayout() {
  const data = useData();
  return (
    <div className="bg-[#f4f6fa] flex flex-col items-start w-full" data-node-id="1:41">
      {/* Top bar */}
      <div className="bg-white border-b border-[#e3e7ef] flex h-[72px] items-center justify-between px-4 w-full shrink-0">
        <div className="flex flex-col gap-[2px] items-start">
          <p className="font-['Inter:Bold'] font-bold text-[#ff315f] text-[20px]">pulse.</p>
          <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px]">Quận Hà Đông, HN</p>
        </div>
        <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px]">Cập nhật lúc 10:09</p>
      </div>

      {/* Main content */}
      <div className="flex flex-col gap-5 items-start pb-6 pt-4 px-4 w-full">
        {/* Weather section */}
        <div className="flex flex-col gap-3 items-start w-full">
          <p className="font-['Inter:Semi_Bold'] font-semibold leading-[26px] text-[#182033] text-[20px]">Thời tiết</p>

          {/* Weather hero card */}
          <div className="bg-gradient-to-r from-[#ff8c42] to-[#ff315f] flex flex-col items-start overflow-hidden p-5 rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full">
            <div className="flex gap-[6px] items-center w-full">
              <div className="relative shrink-0 size-[14px]">
                <img alt="" className="absolute inset-0 max-w-none size-full" src={imgMapPin} />
              </div>
              <p className="font-['Inter:Semi_Bold'] font-semibold opacity-90 text-[13px] text-white whitespace-nowrap">
                {data.weather.location}
              </p>
            </div>
            <div className="flex flex-col items-start pt-4 w-full">
              <div className="flex items-end justify-between w-full">
                <div className="flex flex-col gap-1 items-start">
                  <p className="font-['Inter:Bold'] font-bold text-[64px] text-white whitespace-nowrap">{data.weather.temp}°</p>
                  <p className="font-['Inter:Medium'] font-medium opacity-90 text-[18px] text-white whitespace-nowrap">{data.weather.condition}</p>
                </div>
                <p className="font-['Inter:Regular'] font-normal text-[52px] text-black">⛅</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 items-start pt-5 w-full">
              {[
                { label: "Cảm nhận", value: "{data.weather.feels_like}°C" },
                { label: "Độ ẩm", value: "{data.weather.humidity}%" },
                { label: "PM2.5", value: "{data.weather.pm25}" },
                { label: "Gió", value: "{data.weather.wind} km/h" },
              ].map((m) => (
                <div key={m.label} className="bg-[rgba(255,255,255,0.15)] flex flex-col items-start px-3 py-[6px] rounded-full text-white">
                  <p className="font-['Inter:Regular'] font-normal opacity-75 text-[11px]">{m.label}</p>
                  <p className="font-['Inter:Bold'] font-bold text-[14px]">{m.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* 3h forecast */}
          <div className="bg-white flex flex-col gap-3 items-start overflow-hidden p-4 rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full">
            <div className="flex items-center justify-between w-full">
              <p className="font-['Inter:Semi_Bold'] font-semibold text-[#182033] text-[13px]">Dự báo 3 giờ tới</p>
              <div className="relative shrink-0 size-4">
                <img alt="" className="absolute inset-0 max-w-none size-full" src={imgClock} />
              </div>
            </div>
            <div className="flex items-start w-full">
              {[
                { time: "10:00", icon: "⛅", temp: "30°", pct: "0%", pctBg: "bg-[#e8f5e9]", pctColor: "text-[#2e7d32]" },
                { time: "11:00", icon: "🌦", temp: "29°", pct: "40%", pctBg: "bg-[#e3f2fd]", pctColor: "text-[#1565c0]" },
                { time: "12:00", icon: "🌧", temp: "28°", pct: "100%", pctBg: "bg-[#e3f2fd]", pctColor: "text-[#1565c0]" },
                { time: "13:00", icon: "🌧", temp: "27°", pct: "100%", pctBg: "bg-[#e3f2fd]", pctColor: "text-[#1565c0]" },
              ].map((h) => (
                <div key={h.time} className="flex flex-1 flex-col gap-[6px] items-center min-w-0">
                  <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px]">{h.time}</p>
                  <p className="font-['Inter:Regular'] font-normal text-[24px] text-black">{h.icon}</p>
                  <p className="font-['Inter:Semi_Bold'] font-semibold text-[#182033] text-[13px]">{h.temp}</p>
                  <div className={`${h.pctBg} flex items-start px-[6px] py-[2px] rounded-full`}>
                    <p className={`font-['Inter:Semi_Bold'] font-semibold ${h.pctColor} text-[10px]`}>{h.pct}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <WeatherWarning />
          <ActivitySuggestion />
        </div>

        {/* News section */}
        <div className="flex flex-col gap-3 items-start w-full">
          <p className="font-['Inter:Semi_Bold'] font-semibold leading-[26px] text-[#182033] text-[20px]">Tin tức</p>

          {[
            { avatar: imgNews1, author: "Cạnh đảo nổi dừng Tết, làng đảo Hà Đông vào mùa cao điểm", src: "eva.vn · 10:09 AM", body: "Người dân làng chài tấp nập chuẩn bị cho mùa du lịch cao điểm năm nay sau kỳ nghỉ Tết.", img: imgNews1 },
            { avatar: imgNews2, author: "Quần ống rộng giúp quý cô mặc đẹp cả tuần", src: "Thanh Niên · 09:45 AM", body: "Từ đi làm đến đi chơi, bí quyết phối đồ với quần ống rộng phong cách công sở hiện đại.", img: imgNews2 },
            { avatar: null, author: "Hà Nội: Dự báo mưa lớn chiều tối nay, người dân cần chú ý", src: "VnExpress · 09:15 AM", body: "Cơ quan khí tượng thủy văn cảnh báo mưa vừa đến mưa to có thể xảy ra tại nhiều quận huyện.", img: imgNews3 },
            { avatar: null, author: "Chứng khoán Việt Nam tăng mạnh phiên đầu tuần", src: "CafeF · 08:50 AM", body: "VN-Index bứt phá vượt ngưỡng kháng cự, dòng tiền đổ mạnh vào nhóm cổ phiếu vốn hóa lớn.", img: imgNews4 },
            { avatar: null, author: "Đội tuyển Việt Nam chốt danh sách chuẩn bị AFF Cup 2025", src: "Tuổi Trẻ · 08:20 AM", body: "HLV trưởng đội tuyển Việt Nam công bố 25 cầu thủ tập trung cho vòng loại AFF Cup sắp tới.", img: imgNews5 },
          ].map((item, i) => (
            <div key={i} className="bg-white flex flex-col gap-[14px] items-start overflow-hidden p-4 rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full">
              <div className="flex gap-[10px] items-center overflow-hidden w-full">
                <div className="flex flex-col items-center justify-center overflow-hidden rounded-full shrink-0 size-11">
                  {item.avatar ? (
                    <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none rounded-full size-full relative" src={item.avatar} style={{ position: "relative" }} />
                  ) : (
                    <div className="bg-[#ffe8ee] flex items-center justify-center rounded-full size-full">
                      <p className="font-['Inter:Bold'] font-bold text-[#ff315f] text-[15px]">N</p>
                    </div>
                  )}
                </div>
                <div className="flex flex-1 flex-col items-start min-w-0 overflow-hidden">
                  <p className="font-['Inter:Semi_Bold'] font-semibold text-[#182033] text-[14px] line-clamp-1">{item.author}</p>
                  <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px]">{item.src}</p>
                </div>
                <div className="relative shrink-0 size-5">
                  <img alt="" className="absolute inset-0 max-w-none size-full" src={imgMoreHorizontal} />
                </div>
              </div>
              <p className="font-['Inter:Regular'] font-normal leading-[21px] text-[#182033] text-[14px]">{item.body}</p>
              <div className="h-[180px] relative rounded-[10px] w-full overflow-hidden">
                <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={item.img} />
              </div>
              <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[13px]">📰 {item.src}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Tablet Layout ────────────────────────────────────────────────────────────

function TabletLayout() {
  const data = useData();
  return (
    <div className="bg-[#f4f6fa] flex flex-col items-start w-full" data-node-id="1:183">
      {/* Top bar */}
      <div className="bg-white border-b border-[#e3e7ef] flex h-[72px] items-center justify-between px-6 w-full shrink-0">
        <div className="flex gap-3 items-center">
          <p className="font-['Inter:Bold'] font-bold text-[#ff315f] text-[20px] whitespace-nowrap">pulse.</p>
          <p className="font-['Inter:Medium'] font-medium text-[#5f687b] text-[13px] whitespace-nowrap">📍 {data.weather.location}</p>
        </div>
        <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px] whitespace-nowrap">Cập nhật 10:09 SA</p>
      </div>

      {/* Content */}
      <div className="flex gap-5 items-start overflow-hidden p-5 w-full">
        {/* Weather column */}
        <div className="flex flex-col gap-4 items-start shrink-0 w-[calc(50%-10px)] max-w-[580px]">
          {/* Dark weather hero */}
          <div className="bg-gradient-to-r from-[#2d3a4a] to-[#1a2535] flex flex-col items-start overflow-hidden p-6 rounded-2xl shadow-[0px_8px_24px_0px_rgba(23,33,51,0.5)] w-full">
            <div className="flex items-center justify-between w-full">
              <div className="flex gap-[6px] items-center font-['Inter:Medium'] font-medium text-[13px]">
                <p className="text-[rgba(255,255,255,0.6)]">📍</p>
                <p className="text-[rgba(255,255,255,0.8)] tracking-[0.2px]">{data.weather.location}</p>
              </div>
              <p className="font-['Inter:Regular'] font-normal text-[11px] text-[rgba(255,255,255,0.4)]">Cập nhật 10:09 SA</p>
            </div>
            <div className="flex flex-col gap-1 items-start pt-5 w-full">
              <div className="bg-[rgba(255,255,255,0.1)] border border-[rgba(255,255,255,0.15)] flex items-start px-[10px] py-1 rounded-[6px]">
                <p className="font-['Inter:Bold'] font-bold text-[#f7a928] text-[11px] tracking-[0.8px] uppercase">🌤 MÂY THƯA</p>
              </div>
              <div className="flex gap-2 items-end pt-2">
                <p className="font-['Inter:Bold'] font-bold text-[64px] text-white tracking-[-2px] leading-[64px]">{data.weather.temp}</p>
                <p className="font-['Inter:Light'] font-light text-[28px] text-[rgba(255,255,255,0.67)]">°C</p>
              </div>
              <p className="font-['Inter:Regular'] font-normal leading-5 text-[14px] text-[rgba(255,255,255,0.6)]">Cảm nhận như {data.weather.feels_like}°C</p>
            </div>
            <div className="flex items-center pt-6 w-full">
              {[
                { icon: "💧", value: "{data.weather.humidity}%", label: "ĐỘ ẨM", align: "items-start" },
                { icon: null, value: null, label: null, divider: true },
                { icon: "🫧", value: "{data.weather.pm25}", label: "BỤI MỊN PM2.5 μg/m³", align: "items-center", badge: "✓ ĐẠT" },
                { icon: null, value: null, label: null, divider: true },
                { icon: "🌬", value: "{data.weather.wind} km/h", label: "GIÓ", align: "items-end" },
              ].map((m, i) => {
                if (m.divider) return <div key={i} className="bg-[rgba(255,255,255,0.15)] h-[52px] shrink-0 w-px" />;
                return (
                  <div key={i} className={`border-t border-[rgba(255,255,255,0.1)] flex flex-1 flex-col gap-1 ${m.align} min-w-0 overflow-hidden pt-4`}>
                    <p className="font-['Inter:Regular'] font-normal text-[20px] text-black">{m.icon}</p>
                    <div className="flex gap-[6px] items-center">
                      <p className="font-['Inter:Bold'] font-bold text-[22px] text-white whitespace-nowrap">{m.value}</p>
                      {m.badge && (
                        <div className="bg-[rgba(34,197,94,0.15)] flex items-start px-[6px] py-[2px] rounded-[4px]">
                          <p className="font-['Inter:Bold'] font-bold text-[#4ade80] text-[10px]">{m.badge}</p>
                        </div>
                      )}
                    </div>
                    <p className="font-['Inter:Regular'] font-normal text-[11px] text-[rgba(255,255,255,0.6)] tracking-[0.3px]">{m.label}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* 3h forecast */}
          <div className="bg-white flex flex-col gap-3 items-start overflow-hidden p-4 rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full">
            <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[13px] tracking-[0.3px] uppercase">📅 DỰ BÁO 3 GIỜ TỚI</p>
            <div className="flex items-start w-full">
              {[
                { label: "BÂY GIỜ", icon: "🌤", temp: "30°", desc: "Mây thưa", active: true },
                { label: "11:00", icon: "🌦", temp: "29°", desc: "Mưa nhẹ", active: false },
                { label: "12:00", icon: "🌧", temp: "28°", desc: "Mưa", active: false },
                { label: "13:00", icon: "🌧", temp: "27°", desc: "Mưa", active: false },
              ].map((h) => (
                <div key={h.label} className={`flex flex-1 flex-col gap-[6px] items-center min-w-0 overflow-hidden p-2 ${h.active ? "bg-[#ffe8ee] rounded-[10px]" : ""}`}>
                  <p className={`font-['Inter:Semi_Bold'] font-semibold text-[11px] ${h.active ? "text-[#ff315f]" : "text-[#5f687b]"}`}>{h.label}</p>
                  <p className="font-['Inter:Regular'] font-normal text-[22px] text-black">{h.icon}</p>
                  <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[16px]">{h.temp}</p>
                  <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[10px]">{h.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <WeatherWarning className="border-l-4 border-[#f7a928] bg-[#fff8e6] rounded-[10px]" />
          <ActivitySuggestion className="rounded-[10px]" />
        </div>

        {/* News panel */}
        <div className="flex flex-1 flex-col gap-3 items-start min-w-0 overflow-hidden">
          <div className="flex items-center justify-between w-full">
            <div className="flex flex-col gap-[2px] items-start">
              <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[20px] tracking-[-0.3px]">Tin tức</p>
              <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px]">Quận Hà Đông · 5 bài mới nhất</p>
            </div>
          </div>

          {/* Featured article */}
          <div className="bg-white flex flex-col items-start overflow-hidden rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full">
            <div className="h-[180px] relative rounded-tl-2xl rounded-tr-2xl w-full overflow-hidden">
              <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={imgNews1} />
              <div className="absolute bg-[#ff315f] flex items-start left-3 px-[10px] py-1 rounded-[6px] top-3">
                <p className="font-['Inter:Bold'] font-bold text-[10px] text-white tracking-[0.5px] uppercase">NỔI BẬT</p>
              </div>
            </div>
            <div className="flex flex-col gap-2 items-start overflow-hidden p-[14px] w-full">
              <p className="font-['Inter:Bold'] font-bold leading-[22px] text-[#182033] text-[15px] w-full">
                Cảnh đảo nổi dừng Tết, làng đảo Hà Đông vào mùa cao điểm - eva.vn
              </p>
              <p className="font-['Inter:Regular'] font-normal leading-[18px] text-[#5f687b] text-[12px] w-full">
                Quần ống rộng giúp quý cô mặc đẹp cả tuần, từ đi làm đến đi chơi. Bản phối ngày đầu thu hướng đến hình ảnh cô diễn giao hòa với phong cách công sở hiện đại.
              </p>
              <div className="flex items-center justify-between pt-1 w-full">
                <div className="flex gap-[6px] items-center">
                  <div className="bg-[#f7a928] rounded-[4px] size-2" />
                  <p className="font-['Inter:Semi_Bold'] font-semibold text-[#ff315f] text-[11px]">Thanh Niên</p>
                </div>
                <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px]">10:09 SA</p>
              </div>
            </div>
          </div>

          {/* Article list */}
          {[
            { img: imgNews2, cat: "KINH TẾ", catBg: "bg-[#ffe8ee]", catColor: "text-[#ff315f]", title: "Hà Đông đầu tư hạ tầng giao thông, kỳ vọng thu hút đầu tư mới năm 2025", src: "VnExpress", time: "2 giờ trước" },
            { img: imgTabletNews3, cat: "XÃ HỘI", catBg: "bg-[#e0f2fe]", catColor: "text-[#0369a1]", title: "Lễ hội truyền thống làng Mọc Quan Nhân thu hút hàng nghìn người tham dự", src: "Dân Trí", time: "4 giờ trước" },
            { img: imgTabletNews4, cat: "QUY HOẠCH", catBg: "bg-[#fef3c7]", catColor: "text-[#92400e]", title: "Dự án metro Hà Nội sắp thông xe ga Hà Đông - người dân háo hức chờ đón", src: "Tuổi Trẻ", time: "6 giờ trước" },
            { img: imgTabletNews5, cat: "ẨM THỰC", catBg: "bg-[#f0fdf4]", catColor: "text-[#166534]", title: "Top 10 quán bún bò nổi tiếng tại Hà Đông được giới trẻ check-in nhiều nhất hè này", src: "Zing News", time: "8 giờ trước" },
          ].map((a, i) => (
            <div key={i} className="bg-white flex gap-3 items-center overflow-hidden p-3 rounded-[10px] shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full">
              <div className="bg-[#f4f6fa] relative rounded-[10px] shrink-0 size-[72px] overflow-hidden">
                <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={a.img} />
              </div>
              <div className="flex flex-1 flex-col gap-1 items-start min-w-0 overflow-hidden">
                <div className={`${a.catBg} flex items-start px-[7px] py-[2px] rounded-[4px]`}>
                  <p className={`font-['Inter:Bold'] font-bold ${a.catColor} text-[10px]`}>{a.cat}</p>
                </div>
                <p className="font-['Inter:Semi_Bold'] font-semibold leading-[19px] text-[#182033] text-[13px] overflow-hidden text-ellipsis line-clamp-2">{a.title}</p>
                <div className="flex items-center justify-between text-[11px] w-full">
                  <p className="font-['Inter:Medium'] font-medium text-[#ff315f]">{a.src}</p>
                  <p className="font-['Inter:Regular'] font-normal text-[#5f687b]">{a.time}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Desktop Layout ───────────────────────────────────────────────────────────

function DesktopLayout() {
  const data = useData();
  return (
    <div className="bg-[#f4f6fa] flex flex-col items-start w-full" data-node-id="1:323">
      {/* Top bar */}
      <div className="bg-white border-b border-[#e3e7ef] flex h-[72px] items-center justify-between px-6 w-full shrink-0">
        <div className="flex gap-4 items-center">
          <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[18px] whitespace-nowrap">Dashboard</p>
          <div className="bg-[#f4f6fa] flex items-start px-3 py-1 rounded-full">
            <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px] whitespace-nowrap">Thứ 4, 18 Tháng 6 · 10:09 SA</p>
          </div>
        </div>
        <div className="bg-[#f4f6fa] border border-[#e3e7ef] flex gap-[10px] h-12 items-center overflow-hidden px-[14px] rounded-[10px] w-[300px]">
          <div className="relative shrink-0 size-[18px]">
            <img alt="" className="absolute inset-0 max-w-none size-full" src={imgSearch} />
          </div>
          <p className="font-['Inter:Regular'] font-normal leading-[21px] text-[#5f687b] text-[14px] whitespace-nowrap">Tìm kiếm thời tiết, tin tức...</p>
        </div>
      </div>

      {/* Content */}
      <div className="flex gap-6 items-start overflow-hidden p-6 w-full">
        {/* Weather column */}
        <div className="flex flex-col gap-4 items-start shrink-0 w-[480px]">
          {/* Hero */}
          <div
            className="flex flex-col h-[260px] items-start overflow-hidden relative rounded-2xl w-full"
            style={{ background: "linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 50%, #f7a928 100%)" }}
          >
            <div className="absolute bg-[rgba(0,0,0,0.18)] inset-0" />
            <div className="flex flex-1 flex-col items-start min-h-0 pb-6 pt-7 px-7 relative w-full">
              <div className="flex items-center justify-between w-full">
                <div className="flex gap-[6px] items-center text-[14px] text-white">
                  <p className="font-['Inter:Regular'] font-normal">📍</p>
                  <p className="font-['Inter:Semi_Bold'] font-semibold">{data.weather.location}</p>
                </div>
                <p className="font-['Inter:Regular'] font-normal text-[12px] text-[rgba(255,255,255,0.7)]">Cập nhật 10:09 SA</p>
              </div>
              <div className="flex gap-4 items-center mt-2 w-full">
                <div className="flex flex-1 flex-col gap-[2px] items-start min-w-0">
                  <div className="flex items-baseline">
                    <p className="font-['Inter:Extra_Bold'] font-extrabold leading-[80px] text-[72px] text-white whitespace-nowrap">30°C</p>
                  </div>
                  <p className="font-['Inter:Regular'] font-normal text-[15px] text-[rgba(255,255,255,0.85)] whitespace-nowrap">Cảm nhận {data.weather.feels_like}°C</p>
                  <p className="font-['Inter:Semi_Bold'] font-semibold text-[16px] text-white whitespace-nowrap">🌤 Mây thưa</p>
                </div>
                <p className="font-['Inter:Regular'] font-normal text-[80px] text-black">🌤</p>
              </div>
            </div>
          </div>

          {/* Metrics row */}
          <div className="flex gap-3 items-start w-full">
            {[
              { icon: "💧", value: "{data.weather.humidity}%", label: "Độ ẩm" },
              { icon: "🌫", value: "{data.weather.pm25}", label: "Bụi mịn PM2.5 µg/m³", badge: "Tốt" },
              { icon: "💨", value: "{data.weather.wind} km/h", label: "Tốc độ gió" },
            ].map((m, i) => (
              <div key={i} className="bg-white drop-shadow-[0px_4px_6px_rgba(23,33,51,0.1)] flex flex-1 flex-col gap-2 items-start min-w-0 p-4 rounded-2xl">
                <p className="font-['Inter:Regular'] font-normal text-[22px] text-black">{m.icon}</p>
                <div className="flex gap-1 items-center">
                  <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[22px] whitespace-nowrap">{m.value}</p>
                  {m.badge && (
                    <div className="bg-[#dcfce7] flex flex-col items-start px-[6px] py-[2px] rounded-full">
                      <p className="font-['Inter:Bold'] font-bold text-[#16a34a] text-[10px]">{m.badge}</p>
                    </div>
                  )}
                </div>
                <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px]">{m.label}</p>
              </div>
            ))}
          </div>

          {/* Forecast card */}
          <div className="bg-white drop-shadow-[0px_4px_6px_rgba(23,33,51,0.1)] flex flex-col gap-[14px] items-start p-5 rounded-2xl w-full">
            <div className="flex items-center justify-between w-full">
              <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[15px]">Dự báo 3 giờ tới</p>
              <p className="font-['Inter:Semi_Bold'] font-semibold text-[#ff315f] text-[12px]">Xem chi tiết →</p>
            </div>
            <div className="flex items-start w-full">
              {[
                { time: "10:00", icon: "🌤", temp: "30°", pct: "0%", active: true },
                { time: "11:00", icon: "⛅", temp: "31°", pct: "20%", active: false },
                { time: "12:00", icon: "🌧", temp: "30°", pct: "100%", active: false, pctColor: "text-[#3b82f6]" },
              ].map((h, i) => (
                <div
                  key={h.time}
                  className={`flex flex-1 flex-col gap-[6px] items-center min-w-0 px-2 py-3
                    ${h.active ? "bg-[#ffe8ee] rounded-bl-[10px] rounded-tl-[10px]" : "bg-[#f4f6fa]"}
                    ${i === 2 ? "rounded-br-[10px] rounded-tr-[10px]" : ""}`}
                >
                  <p className={`font-['Inter:Semi_Bold'] font-semibold text-[12px] ${h.active ? "text-[#ff315f]" : "text-[#5f687b]"}`}>{h.time}</p>
                  <p className="font-['Inter:Regular'] font-normal text-[24px] text-black">{h.icon}</p>
                  <p className="font-['Inter:Bold'] font-bold text-[#182033] text-[14px]">{h.temp}</p>
                  <p className={`font-['Inter:Regular'] font-normal ${h.pctColor ?? "text-[#5f687b]"} text-[11px]`}>{h.pct}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Warning card */}
          <div className="bg-[#fff7ed] border border-[#f97316] flex flex-col gap-[10px] items-start overflow-hidden p-4 rounded-2xl w-full">
            <div className="flex gap-2 items-center">
              <p className="font-['Inter:Regular'] font-normal text-[18px] text-black">⚠️</p>
              <p className="font-['Inter:Bold'] font-bold text-[#c2410c] text-[14px]">Cảnh báo trọng tâm</p>
            </div>
            <p className="font-['Inter:Regular'] font-normal leading-5 text-[#9a3412] text-[13px] w-full">
              Trời đang tạnh ráo (Mây thưa), nhưng mây dông đang tích tụ. Dự báo vài giờ tới có khả năng đổ mưa (Xác suất: 100%).
            </p>
          </div>

          {/* Suggestion card */}
          <div className="bg-[#f0fdf4] border border-[#22c55e] flex flex-col gap-[10px] items-start overflow-hidden p-4 rounded-2xl w-full">
            <div className="flex gap-2 items-center">
              <p className="font-['Inter:Regular'] font-normal text-[18px] text-black">💡</p>
              <p className="font-['Inter:Bold'] font-bold text-[#15803d] text-[14px]">Gợi ý lịch trình thực tế</p>
            </div>
            <p className="font-['Inter:Regular'] font-normal leading-5 text-[#166534] text-[13px] w-full">
              Lộ trình: Trời chưa mưa nhưng cần mang sẵn áo mưa dự phòng.
            </p>
          </div>
        </div>

        {/* News column */}
        <div className="flex flex-1 flex-col gap-4 items-start min-w-0 overflow-hidden">
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

          {/* Featured feed card */}
          <div className="bg-white flex flex-col gap-[14px] items-start overflow-hidden p-4 rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-full">
            <div className="flex gap-[10px] items-center overflow-hidden w-full">
              <div className="bg-[#ffe8ee] flex flex-col items-center justify-center overflow-hidden rounded-full shrink-0 size-11">
                <p className="font-['Inter:Bold'] font-bold text-[#ff315f] text-[15.84px]">H</p>
              </div>
              <div className="flex flex-1 flex-col items-start min-w-0 overflow-hidden">
                <p className="font-['Inter:Semi_Bold'] font-semibold text-[#182033] text-[14px]">Howard Barton</p>
                <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[12px]">2 hours ago</p>
              </div>
              <div className="relative shrink-0 size-5">
                <img alt="" className="absolute inset-0 max-w-none size-full" src={imgMoreHorizontal} />
              </div>
            </div>
            <p className="font-['Inter:Regular'] font-normal leading-[21px] text-[#182033] text-[14px] w-full">
              Canh đảo nở dừng Tết, làng đảo Hà Đông vào mùa cao điểm - phong trào du lịch cộng đồng ngày càng nở rộ tại các vùng ven đô.
            </p>
            <div className="h-[180px] relative rounded-[10px] w-full overflow-hidden">
              <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={imgNews1} />
            </div>
            <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[13px]">♡ 2,341 ◯ 128 · eva.vn</p>
          </div>

          {/* News grid */}
          <div className="flex flex-wrap gap-3 items-start w-full">
            {[
              { img: imgNews2, src: "Thanh Niên", time: "10:09 SA", title: "Quần ống rộng giúp quý cô mặc đẹp cả tuần, từ đi làm đến đi chơi", desc: "Bạn phối ngày đầu thu hướng đến hình ảnh cô điển giao hòa với phong cách công sở hiện đại." },
              { img: imgDesktopNews3, src: "VnExpress", time: "9:45 SA", title: "Dự báo thời tiết Hà Nội: Chiều tối có mưa rào và dông cục bộ", desc: "Cơ quan khí tượng dự báo Hà Nội chiều tối có mưa rào, nhiệt độ giảm 2-3 độ so với sáng." },
              { img: imgDesktopNews4, src: "ICTNews", time: "9:12 SA", title: "Việt Nam đẩy mạnh chuyển đổi số trong lĩnh vực y tế và giáo dục", desc: "Bộ TT&TT công bố lộ trình chuyển đổi số 2024-2025 với trọng tâm là y tế số và giáo dục thông minh." },
              { img: imgDesktopNews5, src: "Tuổi Trẻ", time: "8:55 SA", title: "Đội tuyển U23 Việt Nam chuẩn bị cho vòng loại giải châu Á 2025", desc: "HLV Hoàng Anh Tuấn công bố danh sách 25 cầu thủ tham dự vòng loại U23 châu Á tại Uzbekistan." },
            ].map((n, i) => (
              <div key={i} className="bg-white flex flex-col items-start overflow-hidden rounded-2xl shadow-[0px_4px_12px_0px_rgba(23,33,51,0.1)] w-[calc(50%-6px)]">
                <div className="h-[140px] relative w-full overflow-hidden">
                  <img alt="" className="absolute inset-0 max-w-none object-cover pointer-events-none size-full" src={n.img} />
                </div>
                <div className="flex flex-col gap-[6px] items-start p-[14px] w-full">
                  <div className="flex gap-2 items-center">
                    <div className="bg-[#ffe8ee] flex items-start px-2 py-[3px] rounded-full">
                      <p className="font-['Inter:Semi_Bold'] font-semibold text-[#ff315f] text-[11px]">{n.src}</p>
                    </div>
                    <p className="font-['Inter:Regular'] font-normal text-[#5f687b] text-[11px]">{n.time}</p>
                  </div>
                  <p className="font-['Inter:Bold'] font-bold leading-5 text-[#182033] text-[14px] w-full">{n.title}</p>
                  <p className="font-['Inter:Regular'] font-normal leading-[18px] text-[#5f687b] text-[12px] w-full line-clamp-2">{n.desc}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Load more */}
          <div className="flex items-start justify-center py-2 w-full">
            <div className="bg-white border border-[#e3e7ef] drop-shadow-[0px_4px_6px_rgba(23,33,51,0.1)] flex items-start px-7 py-[10px] rounded-full">
              <p className="font-['Inter:Semi_Bold'] font-semibold text-[#5f687b] text-[13px]">Xem thêm tin tức</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Root ─────────────────────────────────────────────────────────────────────

export default function App() {
  const [data, setData] = useState(defaultData);
  
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const d = params.get("data");
    if (d) {
      try {
        const decoded = LZString.decompressFromEncodedURIComponent(d);
        if (decoded) {
            setData({ ...defaultData, ...JSON.parse(decoded) });
        }
      } catch (e) {
        console.error(e);
      }
    }
  }, []);

  return (
    <DataContext.Provider value={data}>
      <div className="min-h-screen w-full bg-[#f4f6fa]">
        <div className="md:hidden"><MobileLayout /></div>
        <div className="hidden md:block xl:hidden"><TabletLayout /></div>
        <div className="hidden xl:block"><DesktopLayout /></div>
      </div>
    </DataContext.Provider>
  );
}
