《第 134 次记录：资源的命运 —— 加载失败时的优雅处理》

## CDN 故障引发的灾难

周四下午 2 点 47 分，客服部门的电话快被打爆了："网站图片全部显示不出来！"

你立刻打开线上页面，首页的商品图片确实全部无法显示，控制台里密密麻麻全是 404 错误：

```
GET https://cdn.example.com/images/product1.jpg 404 (Not Found)
GET https://cdn.example.com/images/product2.jpg 404 (Not Found)
GET https://cdn.example.com/images/product3.jpg 404 (Not Found)
...（上百个 404 错误）
```

你检查了 CDN 状态页面，发现服务商正在经历大规模故障。你的页面 HTML 是这样写的：

```html
<div class="product-list">
  <div class="product">
    <img src="https://cdn.example.com/images/product1.jpg" alt="商品1">
    <h3>商品名称</h3>
    <p>¥99.00</p>
  </div>
  <!-- 还有几百个商品... -->
</div>
```

所有商品图片都变成了浏览器默认的破损图片图标，整个页面看起来非常糟糕。运营部门说："这样的页面不能给用户看，赶紧想办法！"

前端负责人老陈说："你需要监听图片加载错误，提供降级方案。CDN 故障是常见的，必须有容错机制。"

## 监听资源加载错误

老陈展示了如何监听资源加载错误：

```javascript
// 方法 1: 使用 onerror 属性
const img = document.querySelector('img');

img.addEventListener('error', (event) => {
  console.log('图片加载失败:', event.target.src);

  // 显示占位图
  event.target.src = '/images/placeholder.png';

  // 或者隐藏图片
  // event.target.style.display = 'none';

  // 或者显示文字
  // event.target.alt = '图片加载失败';
});

img.addEventListener('load', (event) => {
  console.log('图片加载成功:', event.target.src);
});
```

你快速实现了一个全局的图片错误处理：

```javascript
// 全局监听所有图片加载错误
document.addEventListener('error', (event) => {
  const target = event.target;

  if (target.tagName === 'IMG') {
    console.error('图片加载失败:', target.src);

    // 避免无限重试（如果占位图也加载失败）
    if (target.src === '/images/placeholder.png') {
      return;
    }

    // 使用占位图
    target.src = '/images/placeholder.png';
    target.classList.add('image-error');
  }
}, true); // 使用捕获阶段
```

测试：刷新页面，所有加载失败的图片都自动替换成了占位图。"好多了，" 你松了口气。

但老陈说："还不够。你应该实现多级降级：先尝试备用 CDN，然后是本地图片，最后才是占位图。"

## 多级降级方案

老陈展示了更完善的降级方案：

```javascript
class ImageFallback {
  constructor(img) {
    this.img = img;
    this.originalSrc = img.src;
    this.fallbackSources = [
      // 1. 原始 CDN
      this.originalSrc,
      // 2. 备用 CDN
      this.originalSrc.replace('cdn.example.com', 'cdn2.example.com'),
      // 3. 本地服务器
      this.originalSrc.replace('https://cdn.example.com', ''),
      // 4. 占位图
      '/images/placeholder.png'
    ];
    this.currentIndex = 0;
    this.init();
  }

  init() {
    this.img.addEventListener('error', () => this.handleError());
  }

  handleError() {
    this.currentIndex++;

    if (this.currentIndex >= this.fallbackSources.length) {
      console.error('所有降级方案都失败:', this.originalSrc);
      this.img.classList.add('image-failed');
      return;
    }

    console.log(`尝试降级方案 ${this.currentIndex + 1}:`, this.fallbackSources[this.currentIndex]);
    this.img.src = this.fallbackSources[this.currentIndex];
  }
}

// 全局应用
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('img').forEach(img => {
    new ImageFallback(img);
  });
});
```

测试：CDN 故障时，图片自动尝试备用 CDN，失败后尝试本地服务器，最后才显示占位图。"这样用户体验好多了，" 老陈说。

## 脚本加载错误处理

老陈展示了如何处理脚本加载错误：

```html
<!-- 1. 使用 onerror 属性 -->
<script
  src="https://cdn.example.com/js/app.js"
  onerror="handleScriptError(this)"
></script>

<script>
function handleScriptError(script) {
  console.error('脚本加载失败:', script.src);

  // 尝试备用 CDN
  const fallbackSrc = script.src.replace('cdn.example.com', 'cdn2.example.com');

  if (script.src !== fallbackSrc) {
    console.log('尝试备用 CDN:', fallbackSrc);

    const fallbackScript = document.createElement('script');
    fallbackScript.src = fallbackSrc;
    fallbackScript.onerror = () => {
      console.error('备用 CDN 也失败');
      alert('系统资源加载失败，请刷新页面重试');
    };

    document.head.appendChild(fallbackScript);
  }
}
</script>
```

