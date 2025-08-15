document.getElementById('searchForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const keyword = document.getElementById('keyword').value;
    const maxPages = document.getElementById('maxPages').value;
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const productsList = document.getElementById('productsList');

    // 显示加载状态
    loading.classList.remove('d-none');
    results.classList.add('d-none');
    productsList.innerHTML = '';

    try {
        // 调用后端API获取产品数据
        const response = await fetch(`/api/search?keyword=${encodeURIComponent(keyword)}&maxPages=${maxPages}`);

        // 添加HTTP错误处理
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }

        const products = await response.json();

        // 隐藏加载状态，显示结果
        loading.classList.add('d-none');
        results.classList.remove('d-none');

        // 渲染产品列表
        products.forEach(product => {
            const productCard = `
                <div class="col-md-6 mb-4">
                    <div class="card h-100">
                        <img src="${product.image_url || 'static/images/placeholder.jpg'}" class="card-img-top" alt="${product.title}">
                        <div class="card-body">
                            <h5 class="card-title">${product.title}</h5>
                            <p class="card-text"><small class="text-muted">产品ID: ${product.product_id}</small></p>
                            <button class="btn btn-success analyze-btn" data-product-id="${product.product_id}" data-product-title="${product.title}">分析评论</button>
                        </div>
                    </div>
                </div>
            `;
            productsList.innerHTML += productCard;
        });

        // 添加分析按钮事件监听
        document.querySelectorAll('.analyze-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const productId = this.getAttribute('data-product-id');
                const productTitle = this.getAttribute('data-product-title');
                // 跳转到结果页面并传递产品信息
                window.location.href = `results.html?id=${productId}&title=${encodeURIComponent(productTitle)}`;
            });
        });
    } catch (error) {
        // 错误处理增强
        loading.classList.add('d-none');
        const errorHtml = `
            <div class="alert alert-danger" role="alert">
                <h4 class="alert-heading">搜索失败</h4>
                <p>${error.message}</p>
                <hr>
                <p class="mb-0">请检查网络连接或尝试使用不同的搜索关键词</p>
            </div>
        `;
        productsList.innerHTML = errorHtml;
        results.classList.remove('d-none');
    }
});