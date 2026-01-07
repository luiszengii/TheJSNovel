《第 132 次记录：页面的生与死 —— 从加载到卸载的完整旅程》

## 数据丢失之谜

周二下午 3 点 18 分，你正在调试一个统计功能："记录用户在页面停留的时长。"

产品需求很简单：用户打开页面时开始计时，离开页面时把停留时长发送到服务器。你实现了这个功能：

```javascript
let startTime = Date.now();

window.addEventListener('beforeunload', () => {
  const duration = Date.now() - startTime;

  // 发送统计数据
  fetch('/api/analytics', {
    method: 'POST',
    body: JSON.stringify({ duration }),
    headers: { 'Content-Type': 'application/json' }
  });

  console.log('页面停留时长:', duration);
});
```

你测试了一下：在页面停留 10 秒后关闭标签页，控制台输出"页面停留时长: 10234"。你检查了服务器日志 —— 没有收到任何数据！

"怎么回事？" 你困惑地想。你又测试了几次，发现：
- 点击链接跳转 → 数据有时发送成功，有时失败
- 关闭标签页 → 数据基本不发送
- 刷新页面 → 数据偶尔发送成功

前端负责人老韩走过来："你用 `fetch` 在 `beforeunload` 里发送数据？那不行，`fetch` 是异步的，页面卸载前请求就被取消了。要用 `sendBeacon` 或者 `keepalive` 选项。"

## 页面生命周期概览

老韩给你画了一个页面生命周期的流程图：

```
用户打开页面
    ↓
DOMContentLoaded: DOM 解析完成（JS 可以访问 DOM）
    ↓
load: 所有资源加载完成（图片、CSS、脚本）
    ↓
用户交互...
    ↓
visibilitychange: 页面可见性变化（切换标签页）
    ↓
pagehide/beforeunload: 页面即将卸载
    ↓
unload: 页面卸载（不推荐使用）
```

老韩解释道："页面生命周期有几个关键事件，每个事件都有特定的用途和限制。"

## DOMContentLoaded vs load

老韩展示了 `DOMContentLoaded` 和 `load` 的区别：

```javascript
// DOMContentLoaded: DOM 解析完成
document.addEventListener('DOMContentLoaded', () => {
  console.log('1. DOMContentLoaded');
  console.log('  DOM 树已构建完成');
  console.log('  可以访问所有元素:', document.querySelectorAll('*').length);

  // ✅ 可以操作 DOM
  const button = document.querySelector('button');
  console.log('  找到按钮:', button);

  // ❌ 图片可能还没加载完
  const img = document.querySelector('img');
  console.log('  图片尺寸:', img.naturalWidth, img.naturalHeight);
  // 可能输出 0, 0（图片还没加载完）
});

// load: 所有资源加载完成
window.addEventListener('load', () => {
  console.log('2. load');
  console.log('  所有资源已加载完成');

  // ✅ 图片已加载完成
  const img = document.querySelector('img');
  console.log('  图片尺寸:', img.naturalWidth, img.naturalHeight);
  // 输出实际尺寸，如 800, 600
});

// 实际测试
console.time('DOMContentLoaded');
document.addEventListener('DOMContentLoaded', () => {
  console.timeEnd('DOMContentLoaded'); // 可能是 500ms
});

console.time('load');
window.addEventListener('load', () => {
  console.timeEnd('load'); // 可能是 2000ms
});
```

老韩说："大多数情况下，用 `DOMContentLoaded` 就够了。只有需要等待图片、样式等资源加载完成时，才用 `load` 事件。"

## visibilitychange: 页面可见性

老韩展示了 `visibilitychange` 事件：

```javascript
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    console.log('页面被隐藏');
    // 用户切换到其他标签页，或最小化窗口

    // 暂停视频播放
    pauseVideo();

    // 暂停动画
    pauseAnimation();

    // 保存草稿
    saveDraft();
  } else {
    console.log('页面可见');
    // 用户切换回来

    // 恢复视频播放
    resumeVideo();

    // 恢复动画
    resumeAnimation();

    // 刷新数据
    refreshData();
  }
});

// 检查当前可见性
console.log('页面当前可见性:', document.hidden ? '隐藏' : '可见');
console.log('可见性状态:', document.visibilityState);
// 'visible': 页面可见
// 'hidden': 页面隐藏
// 'prerender': 页面正在预渲染（很少用）
```

老韩说："这个事件非常有用。比如视频网站，用户切换标签页时自动暂停视频；游戏网站，切换标签页时暂停游戏。这能节省资源，也符合用户预期。"

## beforeunload: 页面卸载前

老韩展示了 `beforeunload` 事件的正确用法：

