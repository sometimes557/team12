// 主题切换（持久化）
(function() {
  const toggle = document.getElementById('themeToggle');
  const root = document.documentElement;
  const saved = localStorage.getItem('theme') || 'light';
  root.setAttribute('data-bs-theme', saved);
  if (toggle) toggle.checked = saved === 'dark';

  if (toggle) {
    toggle.addEventListener('change', () => {
      const mode = toggle.checked ? 'dark' : 'light';
      root.setAttribute('data-bs-theme', mode);
      localStorage.setItem('theme', mode);
    });
  }
})();

// 页面加载遮罩：对所有 form 提交与具有 data-loading 的链接启用
(function() {
  const overlay = document.getElementById('loadingOverlay');
  function showOverlay() { overlay && overlay.classList.remove('d-none'); }
  function hideOverlay() { overlay && overlay.classList.add('d-none'); }

  // 表单提交
  document.querySelectorAll('form').forEach(f => {
    f.addEventListener('submit', () => {
      showOverlay();
    });
  });

  // 链接
  document.querySelectorAll('a[data-loading="1"]').forEach(a => {
    a.addEventListener('click', () => showOverlay());
  });

  window.addEventListener('pageshow', () => hideOverlay());
})();

// 初始化 DataTable（如果存在）
(function() {
  const tbl = document.getElementById('tblReviews');
  if (tbl && window.DataTable) {
    new DataTable(tbl, {
      responsive: true,
      pageLength: 10,
      order: [[1, 'desc']],
      language: {
        url: 'https://cdn.datatables.net/plug-ins/2.0.8/i18n/zh-CN.json'
      }
    });
  }
})();

// 初始化 Chart.js 图表
(function() {
  const payload = window.__REPORT_DATA__;
  if (!payload || !window.Chart) return;

  // Sentiment Doughnut
  const ctx1 = document.getElementById('chartSentiment');
  if (ctx1) {
    new Chart(ctx1, {
      type: 'doughnut',
      data: {
        labels: payload.sentiment.labels,
        datasets: [{
          data: payload.sentiment.data
        }]
      },
      options: {
        plugins: {
          legend: { position: 'bottom' }
        },
        cutout: '60%'
      }
    });
  }

  // Rating Bar
  const ctx2 = document.getElementById('chartRating');
  if (ctx2 && payload.has_rating) {
    new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: payload.rating.labels,
        datasets: [{
          label: '数量',
          data: payload.rating.data
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { precision:0 } }
        }
      }
    });
  }

  // Cross (Stacked)
  const ctx3 = document.getElementById('chartCross');
  if (ctx3 && payload.has_rating && payload.rating_sentiment) {
    const ds = payload.rating_sentiment.datasets;
    new Chart(ctx3, {
      type: 'bar',
      data: {
        labels: payload.rating_sentiment.labels,
        datasets: ds.map(d => ({...d}))
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom' } },
        scales: { x: { stacked: true }, y: { stacked: true, beginAtZero: true, ticks:{precision:0} } }
      }
    });
  }
})();
