/**
 * BỘ KIỂM THỬ TÍNH TOÀN VẸN THEO TỪNG MÀN HÌNH (SCREEN-BY-SCREEN TEST SUITE)
 * 
 * Phân rã kiểm thử có hệ thống tránh lan man:
 * - Màn hình 1 (SCR-WEA): Cảm biến & Thời tiết đô thị (Weather & Environmental Dashboard)
 * - Màn hình 2 (SCR-COP): Trợ lý AI Antigravity Copilot (AI Active Intelligence Hub)
 * - Màn hình 3 (SCR-VID): Truyền hình nóng & Rạp chiếu Video (Multimedia Video Hub & Cinema Modal)
 * - Màn hình 4 (SCR-NEW): Luồng Tin tức mới nhất (News Feed)
 * - Màn hình 5 (SCR-LAY): Giao diện đa thiết bị Responsive (Desktop, Tablet, Mobile)
 */

import { describe, it, expect, vi, beforeAll, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import React from 'react';
import {
  detectCondition,
  WEATHER_THEMES,
  generateClientCopilotFallback,
  FALLBACK_VIDEOS,
  WeatherColumn,
  AntigravityCopilotModal,
  VideoHubSection,
  VideoModal,
  BrandLogo,
  ArticleDetailModal,
  DesktopLayout,
  TabletLayout,
  MobileLayout,
  type AppData,
  type VideoItem,
} from '../App';
import { VisualTestRunner } from '../VisualTestRunner';

beforeAll(() => {
  // Mock scrollIntoView cho môi trường jsdom
  window.HTMLElement.prototype.scrollIntoView = vi.fn();

  // Mock SpeechSynthesis cho tính năng đọc báo AI TTS
  const mockSpeechSynthesis = {
    speak: vi.fn(),
    cancel: vi.fn(),
    pause: vi.fn(),
    resume: vi.fn(),
    speaking: false,
  };
  Object.defineProperty(window, 'speechSynthesis', {
    value: mockSpeechSynthesis,
    writable: true,
  });

  class MockSpeechSynthesisUtterance {
    text: string;
    lang = '';
    rate = 1;
    onend: (() => void) | null = null;
    onerror: (() => void) | null = null;
    constructor(text: string) {
      this.text = text;
    }
  }
  (window as any).SpeechSynthesisUtterance = MockSpeechSynthesisUtterance;
  (globalThis as any).SpeechSynthesisUtterance = MockSpeechSynthesisUtterance;
});

afterEach(() => {
  cleanup();
});

// ── Mock Dữ liệu chuẩn bị cho các màn hình ──────────────────────────────────
const mockData: AppData = {
  location: "Hà Nội",
  updateTime: "22:30 CH",
  weather: {
    temp: 28.5,
    feelsLike: 30.2,
    humidity: 78,
    windSpeed: 14,
    description: "Mây rải rác",
    icon: "⛅",
    pm25: 38.5,
    aqiLevel: 3,
    condKey: "nang",
  },
  forecast: [
    { time: "23:00", temp: 28, pop: 10, icon: "⛅", desc: "Mây rải rác" },
    { time: "00:00", temp: 27, pop: 15, icon: "☁️", desc: "Nhiều mây" },
    { time: "01:00", temp: 26, pop: 20, icon: "☁️", desc: "Nhiều mây" },
    { time: "02:00", temp: 26, pop: 20, icon: "☁️", desc: "Nhiều mây" },
  ],
  news: [
    {
      title: "Hà Nội tăng cường ứng trực bảo đảm an toàn giao thông đô thị",
      description: "Các lực lượng chức năng đồng loạt kiểm tra xử lý điểm nóng giao thông.",
      link: "https://tienphong.vn/tin-tuc-1",
      image: "https://example.com/img1.jpg",
      source: "Báo Tiền Phong",
    },
    {
      title: "Giải pháp công nghệ mới trong điều hành đèn tín hiệu thông minh",
      description: "Ứng dụng AI phân luồng giảm thiểu ùn tắc giờ cao điểm.",
      link: "https://tuoitre.vn/tin-tuc-2",
      image: "https://example.com/img2.jpg",
      source: "Tuổi Trẻ",
    },
    {
      title: "Dự báo thời tiết và diễn biến thủy văn các sông hồ lớn",
      description: "Mực nước sông Đáy và sông Nhuệ duy trì ở mức an toàn.",
      link: "https://vtv.vn/tin-tuc-3",
      image: "https://example.com/img3.jpg",
      source: "VTV24",
    },
  ],
  videos: FALLBACK_VIDEOS,
};

// ============================================================================
// MÀN HÌNH 1: CẢM BIẾN & THỜI TIẾT ĐÔ THỊ (SCR-WEATHER-01)
// ============================================================================
describe('Màn hình 1: Phân hệ Cảm biến & Thời tiết đô thị (SCR-WEATHER-01)', () => {
  it('F-WEA-01: Phân loại chính xác 6 trạng thái thời tiết', () => {
    // 1. Nắng gắt
    expect(detectCondition(36, 38, "Trời nắng", 10, 50)).toBe("nang-gat");
    // 2. Nắng đẹp
    expect(detectCondition(30, 31, "Trời nắng nhẹ", 10, 60)).toBe("nang");
    // 3. Mưa dông sấm sét
    expect(detectCondition(25, 25, "Có dông kèm sấm chớp", 70, 90)).toBe("mua-dong");
    // 4. Mưa nhỏ
    expect(detectCondition(22, 22, "Mưa nhỏ lất phất", 50, 80)).toBe("mua-nho");
    // 5. Âm u nhiều mây
    expect(detectCondition(24, 24, "Trời âm u xám xịt", 20, 88)).toBe("am-u");
    // 6. Bình thường
    expect(detectCondition(25, 25, "Quang đãng", 10, 65)).toBe("binh-thuong");
  });

  it('F-WEA-02: Bảng chủ đề thời tiết WEATHER_THEMES đầy đủ gradient và khuyến nghị', () => {
    const keys = ["binh-thuong", "nang", "nang-gat", "am-u", "mua-nho", "mua-dong"] as const;
    keys.forEach((key) => {
      const theme = WEATHER_THEMES[key];
      expect(theme).toBeDefined();
      expect(theme.gradient).toContain("linear-gradient");
      expect(theme.warningText.length).toBeGreaterThan(15);
      expect(theme.suggestionItems.length).toBeGreaterThanOrEqual(2);
    });
  });

  it('F-WEA-03: Render giao diện WeatherColumn hiển thị đầy đủ Hero Card, 3 Cảm biến và Dự báo 3h', () => {
    const onOpenCopilotMock = vi.fn();
    render(<WeatherColumn data={mockData} onOpenCopilot={onOpenCopilotMock} />);

    // Hero Card
    expect(screen.getByText(/28.5°C/i)).toBeDefined();
    expect(screen.getByText(/Hà Nội · Cập nhật 22:30 CH/i)).toBeDefined();
    expect(screen.getByText(/Cảm nhận 30.2°C/i)).toBeDefined();

    // 3 Hộp chỉ số môi trường
    expect(screen.getByText(/💧 Độ ẩm/i)).toBeDefined();
    expect(screen.getByText(/78%/i)).toBeDefined();
    expect(screen.getAllByText(/PM2.5/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/38.5 µg\/m³/i)).toBeDefined();
    expect(screen.getByText(/💨 Tốc độ gió/i)).toBeDefined();
    expect(screen.getByText(/14 km\/h/i)).toBeDefined();

    // Dự báo 3 giờ tới
    expect(screen.getByText(/Dự báo 3 giờ tới/i)).toBeDefined();
    expect(screen.getByText(/23:00/i)).toBeDefined();
    expect(screen.getByText(/00:00/i)).toBeDefined();
  });

  it('F-WEA-04: Hiển thị bảng điểm đen ngập úng khi thời tiết có mưa', () => {
    const rainData: AppData = {
      ...mockData,
      weather: { ...mockData.weather, condKey: "mua-dong" },
    };
    render(<WeatherColumn data={rainData} onOpenCopilot={vi.fn()} />);
    expect(screen.getByText(/BẢNG ĐIỂM ĐEN NGẬP ÚNG/i)).toBeDefined();
    expect(screen.getAllByText(/KHUYẾN CÁO LỘ TRÌNH/i).length).toBeGreaterThan(0);
  });
});

// ============================================================================
// MÀN HÌNH 2: TRỢ LÝ AI ANTIGRAVITY COPILOT (SCR-COPILOT-02)
// ============================================================================
describe('Màn hình 2: Trợ lý AI Antigravity Copilot (SCR-COPILOT-02)', () => {
  it('F-COP-01: Thẻ Copilot trong WeatherColumn kích hoạt đúng callback khi bấm các nút', () => {
    const onOpenCopilotMock = vi.fn();
    render(<WeatherColumn data={mockData} onOpenCopilot={onOpenCopilotMock} />);

    // Kiểm tra card Copilot có mặt
    expect(screen.getByText(/AI COPILOT ACTIVE/i)).toBeDefined();
    expect(screen.getAllByText(/Antigravity Copilot/i).length).toBeGreaterThan(0);

    // Bấm nút "Tác động thời tiết"
    const btnWeather = screen.getByRole('button', { name: /Tác động thời tiết/i });
    fireEvent.click(btnWeather);
    expect(onOpenCopilotMock).toHaveBeenCalledWith("weather_impact");

    // Bấm nút "Tóm tắt tin nóng"
    const btnNews = screen.getByRole('button', { name: /Tóm tắt tin nóng/i });
    fireEvent.click(btnNews);
    expect(onOpenCopilotMock).toHaveBeenCalledWith("news_digest");

    // Bấm nút "Đánh giá PM2.5"
    const btnPM25 = screen.getByRole('button', { name: /Đánh giá PM2.5/i });
    fireEvent.click(btnPM25);
    expect(onOpenCopilotMock).toHaveBeenCalledWith("health_pm25");

    // Bấm nút "Tuyến đường an toàn"
    const btnRoute = screen.getByRole('button', { name: /Tuyến đường an toàn/i });
    fireEvent.click(btnRoute);
    expect(onOpenCopilotMock).toHaveBeenCalledWith("smart_route");

    // Bấm nút "Mở Hộp Thoại Tương Tác Trực Tiếp"
    const btnFull = screen.getByRole('button', { name: /Mở Hộp Thoại Tương Tác Trực Tiếp Với AI/i });
    fireEvent.click(btnFull);
    expect(onOpenCopilotMock).toHaveBeenCalledWith(null);
  });

  it('F-COP-02: Bộ máy nội suy thông minh (Fallback Engine) xử lý đầy đủ 4 tác vụ với phân tích có giá trị thực tế', () => {
    const context = {
      location: "Hà Đông, Hà Nội",
      temp: 34.0,
      feelsLike: 38.0,
      desc: "Trời nắng gắt",
      pm25: 65.0,
      news_titles: ["Tin số 1", "Tin số 2", "Tin số 3"],
    };

    // 1. Phân tích tác động thời tiết
    const resWeather = generateClientCopilotFallback("weather_impact", "", context);
    expect(resWeather.reply).toContain("PHÂN TÍCH TÁC ĐỘNG THỜI TIẾT");
    expect(resWeather.reply).toContain("Nhiệt độ & Cảm giác nhiệt");
    expect(resWeather.reply).toContain("Khuyến nghị Antigravity Copilot");
    expect(resWeather.riskLevel).toBe("medium");

    // 2. Tóm tắt 3 tin nóng
    const resNews = generateClientCopilotFallback("news_digest", "", context);
    expect(resNews.reply).toContain("TỔNG HỢP & PHÂN TÍCH TIÊU ĐIỂM TIN NÓNG");
    expect(resNews.reply).toContain("Nhận định AI");
    expect(resNews.reply).toContain("Tin số 1");

    // 3. Đánh giá PM2.5
    const resPM = generateClientCopilotFallback("health_pm25", "", context);
    expect(resPM.reply).toContain("ĐÁNH GIÁ CHỈ SỐ BỤI MỊN PM2.5");
    expect(resPM.reply).toContain("Khuyến cáo y tế AI");
    expect(resPM.riskLevel).toBe("high");

    // 4. Tư vấn lộ trình & điểm ngập (thời tiết khô ráo)
    const resRouteDry = generateClientCopilotFallback("smart_route", "", context);
    expect(resRouteDry.reply).toContain("KHUYẾN CÁO LỘ TRÌNH THÔNG MINH");
    expect(resRouteDry.reply).toContain("KHÔ RÁO");

    // 4b. Tư vấn lộ trình & điểm ngập khi có mưa dông
    const rainContext = { ...context, desc: "Mưa dông to kèm sấm sét" };
    const resRouteRain = generateClientCopilotFallback("smart_route", "", rainContext);
    expect(resRouteRain.reply).toContain("Chiến Thắng");
    expect(resRouteRain.riskLevel).toBe("high");

    // 5. Câu hỏi tự do (General Chat)
    const resChat = generateClientCopilotFallback("general_chat", "Hôm nay tôi nên đi làm giờ nào?", context);
    expect(resChat.reply).toContain("Hôm nay tôi nên đi làm giờ nào?");
  });

  it('F-COP-03: Modal Copilot đóng mở chuẩn xác, hiển thị thanh ngữ cảnh trực tiếp và nút gửi tin nhắn', () => {
    const onCloseMock = vi.fn();
    const { rerender } = render(
      <AntigravityCopilotModal
        isOpen={false}
        onClose={onCloseMock}
        data={mockData}
        initialAction={null}
      />
    );

    // Khi isOpen = false: Không render
    expect(screen.queryByText(/Gemini 2.5 Active/i)).toBeNull();

    // Mở Modal
    rerender(
      <AntigravityCopilotModal
        isOpen={true}
        onClose={onCloseMock}
        data={mockData}
        initialAction={null}
      />
    );

    // Header & Live Context Bar
    expect(screen.getByText(/Gemini 2.5 Active/i)).toBeDefined();
    expect(screen.getByText(/📍 Hà Nội/i)).toBeDefined();
    expect(screen.getByText(/🍃 PM2.5: 38.5 µg\/m³/i)).toBeDefined();
    expect(screen.getByText(/💨 Gió: 14 km\/h/i)).toBeDefined();

    // Form nhập liệu
    expect(screen.getByPlaceholderText(/Hỏi Copilot bất kỳ điều gì/i)).toBeDefined();
    expect(screen.getByText(/Gửi/i)).toBeDefined();

    // Bấm nút đóng
    const btnClose = screen.getByLabelText(/Đóng Copilot/i);
    fireEvent.click(btnClose);
    expect(onCloseMock).toHaveBeenCalled();
  });
});

// ============================================================================
// MÀN HÌNH 3: TRUYỀN HÌNH NÓNG & VIDEO TIÊU ĐIỂM (SCR-VIDEO-03)
// ============================================================================
describe('Màn hình 3: Truyền hình nóng & Video Tiêu điểm (SCR-VIDEO-03)', () => {
  it('F-VID-01: VideoHubSection hiển thị bộ lọc chuyên mục và phản hồi khi click tab', () => {
    const onPlayMock = vi.fn();
    render(<VideoHubSection videos={mockData.videos} onPlayVideo={onPlayMock} />);

    expect(screen.getByText(/Truyền Hình Nóng & Video Tiêu Điểm/i)).toBeDefined();
    expect(screen.getByText(/LIVE HUB/i)).toBeDefined();

    // Các tab chuyên mục (dùng getByRole button để định danh chính xác)
    const tabWeather = screen.getByRole('button', { name: /Thời tiết & Bão lũ/i });
    expect(tabWeather).toBeDefined();
    fireEvent.click(tabWeather);

    const tabTraffic = screen.getByRole('button', { name: /Giao thông & Đô thị/i });
    expect(tabTraffic).toBeDefined();
    fireEvent.click(tabTraffic);
  });

  it('F-VID-02: Bộ catalog video đảm bảo 100% video dài, loại bỏ hoàn toàn Shorts', () => {
    expect(FALLBACK_VIDEOS.length).toBeGreaterThanOrEqual(5);

    FALLBACK_VIDEOS.forEach((v) => {
      // 1. Link không được chứa /shorts/
      expect(v.link.toLowerCase()).not.toContain('/shorts/');
      // 2. Tiêu đề không chứa hashtag shorts
      const titleLower = v.title.toLowerCase();
      expect(titleLower).not.toContain('#short');
      expect(titleLower).not.toContain('#shorts');
      expect(titleLower).not.toContain('30s nóng');
      expect(titleLower).not.toContain('tiktok');
      // 3. embedUrl chuẩn
      expect(v.embedUrl).toContain('/embed/');
      expect(v.id.length).toBe(11);
    });
  });

  it('F-VID-03: VideoModal mở chế độ rạp chiếu phim với iframe và thông tin kênh', () => {
    const onCloseMock = vi.fn();
    const testVideo: VideoItem = FALLBACK_VIDEOS[0];

    const { rerender } = render(<VideoModal video={null} onClose={onCloseMock} />);
    expect(screen.queryByTitle(testVideo.title)).toBeNull();

    rerender(<VideoModal video={testVideo} onClose={onCloseMock} />);
    expect(screen.getByTitle(testVideo.title)).toBeDefined();
    expect(screen.getByText(new RegExp(`Kênh: ${testVideo.channel}`, "i"))).toBeDefined();
    expect(screen.getByText(/Mở YouTube ↗/i)).toBeDefined();

    const btnClose = screen.getByLabelText(/Đóng video/i);
    fireEvent.click(btnClose);
    expect(onCloseMock).toHaveBeenCalled();
  });
});

// ============================================================================
// MÀN HÌNH 4 & 5: TIN TỨC & GIAO DIỆN RESPONSIVE (SCR-NEWS-04 & SCR-LAY-05)
// ============================================================================
describe('Màn hình 4 & 5: Tin tức và Giao diện Responsive (SCR-NEWS-04 & SCR-LAY-05)', () => {
  it('F-LAY-01: DesktopLayout tích hợp thanh Dashboard, nút Copilot Header và 2 cột', () => {
    const onPlayMock = vi.fn();
    const onOpenCopilotMock = vi.fn();

    render(
      <DesktopLayout
        data={mockData}
        onPlayVideo={onPlayMock}
        onOpenCopilot={onOpenCopilotMock}
      />
    );

    // Dashboard Header
    expect(screen.getByText(/Dashboard/i)).toBeDefined();
    expect(screen.getByText(/Tìm kiếm thời tiết, tin tức.../i)).toBeDefined();

    // Nút Header Antigravity Copilot
    const btnCopilotHeader = screen.getByRole('button', { name: /Antigravity Copilot/i });
    expect(btnCopilotHeader).toBeDefined();
    fireEvent.click(btnCopilotHeader);
    expect(onOpenCopilotMock).toHaveBeenCalled();

    // Cột tin tức
    expect(screen.getByText(/Tin Tức Mới Nhất/i)).toBeDefined();
    expect(screen.getByText(mockData.news[0].description)).toBeDefined();
    expect(screen.getByText(mockData.news[1].title)).toBeDefined();
  });

  it('F-LAY-02: TabletLayout và MobileLayout render mượt mà, đầy đủ chức năng', () => {
    const onPlayMock = vi.fn();
    const onOpenCopilotMock = vi.fn();

    // Tablet Layout
    const { unmount } = render(
      <TabletLayout
        data={mockData}
        onPlayVideo={onPlayMock}
        onOpenCopilot={onOpenCopilotMock}
      />
    );
    expect(screen.getByText(/pulse./i)).toBeDefined();
    unmount();

    // Mobile Layout
    render(
      <MobileLayout
        data={mockData}
        onPlayVideo={onPlayMock}
        onOpenCopilot={onOpenCopilotMock}
      />
    );
    expect(screen.getAllByText(/pulse./i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Copilot/i).length).toBeGreaterThan(0);
  });

  it('F-NEW-01: ArticleDetailModal hiển thị chi tiết nội dung bài viết, tóm tắt AI và nút điều hướng', () => {
    const onCloseMock = vi.fn();
    const onCopilotPromptMock = vi.fn();
    const testArticle = mockData.news[0];

    // Khi article = null: Không render modal
    const { rerender } = render(
      <ArticleDetailModal
        article={null}
        onClose={onCloseMock}
        onOpenCopilotWithContext={onCopilotPromptMock}
      />
    );
    expect(screen.queryByText(testArticle.title)).toBeNull();

    // Mở modal bài viết
    rerender(
      <ArticleDetailModal
        article={testArticle}
        onClose={onCloseMock}
        onOpenCopilotWithContext={onCopilotPromptMock}
      />
    );

    // Tiêu đề & Tòa soạn
    expect(screen.getByText(testArticle.title)).toBeDefined();
    expect(screen.getAllByText(new RegExp(testArticle.source, "i")).length).toBeGreaterThan(0);

    // Hộp Tóm tắt nhanh bởi Antigravity Copilot
    expect(screen.getByText(/Tóm Tắt Nhanh Bởi Antigravity Copilot/i)).toBeDefined();
    expect(screen.getByText(/AI INSIGHT/i)).toBeDefined();

    // Nút Hỏi Copilot về bài này
    const btnAskCopilot = screen.getByText(/Hỏi Copilot về bài này/i);
    expect(btnAskCopilot).toBeDefined();
    fireEvent.click(btnAskCopilot);
    expect(onCopilotPromptMock).toHaveBeenCalled();
    expect(onCloseMock).toHaveBeenCalled();
  });

  it('F-NEW-02: Đọc báo thông minh AI Voice TTS (bật/tắt giọng nói vi-VN, chỉnh tốc độ đọc, tự dừng khi thoát)', () => {
    const onCloseMock = vi.fn();
    const testArticle = mockData.news[0];

    render(
      <ArticleDetailModal
        article={testArticle}
        onClose={onCloseMock}
      />
    );

    const btnTTS = screen.getByTestId('tts-toggle-btn');
    expect(btnTTS).toBeDefined();
    expect(btnTTS.textContent).toContain('Nghe đọc báo AI');

    // Bật đọc báo
    fireEvent.click(btnTTS);
    expect(window.speechSynthesis.speak).toHaveBeenCalled();
    expect(screen.getByText(/Tạm dừng đọc/i)).toBeDefined();
    expect(screen.getByText(/Đang phát/i)).toBeDefined();

    // Điều chỉnh tốc độ 1.25x
    const btnRate125 = screen.getByText('1.25x');
    expect(btnRate125).toBeDefined();
    fireEvent.click(btnRate125);

    // Tắt đọc báo bằng nút tạm dừng
    fireEvent.click(btnTTS);
    expect(window.speechSynthesis.cancel).toHaveBeenCalled();
    expect(screen.getByText(/Nghe đọc báo AI/i)).toBeDefined();

    // Đóng modal tự động ngắt âm thanh
    const btnClose = screen.getByTestId('close-article-modal');
    fireEvent.click(btnClose);
    expect(window.speechSynthesis.cancel).toHaveBeenCalled();
    expect(onCloseMock).toHaveBeenCalled();
  });

  it('F-NEW-03: Tùy biến trải nghiệm đọc trực quan: Cỡ chữ đa cấp (sm, base, lg, xl) và 3 chế độ nền đọc', () => {
    const testArticle = mockData.news[0];

    render(
      <ArticleDetailModal
        article={testArticle}
        onClose={vi.fn()}
      />
    );

    // Kiểm tra các nút cỡ chữ
    const btnAminus = screen.getByTitle('Cỡ chữ sm');
    const btnAplus = screen.getByTitle('Cỡ chữ lg');
    const btnAplusplus = screen.getByTitle('Cỡ chữ xl');
    expect(btnAminus).toBeDefined();
    expect(btnAplus).toBeDefined();
    expect(btnAplusplus).toBeDefined();

    fireEvent.click(btnAplus);
    fireEvent.click(btnAplusplus);
    fireEvent.click(btnAminus);

    // Kiểm tra các chế độ nền
    const btnLight = screen.getByTitle(/Chế độ Sáng chuẩn/i);
    const btnSepia = screen.getByTitle(/Chế độ Giấy ấm/i);
    const btnDark = screen.getByTitle(/Chế độ Ban đêm/i);

    expect(btnLight).toBeDefined();
    expect(btnSepia).toBeDefined();
    expect(btnDark).toBeDefined();

    // Chuyển sang Giấy ấm Sepia
    fireEvent.click(btnSepia);
    expect(screen.getByText(/Giấy ấm/i)).toBeDefined();

    // Chuyển sang Ban đêm Dark
    fireEvent.click(btnDark);
    expect(screen.getByText(/Đêm/i)).toBeDefined();
  });

  it('F-NEW-04: Đánh dấu bài viết yêu thích (Bookmark) lưu trữ LocalStorage và Thả cảm xúc độc giả (Reactions)', () => {
    const testArticle = mockData.news[0];
    localStorage.clear();

    render(
      <ArticleDetailModal
        article={testArticle}
        onClose={vi.fn()}
      />
    );

    // Nút Bookmark
    const btnBookmark = screen.getByTestId('bookmark-article-btn');
    expect(btnBookmark).toBeDefined();
    expect(btnBookmark.textContent).toContain('Lưu bài');

    // Bấm lưu bài
    fireEvent.click(btnBookmark);
    expect(btnBookmark.textContent).toContain('Đã lưu');
    const saved = JSON.parse(localStorage.getItem('pulse_saved_articles') || '[]');
    expect(saved.length).toBe(1);
    expect(saved[0].title).toBe(testArticle.title);

    // Bấm lại để bỏ lưu
    fireEvent.click(btnBookmark);
    expect(btnBookmark.textContent).toContain('Lưu bài');
    const unsaved = JSON.parse(localStorage.getItem('pulse_saved_articles') || '[]');
    expect(unsaved.length).toBe(0);

    // Reactions
    const btnHelpful = screen.getByTestId('react-helpful-btn');
    const btnInterested = screen.getByTestId('react-interested-btn');
    const btnInsightful = screen.getByTestId('react-insightful-btn');

    expect(btnHelpful).toBeDefined();
    expect(btnInterested).toBeDefined();
    expect(btnInsightful).toBeDefined();

    // Thả tim Quan tâm
    fireEvent.click(btnInterested);
    expect(btnInterested.className).toContain('bg-rose-600');

    // Đổi sang Hữu ích
    fireEvent.click(btnHelpful);
    expect(btnHelpful.className).toContain('bg-emerald-600');
  });

  it('F-NEW-05: Chuyển đổi đọc bài liên quan trong Modal và Bộ lọc danh mục tin tức (Category Tabs) kèm nút xem thêm', () => {
    const onSelectArticleMock = vi.fn();
    const testArticle = mockData.news[0];

    // 1. Modal liên quan
    render(
      <ArticleDetailModal
        article={testArticle}
        onClose={vi.fn()}
        allNews={mockData.news}
        onSelectArticle={onSelectArticleMock}
      />
    );

    expect(screen.getByText(/Tin tức cùng chuyên mục/i)).toBeDefined();
    const relatedItem = screen.getByText(mockData.news[1].title);
    expect(relatedItem).toBeDefined();
    fireEvent.click(relatedItem);
    expect(onSelectArticleMock).toHaveBeenCalledWith(mockData.news[1]);

    cleanup();

    // 2. DesktopLayout với Category Tabs
    render(
      <DesktopLayout
        data={mockData}
        onPlayVideo={vi.fn()}
        onOpenCopilot={vi.fn()}
        onSelectArticle={onSelectArticleMock}
      />
    );

    const tabWeather = screen.getByTestId('news-tab-weather');
    const tabTraffic = screen.getByTestId('news-tab-traffic');
    const tabAll = screen.getByTestId('news-tab-all');

    expect(tabWeather).toBeDefined();
    expect(tabTraffic).toBeDefined();
    expect(tabAll).toBeDefined();

    // Click tab Thời tiết
    fireEvent.click(tabWeather);
    expect(tabWeather.className).toContain('bg-[#ff315f]');

    // Click tab Tất cả
    fireEvent.click(tabAll);
    expect(tabAll.className).toContain('bg-[#ff315f]');
  });

  it('F-NEW-06: Chuyển đổi bộ engine VieNeu-TTS AI (Siêu thực) và danh sách nhân vật phát thanh', () => {
    const testArticle = mockData.news[0];
    render(
      <ArticleDetailModal
        article={testArticle}
        onClose={vi.fn()}
      />
    );

    // Kiểm tra các tùy chọn động cơ
    expect(screen.getByText(/🦜 VieNeu-TTS AI \(Siêu thực\)/i)).toBeDefined();
    const btnWebSpeech = screen.getByText(/🎙️ Web Speech \(Trình duyệt\)/i);
    expect(btnWebSpeech).toBeDefined();

    // Chuyển sang Web Speech
    fireEvent.click(btnWebSpeech);
    expect(btnWebSpeech.className).toContain('bg-indigo-600');

    // Chuyển lại VieNeu-TTS AI
    const btnVieNeu = screen.getByText(/🦜 VieNeu-TTS AI \(Siêu thực\)/i);
    fireEvent.click(btnVieNeu);
    expect(btnVieNeu.className).toContain('bg-indigo-600');

    // Kiểm tra danh sách giọng đọc phát thanh
    expect(screen.getByText(/Giọng phát thanh:/i)).toBeDefined();
    expect(screen.getByText(/ONNX 24kHz/i)).toBeDefined();
    expect(screen.getByText(/Mai Anh \(Nữ · Miền Bắc\) - Thời sự Tiền Phong/i)).toBeDefined();
  });

  it('F-LAY-03: BrandLogo nhận diện thương hiệu chuẩn xác và bộ lọc tìm kiếm tin tức tức thời', () => {
    // 1. BrandLogo
    render(<BrandLogo />);
    expect(screen.getByText(/pulse./i)).toBeDefined();
    expect(screen.getByText(/TIỀN PHONG/i)).toBeDefined();
    expect(screen.getByText(/Tin tức & Thời tiết Đô thị 24\/7/i)).toBeDefined();

    // 2. DesktopLayout với search query
    const onSearchChangeMock = vi.fn();
    const { rerender } = render(
      <DesktopLayout
        data={mockData}
        onPlayVideo={vi.fn()}
        onOpenCopilot={vi.fn()}
        searchQuery="công nghệ"
        onSearchChange={onSearchChangeMock}
      />
    );

    // Hiển thị thanh thông báo kết quả tìm kiếm
    expect(screen.getByText(/Tìm thấy/i)).toBeDefined();
    expect(screen.getAllByText(/công nghệ/i).length).toBeGreaterThanOrEqual(1);

    // Nút Xóa bộ lọc
    const btnClear = screen.getByText(/Xóa bộ lọc/i);
    expect(btnClear).toBeDefined();
    fireEvent.click(btnClear);
    expect(onSearchChangeMock).toHaveBeenCalledWith("");
  });

  it('F-TST-01: VisualTestRunner hiển thị đầy đủ bảng điều khiển HUD (Tiến độ, Nút Pause/Resume, Bỏ qua, Đóng) và các bước mô phỏng', () => {
    const onCloseMock = vi.fn();
    const onOpenCopilotMock = vi.fn();
    const onCloseCopilotMock = vi.fn();
    const onPlayVideoMock = vi.fn();
    const onCloseVideoMock = vi.fn();
    const onSelectArticleMock = vi.fn();
    const onCloseArticleMock = vi.fn();
    const onSearchMock = vi.fn();

    // 1. Khi isOpen = false: Không render
    const { rerender } = render(
      <VisualTestRunner
        data={mockData}
        isOpen={false}
        onClose={onCloseMock}
        onOpenCopilot={onOpenCopilotMock}
        onCloseCopilot={onCloseCopilotMock}
        onPlayVideo={onPlayVideoMock}
        onCloseVideo={onCloseVideoMock}
        onSelectArticle={onSelectArticleMock}
        onCloseArticle={onCloseArticleMock}
        onSearch={onSearchMock}
      />
    );
    expect(screen.queryByText(/BẢNG ĐIỀU KHIỂN KIỂM THỬ TRỰC QUAN/i)).toBeNull();

    // 2. Khi isOpen = true: Render HUD và các nút điều khiển
    rerender(
      <VisualTestRunner
        data={mockData}
        isOpen={true}
        onClose={onCloseMock}
        onOpenCopilot={onOpenCopilotMock}
        onCloseCopilot={onCloseCopilotMock}
        onPlayVideo={onPlayVideoMock}
        onCloseVideo={onCloseVideoMock}
        onSelectArticle={onSelectArticleMock}
        onCloseArticle={onCloseArticleMock}
        onSearch={onSearchMock}
      />
    );

    // Tiêu đề HUD
    expect(screen.getByText(/VISUAL TEST RUNNER/i)).toBeDefined();
    // Nút Tạm dừng / Tiếp tục
    const btnPause = screen.getByText(/Tạm dừng/i);
    expect(btnPause).toBeDefined();
    fireEvent.click(btnPause);
    expect(screen.getByText(/Tiếp tục/i)).toBeDefined();

    // Nút Bỏ qua bước
    const btnSkip = screen.getByText(/Bỏ qua/i);
    expect(btnSkip).toBeDefined();
    fireEvent.click(btnSkip);

    // Nút Dừng
    const btnStop = screen.getByText(/Dừng Test/i);
    expect(btnStop).toBeDefined();
    fireEvent.click(btnStop);
    expect(onCloseMock).toHaveBeenCalled();
  });

  it('F-TST-02: DesktopLayout hiển thị nút Kích hoạt Kiểm thử trực quan trên Header', () => {
    const onStartTestMock = vi.fn();
    render(
      <DesktopLayout
        data={mockData}
        onPlayVideo={vi.fn()}
        onOpenCopilot={vi.fn()}
        onStartVisualTest={onStartTestMock}
      />
    );

    const btnTest = screen.getByTestId('start-visual-test-btn');
    expect(btnTest).toBeDefined();
    expect(btnTest.textContent).toContain('Test Trực Quan');
    fireEvent.click(btnTest);
    expect(onStartTestMock).toHaveBeenCalled();
  });
});