```javascript
let hasUnsavedChanges = false;

// 监听表单输入
document.querySelector('form').addEventListener('input', () => {
  hasUnsavedChanges = true;
});

// 页面卸载前提示
window.addEventListener('beforeunload', (event) => {
  if (hasUnsavedChanges) {
    // 标准做法：设置 returnValue
    event.preventDefault();
    event.returnValue = ''; // 必须设置，但现代浏览器会忽略自定义文本

    // ❌ 已被废弃：自定义提示文本
    return '有未保存的更改，确定要离开吗？';
    // 现代浏览器会显示通用提示，不会显示自定义文本
  }
});

// 提交表单后清除标志
document.querySelector('form').addEventListener('submit', () => {
  hasUnsavedChanges = false;
});
```

老韩特别强调："现代浏览器出于安全考虑，不允许自定义 `beforeunload` 的提示文本。你只能控制是否显示提示，但不能控制提示内容。"

## sendBeacon: 可靠的数据发送

老韩展示了如何用 `sendBeacon` 在页面卸载时发送数据：

```javascript
let startTime = Date.now();

window.addEventListener('beforeunload', () => {
  const duration = Date.now() - startTime;

  // ✅ 使用 sendBeacon（推荐）
  const data = JSON.stringify({
    duration,
    page: window.location.pathname,
    timestamp: Date.now()
  });

  navigator.sendBeacon('/api/analytics', data);
  console.log('数据已发送（sendBeacon）');
});

// sendBeacon 的特点：
// 1. 异步发送，不阻塞页面卸载
// 2. 浏览器保证发送完成（即使页面已关闭）
// 3. 只支持 POST 请求
// 4. 有大小限制（通常 64KB）
```

老韩说："如果必须用 `fetch`，可以加 `keepalive` 选项：

```javascript
window.addEventListener('beforeunload', () => {
  const duration = Date.now() - startTime;

  // ✅ 使用 fetch + keepalive
  fetch('/api/analytics', {
    method: 'POST',
    body: JSON.stringify({ duration }),
    headers: { 'Content-Type': 'application/json' },
    keepalive: true // 保持连接，即使页面关闭
  });
});
```

"但 `sendBeacon` 更简单可靠，优先使用它。"

## pagehide vs beforeunload

老韩展示了 `pagehide` 事件：

```javascript
// beforeunload: 可以取消页面卸载
window.addEventListener('beforeunload', (event) => {
  if (hasUnsavedChanges) {
    event.preventDefault();
    event.returnValue = '';
    // 用户可以选择"留在页面"
  }
});

// pagehide: 页面一定会卸载，无法取消
window.addEventListener('pagehide', (event) => {
  console.log('页面即将卸载');
  console.log('是否进入 bfcache:', event.persisted);

  // 发送统计数据
  const duration = Date.now() - startTime;
  navigator.sendBeacon('/api/analytics', JSON.stringify({ duration }));

  // 清理资源
  clearInterval(timerInterval);
  cancelAnimationFrame(animationId);
});

// pageshow: 页面显示（包括从 bfcache 恢复）
window.addEventListener('pageshow', (event) => {
  console.log('页面显示');
  console.log('是否从 bfcache 恢复:', event.persisted);

  if (event.persisted) {
    // 从 bfcache 恢复，需要重新初始化
    console.log('从缓存恢复，重新初始化状态');
    reinitialize();
  }
});
```

老韩解释："移动端 Safari 和 Chrome 有 Back/Forward Cache（bfcache），按浏览器后退按钮时，页面不会重新加载，而是从内存缓存恢复。这时 `pagehide` 的 `event.persisted` 是 `true`，表示页面进入了 bfcache。"

## unload: 不推荐使用

老韩特别强调："不要用 `unload` 事件！"

```javascript
// ❌ 不推荐：unload 事件
window.addEventListener('unload', () => {
  console.log('页面卸载');

  // ⚠️ 问题 1: 可能不触发（移动端浏览器）
  // ⚠️ 问题 2: 阻止 bfcache（影响后退性能）
  // ⚠️ 问题 3: 不可靠（浏览器可能忽略）

  // ❌ 千万不要在 unload 里做这些：
  fetch('/api/log'); // 请求会被取消
  alert('确定离开吗？'); // 不会显示
  localStorage.setItem('key', 'value'); // 可能失败
});

// ✅ 推荐：使用 pagehide
window.addEventListener('pagehide', () => {
  console.log('页面卸载（推荐）');

  // 用 sendBeacon 发送数据
  navigator.sendBeacon('/api/log', data);
});
```

## 完整的页面生命周期管理

