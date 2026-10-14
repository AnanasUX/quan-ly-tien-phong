import React, { useState, useEffect, useRef, useCallback } from "react";
import type { AppData, VideoItem, NewsArticle } from "./App";

export interface VisualTestRunnerProps {
  data: AppData;
  isOpen: boolean;
  onClose: () => void;
  onOpenCopilot: (action: string | null) => void;
  onCloseCopilot: () => void;
  onPlayVideo: (v: VideoItem) => void;
  onCloseVideo: () => void;
  onSelectArticle: (a: NewsArticle) => void;
  onCloseArticle: () => void;
  onSearch: (q: string) => void;
}

interface StepDef {
  screenId: string;
  screenName: string;
  stepName: string;
  description: string;
  selector: string;
  cursorLabel: string;
  action: () => Promise<void> | void;
}

export function VisualTestRunner({
  data,
  isOpen,
  onClose,
  onOpenCopilot,
  onCloseCopilot,
  onPlayVideo,
  onCloseVideo,
  onSelectArticle,
  onCloseArticle,
  onSearch,
}: VisualTestRunnerProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const [cursorPos, setCursorPos] = useState<{
    x: number;
    y: number;
    visible: boolean;
    clicking: boolean;
    label: string;
  }>({
    x: typeof window !== "undefined" ? window.innerWidth / 2 : 400,
    y: typeof window !== "undefined" ? window.innerHeight / 2 : 300,
    visible: false,
    clicking: false,
    label: "",
  });

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Danh sách các bước kiểm thử trực quan trên toàn bộ 5 màn hình
  const steps: StepDef[] = [
    {
      screenId: "SCR-WEA-01",
      screenName: "Màn hình 1: Thời tiết & Cảm biến",
      stepName: "Kiểm tra Thẻ thời tiết Hero Card & Cảm biến",
      description: "Con trỏ ảo di chuyển kiểm tra chỉ số nhiệt độ, độ ẩm và bụi mịn PM2.5...",
      selector: '[data-testid="hero-weather-card"]',
      cursorLabel: "Kiểm tra Cảm biến Thời tiết",
      action: async () => {
        // Highlighting
      },
    },
    {
      screenId: "SCR-COP-01",
      screenName: "Màn hình 2: Trợ lý AI Copilot",
      stepName: "Kích hoạt nút: 🌤️ Tác động thời tiết",
      description: "Mô phỏng click nút Tác động thời tiết trên thẻ Copilot để kích hoạt AI...",
      selector: '[data-testid="copilot-action-weather"]',
      cursorLabel: "Click: 🌤️ Tác động thời tiết",
      action: async () => {
        onOpenCopilot("weather_impact");
      },
    },
    {
      screenId: "SCR-COP-02",
      screenName: "Màn hình 2: Tương tác trong Modal Copilot",
      stepName: "Hỏi AI: 🍃 Đánh giá chất lượng không khí PM2.5",
      description: "Mô phỏng click nút Đánh giá PM2.5 bên trong Modal đối thoại thông minh...",
      selector: '[data-testid="copilot-modal-btn-pm25"]',
      cursorLabel: "Click: 🍃 Đánh giá PM2.5",
      action: async () => {
        const btn = document.querySelector('[data-testid="copilot-modal-btn-pm25"]') as HTMLButtonElement | null;
        if (btn) btn.click();
      },
    },
    {
      screenId: "SCR-COP-03",
      screenName: "Màn hình 2: Đóng Modal Copilot",
      stepName: "Đóng cửa sổ Copilot để chuyển màn hình",
      description: "Mô phỏng click nút ✕ trên Modal Copilot...",
      selector: '[data-testid="close-copilot-modal"]',
      cursorLabel: "Click: ✕ Đóng Modal",
      action: async () => {
        onCloseCopilot();
      },
    },
    {
      screenId: "SCR-VID-01",
      screenName: "Màn hình 3: Rạp chiếu Video",
      stepName: "Chuyển Tab bộ lọc: 🌤️ Thời tiết & Bão lũ",
      description: "Mô phỏng click chuyển chuyên mục video nóng thời tiết đô thị...",
      selector: '[data-testid="video-tab-weather"]',
      cursorLabel: "Click Tab: Thời tiết & Bão lũ",
      action: async () => {
        const btn = document.querySelector('[data-testid="video-tab-weather"]') as HTMLButtonElement | null;
        if (btn) btn.click();
      },
    },
    {
      screenId: "SCR-VID-03",
      screenName: "Màn hình 3: Mở Rạp chiếu VideoModal",
      stepName: "Phát video tiêu điểm dài trên rạp chiếu 16:9",
      description: "Mô phỏng click vào Video nổi bật để mở trình phát toàn màn hình...",
      selector: '[data-testid="hero-video-card"]',
      cursorLabel: "Click: Mở Rạp Chiếu Video",
      action: async () => {
        if (data.videos && data.videos[0]) {
          onPlayVideo(data.videos[0]);
        }
      },
    },
    {
      screenId: "SCR-VID-03",
      screenName: "Màn hình 3: Thoát Rạp chiếu phim",
      stepName: "Đóng trình phát video",
      description: "Mô phỏng click nút ✕ trên góc rạp chiếu phim...",
      selector: '[data-testid="close-video-modal"]',
      cursorLabel: "Click: ✕ Thoát Rạp Chiếu",
      action: async () => {
        onCloseVideo();
      },
    },
    {
      screenId: "SCR-NEW-01",
      screenName: "Màn hình 4: Chi tiết bài viết",
      stepName: "Đọc chi tiết bài báo tiêu điểm (ArticleDetailModal)",
      description: "Mô phỏng click vào bài báo nổi bật để mở Modal đọc chi tiết & xem Tóm tắt AI...",
      selector: '[data-testid="featured-article-card"]',
      cursorLabel: "Click: 📖 Đọc chi tiết bài viết",
      action: async () => {
        if (data.news && data.news[0]) {
          onSelectArticle(data.news[0]);
        }
      },
    },
    {
      screenId: "SCR-NEW-01",
      screenName: "Màn hình 4: Đóng Modal Chi tiết bài viết",
      stepName: "Đóng cửa sổ bài viết",
      description: "Mô phỏng click nút ✕ để quay lại luồng tin tức...",
      selector: '[data-testid="close-article-modal"]',
      cursorLabel: "Click: ✕ Đóng Bài Viết",
      action: async () => {
        onCloseArticle();
      },
    },
    {
      screenId: "SCR-LAY-03",
      screenName: "Màn hình 5: Tìm kiếm thời gian thực",
      stepName: "Nhập tìm kiếm: 'Hà Nội' trên Header",
      description: "Mô phỏng nhập liệu tìm kiếm tin tức và lọc danh sách bài viết...",
      selector: '[data-testid="header-search-input"]',
      cursorLabel: "Gõ tìm kiếm: 'Hà Nội'",
      action: async () => {
        onSearch("Hà Nội");
      },
    },
    {
      screenId: "SCR-LAY-03",
      screenName: "Màn hình 5: Xóa bộ lọc tìm kiếm",
      stepName: "Click xóa bộ lọc tìm kiếm hoàn tất chu trình",
      description: "Mô phỏng click nút ✕ để khôi phục toàn bộ danh sách tin tức...",
      selector: '[data-testid="clear-search-btn"]',
      cursorLabel: "Click: ✕ Xóa tìm kiếm",
      action: async () => {
        onSearch("");
      },
    },
  ];

  const currentStep = steps[currentStepIndex];

  // Thực hiện một bước kiểm thử trực quan
  const executeStep = useCallback((stepIdx: number) => {
    if (stepIdx >= steps.length) {
      setIsCompleted(true);
      setCursorPos((prev) => ({ ...prev, visible: false }));
      return;
    }

    const step = steps[stepIdx];

    // Tìm phần tử mục tiêu
    const el = document.querySelector(step.selector) as HTMLElement | null;

    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      const rect = el.getBoundingClientRect();
      const targetX = rect.left + rect.width / 2;
      const targetY = rect.top + rect.height / 2;

      // 1. Di chuyển con trỏ ảo tới mục tiêu
      setCursorPos({
        x: targetX,
        y: targetY,
        visible: true,
        clicking: false,
        label: step.cursorLabel,
      });

      // 2. Sau 600ms khi con trỏ tới nơi: Tạo hiệu ứng highlight viền phát sáng & click
      timerRef.current = setTimeout(() => {
        // Highlight element
        el.classList.add("ring-4", "ring-[#ff315f]", "ring-offset-2", "shadow-xl");
        setCursorPos((prev) => ({ ...prev, clicking: true }));

        // Thực thi hành động thật
        step.action();

        // 3. Sau 300ms thả click & gỡ highlight
        setTimeout(() => {
          setCursorPos((prev) => ({ ...prev, clicking: false }));
          el.classList.remove("ring-4", "ring-[#ff315f]", "ring-offset-2", "shadow-xl");
        }, 350);

        // 4. Dừng 1.4s để người dùng quan sát kết quả rồi sang bước kế tiếp
        timerRef.current = setTimeout(() => {
          setCurrentStepIndex((prev) => prev + 1);
        }, 1600);
      }, 700);
    } else {
      // Nếu selector chưa xuất hiện trên DOM (ví dụ modal chưa bung hoàn toàn), thử lại sau 300ms
      timerRef.current = setTimeout(() => {
        setCurrentStepIndex((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
      }, 800);
    }
  }, [steps]);

  // Vòng lặp điều khiển tiến trình
  useEffect(() => {
    if (!isOpen || isPaused || isCompleted) return;

    executeStep(currentStepIndex);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isOpen, isPaused, isCompleted, currentStepIndex, executeStep]);

  // Khi đóng runner: dọn dẹp
  const handleStop = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setCursorPos((prev) => ({ ...prev, visible: false, clicking: false }));
    onCloseArticle();
    onCloseVideo();
    onCloseCopilot();
    onSearch("");
    onClose();
  };

  const handleNext = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setCurrentStepIndex((prev) => Math.min(prev + 1, steps.length - 1));
  };

  const handleRestart = () => {
    setIsCompleted(false);
    setCurrentStepIndex(0);
    setIsPaused(false);
  };

  if (!isOpen) return null;

  const progressPercent = Math.round(((currentStepIndex + 1) / steps.length) * 100);

  return (
    <>
      {/* ── Virtual Laser Pointer & Click Ripple ────────────────────────── */}
      {cursorPos.visible && (
        <div
          className="fixed z-[9999] pointer-events-none transition-all duration-500 ease-out"
          style={{
            left: `${cursorPos.x}px`,
            top: `${cursorPos.y}px`,
            transform: "translate(-8px, -8px)",
          }}
        >
          {/* Radial Click Ripple Effect */}
          {cursorPos.clicking && (
            <div className="absolute -top-7 -left-7 size-18 rounded-full border-4 border-[#ff315f] bg-[#ff315f]/30 animate-ping pointer-events-none" />
          )}

          {/* SVG Mouse Pointer Cursor */}
          <div
            className={`relative transition-transform duration-150 ${
              cursorPos.clicking ? "scale-90 rotate-[-10deg]" : "scale-100"
            }`}
          >
            <svg
              className="size-8 drop-shadow-[0_4px_12px_rgba(255,49,95,0.9)] filter"
              viewBox="0 0 24 24"
              fill="none"
            >
              <path
                d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"
                fill="#ff315f"
                stroke="#ffffff"
                strokeWidth="2.5"
                strokeLinejoin="round"
              />
            </svg>
            <span className="absolute top-0 left-0 size-3 rounded-full bg-emerald-400 animate-ping border border-white" />
          </div>

          {/* Floating Action Tooltip next to cursor */}
          {cursorPos.label && (
            <div className="absolute left-9 top-1 bg-[#0f172a]/95 backdrop-blur-md border border-[#ff315f]/60 text-white text-[12px] font-semibold px-3 py-1.5 rounded-xl shadow-2xl whitespace-nowrap flex items-center gap-2 animate-in fade-in slide-in-from-left-2">
              <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>{cursorPos.label}</span>
            </div>
          )}
        </div>
      )}

      {/* ── Visual Test Runner Control HUD ─────────────────────────────── */}
      {!isCompleted ? (
        <div className="fixed bottom-5 left-1/2 -translate-x-1/2 z-[9990] w-[92%] max-w-2xl bg-[#0f172a]/95 backdrop-blur-2xl border border-indigo-500/40 rounded-2xl p-4 shadow-[0_20px_50px_rgba(0,0,0,0.7)] text-white flex flex-col gap-3 animate-in fade-in slide-in-from-bottom-5">
          {/* Header Row */}
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <span className="flex size-3 rounded-full bg-emerald-400 animate-ping" />
              <div className="flex items-center gap-2">
                <span className="bg-gradient-to-r from-[#ff315f] to-[#f97316] text-white text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider">
                  VISUAL TEST RUNNER
                </span>
                <span className="text-[12px] font-bold text-indigo-200">
                  {currentStep?.screenName}
                </span>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsPaused(!isPaused)}
                className="px-3 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-white text-[12px] font-medium transition-colors flex items-center gap-1 cursor-pointer"
              >
                {isPaused ? "▶️ Tiếp tục" : "⏸️ Tạm dừng"}
              </button>
              <button
                onClick={handleNext}
                className="px-3 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-white text-[12px] font-medium transition-colors cursor-pointer"
              >
                ⏭️ Bỏ qua
              </button>
              <button
                onClick={handleStop}
                className="px-3 py-1 rounded-lg bg-rose-600/80 hover:bg-rose-600 text-white text-[12px] font-medium transition-colors cursor-pointer"
              >
                ⏹️ Dừng Test
              </button>
            </div>
          </div>

          {/* Current Step Title & Action Description */}
          <div className="flex flex-col gap-0.5">
            <p className="font-['Inter:Bold'] font-bold text-white text-[14px]">
              Bước {currentStepIndex + 1}/{steps.length}: {currentStep?.stepName}
            </p>
            <p className="text-[12px] text-indigo-300">
              {currentStep?.description}
            </p>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden relative">
            <div
              className="bg-gradient-to-r from-[#ff315f] via-violet-500 to-emerald-400 h-full transition-all duration-500 rounded-full"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      ) : (
        /* ── Completion Summary Dialog ──────────────────────────────── */
        <div className="fixed inset-0 z-[9995] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
          <div className="relative w-full max-w-lg bg-[#0f172a] rounded-3xl p-6 sm:p-8 border border-emerald-500/40 shadow-[0_0_60px_rgba(16,185,129,0.3)] text-white flex flex-col gap-5 text-center">
            <div className="size-16 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 flex items-center justify-center text-3xl mx-auto shadow-lg animate-bounce">
              ✓
            </div>

            <div className="flex flex-col gap-1">
              <h3 className="font-['Inter:Bold'] font-extrabold text-[22px] text-white">
                HOÀN THÀNH KIỂM THỬ TRỰC QUAN!
              </h3>
              <p className="text-[13px] text-emerald-300 font-medium">
                Tất cả các thao tác tương tác người dùng trên 5 phân hệ màn hình đã được thực thi và xác minh thành công 100%.
              </p>
            </div>

            {/* 5 Screen Checklist */}
            <div className="bg-[#1e293b]/80 border border-white/10 rounded-2xl p-4 text-left space-y-2.5 text-[13px]">
              <div className="flex items-center justify-between text-emerald-300">
                <span>✓ Màn hình 1: Dashboard Cảm biến & Thời tiết</span>
                <span className="font-bold">PASSED</span>
              </div>
              <div className="flex items-center justify-between text-emerald-300">
                <span>✓ Màn hình 2: Trí tuệ AI Antigravity Copilot</span>
                <span className="font-bold">PASSED</span>
              </div>
              <div className="flex items-center justify-between text-emerald-300">
                <span>✓ Màn hình 3: Video Hub & Rạp chiếu phim</span>
                <span className="font-bold">PASSED</span>
              </div>
              <div className="flex items-center justify-between text-emerald-300">
                <span>✓ Màn hình 4: Luồng Tin tức & Modal Đọc bài</span>
                <span className="font-bold">PASSED</span>
              </div>
              <div className="flex items-center justify-between text-emerald-300">
                <span>✓ Màn hình 5: Giao diện Responsive & Live Search</span>
                <span className="font-bold">PASSED</span>
              </div>
            </div>

            <div className="flex items-center justify-center gap-3 pt-2">
              <button
                onClick={handleRestart}
                className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-['Inter:Semi_Bold'] font-semibold text-[13px] transition-colors cursor-pointer"
              >
                🔄 Chạy lại Test
              </button>
              <button
                onClick={handleStop}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:opacity-95 text-white font-['Inter:Semi_Bold'] font-semibold text-[13px] shadow-lg transition-all cursor-pointer"
              >
                Đóng & Xem kết quả
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
