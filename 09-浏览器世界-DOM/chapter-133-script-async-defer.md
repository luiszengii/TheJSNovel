《第 133 次记录：脚本的加载时机 —— async、defer 与阻塞渲染的真相》

## 白屏时间过长

周三上午 10 点 26 分，你收到了性能监控系统的告警："首屏渲染时间（FCP）从 800ms 飙升到 3200ms！"

你打开线上页面，确实感觉到明显的白屏时间变长。你查看了昨天的部署记录，发现市场部要求在页面顶部添加了一个第三方广告脚本：

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>商城首页</title>
  <link rel="stylesheet" href="/css/main.css">

  <!-- 新添加的广告脚本 -->
  <script src="https://ads.example.com/sdk.js"></script>
</head>
<body>
  <div id="app">...</div>
  <script src="/js/main.js"></script>
</body>
</html>
```

你打开 Chrome DevTools 的 Network 面板，刷新页面。发现 `ads.example.com/sdk.js` 加载了整整 2.5 秒！在这 2.5 秒内，页面一片空白，DOM 完全没有渲染。

"问题找到了，" 你自言自语，"`<head>` 里的阻塞脚本拖慢了整个页面的渲染。"

前端架构师老刘走过来："外部脚本放在 `<head>` 里，而且没有 `async` 或 `defer`，当然会阻塞渲染。你需要理解脚本加载的三种模式。"

## 普通脚本：阻塞解析

老刘画了一个时间线图：

```
<!-- 普通脚本（无 async/defer） -->
<script src="script.js"></script>

时间线：
HTML 解析 ──┐
            ▼ 停止解析
            下载 script.js ───┐
                              ▼
                              执行 script.js ───┐
                                                ▼
                                                继续解析 HTML ───┐
                                                                ▼
                                                                DOMContentLoaded
```

老刘解释道："普通 `<script>` 标签会立即停止 HTML 解析，下载并执行脚本，然后才继续解析。这就是为什么你的页面白屏了 2.5 秒。"

你做了一个实验：

```html
<!DOCTYPE html>
<html>
<head>
  <title>测试页面</title>
  <script>
    console.log('1. head 中的内联脚本');
    console.log('此时 body 存在吗？', document.body); // null
  </script>

  <script src="slow-script.js"></script>
  <!-- slow-script.js 需要 3 秒加载 -->
</head>
<body>
  <h1>Hello World</h1>

  <script>
    console.log('2. body 中的内联脚本');
    console.log('此时 h1 存在吗？', document.querySelector('h1')); // 存在
  </script>

  <script src="fast-script.js"></script>
</body>
</html>
```

刷新页面，控制台输出：

```
1. head 中的内联脚本
此时 body 存在吗？ null

（等待 3 秒...页面白屏）

2. body 中的内联脚本
此时 h1 存在吗？ <h1>Hello World</h1>
```

"看，" 老刘说，"`<head>` 里的脚本执行时，`<body>` 还不存在。而且脚本加载期间，页面完全白屏，用户体验很差。"

## defer: 延迟执行

老刘展示了 `defer` 的用法：

```html
<head>
  <script defer src="script.js"></script>
</head>

时间线：
HTML 解析 ─────────────────────────────────┐
           ▼                                ▼
           下载 script.js（并行）            DOMContentLoaded 前
                          ▼                 ▼
                          等待 HTML 解析完成 │
                                           ▼
                                           执行 script.js ──┐
                                                           ▼
                                                           DOMContentLoaded
```

老刘解释："`defer` 让脚本在后台下载，不阻塞 HTML 解析。等 HTML 完全解析完成后，按照脚本在文档中的顺序依次执行，然后触发 `DOMContentLoaded`。"

你测试了 `defer`：

```html
<!DOCTYPE html>
<html>
<head>
  <script defer src="defer1.js"></script>
  <script defer src="defer2.js"></script>
  <script defer src="defer3.js"></script>

  <script>
    console.log('1. head 中的内联脚本');
  </script>
</head>
<body>
  <h1>Hello World</h1>

  <script>
    console.log('2. body 中的内联脚本');
    console.log('此时 defer 脚本执行了吗？', window.defer1Loaded); // undefined
  </script>