老韩展示了一个完整的页面生命周期管理方案：

```javascript
class PageLifecycle {
  constructor() {
    this.startTime = Date.now();
    this.isVisible = !document.hidden;
    this.hasUnsavedChanges = false;
    this.init();
  }

  init() {
    // 1. DOM 加载完成
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', this.onDOMReady);
    } else {
      this.onDOMReady();
    }

    // 2. 所有资源加载完成
    if (document.readyState === 'complete') {
      this.onLoad();
    } else {
      window.addEventListener('load', this.onLoad);
    }

    // 3. 页面可见性变化
    document.addEventListener('visibilitychange', this.onVisibilityChange);

    // 4. 页面卸载前
    window.addEventListener('beforeunload', this.onBeforeUnload);

    // 5. 页面卸载
    window.addEventListener('pagehide', this.onPageHide);

    // 6. 页面显示（包括 bfcache 恢复）
    window.addEventListener('pageshow', this.onPageShow);
  }

  onDOMReady = () => {
    console.log('DOM 加载完成');

    // 初始化 UI
    this.initUI();

    // 绑定事件
    this.bindEvents();
  }

  onLoad = () => {
    console.log('所有资源加载完成');

    // 初始化需要等待资源的功能
    this.initGallery(); // 需要等待图片加载
    this.initVideo();   // 需要等待视频加载
  }

  onVisibilityChange = () => {
    this.isVisible = !document.hidden;

    if (document.hidden) {
      console.log('页面被隐藏');

      // 暂停资源密集型操作
      this.pauseAnimations();
      this.pauseVideo();

      // 保存草稿
      if (this.hasUnsavedChanges) {
        this.saveDraft();
      }
    } else {
      console.log('页面可见');

      // 恢复操作
      this.resumeAnimations();
      this.resumeVideo();

      // 刷新数据
      this.refreshData();
    }
  }

  onBeforeUnload = (event) => {
    if (this.hasUnsavedChanges) {
      console.log('有未保存的更改，提示用户');
      event.preventDefault();
      event.returnValue = '';
    }
  }

  onPageHide = (event) => {
    console.log('页面卸载');
    console.log('进入 bfcache:', event.persisted);

    // 发送统计数据
    this.sendAnalytics();

    // 清理资源
    this.cleanup();
  }

  onPageShow = (event) => {
    console.log('页面显示');
    console.log('从 bfcache 恢复:', event.persisted);

    if (event.persisted) {
      // 从 bfcache 恢复，重新初始化
      this.startTime = Date.now();
      this.refreshData();
    }
  }

  sendAnalytics() {
    const duration = Date.now() - this.startTime;

    const data = JSON.stringify({
      page: window.location.pathname,
      duration,
      timestamp: Date.now(),
      userAgent: navigator.userAgent
    });

    // 使用 sendBeacon 可靠发送
    navigator.sendBeacon('/api/analytics', data);
  }

  cleanup() {
    // 清理定时器
    if (this.timerId) {
      clearInterval(this.timerId);
    }

    // 取消动画帧
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }

    // 移除事件监听器
    document.removeEventListener('visibilitychange', this.onVisibilityChange);
    window.removeEventListener('beforeunload', this.onBeforeUnload);
    window.removeEventListener('pagehide', this.onPageHide);
  }

  // 其他方法...
  initUI() {}
  bindEvents() {}
  initGallery() {}
  initVideo() {}
  pauseAnimations() {}
  resumeAnimations() {}
  pauseVideo() {}
  resumeVideo() {}
  saveDraft() {}
  refreshData() {}
}

// 使用页面生命周期管理器
const lifecycle = new PageLifecycle();
```

下午 5 点，你重构了统计功能。现在使用 `sendBeacon` 在 `pagehide` 事件中发送数据，并且处理了 `visibilitychange` 事件，在用户切换标签页时也会记录停留时长。你给产品经理发消息："统计功能已修复，现在数据发送 100% 可靠，还支持切换标签页的时长统计。"

## 页面生命周期法则

**规则 1: DOMContentLoaded 用于 DOM 操作，load 用于资源依赖**

`DOMContentLoaded` 在 DOM 解析完成时触发，适合初始化 DOM 操作；`load` 在所有资源（图片、CSS、脚本）加载完成时触发，适合需要资源尺寸或完整性的操作。

