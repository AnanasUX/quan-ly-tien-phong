"""
Module Web App: Giao diện Web Dashboard và REST API cho hệ thống thu thập tin tức.
Tuân thủ Mục 6 (Lưu trữ và giao diện) và Mục 7 (Báo cáo kết quả) trong yêu cầu kỹ thuật:
- Giao diện trực quan, hiển thị tiêu đề, ảnh, tóm tắt, thời gian đăng, nút mở bài viết gốc.
- Bộ lọc đa chiều: website, chuyên mục, ngày đăng và trạng thái nội dung (full, partial, summary_only, failed).
- Xuất dữ liệu trực tiếp: JSON, CSV, Excel (.xlsx).
- Nút kích hoạt thu thập ngay và xem tiến trình thời gian thực.
"""

import os
import threading
from typing import Dict, Any
from flask import Flask, request, jsonify, render_template_string, send_file
from news_collector.database import NewsDatabase
from news_collector.collector_engine import NewsCollectorEngine

app = Flask(__name__)
db = NewsDatabase()
engine = NewsCollectorEngine(db=db)

# Biến toàn cục theo dõi tiến trình crawl
crawl_state = {
    "is_crawling": False,
    "processed": 0,
    "total": 0,
    "last_report": None
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hệ thống Thu thập Tin tức & Toàn văn Báo chí Việt Nam</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Merriweather:ital,wght@0,300;0,400;0,700;1,400&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        .font-serif-reading { font-family: 'Merriweather', serif; }
    </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen flex flex-col">
    <!-- Header -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-600 via-red-500 to-amber-500 flex items-center justify-center text-white font-black text-xl shadow-md">
                    R
                </div>
                <div>
                    <h1 class="font-extrabold text-lg text-slate-900 leading-tight">VietNews RSS & Full-Text Extractor</h1>
                    <p class="text-xs text-slate-500 font-medium">Hệ thống thu thập & trích xuất nội dung toàn văn chuẩn hóa</p>
                </div>
            </div>

            <div class="flex items-center gap-2">
                <button onclick="triggerCrawl()" id="crawlBtn" class="flex items-center gap-2 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-bold text-xs shadow-xs transition-all cursor-pointer">
                    <svg class="size-4 animate-spin hidden" id="crawlSpinner" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
                    <svg class="size-4" id="crawlIcon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
                    <span id="crawlBtnText">Thu thập ngay</span>
                </button>

                <div class="relative group">
                    <button class="flex items-center gap-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-bold text-xs transition-colors">
                        <svg class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                        <span>Xuất dữ liệu</span>
                    </button>
                    <div class="absolute right-0 mt-1 w-44 bg-white border border-slate-200 rounded-xl shadow-lg py-1.5 hidden group-hover:block z-40">
                        <a href="/api/export/excel" class="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-emerald-700 hover:bg-emerald-50">
                            📊 Xuất Excel (.xlsx)
                        </a>
                        <a href="/api/export/csv" class="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-50">
                            📄 Xuất CSV (UTF-8)
                        </a>
                        <a href="/api/export/json" class="flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-amber-700 hover:bg-amber-50">
                            📦 Xuất JSON chuẩn hóa
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full flex-1">
        <!-- Thống kê trạng thái (Metrics Cards) -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5 mb-6">
            <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs">
                <span class="text-xs font-semibold text-slate-500 block mb-1">Tổng số bài viết</span>
                <span class="text-2xl font-black text-slate-900" id="statTotal">--</span>
            </div>
            <div class="bg-emerald-50/80 p-4 rounded-2xl border border-emerald-200/80 shadow-xs">
                <span class="text-xs font-semibold text-emerald-700 block mb-1">Toàn văn (Full)</span>
                <span class="text-2xl font-black text-emerald-800" id="statFull">--</span>
            </div>
            <div class="bg-amber-50/80 p-4 rounded-2xl border border-amber-200/80 shadow-xs">
                <span class="text-xs font-semibold text-amber-700 block mb-1">Một phần (Partial)</span>
                <span class="text-2xl font-black text-amber-800" id="statPartial">--</span>
            </div>
            <div class="bg-blue-50/80 p-4 rounded-2xl border border-blue-200/80 shadow-xs">
                <span class="text-xs font-semibold text-blue-700 block mb-1">Chỉ tóm tắt (Summary)</span>
                <span class="text-2xl font-black text-blue-800" id="statSummary">--</span>
            </div>
            <div class="bg-rose-50/80 p-4 rounded-2xl border border-rose-200/80 shadow-xs">
                <span class="text-xs font-semibold text-rose-700 block mb-1">Lỗi / Chặn (Failed)</span>
                <span class="text-2xl font-black text-rose-800" id="statFailed">--</span>
            </div>
        </div>

        <!-- Thanh lọc đa chiều -->
        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs mb-6">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                <div>
                    <label class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">Nguồn website</label>
                    <select id="filterSource" class="w-full text-xs font-medium border border-slate-200 rounded-xl px-3 py-2 bg-slate-50 focus:bg-white focus:outline-rose-500">
                        <option value="">-- Tất cả nguồn báo --</option>
                    </select>
                </div>

                <div>
                    <label class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">Chuyên mục</label>
                    <select id="filterCategory" class="w-full text-xs font-medium border border-slate-200 rounded-xl px-3 py-2 bg-slate-50 focus:bg-white focus:outline-rose-500">
                        <option value="">-- Tất cả chuyên mục --</option>
                        <option value="thoi_su_xa_hoi">Thời sự, chính trị, xã hội</option>
                        <option value="cong_nghe_ai">Công nghệ, AI, chuyển đổi số</option>
                        <option value="gioi_tre_doi_song">Giới trẻ, Gen Z, đời sống</option>
                        <option value="giao_duc_tuyen_sinh">Giáo dục, tuyển sinh</option>
                        <option value="kinh_te_tai_chinh">Kinh tế, tài chính, khởi nghiệp</option>
                        <option value="giai_tri_van_hoa">Giải trí, văn hóa, thể thao</option>
                        <option value="khoa_hoc_suc_khoe">Khoa học, sức khỏe, môi trường</option>
                    </select>
                </div>

                <div>
                    <label class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">Trạng thái nội dung</label>
                    <select id="filterStatus" class="w-full text-xs font-medium border border-slate-200 rounded-xl px-3 py-2 bg-slate-50 focus:bg-white focus:outline-rose-500">
                        <option value="">-- Tất cả trạng thái --</option>
                        <option value="full">🟢 Toàn văn (Full content)</option>
                        <option value="partial">🟡 Một phần (Partial)</option>
                        <option value="summary_only">🔵 Chỉ tóm tắt (Summary only)</option>
                        <option value="failed">🔴 Lỗi / Không lấy được</option>
                    </select>
                </div>

                <div>
                    <label class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">Từ khóa tìm kiếm</label>
                    <input type="text" id="filterKeyword" placeholder="Tiêu đề, nội dung..." class="w-full text-xs font-medium border border-slate-200 rounded-xl px-3 py-2 bg-slate-50 focus:bg-white focus:outline-rose-500">
                </div>

                <div class="flex items-end gap-2">
                    <button onclick="loadArticles()" class="flex-1 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs py-2 rounded-xl transition-all cursor-pointer">
                        Lọc bài viết
                    </button>
                    <button onclick="resetFilters()" class="px-3 bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold text-xs py-2 rounded-xl transition-all cursor-pointer" title="Đặt lại bộ lọc">
                        ↺
                    </button>
                </div>
            </div>
        </div>

        <!-- Trạng thái Crawling Banner -->
        <div id="crawlingBanner" class="hidden mb-6 p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="w-3 h-3 rounded-full bg-rose-600 animate-ping"></div>
                <div>
                    <p class="text-xs font-bold text-rose-900" id="crawlProgressText">Hệ thống đang thu thập tin tức và cào bài viết gốc...</p>
                    <p class="text-[11px] text-rose-700 font-medium">Quá trình đang thực thi ngầm với cơ chế Rate Limiter và kiểm soát lỗi.</p>
                </div>
            </div>
            <span class="text-xs font-mono font-bold text-rose-800 bg-white px-3 py-1 rounded-lg border border-rose-200" id="crawlCounter">0 / 0</span>
        </div>

        <!-- Danh sách bài viết -->
        <div id="articlesList" class="flex flex-col gap-3.5">
            <div class="p-8 text-center text-slate-400 text-sm font-medium">Đang tải dữ liệu bài viết...</div>
        </div>

        <!-- Phân trang -->
        <div class="flex items-center justify-between mt-6 pt-4 border-t border-slate-200">
            <span class="text-xs text-slate-500 font-medium" id="pageInfo">Hiển thị bài viết</span>
            <div class="flex items-center gap-2">
                <button onclick="prevPage()" id="prevBtn" class="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-600 disabled:opacity-40 cursor-pointer">Trước</button>
                <button onclick="nextPage()" id="nextBtn" class="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-600 disabled:opacity-40 cursor-pointer">Tiếp</button>
            </div>
        </div>
    </main>

    <!-- Modal Xem Chi Tiết Toàn Văn Bài Viết -->
    <div id="articleModal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 hidden flex items-center justify-center p-4">
        <div class="bg-white w-full max-w-3xl max-h-[90vh] rounded-3xl shadow-2xl flex flex-col overflow-hidden border border-slate-200">
            <div class="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
                <div class="flex items-center gap-2" id="modalBadges"></div>
                <button onclick="closeModal()" class="w-8 h-8 rounded-full bg-slate-200 hover:bg-slate-300 flex items-center justify-center text-slate-600 font-bold transition-colors cursor-pointer">✕</button>
            </div>

            <div class="p-6 overflow-y-auto flex-1 space-y-4">
                <h2 id="modalTitle" class="text-xl sm:text-2xl font-bold text-slate-900 leading-snug"></h2>
                
                <div class="flex items-center gap-3 text-xs text-slate-500 font-medium border-b border-slate-100 pb-3" id="modalMeta">
                    <span id="modalAuthor"></span>
                    <span id="modalDate"></span>
                </div>

                <div id="modalSapo" class="p-4 bg-slate-50 border-l-4 border-rose-600 rounded-r-xl font-semibold text-slate-800 text-sm leading-relaxed italic"></div>

                <div id="modalBody" class="font-serif-reading text-slate-800 text-[16px] leading-relaxed space-y-4"></div>
            </div>

            <div class="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
                <a id="modalOriginalLink" href="#" target="_blank" class="flex items-center gap-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold transition-colors">
                    <span>Mở bài viết gốc</span>
                    <svg class="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
                </a>
                <button onclick="closeModal()" class="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 rounded-xl text-xs font-bold transition-colors cursor-pointer">Đóng lại</button>
            </div>
        </div>
    </div>

    <script>
        let currentPage = 0;
        const pageSize = 20;

        function getStatusBadge(status) {
            if (status === 'full') {
                return '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">🟢 Toàn văn</span>';
            } else if (status === 'partial') {
                return '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">🟡 Một phần</span>';
            } else if (status === 'summary_only') {
                return '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-800">🔵 Chỉ tóm tắt</span>';
            } else {
                return '<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">🔴 Lỗi / Chặn</span>';
            }
        }

        async function loadStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                document.getElementById('statTotal').innerText = (data.total_articles || 0).toLocaleString();
                document.getElementById('statFull').innerText = (data.full_count || 0).toLocaleString();
                document.getElementById('statPartial').innerText = (data.partial_count || 0).toLocaleString();
                document.getElementById('statSummary').innerText = (data.summary_only_count || 0).toLocaleString();
                document.getElementById('statFailed').innerText = (data.failed_count || 0).toLocaleString();

                // Nạp danh sách source vào dropdown
                const srcSelect = document.getElementById('filterSource');
                const currentVal = srcSelect.value;
                if (srcSelect.options.length <= 1 && data.top_sources) {
                    for (const [sName, cnt] of Object.entries(data.top_sources)) {
                        const opt = document.createElement('option');
                        opt.value = sName;
                        opt.innerText = `${sName} (${cnt})`;
                        srcSelect.appendChild(opt);
                    }
                    srcSelect.value = currentVal;
                }
            } catch(e) {
                console.error(e);
            }
        }

        async function loadArticles() {
            const source = document.getElementById('filterSource').value;
            const category = document.getElementById('filterCategory').value;
            const status = document.getElementById('filterStatus').value;
            const keyword = document.getElementById('filterKeyword').value;

            const params = new URLSearchParams({
                limit: pageSize,
                offset: currentPage * pageSize
            });
            if (source) params.append('source_name', source);
            if (category) params.append('category', category);
            if (status) params.append('content_status', status);
            if (keyword) params.append('keyword', keyword);

            const container = document.getElementById('articlesList');
            container.innerHTML = '<div class="p-8 text-center text-slate-400 text-sm">Đang nạp danh sách bài viết...</div>';

            try {
                const res = await fetch(`/api/articles?${params.toString()}`);
                const articles = await res.json();

                if (!articles || articles.length === 0) {
                    container.innerHTML = '<div class="p-12 text-center text-slate-400 bg-white rounded-2xl border border-slate-200">Không tìm thấy bài viết nào phù hợp với bộ lọc.</div>';
                    document.getElementById('pageInfo').innerText = `Trang ${currentPage + 1}`;
                    document.getElementById('prevBtn').disabled = currentPage === 0;
                    document.getElementById('nextBtn').disabled = true;
                    return;
                }

                let html = '';
                articles.forEach(a => {
                    const imgTag = a.image_url ? `
                        <img src="${a.image_url}" alt="" class="w-full sm:w-44 h-32 object-cover rounded-xl shrink-0 border border-slate-100" onerror="this.style.display='none'">
                    ` : '';

                    html += `
                        <div class="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs hover:shadow-md transition-shadow flex flex-col sm:flex-row gap-4">
                            ${imgTag}
                            <div class="flex-1 flex flex-col justify-between min-w-0">
                                <div>
                                    <div class="flex items-center gap-2 flex-wrap mb-1.5">
                                        <span class="text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded-md">${a.source_name}</span>
                                        <span class="text-[11px] font-medium text-slate-500">${a.category}</span>
                                        ${getStatusBadge(a.content_status)}
                                    </div>
                                    <h3 class="text-base font-bold text-slate-900 hover:text-rose-600 transition-colors line-clamp-2 cursor-pointer" onclick="viewArticle(${a.id})">
                                        ${a.title}
                                    </h3>
                                    <p class="text-xs text-slate-600 line-clamp-2 mt-1.5 leading-relaxed font-sans">${a.summary || 'Không có bản tóm tắt'}</p>
                                </div>

                                <div class="flex items-center justify-between mt-3 pt-2.5 border-t border-slate-100 text-[11px] text-slate-400">
                                    <div class="flex items-center gap-2">
                                        <span>✍️ ${a.author || 'Ban biên tập'}</span>
                                        <span>•</span>
                                        <span>🕒 ${new Date(a.published_at).toLocaleString('vi-VN')}</span>
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <button onclick="viewArticle(${a.id})" class="text-xs font-bold text-rose-600 hover:underline cursor-pointer">Xem toàn văn</button>
                                        <span>•</span>
                                        <a href="${a.article_url}" target="_blank" class="text-xs font-medium text-slate-500 hover:text-slate-800">Mở bài gốc ↗</a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });

                container.innerHTML = html;
                document.getElementById('pageInfo').innerText = `Hiển thị từ bài ${currentPage * pageSize + 1} đến ${currentPage * pageSize + articles.length}`;
                document.getElementById('prevBtn').disabled = currentPage === 0;
                document.getElementById('nextBtn').disabled = articles.length < pageSize;
            } catch(e) {
                container.innerHTML = `<div class="p-8 text-center text-rose-600 bg-rose-50 rounded-2xl border border-rose-200">Lỗi khi tải dữ liệu: ${e.message}</div>`;
            }
        }

        async function viewArticle(id) {
            try {
                const res = await fetch(`/api/articles/${id}`);
                const a = await res.json();
                if (!a) return;

                document.getElementById('modalTitle').innerText = a.title;
                document.getElementById('modalBadges').innerHTML = `
                    <span class="px-2.5 py-0.5 rounded-lg text-xs font-bold bg-slate-200 text-slate-800">${a.source_name}</span>
                    ${getStatusBadge(a.content_status)}
                `;
                document.getElementById('modalAuthor').innerText = `Tác giả: ${a.author || 'Ban biên tập'}`;
                document.getElementById('modalDate').innerText = `Xuất bản: ${new Date(a.published_at).toLocaleString('vi-VN')}`;
                
                if (a.summary) {
                    document.getElementById('modalSapo').innerText = a.summary;
                    document.getElementById('modalSapo').style.display = 'block';
                } else {
                    document.getElementById('modalSapo').style.display = 'none';
                }

                // Hiển thị nội dung đoạn văn
                const rawContent = a.content || '';
                const paragraphs = rawContent.split(/\\n\\n+/);
                let bodyHtml = '';
                paragraphs.forEach(p => {
                    const t = p.trim();
                    if (!t) return;
                    if (t.startsWith('### ')) {
                        bodyHtml += `<h3 class="text-lg font-bold text-slate-900 mt-4 mb-1">${t.replace('### ', '')}</h3>`;
                    } else if (t.startsWith('> ')) {
                        bodyHtml += `<blockquote class="pl-4 border-l-4 border-slate-300 italic text-slate-600 my-2">${t.replace('> ', '')}</blockquote>`;
                    } else {
                        bodyHtml += `<p class="leading-relaxed mb-3">${t}</p>`;
                    }
                });

                if (!bodyHtml) {
                    bodyHtml = '<p class="text-slate-400 italic text-center py-6">Chưa có thân bài chi tiết (Bài viết ở trạng thái chỉ có tóm tắt hoặc chưa cào được).</p>';
                }

                document.getElementById('modalBody').innerHTML = bodyHtml;
                document.getElementById('modalOriginalLink').href = a.article_url;
                document.getElementById('articleModal').classList.remove('hidden');
            } catch(e) {
                alert('Không thể mở bài viết: ' + e.message);
            }
        }

        function closeModal() {
            document.getElementById('articleModal').classList.add('hidden');
        }

        function prevPage() {
            if (currentPage > 0) {
                currentPage--;
                loadArticles();
            }
        }

        function nextPage() {
            currentPage++;
            loadArticles();
        }

        function resetFilters() {
            document.getElementById('filterSource').value = '';
            document.getElementById('filterCategory').value = '';
            document.getElementById('filterStatus').value = '';
            document.getElementById('filterKeyword').value = '';
            currentPage = 0;
            loadArticles();
        }

        async function triggerCrawl() {
            const btn = document.getElementById('crawlBtn');
            const spinner = document.getElementById('crawlSpinner');
            const icon = document.getElementById('crawlIcon');
            const text = document.getElementById('crawlBtnText');
            const banner = document.getElementById('crawlingBanner');

            btn.disabled = true;
            spinner.classList.remove('hidden');
            icon.classList.add('hidden');
            text.innerText = 'Đang thu thập...';
            banner.classList.remove('hidden');

            try {
                await fetch('/api/crawl', { method: 'POST' });
                pollCrawlStatus();
            } catch(e) {
                alert('Không thể kích hoạt thu thập: ' + e.message);
                resetCrawlBtn();
            }
        }

        function resetCrawlBtn() {
            const btn = document.getElementById('crawlBtn');
            const spinner = document.getElementById('crawlSpinner');
            const icon = document.getElementById('crawlIcon');
            const text = document.getElementById('crawlBtnText');
            const banner = document.getElementById('crawlingBanner');

            btn.disabled = false;
            spinner.classList.add('hidden');
            icon.classList.remove('hidden');
            text.innerText = 'Thu thập ngay';
            banner.classList.add('hidden');
        }

        function pollCrawlStatus() {
            const interval = setInterval(async () => {
                try {
                    const res = await fetch('/api/crawl/status');
                    const status = await res.json();
                    if (status.is_crawling) {
                        document.getElementById('crawlCounter').innerText = `${status.processed} / ${status.total}`;
                    } else {
                        clearInterval(interval);
                        resetCrawlBtn();
                        loadStats();
                        loadArticles();
                        if (status.last_report) {
                            alert(
                                `Thu thập hoàn tất!\\n` +
                                `- Tổng số bài tìm thấy: ${status.last_report.total_found}\\n` +
                                `- Bài mới: ${status.last_report.new_inserted}\\n` +
                                `- Toàn văn: ${status.last_report.full_count}\\n` +
                                `- Một phần: ${status.last_report.partial_count}\\n` +
                                `- Tóm tắt: ${status.last_report.summary_only_count}\\n` +
                                `- Lỗi: ${status.last_report.failed_count}`
                            );
                        }
                    }
                } catch(e) {
                    clearInterval(interval);
                    resetCrawlBtn();
                }
            }, 1500);
        }

        // Tự động khởi tạo nạp dữ liệu ban đầu
        window.addEventListener('DOMContentLoaded', () => {
            loadStats();
            loadArticles();
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/articles", methods=["GET"])
def api_articles():
    source_name = request.args.get("source_name")
    category = request.args.get("category")
    content_status = request.args.get("content_status")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    keyword = request.args.get("keyword")
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    articles = db.query_articles(
        source_name=source_name,
        category=category,
        content_status=content_status,
        from_date=from_date,
        to_date=to_date,
        keyword=keyword,
        limit=limit,
        offset=offset
    )
    return jsonify(articles)

@app.route("/api/articles/<int:article_id>", methods=["GET"])
def api_article_detail(article_id):
    article = db.get_article_by_id(article_id)
    if not article:
        return jsonify({"error": "Không tìm thấy bài viết"}), 404
    return jsonify(article)

@app.route("/api/stats", methods=["GET"])
def api_stats():
    stats = db.get_statistics()
    return jsonify(stats)

@app.route("/api/sources", methods=["GET"])
def api_sources():
    sources = engine.sources_config
    return jsonify(sources)

@app.route("/api/crawl", methods=["POST"])
def api_trigger_crawl():
    if crawl_state["is_crawling"]:
        return jsonify({"status": "already_running"}), 400

    category = request.args.get("category")

    def run_background():
        crawl_state["is_crawling"] = True
        crawl_state["processed"] = 0
        crawl_state["total"] = 0

        def on_progress(p):
            crawl_state["processed"] = p.get("processed", 0)
            crawl_state["total"] = p.get("total", 0)

        report = engine.run_crawl(category=category, progress_callback=on_progress)
        crawl_state["is_crawling"] = False
        crawl_state["last_report"] = report

    threading.Thread(target=run_background, daemon=True).start()
    return jsonify({"status": "started"})

@app.route("/api/crawl/status", methods=["GET"])
def api_crawl_status():
    return jsonify(crawl_state)

@app.route("/api/export/json", methods=["GET"])
def api_export_json():
    out_file = os.path.join(os.path.dirname(__file__), "export_articles.json")
    db.export_json(out_file)
    return send_file(out_file, as_attachment=True, download_name="articles_export.json", mimetype="application/json")

@app.route("/api/export/csv", methods=["GET"])
def api_export_csv():
    out_file = os.path.join(os.path.dirname(__file__), "export_articles.csv")
    db.export_csv(out_file)
    return send_file(out_file, as_attachment=True, download_name="articles_export.csv", mimetype="text/csv")

@app.route("/api/export/excel", methods=["GET"])
def api_export_excel():
    out_file = os.path.join(os.path.dirname(__file__), "export_articles.xlsx")
    db.export_excel(out_file)
    return send_file(
        out_file,
        as_attachment=True,
        download_name="articles_export.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def start_server(host: str = "127.0.0.1", port: int = 5050, debug: bool = False):
    """Khởi chạy máy chủ Web Dashboard."""
    print(f"🚀 VietNews RSS & Full-Text Extractor Server running at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, use_reloader=False)

if __name__ == "__main__":
    start_server()