老陈说："更好的做法是用 JavaScript 动态加载脚本，完全控制错误处理：

```javascript
function loadScript(src, fallbacks = []) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;

    script.onload = () => {
      console.log('脚本加载成功:', src);
      resolve(script);
    };

    script.onerror = () => {
      console.error('脚本加载失败:', src);

      // 尝试降级方案
      if (fallbacks.length > 0) {
        const nextSrc = fallbacks.shift();
        console.log('尝试降级方案:', nextSrc);

        loadScript(nextSrc, fallbacks)
          .then(resolve)
          .catch(reject);
      } else {
        reject(new Error(`Failed to load script: ${src}`));
      }
    };

    document.head.appendChild(script);
  });
}

// 使用示例
loadScript('https://cdn.example.com/js/app.js', [
  'https://cdn2.example.com/js/app.js',
  '/js/app.js'
])
.then(() => {
  console.log('应用初始化成功');
  initApp();
})
.catch(error => {
  console.error('应用加载失败:', error);
  document.body.innerHTML = `
    <div class="error-message">
      <h1>加载失败</h1>
      <p>系统资源加载失败，请检查网络连接后刷新页面。</p>
      <button onclick="location.reload()">刷新页面</button>
    </div>
  `;
});
```

## 样式表加载错误

老陈展示了如何处理 CSS 加载错误：

```javascript
// CSS 加载监听
function loadStylesheet(href, fallbacks = []) {
  return new Promise((resolve, reject) => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;

    link.onload = () => {
      console.log('样式表加载成功:', href);
      resolve(link);
    };

    link.onerror = () => {
      console.error('样式表加载失败:', href);

      if (fallbacks.length > 0) {
        const nextHref = fallbacks.shift();
        console.log('尝试降级方案:', nextHref);

        loadStylesheet(nextHref, fallbacks)
          .then(resolve)
          .catch(reject);
      } else {
        reject(new Error(`Failed to load stylesheet: ${href}`));
      }
    };

    document.head.appendChild(link);
  });
}

// 使用示例
loadStylesheet('https://cdn.example.com/css/main.css', [
  'https://cdn2.example.com/css/main.css',
  '/css/main.css'
])
.catch(error => {
  console.error('样式表加载失败:', error);

  // 使用内联样式作为最终降级
  const style = document.createElement('style');
  style.textContent = `
    body { font-family: sans-serif; }
    .error-message { padding: 20px; text-align: center; }
  `;
  document.head.appendChild(style);
});
```

## 懒加载图片的错误处理

老陈展示了懒加载图片的错误处理：

```javascript
class LazyImage {
  constructor(img) {
    this.img = img;
    this.src = img.dataset.src;
    this.fallbacks = [
      this.src,
      this.src.replace('cdn.example.com', 'cdn2.example.com'),
      '/images/placeholder.png'
    ];
    this.currentIndex = 0;
    this.observer = null;
    this.init();
  }

  init() {
    // 使用 IntersectionObserver 实现懒加载
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this.load();
          this.observer.disconnect();
        }
      });
    });

    this.observer.observe(this.img);
  }

  load() {
    const currentSrc = this.fallbacks[this.currentIndex];

    // 显示加载中状态
    this.img.classList.add('loading');

    // 预加载图片
    const tempImg = new Image();

    tempImg.onload = () => {
      this.img.src = currentSrc;
      this.img.classList.remove('loading');
      this.img.classList.add('loaded');
      console.log('图片加载成功:', currentSrc);
    };

    tempImg.onerror = () => {
      console.error('图片加载失败:', currentSrc);
      this.currentIndex++;

      if (this.currentIndex < this.fallbacks.length) {
        console.log('尝试降级方案:', this.fallbacks[this.currentIndex]);
        this.load();
      } else {
        this.img.classList.remove('loading');
        this.img.classList.add('failed');
        console.error('所有降级方案都失败');
      }
    };

    tempImg.src = currentSrc;
  }
}

// 使用懒加载
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('img[data-src]').forEach(img => {
    new LazyImage(img);
  });
});
```