```javascript
// ✅ DOM 操作：使用 DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM 准备好了');

  // 绑定事件
  document.querySelector('button').addEventListener('click', handleClick);

  // 初始化组件
  initComponents();

  // 从 API 加载数据
  fetchData();
});

// ✅ 资源依赖：使用 load
window.addEventListener('load', () => {
  console.log('所有资源已加载');

  // 获取图片尺寸
  const img = document.querySelector('img');
  console.log('图片尺寸:', img.naturalWidth, img.naturalHeight);

  // 初始化图片库（需要图片尺寸）
  initPhotoGallery();

  // 播放视频（需要视频元数据）
  initVideoPlayer();
});

// 检查当前加载状态
console.log('readyState:', document.readyState);
// 'loading': 文档正在加载
// 'interactive': 文档已解析完成（DOMContentLoaded 前后）
// 'complete': 文档和所有资源已加载（load 前后）

// 处理脚本在 DOMContentLoaded 后加载的情况
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init(); // DOM 已经准备好
}
```

**规则 2: visibilitychange 优化后台性能**

使用 `visibilitychange` 事件检测页面可见性变化，在页面隐藏时暂停资源密集型操作（视频、动画、定时器），节省资源并符合用户预期。

```javascript
let animationId;
let timerInterval;

document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    console.log('页面隐藏，暂停操作');

    // 暂停动画
    if (animationId) {
      cancelAnimationFrame(animationId);
    }

    // 暂停定时器
    if (timerInterval) {
      clearInterval(timerInterval);
    }

    // 暂停视频
    const video = document.querySelector('video');
    if (video && !video.paused) {
      video.pause();
      video.dataset.wasPlaying = 'true';
    }

    // 保存状态
    saveState();
  } else {
    console.log('页面可见，恢复操作');

    // 恢复动画
    animate();

    // 恢复定时器
    timerInterval = setInterval(updateTimer, 1000);

    // 恢复视频
    const video = document.querySelector('video');
    if (video && video.dataset.wasPlaying === 'true') {
      video.play();
      delete video.dataset.wasPlaying;
    }

    // 刷新数据
    refreshData();
  }
});

function animate() {
  // 动画逻辑
  animationId = requestAnimationFrame(animate);
}
```

**规则 3: 使用 sendBeacon 可靠发送数据**

在页面卸载时使用 `navigator.sendBeacon()` 发送数据，浏览器保证异步发送完成，即使页面已关闭。不要在 `beforeunload` 或 `pagehide` 中使用普通 `fetch`。

```javascript
let startTime = Date.now();

window.addEventListener('pagehide', () => {
  const duration = Date.now() - startTime;

  // ✅ 推荐：sendBeacon（简单可靠）
  const data = JSON.stringify({
    page: window.location.pathname,
    duration,
    timestamp: Date.now()
  });

  const success = navigator.sendBeacon('/api/analytics', data);
  console.log('sendBeacon:', success ? '已发送' : '失败');

  // ✅ 备选：fetch + keepalive
  if (!success) {
    fetch('/api/analytics', {
      method: 'POST',
      body: data,
      headers: { 'Content-Type': 'application/json' },
      keepalive: true // 保持连接
    });
  }
});

// ❌ 错误：普通 fetch（请求会被取消）
window.addEventListener('beforeunload', () => {
  fetch('/api/analytics', {
    method: 'POST',
    body: JSON.stringify({ duration })
  });
  // ⚠️ 页面卸载时请求会被取消，数据丢失
});

// sendBeacon 的特点：
// 1. POST 请求
// 2. 异步发送，不阻塞页面卸载
// 3. 浏览器保证发送完成
// 4. 大小限制约 64KB
// 5. 不能设置自定义请求头（Content-Type 自动设置）
```

**规则 4: 使用 pagehide 而非 unload**

`pagehide` 比 `unload` 更可靠，支持 bfcache，在移动端也能稳定触发。`unload` 已废弃，会阻止 bfcache，不推荐使用。

```javascript
// ✅ 推荐：pagehide
window.addEventListener('pagehide', (event) => {
  console.log('页面卸载');
  console.log('进入 bfcache:', event.persisted);

  // 发送数据
  sendAnalytics();

  // 清理资源
  cleanup();
});

// ✅ 页面恢复：pageshow
window.addEventListener('pageshow', (event) => {
  console.log('页面显示');
  console.log('从 bfcache 恢复:', event.persisted);

  if (event.persisted) {
    // 从 bfcache 恢复，重新初始化
    reinitialize();
  }
});

// ❌ 不推荐：unload
window.addEventListener('unload', () => {
  // ⚠️ 问题 1: 移动端可能不触发
  // ⚠️ 问题 2: 阻止 bfcache（影响后退性能）
  // ⚠️ 问题 3: 浏览器可能忽略
});

// bfcache（Back/Forward Cache）说明：
// - 浏览器缓存整个页面，包括 JavaScript 状态
// - 点击后退/前进时瞬间恢复，不重新加载
// - pagehide 的 event.persisted === true 表示进入 bfcache
// - pageshow 的 event.persisted === true 表示从 bfcache 恢复
```