</body>
</html>
```

```javascript
// defer1.js
console.log('3. defer1.js 执行');
window.defer1Loaded = true;

// defer2.js
console.log('4. defer2.js 执行');

// defer3.js
console.log('5. defer3.js 执行');
```

控制台输出：

```
1. head 中的内联脚本
2. body 中的内联脚本
此时 defer 脚本执行了吗？ undefined

（HTML 解析完成）

3. defer1.js 执行
4. defer2.js 执行
5. defer3.js 执行
DOMContentLoaded
```

"注意顺序，" 老刘说，"defer 脚本严格按照文档顺序执行，在 `DOMContentLoaded` 之前。"

## async: 异步执行

老刘展示了 `async` 的用法：

```html
<head>
  <script async src="script.js"></script>
</head>

时间线：
HTML 解析 ──────────┐（可能被打断）──────────┐
           ▼        ▼                        ▼
           下载 script.js（并行）            DOMContentLoaded
                  ▼
                  下载完成，立即执行 ──┐
                                     ▼
                                     继续解析 HTML
```

老刘解释："`async` 让脚本在后台下载，下载完成后立即执行，可能在 HTML 解析过程中打断解析。执行顺序不确定，哪个先下载完就先执行哪个。"

你测试了 `async`：

```html
<!DOCTYPE html>
<html>
<head>
  <script async src="async1.js"></script>
  <script async src="async2.js"></script>
  <script async src="async3.js"></script>
</head>
<body>
  <h1>Hello World</h1>

  <script>
    console.log('body 中的内联脚本');
  </script>
</body>
</html>
```

```javascript
// async1.js（100KB，慢）
console.log('async1.js 执行');

// async2.js（10KB，快）
console.log('async2.js 执行');

// async3.js（50KB，中等）
console.log('async3.js 执行');
```

刷新页面几次，控制台输出顺序每次都不同：

```
第一次：
body 中的内联脚本
async2.js 执行
async3.js 执行
async1.js 执行

第二次：
async2.js 执行
body 中的内联脚本
async1.js 执行
async3.js 执行

第三次：
async2.js 执行
async3.js 执行
body 中的内联脚本
async1.js 执行
```

"看到了吗？" 老刘说，"`async` 脚本的执行顺序完全不确定，取决于下载速度。而且可能在 DOM 解析完成前或完成后执行。"

## 三种模式对比

老刘整理了一个对比表：

| 特性 | 普通 `<script>` | `defer` | `async` |
|------|----------------|---------|---------|
| 下载时机 | 立即下载 | 立即下载（并行） | 立即下载（并行） |
| 执行时机 | 立即执行（阻塞） | HTML 解析完成后 | 下载完成后立即执行 |
| 阻塞 HTML 解析 | ✅ 阻塞 | ❌ 不阻塞 | ❌ 不阻塞下载<br>⚠️ 可能阻塞执行 |
| 执行顺序 | 按文档顺序 | 按文档顺序 | 不确定（先下载完先执行） |
| DOMContentLoaded | 脚本执行后触发 | 脚本执行后触发 | 可能在脚本前或后触发 |
| DOM 可用性 | 取决于位置 | ✅ DOM 完全可用 | ⚠️ 不确定 |
| 适用场景 | 需要立即执行<br>依赖 DOM 位置 | 依赖 DOM<br>脚本间有依赖 | 独立脚本<br>无依赖（如统计） |

老刘说："总结一下：
- **普通脚本**：阻塞解析，按顺序执行，适合必须立即执行的脚本
- **defer**：不阻塞解析，按顺序执行，适合依赖 DOM 和脚本顺序的主应用脚本
- **async**：不阻塞解析，乱序执行，适合完全独立的第三方脚本"

## 实际应用场景

老刘展示了几个实际应用场景：

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>最佳实践</title>

  <!-- 1. 关键 CSS（同步加载，阻塞渲染） -->
  <link rel="stylesheet" href="/css/critical.css">

  <!-- 2. 非关键 CSS（异步加载） -->
  <link rel="preload" href="/css/non-critical.css" as="style" onload="this.onload=null;this.rel='stylesheet'">

  <!-- 3. 独立的第三方脚本（async） -->
  <script async src="https://www.googletagmanager.com/gtag/js"></script>
  <script async src="https://analytics.example.com/tracker.js"></script>

  <!-- 4. 主应用脚本（defer） -->
  <script defer src="/js/vendor.js"></script>
  <script defer src="/js/app.js"></script>
</head>
<body>
  <div id="app">...</div>

  <!-- 5. 需要立即执行的内联脚本 -->
  <script>
    // 初始化全局配置
    window.APP_CONFIG = {
      apiUrl: '/api',
      version: '1.0.0'
    };
  </script>

  <!-- 6. 依赖 DOM 的内联脚本（不要用 defer） -->
  <script>
    // 内联脚本不支持 defer/async，总是立即执行
    document.querySelector('#app').classList.add('initialized');
  </script>
</body>
</html>
```