```html
<!-- HTML 使用示例 -->
<img
  data-src="https://cdn.example.com/images/product.jpg"
  alt="商品图片"
  class="lazy"
>

<style>
.lazy {
  min-height: 200px;
  background: #f0f0f0;
}

.lazy.loading {
  background: #f0f0f0 url('/images/spinner.gif') center no-repeat;
}

.lazy.loaded {
  background: none;
}

.lazy.failed {
  background: #f0f0f0 url('/images/placeholder.png') center no-repeat;
}
</style>
```

## 全局错误监控

老陈展示了完整的资源加载错误监控方案：

```javascript
class ResourceMonitor {
  constructor() {
    this.failedResources = [];
    this.init();
  }

  init() {
    // 监听所有资源加载错误（捕获阶段）
    window.addEventListener('error', (event) => {
      const target = event.target;

      // 只处理资源加载错误，不处理 JavaScript 错误
      if (target !== window) {
        this.handleResourceError(event);
      }
    }, true);

    // 监听未捕获的 Promise 错误
    window.addEventListener('unhandledrejection', (event) => {
      console.error('未捕获的 Promise 错误:', event.reason);
      this.reportError('promise', event.reason);
    });
  }

  handleResourceError(event) {
    const target = event.target;
    const tagName = target.tagName;
    const src = target.src || target.href;

    console.error('资源加载失败:', {
      type: tagName,
      url: src,
      time: new Date().toISOString()
    });

    // 记录失败资源
    this.failedResources.push({
      type: tagName,
      url: src,
      time: Date.now()
    });

    // 上报错误
    this.reportError(tagName, src);

    // 根据资源类型处理
    switch (tagName) {
      case 'IMG':
        this.handleImageError(target);
        break;
      case 'SCRIPT':
        this.handleScriptError(target);
        break;
      case 'LINK':
        this.handleStylesheetError(target);
        break;
    }
  }

  handleImageError(img) {
    if (img.dataset.fallback && img.src !== img.dataset.fallback) {
      img.src = img.dataset.fallback;
    } else {
      img.src = '/images/placeholder.png';
      img.classList.add('image-error');
    }
  }

  handleScriptError(script) {
    const fallback = script.dataset.fallback;

    if (fallback && script.src !== fallback) {
      const newScript = document.createElement('script');
      newScript.src = fallback;
      document.head.appendChild(newScript);
    } else {
      console.error('关键脚本加载失败，显示错误页面');
      this.showErrorPage();
    }
  }

  handleStylesheetError(link) {
    const fallback = link.dataset.fallback;

    if (fallback && link.href !== fallback) {
      const newLink = document.createElement('link');
      newLink.rel = 'stylesheet';
      newLink.href = fallback;
      document.head.appendChild(newLink);
    }
  }

  reportError(type, url) {
    // 上报到错误监控系统
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/errors', JSON.stringify({
        type,
        url,
        userAgent: navigator.userAgent,
        timestamp: Date.now()
      }));
    }
  }

  showErrorPage() {
    document.body.innerHTML = `
      <div class="error-page">
        <h1>系统加载失败</h1>
        <p>部分关键资源无法加载，请检查网络连接后刷新页面。</p>
        <button onclick="location.reload()">刷新页面</button>
      </div>
    `;
  }

  getFailedResources() {
    return this.failedResources;
  }
}

// 启动资源监控
const monitor = new ResourceMonitor();
```

下午 6 点，你部署了新版本的资源加载错误处理机制。即使 CDN 故障，页面也能自动降级到备用方案，用户看到的是占位图而不是破损图标。你给运营部门发消息："已实现资源加载的多级降级方案，CDN 故障时页面仍能正常显示。"

## 资源加载错误法则

**规则 1: 使用捕获阶段监听全局错误**

在 `window` 上使用捕获阶段监听 `error` 事件，可以捕获所有资源加载错误（图片、脚本、样式表）。目标阶段和冒泡阶段不会触发资源错误。

```javascript
// ✅ 正确：捕获阶段监听
window.addEventListener('error', (event) => {
  const target = event.target;

  // 区分资源错误和 JavaScript 错误
  if (target !== window) {
    console.error('资源加载失败:', target.tagName, target.src || target.href);

    if (target.tagName === 'IMG') {
      target.src = '/images/placeholder.png';
    }
  }
}, true); // 必须使用捕获阶段

// ❌ 错误：冒泡阶段（不会触发）
window.addEventListener('error', (event) => {
  // 资源错误不会在这里触发
}, false);

// JavaScript 错误和资源错误的区分
window.addEventListener('error', (event) => {
  if (event.target !== window) {
    console.log('资源错误:', event.target.src);
  } else {
    console.log('JavaScript 错误:', event.message, event.filename, event.lineno);
  }
}, true);
```