**规则 5: beforeunload 只用于未保存提示**

`beforeunload` 只应在有未保存更改时提示用户，不能自定义提示文本，不要在其中发送数据或执行耗时操作。

```javascript
let hasUnsavedChanges = false;

// 监听表单变化
document.querySelector('form').addEventListener('input', () => {
  hasUnsavedChanges = true;
});

// ✅ 正确：只在有未保存更改时提示
window.addEventListener('beforeunload', (event) => {
  if (hasUnsavedChanges) {
    event.preventDefault();
    event.returnValue = ''; // 必须设置，但浏览器会显示通用提示

    // ❌ 已废弃：自定义文本（浏览器会忽略）
    return '有未保存的更改，确定要离开吗？';
  }
});

// 表单提交后清除标志
document.querySelector('form').addEventListener('submit', () => {
  hasUnsavedChanges = false;
});

// ❌ 错误用法：
window.addEventListener('beforeunload', (event) => {
  // ❌ 不要发送数据（不可靠）
  fetch('/api/log', { method: 'POST', body: data });

  // ❌ 不要执行耗时操作（会阻塞页面卸载）
  for (let i = 0; i < 1000000; i++) {
    // ...
  }

  // ❌ 不要显示弹窗（无效）
  alert('确定离开吗？');
});
```

**规则 6: 综合处理页面生命周期**

综合使用 `DOMContentLoaded`、`load`、`visibilitychange`、`beforeunload`、`pagehide`、`pageshow` 事件，实现完整的页面生命周期管理。

```javascript
class PageLifecycleManager {
  constructor() {
    this.startTime = Date.now();
    this.isVisible = !document.hidden;
    this.hasUnsavedChanges = false;
    this.setupListeners();
  }

  setupListeners() {
    // DOM 准备好
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
    } else {
      this.onDOMReady();
    }

    // 资源加载完成
    window.addEventListener('load', () => this.onLoad());

    // 可见性变化
    document.addEventListener('visibilitychange', () => this.onVisibilityChange());

    // 卸载前提示
    window.addEventListener('beforeunload', (e) => this.onBeforeUnload(e));

    // 页面卸载
    window.addEventListener('pagehide', (e) => this.onPageHide(e));

    // 页面显示
    window.addEventListener('pageshow', (e) => this.onPageShow(e));
  }

  onDOMReady() {
    console.log('[生命周期] DOM 准备好');
    this.initUI();
  }

  onLoad() {
    console.log('[生命周期] 资源加载完成');
    this.initResources();
  }

  onVisibilityChange() {
    if (document.hidden) {
      console.log('[生命周期] 页面隐藏');
      this.pause();
    } else {
      console.log('[生命周期] 页面可见');
      this.resume();
    }
  }

  onBeforeUnload(event) {
    if (this.hasUnsavedChanges) {
      event.preventDefault();
      event.returnValue = '';
    }
  }

  onPageHide(event) {
    console.log('[生命周期] 页面卸载, bfcache:', event.persisted);
    this.sendAnalytics();
    this.cleanup();
  }

  onPageShow(event) {
    console.log('[生命周期] 页面显示, bfcache:', event.persisted);
    if (event.persisted) {
      this.reinitialize();
    }
  }

  sendAnalytics() {
    const duration = Date.now() - this.startTime;
    navigator.sendBeacon('/api/analytics', JSON.stringify({ duration }));
  }

  // 其他方法...
  initUI() {}
  initResources() {}
  pause() {}
  resume() {}
  cleanup() {}
  reinitialize() {}
}

new PageLifecycleManager();
```

---

**记录者注**:

页面从加载到卸载，经历了一系列生命周期事件，每个事件都有特定的用途和限制。`DOMContentLoaded` 标志 DOM 准备就绪，`load` 标志资源加载完成，`visibilitychange` 标志可见性变化，`beforeunload` 提示未保存更改，`pagehide` 处理页面卸载。

关键在于理解每个事件的触发时机和适用场景。在页面卸载时使用 `sendBeacon` 可靠发送数据，优先使用 `pagehide` 而非废弃的 `unload`，利用 `visibilitychange` 优化后台性能，处理 bfcache 恢复场景。

记住：**`DOMContentLoaded` 用于 DOM 操作，`load` 用于资源依赖，`visibilitychange` 优化性能，`sendBeacon` 可靠发送数据，`pagehide` 处理卸载，`beforeunload` 只用于提示。完整的生命周期管理是高质量网页的基础**。