老刘解释每个场景：

```javascript
// 场景 1: Google Analytics（async）
// 完全独立，不依赖其他脚本，不需要 DOM
<script async src="https://www.googletagmanager.com/gtag/js"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>

// 场景 2: jQuery + 插件（defer）
// 插件依赖 jQuery，需要保证顺序
<script defer src="/js/jquery.js"></script>
<script defer src="/js/jquery.plugin.js"></script>
<script defer src="/js/app.js"></script>

// 场景 3: React 应用（defer）
// 组件依赖 React 库，需要 DOM 完全加载
<script defer src="/js/react.js"></script>
<script defer src="/js/react-dom.js"></script>
<script defer src="/js/app.js"></script>

// 场景 4: 广告脚本（async）
// 独立运行，不影响主应用
<script async src="https://ads.example.com/sdk.js"></script>

// 场景 5: Polyfill（普通脚本）
// 必须在其他脚本前加载，放在 <head> 最前面
<script src="/js/polyfill.js"></script>
```

## 动态加载脚本

老刘展示了如何用 JavaScript 动态加载脚本：

```javascript
// 动态加载脚本（默认行为类似 async）
function loadScript(src, options = {}) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;

    // 设置 async 或 defer
    if (options.async !== undefined) {
      script.async = options.async;
    }
    if (options.defer) {
      script.defer = true;
    }

    // 监听加载完成
    script.onload = () => {
      console.log('脚本加载成功:', src);
      resolve(script);
    };

    // 监听加载失败
    script.onerror = () => {
      console.error('脚本加载失败:', src);
      reject(new Error(`Failed to load script: ${src}`));
    };

    document.head.appendChild(script);
  });
}

// 使用示例
async function initApp() {
  try {
    // 加载依赖脚本（按顺序）
    await loadScript('/js/jquery.js');
    await loadScript('/js/plugin.js');
    await loadScript('/js/app.js');

    console.log('所有脚本加载完成');
  } catch (error) {
    console.error('脚本加载失败:', error);
  }
}

// 并行加载多个独立脚本
Promise.all([
  loadScript('https://analytics.com/tracker.js', { async: true }),
  loadScript('https://ads.com/sdk.js', { async: true }),
  loadScript('https://chat.com/widget.js', { async: true })
]).then(() => {
  console.log('所有第三方脚本加载完成');
});
```

## 修复白屏问题

老刘帮你重构了页面的脚本加载：

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>商城首页</title>
  <link rel="stylesheet" href="/css/main.css">

  <!-- ✅ 改进：广告脚本改用 async，不阻塞渲染 -->
  <script async src="https://ads.example.com/sdk.js"></script>

  <!-- ✅ 主应用脚本使用 defer -->
  <script defer src="/js/main.js"></script>
</head>
<body>
  <div id="app">
    <!-- 关键内容，优先渲染 -->
    <header>...</header>
    <main>...</main>
  </div>

  <!-- ✅ 广告位容器，即使脚本加载慢也不影响主内容 -->
  <div id="ad-container"></div>

  <script>
    // 广告脚本加载完成后初始化
    window.addEventListener('load', () => {
      if (window.AdSDK) {
        window.AdSDK.init({ container: '#ad-container' });
      }
    });
  </script>