**规则 2: 实现多级降级方案**

不要直接使用占位图，而是实现多级降级：原始 CDN → 备用 CDN → 本地服务器 → 占位图，提高资源加载成功率。

```javascript
class ResourceFallback {
  constructor(element, fallbacks) {
    this.element = element;
    this.fallbacks = fallbacks;
    this.currentIndex = 0;
    this.init();
  }

  init() {
    this.element.addEventListener('error', () => this.tryNextFallback());
  }

  tryNextFallback() {
    this.currentIndex++;

    if (this.currentIndex >= this.fallbacks.length) {
      console.error('所有降级方案失败');
      this.onAllFallbacksFailed();
      return;
    }

    const nextSrc = this.fallbacks[this.currentIndex];
    console.log(`尝试降级方案 ${this.currentIndex + 1}:`, nextSrc);

    if (this.element.tagName === 'IMG') {
      this.element.src = nextSrc;
    } else if (this.element.tagName === 'SCRIPT') {
      this.loadScript(nextSrc);
    }
  }

  onAllFallbacksFailed() {
    if (this.element.tagName === 'IMG') {
      this.element.src = '/images/placeholder.png';
      this.element.classList.add('resource-failed');
    }
  }

  loadScript(src) {
    const script = document.createElement('script');
    script.src = src;
    script.onerror = () => this.tryNextFallback();
    document.head.appendChild(script);
  }
}

// 使用多级降级
new ResourceFallback(imgElement, [
  'https://cdn1.example.com/image.jpg',  // 原始 CDN
  'https://cdn2.example.com/image.jpg',  // 备用 CDN
  '/images/image.jpg',                   // 本地服务器
  '/images/placeholder.png'              // 占位图
]);
```

**规则 3: 动态加载资源时处理错误**

动态创建的 `<script>`、`<img>`、`<link>` 元素必须监听 `error` 事件，避免静默失败。使用 Promise 封装加载过程。

```javascript
// ✅ 正确：Promise 封装资源加载
function loadResource(tagName, src, attributes = {}) {
  return new Promise((resolve, reject) => {
    const element = document.createElement(tagName);

    // 设置属性
    Object.entries(attributes).forEach(([key, value]) => {
      element[key] = value;
    });

    // 监听加载完成
    element.onload = () => {
      console.log('资源加载成功:', src);
      resolve(element);
    };

    // 监听加载失败
    element.onerror = () => {
      console.error('资源加载失败:', src);
      reject(new Error(`Failed to load ${tagName}: ${src}`));
    };

    // 设置 src/href
    if (tagName === 'script' || tagName === 'img') {
      element.src = src;
    } else if (tagName === 'link') {
      element.href = src;
    }

    document.head.appendChild(element);
  });
}

// 使用示例
async function loadResources() {
  try {
    await loadResource('script', '/js/vendor.js');
    await loadResource('script', '/js/app.js');
    await loadResource('link', '/css/main.css', { rel: 'stylesheet' });

    console.log('所有资源加载完成');
    initApp();
  } catch (error) {
    console.error('资源加载失败:', error);
    showErrorMessage('系统加载失败，请刷新页面');
  }
}
```

**规则 4: 避免降级死循环**

降级方案中的资源（如占位图）也可能加载失败，必须设置终止条件避免无限重试。

```javascript
class SafeImageFallback {
  constructor(img) {
    this.img = img;
    this.originalSrc = img.src;
    this.retryCount = 0;
    this.maxRetries = 3;
    this.hasFallback = false;
    this.init();
  }

  init() {
    this.img.addEventListener('error', () => this.handleError());
  }

  handleError() {
    // ✅ 防止无限重试
    if (this.hasFallback) {
      console.error('占位图也加载失败，停止重试');
      return;
    }

    // ✅ 限制重试次数
    this.retryCount++;
    if (this.retryCount > this.maxRetries) {
      console.error('达到最大重试次数');
      this.useFallback();
      return;
    }

    console.log(`重试第 ${this.retryCount} 次`);
    // 添加时间戳防止缓存
    this.img.src = this.originalSrc + '?retry=' + this.retryCount;
  }

  useFallback() {
    this.hasFallback = true;
    this.img.src = '/images/placeholder.png';
    this.img.classList.add('image-failed');
  }
}
```

