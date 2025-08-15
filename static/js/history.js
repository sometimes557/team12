// 搜索历史管理模块
const HistoryManager = {
    // 添加搜索历史
    addHistory: function(keyword) {
        if (!keyword) return false;

        let history = this.getHistory();
        // 去重，如果关键词已存在则移到最前面
        history = history.filter(item => item !== keyword);
        history.unshift(keyword);
        // 限制最多存储20条记录
        if (history.length > 20) {
            history = history.slice(0, 20);
        }
        localStorage.setItem('searchHistory', JSON.stringify(history));
        return true;
    },

    // 获取搜索历史
    getHistory: function() {
        const historyStr = localStorage.getItem('searchHistory');
        return historyStr ? JSON.parse(historyStr) : [];
    },

    // 清除所有搜索历史
    clearHistory: function() {
        localStorage.removeItem('searchHistory');
        return true;
    },

    // 删除单个搜索历史
    deleteHistory: function(keyword) {
        let history = this.getHistory();
        history = history.filter(item => item !== keyword);
        localStorage.setItem('searchHistory', JSON.stringify(history));
        return true;
    },

    // 渲染历史记录到页面
    renderHistory: function(containerSelector) {
        const container = document.querySelector(containerSelector);
        if (!container) return;

        const history = this.getHistory();
        if (history.length === 0) {
            container.innerHTML = '<p class="text-muted">暂无搜索历史</p>';
            return;
        }

        let html = '<ul class="list-group">';
        history.forEach(keyword => {
            html += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <a href="#" class="history-item">${keyword}</a>
                    <button class="btn btn-sm btn-danger delete-history" data-keyword="${keyword}">删除</button>
                </li>
            `;
        });
        html += '</ul>';
        container.innerHTML = html;

        // 绑定事件
        this.bindEvents();
    },

    // 绑定事件
    bindEvents: function() {
        // 历史记录点击事件
        document.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const keyword = item.textContent.trim();
                // 触发搜索事件
                const event = new CustomEvent('historySearch', { detail: { keyword } });
                document.dispatchEvent(event);
            });
        });

        // 删除历史记录事件
        document.querySelectorAll('.delete-history').forEach(btn => {
            btn.addEventListener('click', () => {
                const keyword = btn.getAttribute('data-keyword');
                this.deleteHistory(keyword);
                // 重新渲染
                this.renderHistory('#historyContainer');
            });
        });
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 如果有历史记录容器，则渲染历史记录
    if (document.querySelector('#historyContainer')) {
        HistoryManager.renderHistory('#historyContainer');
    }

    // 清除历史记录按钮事件
    const clearBtn = document.querySelector('#clearHistoryBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            if (confirm('确定要清除所有搜索历史吗？')) {
                HistoryManager.clearHistory();
                HistoryManager.renderHistory('#historyContainer');
            }
        });
    }

    // 搜索框提交事件，添加到历史记录
    const searchForm = document.querySelector('#searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            const input = searchForm.querySelector('input[name="keyword"]');
            if (input) {
                const keyword = input.value.trim();
                if (keyword) {
                    HistoryManager.addHistory(keyword);
                }
            }
        });
    }
});