</body>
</html>
```

你测试了新版本：
- 首屏渲染时间（FCP）：从 3200ms 降到 850ms ✅
- 可交互时间（TTI）：从 3500ms 降到 1200ms ✅
- 广告加载慢时不影响主内容显示 ✅

下午 4 点，你部署了优化后的版本。性能监控显示 FCP 恢复正常，用户不再抱怨白屏时间长。你给市场部发邮件："广告脚本已优化为异步加载，不会再影响页面性能了。"

## 脚本加载模式法则

**规则 1: 理解三种加载模式的差异**

普通 `<script>` 阻塞 HTML 解析；`defer` 并行下载、顺序执行、DOM 后执行；`async` 并行下载、乱序执行、下载完立即执行。

```html
<!-- 普通脚本：阻塞解析 -->
<script src="script.js"></script>
<!-- HTML 解析停止 → 下载脚本 → 执行脚本 → 继续解析 -->

<!-- defer：并行下载，顺序执行，DOM 后执行 -->
<script defer src="script.js"></script>
<!-- HTML 继续解析（并行下载） → HTML 解析完成 → 执行脚本 → DOMContentLoaded -->

<!-- async：并行下载，乱序执行，下载完立即执行 -->
<script async src="script.js"></script>
<!-- HTML 继续解析（并行下载） → 下载完成 → 暂停解析 → 执行脚本 → 继续解析 -->

<!-- 对比表 -->
<!--
特性              | 普通        | defer         | async
------------------|-------------|---------------|---------------
阻塞 HTML 解析    | ✅ 是       | ❌ 否         | ❌ 否（下载）
执行时机          | 立即        | DOM 解析完成后 | 下载完成后
执行顺序          | 按文档顺序  | 按文档顺序     | 不确定
DOM 可用性        | 取决于位置  | ✅ 完全可用   | ⚠️ 不确定
DOMContentLoaded  | 脚本后触发  | 脚本后触发     | 可能前或后
-->
```

**规则 2: defer 用于主应用脚本**

主应用脚本通常依赖 DOM 和脚本间的执行顺序，使用 `defer` 确保 DOM 完全加载且脚本按顺序执行。

```html
<!-- ✅ 正确：主应用使用 defer -->
<head>
  <!-- 库和框架 -->
  <script defer src="/js/react.js"></script>
  <script defer src="/js/react-dom.js"></script>

  <!-- 应用代码 -->
  <script defer src="/js/app.js"></script>
</head>
<body>
  <div id="root"></div>
</body>

<!-- app.js 执行时的保证：
  1. DOM 完全加载（document.querySelector 可用）
  2. React 和 ReactDOM 已加载（依赖满足）
  3. 在 DOMContentLoaded 之前执行
-->

<!-- ❌ 错误：主应用使用 async -->
<script async src="/js/react.js"></script>
<script async src="/js/app.js"></script>
<!-- 问题：app.js 可能在 react.js 之前执行，导致错误 -->

<!-- ❌ 错误：主应用使用普通脚本放在 head -->
<head>
  <script src="/js/app.js"></script>
  <!-- 问题：阻塞渲染，且 DOM 不可用 -->
</head>
```

**规则 3: async 用于独立的第三方脚本**

第三方统计、广告、社交插件等独立脚本使用 `async`，它们不依赖其他脚本和 DOM，下载完立即执行不影响主应用。

```html
<!-- ✅ 正确：独立脚本使用 async -->
<head>
  <!-- Google Analytics -->
  <script async src="https://www.googletagmanager.com/gtag/js"></script>

  <!-- 广告脚本 -->
  <script async src="https://ads.example.com/sdk.js"></script>

  <!-- 社交分享按钮 -->
  <script async src="https://platform.twitter.com/widgets.js"></script>

  <!-- 客服聊天插件 -->
  <script async src="https://chat.example.com/widget.js"></script>
</head>

<!-- 这些脚本的特点：
  1. 完全独立，不依赖其他脚本
  2. 不需要 DOM 立即可用（会自行等待）
  3. 执行顺序不重要
  4. 加载慢不影响主应用
-->