**规则 5: 上报资源加载错误**

收集资源加载错误信息并上报到监控系统，帮助发现 CDN 故障、网络问题、资源丢失等问题。

```javascript
class ResourceErrorReporter {
  constructor() {
    this.errors = [];
    this.reportInterval = 10000; // 每 10 秒上报一次
    this.init();
  }

  init() {
    // 监听资源错误
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.collectError(event);
      }
    }, true);

    // 定期上报
    setInterval(() => this.report(), this.reportInterval);

    // 页面卸载时上报
    window.addEventListener('pagehide', () => this.report());
  }

  collectError(event) {
    const target = event.target;

    this.errors.push({
      type: target.tagName,
      url: target.src || target.href,
      page: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: Date.now()
    });
  }

  report() {
    if (this.errors.length === 0) return;

    const data = {
      errors: this.errors,
      session: this.getSessionId()
    };

    // 使用 sendBeacon 可靠上报
    navigator.sendBeacon('/api/resource-errors', JSON.stringify(data));

    // 清空已上报的错误
    this.errors = [];
  }

  getSessionId() {
    let sessionId = sessionStorage.getItem('sessionId');
    if (!sessionId) {
      sessionId = Date.now() + '-' + Math.random().toString(36);
      sessionStorage.setItem('sessionId', sessionId);
    }
    return sessionId;
  }
}

new ResourceErrorReporter();
```

**规则 6: 处理关键资源失败**

区分关键资源（必需）和非关键资源（可选）。关键资源失败时显示错误页面，非关键资源失败时静默降级。

```javascript
class CriticalResourceLoader {
  constructor() {
    this.criticalResources = new Map();
    this.optionalResources = new Map();
  }

  // 加载关键资源
  async loadCritical(src, fallbacks = []) {
    try {
      await this.loadWithFallback(src, fallbacks);
      this.criticalResources.set(src, 'success');
    } catch (error) {
      this.criticalResources.set(src, 'failed');
      throw error;
    }
  }

  // 加载可选资源
  async loadOptional(src, fallbacks = []) {
    try {
      await this.loadWithFallback(src, fallbacks);
      this.optionalResources.set(src, 'success');
    } catch (error) {
      console.warn('可选资源加载失败:', src);
      this.optionalResources.set(src, 'failed');
      // 不抛出错误，继续执行
    }
  }

  async loadWithFallback(src, fallbacks) {
    const sources = [src, ...fallbacks];

    for (const source of sources) {
      try {
        await this.loadScript(source);
        return;
      } catch (error) {
        console.error('加载失败:', source);
      }
    }

    throw new Error(`所有降级方案失败: ${src}`);
  }

  loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  async init() {
    try {
      // 加载关键资源（必须成功）
      await this.loadCritical('/js/react.js', [
        'https://cdn.jsdelivr.net/npm/react/umd/react.production.min.js'
      ]);

      await this.loadCritical('/js/app.js');

      // 加载可选资源（失败不影响主应用）
      await this.loadOptional('/js/analytics.js');
      await this.loadOptional('/js/chat-widget.js');

      console.log('应用初始化成功');
      this.startApp();
    } catch (error) {
      console.error('关键资源加载失败:', error);
      this.showErrorPage();
    }
  }

  startApp() {
    // 启动应用
  }

  showErrorPage() {
    document.body.innerHTML = `
      <div class="error-page">
        <h1>系统加载失败</h1>
        <p>关键资源无法加载，请检查网络后刷新页面。</p>
        <button onclick="location.reload()">刷新页面</button>
      </div>
    `;
  }
}

const loader = new CriticalResourceLoader();
loader.init();
```

---

**记录者注**:

资源加载失败是 Web 应用常见的问题，CDN 故障、网络不稳定、资源丢失都会导致图片、脚本、样式表加载失败。没有错误处理的页面会显示破损图标、功能失效、白屏，严重影响用户体验。

关键在于实现多级降级方案和全局错误监控。使用捕获阶段监听 `error` 事件捕获所有资源错误，实现原始 CDN → 备用 CDN → 本地服务器 → 占位图的多级降级，避免降级死循环，上报错误信息到监控系统，区分关键资源和可选资源。

记住：**捕获阶段监听全局错误，实现多级降级方案，动态加载时处理错误，避免降级死循环，上报错误信息，区分关键和可选资源**。完善的错误处理是高可用 Web 应用的基础。
