// 历史记录库
const HistoryManager = {
    // 存储搜索历史的键名
    STORAGE_KEY: 'search_history',
    // 最大历史记录数量
    MAX_HISTORY_ITEMS: 20,

    // 检查localStorage是否可用
    isLocalStorageAvailable() {
        try {
            const testKey = '__history_manager_test__';
            localStorage.setItem(testKey, testKey);
            localStorage.removeItem(testKey);
            return true;
        } catch (e) {
            return false;
        }
    },

    // 添加搜索记录
    addSearchHistory(keyword) {
        if (!keyword || keyword.trim() === '') return;

        if (!this.isLocalStorageAvailable()) {
            console.warn('localStorage不可用，无法保存搜索历史');
            return;
        }

        // 获取现有历史记录
        let history = this.getSearchHistory();

        // 检查是否已存在相同记录，如果存在则移除
        history = history.filter(item => item.keyword !== keyword);

        // 添加新记录到开头
        const newRecord = {
            keyword: keyword,
            timestamp: new Date().getTime(),
            id: Date.now().toString() // 生成唯一ID
        };
        history.unshift(newRecord);

        // 限制历史记录数量
        if (history.length > this.MAX_HISTORY_ITEMS) {
            history = history.slice(0, this.MAX_HISTORY_ITEMS);
        }

        // 保存到localStorage
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(history));
    },

    // 获取搜索历史
    getSearchHistory() {
        if (!this.isLocalStorageAvailable()) {
            console.warn('localStorage不可用，无法获取搜索历史');
            return [];
        }

        const history = localStorage.getItem(this.STORAGE_KEY);
        return history ? JSON.parse(history) : [];
    },

    // 清除搜索历史
    clearSearchHistory() {
        if (!this.isLocalStorageAvailable()) {
            console.warn('localStorage不可用，无法清除搜索历史');
            return;
        }

        localStorage.removeItem(this.STORAGE_KEY);
    },

    // 删除单条搜索历史
    deleteHistoryItem(id) {
        if (!this.isLocalStorageAvailable()) {
            console.warn('localStorage不可用，无法删除搜索历史');
            return;
        }

        let history = this.getSearchHistory();
        history = history.filter(item => item.id !== id);
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(history));
    },

    // 生成历史记录HTML
    generateHistoryHTML() {
        if (!this.isLocalStorageAvailable()) {
            return '<p class="no-history">浏览器不支持本地存储，无法显示搜索历史</p>';
        }

        const history = this.getSearchHistory();
        if (history.length === 0) {
            return '<p class="no-history">暂无搜索历史</p>';
        }

        let html = '<ul class="history-list">';
        history.forEach(item => {
            const date = new Date(item.timestamp);
            const formattedDate = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;

            html += `
                <li class="history-item">
                    <a href="result_interface.html?search=${encodeURIComponent(item.keyword)}&redirect=true" class="history-link">${item.keyword}</a>
                    <span class="history-time">${formattedDate}</span>
                    <button class="delete-history" data-id="${item.id}">×</button>
                </li>
            `;
        });
        html += '</ul>';
        return html;
    }
};

// 导出HistoryManager对象
if (typeof window !== 'undefined') {
    window.HistoryManager = HistoryManager;
    
    // 检查是否是跨设备访问
    window.addEventListener('load', function() {
        // 可以在这里添加一个提示，说明历史记录仅保存在当前设备
        // 为了不影响用户体验，我们不在此处添加弹窗，而是在历史记录面板中显示提示
    });
}