<!-- ❌ 错误：有依赖的脚本使用 async -->
<script async src="/js/jquery.js"></script>
<script async src="/js/jquery.plugin.js"></script>
<!-- 问题：plugin 可能在 jQuery 之前执行 -->
```

**规则 4: 避免在 head 中使用普通脚本**

普通脚本在 `<head>` 中会阻塞 HTML 解析和渲染，导致白屏时间长。应使用 `defer`/`async` 或将脚本放在 `</body>` 前。

```html
<!-- ❌ 最差：head 中的普通脚本（阻塞渲染） -->
<head>
  <script src="/js/app.js"></script>
  <!-- 页面白屏直到脚本下载并执行完成 -->
</head>
<body>...</body>

<!-- ✅ 较好：body 末尾的普通脚本 -->
<body>
  <div id="app">...</div>

  <script src="/js/app.js"></script>
  <!-- DOM 已渲染，脚本不阻塞首屏 -->
</body>

<!-- ✅ 最好：head 中的 defer 脚本 -->
<head>
  <script defer src="/js/app.js"></script>
  <!-- 并行下载，不阻塞渲染 -->
</head>
<body>
  <div id="app">...</div>
</body>

<!-- 性能对比（假设脚本需要 1 秒加载）：
  head 普通脚本：FCP = 1000ms + 解析时间
  body 末尾脚本：FCP = 解析时间
  head defer 脚本：FCP = 解析时间（脚本并行下载）
-->
```

**规则 5: 内联脚本不支持 defer/async**

内联脚本（`<script>` 标签内直接写代码）总是立即执行，`defer` 和 `async` 属性对内联脚本无效。

```html
<!-- ❌ 无效：内联脚本的 defer/async 会被忽略 -->
<script defer>
  console.log('立即执行，defer 无效');
</script>

<script async>
  console.log('立即执行，async 无效');
</script>

<!-- ✅ 正确：内联脚本放在合适位置 -->
<body>
  <div id="app"></div>

  <!-- 在 DOM 元素之后执行 -->
  <script>
    document.querySelector('#app').textContent = 'Hello';
  </script>
</body>

<!-- ✅ 正确：等待 DOM 加载 -->
<head>
  <script>
    document.addEventListener('DOMContentLoaded', () => {
      document.querySelector('#app').textContent = 'Hello';
    });
  </script>
</head>
```

**规则 6: 动态加载脚本默认为 async**

使用 JavaScript 动态创建的 `<script>` 元素默认行为类似 `async`，可以显式设置 `async = false` 改为顺序执行。

```javascript
// 动态脚本（默认 async 行为）
const script = document.createElement('script');
script.src = '/js/app.js';
document.head.appendChild(script);
// 下载完立即执行，不保证顺序

// ✅ 按顺序加载多个脚本
async function loadScriptsInOrder(urls) {
  for (const url of urls) {
    const script = document.createElement('script');
    script.src = url;
    script.async = false; // 关键：禁用 async，按顺序执行
    document.head.appendChild(script);

    await new Promise((resolve, reject) => {
      script.onload = resolve;
      script.onerror = reject;
    });
  }
}

await loadScriptsInOrder([
  '/js/jquery.js',
  '/js/plugin.js',
  '/js/app.js'
]);

// ✅ 并行加载独立脚本
function loadScriptAsync(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.async = true; // 明确设置 async
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

await Promise.all([
  loadScriptAsync('https://analytics.com/tracker.js'),
  loadScriptAsync('https://ads.com/sdk.js')
]);
```

---

**记录者注**:

脚本加载是页面性能的关键瓶颈。普通 `<script>` 标签会阻塞 HTML 解析，导致白屏时间长。`defer` 让脚本并行下载、顺序执行、在 DOM 完全加载后执行，适合主应用脚本。`async` 让脚本并行下载、乱序执行、下载完立即执行，适合独立的第三方脚本。

关键在于理解三种模式的差异和适用场景。主应用脚本用 `defer` 保证 DOM 可用和执行顺序，第三方脚本用 `async` 避免阻塞主应用，避免在 `<head>` 中使用普通脚本。内联脚本不支持 `defer`/`async`，动态加载脚本默认为 `async` 行为。

记住：**普通脚本阻塞解析，`defer` 用于主应用（顺序执行、DOM 后），`async` 用于独立脚本（乱序执行、下载完立即执行），避免 head 中的普通脚本，内联脚本总是立即执行**。正确的脚本加载策略是快速渲染的基础。
