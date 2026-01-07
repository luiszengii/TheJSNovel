《第 140 次记录：隐形的陷阱 —— 点击劫持攻击与防御体系》

## 神秘的用户投诉

周四上午 9 点 47 分，客服部门转来一个诡异的投诉："我根本没点关注按钮，为什么显示我关注了这个账号？"

你以为是前端bug，立刻检查了关注功能的代码。逻辑很简单：用户点击"关注"按钮，发送请求到后端，更新关注状态。代码没有任何问题，测试环境也运行正常。

但在你准备回复"可能是用户误操作"时，客服又转来三个类似投诉。更奇怪的是，这些用户都说自己在浏览一个第三方博客网站时，突然发现已经关注了某个账号。他们发誓自己完全没有点击过关注按钮，甚至没有打开过你们的网站。

"这不可能..." 你喃喃自语。用户怎么可能在没有访问网站的情况下触发关注操作？除非...

你突然想到一个可怕的可能：点击劫持攻击（Clickjacking）。你快速搜索了那些用户提到的第三方博客网站，打开页面后，你的心一沉 —— 页面上有一个醒目的"下载PDF"按钮。

你打开浏览器的开发工具，仔细检查 DOM 结构。在"下载PDF"按钮的上方，隐藏着一个透明的 `<iframe>`，它加载的正是你们网站的关注页面。

技术总监老陈走过来，看了一眼你的屏幕："经典的点击劫持。攻击者把你们的页面嵌入透明 iframe，诱导用户点击看似无害的按钮，实际上点击的是 iframe 里的关注按钮。"

## 点击劫持的剖析

老陈在白板上画出了攻击原理：

```
用户看到的:
┌─────────────────────────┐
│  精彩博客内容             │
│                          │
│  [下载PDF] ← 诱饵按钮     │
│                          │
└─────────────────────────┘

实际 DOM 结构:
┌─────────────────────────┐
│  博客内容 (z-index: 1)   │
│                          │
│  透明 iframe (z-index: 2) │
│  ├─ 你们的关注页面        │
│  └─ [关注] 按钮恰好覆盖    │
│     "下载PDF" 的位置      │
└─────────────────────────┘
```

老陈展示了攻击者的恶意代码：

```html
<!-- 攻击者的页面 -->
<!DOCTYPE html>
<html>
<head>
  <title>精彩博客</title>
  <style>
    /* 让 iframe 完全透明且覆盖按钮 */
    #malicious-frame {
      position: absolute;
      top: 300px;
      left: 200px;
      width: 300px;
      height: 100px;
      opacity: 0; /* 完全透明 */
      z-index: 2; /* 在诱饵按钮之上 */
      border: none;
    }

    #decoy-button {
      position: absolute;
      top: 300px;
      left: 200px;
      width: 300px;
      height: 100px;
      z-index: 1; /* 在 iframe 之下 */
      background: #007bff;
      color: white;
      font-size: 18px;
      border: none;
      cursor: pointer;
    }

    /* 为了方便调试，攻击者可能会切换透明度 */
    #malicious-frame.debug {
      opacity: 0.5;
    }
  </style>
</head>
<body>
  <h1>精彩博客文章</h1>
  <p>这是一篇很有价值的技术文章...</p>

  <!-- 诱饵按钮：用户以为点击的是这个 -->
  <button id="decoy-button">下载PDF电子书</button>

  <!-- 恶意 iframe：实际点击的是这个 -->
  <iframe
    id="malicious-frame"
    src="https://yoursite.com/user/follow?userId=attacker123"
  ></iframe>

  <script>
    // 攻击者可能会在开发时启用调试模式查看对齐情况
    // document.getElementById('malicious-frame').classList.add('debug');
  </script>
</body>
</html>
```

你终于明白了："用户以为在点击'下载PDF'，实际上点击的是透明 iframe 里的'关注'按钮。由于用户已经登录了我们的网站，浏览器会携带 cookie，所以关注请求成功执行。"

老陈点头："对。这就是为什么需要实施点击劫持防御。"

## 防御层 1: X-Frame-Options 响应头

老陈展示了第一道防线：

```javascript
// 后端设置 HTTP 响应头（Node.js / Express 示例）
app.use((req, res, next) => {
  // 方案 1: 完全禁止被嵌入 iframe
  res.setHeader('X-Frame-Options', 'DENY');

  // 方案 2: 只允许同源页面嵌入
  // res.setHeader('X-Frame-Options', 'SAMEORIGIN');

  // 方案 3: 只允许特定域名嵌入（已废弃，不推荐）
  // res.setHeader('X-Frame-Options', 'ALLOW-FROM https://trusted.com');

  next();
});

// 或者针对特定路由
app.get('/user/follow', (req, res) => {
  res.setHeader('X-Frame-Options', 'DENY');
  // 返回关注页面
  res.render('follow');
});
```

老陈解释："X-Frame-Options 是传统的防御方式。但它有局限性：`ALLOW-FROM` 指令已被废弃，且只支持一个父域名。现代方案应该使用 CSP。"

## 防御层 2: Content-Security-Policy (CSP)

老陈展示了更现代的防御方案：

```javascript
// 使用 CSP 的 frame-ancestors 指令
app.use((req, res, next) => {
  // 方案 1: 禁止任何页面嵌入
  res.setHeader(
    'Content-Security-Policy',
    "frame-ancestors 'none'"
  );

  // 方案 2: 只允许同源嵌入
  // res.setHeader(
  //   'Content-Security-Policy',
  //   "frame-ancestors 'self'"
  // );

  // 方案 3: 允许特定域名嵌入（支持多个域名）
  // res.setHeader(
  //   'Content-Security-Policy',
  //   "frame-ancestors 'self' https://trusted1.com https://trusted2.com"
  // );

  // 方案 4: 同时设置 X-Frame-Options 和 CSP（最佳实践）
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader(
    'Content-Security-Policy',
    "frame-ancestors 'none'"
  );

  next();
});

// 完整的 CSP 配置示例
app.use((req, res, next) => {
  const csp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://trusted-cdn.com",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self' https://fonts.gstatic.com",
    "connect-src 'self' https://api.yoursite.com",
    "frame-ancestors 'none'", // 点击劫持防御
    "base-uri 'self'",
    "form-action 'self'"
  ].join('; ');

  res.setHeader('Content-Security-Policy', csp);

  // 兼容旧浏览器
  res.setHeader('X-Frame-Options', 'DENY');

  next();
});
```

老陈特别强调："CSP 比 X-Frame-Options 更强大：支持多个域名白名单，是 W3C 标准，支持 Content-Security-Policy-Report-Only 模式进行测试。"

## 防御层 3: JavaScript 检测与阻止

老陈展示了客户端防御方案：

```javascript
// 方法 1: 基本的 Frame Busting 脚本
(function preventFraming() {
  // 检查当前页面是否在 iframe 中
  if (window !== window.top) {
    console.warn('检测到页面被嵌入 iframe');

    // 尝试跳出 iframe（可能被阻止）
    try {
      window.top.location = window.location;
    } catch (error) {
      // 跨域时会失败，采用其他方案
      console.error('无法跳出 iframe:', error);

      // 隐藏页面内容
      document.body.style.display = 'none';

      // 显示警告
      document.body.innerHTML = `
        <div style="
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: white;
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 999999;
          font-family: sans-serif;
        ">
          <div style="text-align: center;">
            <h1>安全警告</h1>
            <p>此页面不允许在 iframe 中显示</p>
            <p>请直接访问: <a href="${window.location.href}">${window.location.href}</a></p>
          </div>
        </div>
      `;
    }
  }
})();

// 方法 2: 增强型防御（防止攻击者禁用 JavaScript）
(function enhancedProtection() {
  // 使用 CSS 默认隐藏内容
  const style = document.createElement('style');
  style.id = 'anticlickjack';
  style.textContent = `
    body {
      display: none !important;
    }
  `;
  document.head.appendChild(style);

  // 如果页面在顶层窗口，移除隐藏样式
  if (window === window.top) {
    const styleElement = document.getElementById('anticlickjack');
    if (styleElement) {
      styleElement.remove();
    }
  } else {
    // 页面在 iframe 中，保持隐藏并显示警告
    document.addEventListener('DOMContentLoaded', () => {
      const styleElement = document.getElementById('anticlickjack');
      if (styleElement) {
        styleElement.textContent = 'body { display: block !important; }';
      }

      document.body.innerHTML = `
        <div class="security-warning">
          <h1>安全警告</h1>
          <p>此页面检测到可能的点击劫持攻击</p>
          <p>请直接访问: <a href="${window.location.href}" target="_top">${window.location.href}</a></p>
        </div>
      `;
    });
  }
})();

// 方法 3: 白名单方式（允许特定父页面）
(function whitelistCheck() {
  if (window === window.top) {
    // 顶层窗口，允许
    return;
  }

  const allowedOrigins = [
    'https://trusted-partner.com',
    'https://our-subdomain.example.com'
  ];

  try {
    // 尝试获取父页面的 origin
    const parentOrigin = document.referrer
      ? new URL(document.referrer).origin
      : null;

    if (!allowedOrigins.includes(parentOrigin)) {
      // 不在白名单中，阻止
      blockPage(`未授权的嵌入来源: ${parentOrigin}`);
    }
  } catch (error) {
    // 跨域时可能无法获取 referrer
    blockPage('无法验证父页面来源');
  }

  function blockPage(reason) {
    console.error('页面被阻止:', reason);

    document.body.style.display = 'none';

    const warning = document.createElement('div');
    warning.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: #f8d7da;
      color: #721c24;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 999999;
    `;
    warning.innerHTML = `
      <div style="text-align: center; max-width: 500px;">
        <h2>访问被拒绝</h2>
        <p>${reason}</p>
        <p>请直接访问: <a href="${window.location.href}" target="_top">${window.location.href}</a></p>
      </div>
    `;

    document.body.appendChild(warning);
    document.body.style.display = 'block';
  }
})();
```

## 防御层 4: 用户交互验证

老陈展示了额外的防御措施：

```javascript
// 关键操作需要二次确认
class SecureActionHandler {
  constructor() {
    this.init();
  }

  init() {
    // 监听所有关键操作按钮
    document.querySelectorAll('[data-critical-action]').forEach(button => {
      button.addEventListener('click', (event) => {
        this.handleCriticalAction(event);
      });
    });
  }

  handleCriticalAction(event) {
    event.preventDefault();

    const button = event.target;
    const action = button.dataset.criticalAction;

    // 检查是否在 iframe 中
    if (window !== window.top) {
      alert('此操作不允许在嵌入页面中执行，请直接访问本站');
      return;
    }

    // 显示确认对话框
    this.showConfirmDialog(action, () => {
      // 用户确认后执行操作
      this.executeAction(action, button);
    });
  }

  showConfirmDialog(action, onConfirm) {
    const dialog = document.createElement('div');
    dialog.className = 'confirm-dialog';
    dialog.innerHTML = `
      <div class="dialog-overlay"></div>
      <div class="dialog-content">
        <h3>确认操作</h3>
        <p>你确定要执行"${action}"操作吗？</p>
        <div class="dialog-actions">
          <button class="btn-cancel">取消</button>
          <button class="btn-confirm">确认</button>
        </div>
      </div>
    `;

    document.body.appendChild(dialog);

    // 绑定事件
    dialog.querySelector('.btn-cancel').addEventListener('click', () => {
      dialog.remove();
    });

    dialog.querySelector('.btn-confirm').addEventListener('click', () => {
      dialog.remove();
      onConfirm();
    });
  }

  executeAction(action, button) {
    console.log('执行操作:', action);

    // 发送请求
    fetch(button.dataset.actionUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest' // AJAX 标识
      },
      body: JSON.stringify({
        action: action,
        timestamp: Date.now()
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        this.showSuccess('操作成功');
      } else {
        this.showError('操作失败: ' + data.error);
      }
    })
    .catch(error => {
      this.showError('网络错误: ' + error.message);
    });
  }

  showSuccess(message) {
    const toast = document.createElement('div');
    toast.className = 'toast success';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
  }

  showError(message) {
    const toast = document.createElement('div');
    toast.className = 'toast error';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 3000);
  }
}

// 使用示例
const secureHandler = new SecureActionHandler();

// HTML 示例
/*
<button
  data-critical-action="关注用户"
  data-action-url="/api/user/follow"
  class="btn-follow"
>
  关注
</button>
*/
```

## 防御层 5: 后端验证与 CSRF 保护

老陈强调："前端防御可以被绕过，必须在后端增加验证。"

```javascript
// 后端验证（Node.js / Express 示例）
const csrf = require('csurf');
const csrfProtection = csrf({ cookie: true });

// 关键操作路由
app.post('/api/user/follow', csrfProtection, (req, res) => {
  // 验证 1: 检查 Referer 头
  const referer = req.headers.referer;

  if (!referer || !referer.startsWith('https://yoursite.com')) {
    return res.status(403).json({
      error: '无效的请求来源'
    });
  }

  // 验证 2: 检查 X-Requested-With 头（AJAX 标识）
  const requestedWith = req.headers['x-requested-with'];

  if (requestedWith !== 'XMLHttpRequest') {
    return res.status(403).json({
      error: '只接受 AJAX 请求'
    });
  }

  // 验证 3: CSRF Token（由 csurf 中间件自动验证）

  // 验证 4: 检查用户会话
  if (!req.session.userId) {
    return res.status(401).json({
      error: '未登录'
    });
  }

  // 验证 5: 二次确认（对于关键操作）
  const confirmToken = req.body.confirmToken;

  if (!confirmToken || !verifyConfirmToken(req.session.userId, confirmToken)) {
    return res.status(403).json({
      error: '缺少二次确认'
    });
  }

  // 执行关注操作
  const targetUserId = req.body.userId;

  followUser(req.session.userId, targetUserId)
    .then(() => {
      res.json({ success: true });
    })
    .catch(error => {
      res.status(500).json({
        error: '操作失败: ' + error.message
      });
    });
});

// 生成确认令牌
app.get('/api/user/follow/confirm-token', (req, res) => {
  if (!req.session.userId) {
    return res.status(401).json({ error: '未登录' });
  }

  const token = generateConfirmToken(req.session.userId);

  res.json({ token });
});

// 确认令牌验证
function verifyConfirmToken(userId, token) {
  // 实现：验证令牌是否有效且未过期
  // 令牌应该是一次性的，验证后立即失效
  return true; // 示例
}

function generateConfirmToken(userId) {
  // 实现：生成一次性确认令牌
  return crypto.randomBytes(32).toString('hex');
}
```

## 完整的防御体系

老陈帮你整理了完整的防御清单：

```javascript
// 防御清单类
class ClickjackingDefense {
  constructor() {
    this.defenseEnabled = true;
    this.init();
  }

  init() {
    // 1. 检查页面是否在 iframe 中
    this.checkFraming();

    // 2. 设置关键操作保护
    this.protectCriticalActions();

    // 3. 监听可疑行为
    this.monitorSuspiciousActivity();
  }

  checkFraming() {
    if (window !== window.top) {
      // 页面在 iframe 中
      console.warn('检测到页面被嵌入 iframe');

      // 记录事件
      this.reportSecurity('page-in-iframe', {
        parentOrigin: document.referrer,
        timestamp: Date.now()
      });

      // 检查是否在白名单中
      if (!this.isAllowedParent()) {
        this.blockPage();
      }
    }
  }

  isAllowedParent() {
    const allowedOrigins = [
      'https://trusted1.com',
      'https://trusted2.com'
    ];

    try {
      const parentOrigin = document.referrer
        ? new URL(document.referrer).origin
        : null;

      return allowedOrigins.includes(parentOrigin);
    } catch (error) {
      return false;
    }
  }

  blockPage() {
    // 隐藏原内容
    document.body.style.display = 'none';

    // 显示安全警告
    const warning = document.createElement('div');
    warning.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: #fff;
      z-index: 999999;
      display: flex;
      align-items: center;
      justify-content: center;
    `;
    warning.innerHTML = `
      <div style="text-align: center; max-width: 500px; padding: 20px;">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#dc3545" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <h1 style="color: #dc3545; margin: 20px 0;">安全警告</h1>
        <p style="color: #666; line-height: 1.6;">
          此页面检测到可能的安全威胁。为保护你的账户安全，页面已被阻止。
        </p>
        <p style="margin-top: 20px;">
          <a href="${window.location.href}" target="_top" style="
            display: inline-block;
            padding: 10px 20px;
            background: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
          ">直接访问本页面</a>
        </p>
      </div>
    `;

    document.body.appendChild(warning);
    document.body.style.display = 'block';
  }

  protectCriticalActions() {
    // 为关键操作按钮添加保护
    const criticalButtons = document.querySelectorAll('[data-critical-action]');

    criticalButtons.forEach(button => {
      button.addEventListener('click', (event) => {
        // 在 iframe 中禁止关键操作
        if (window !== window.top) {
          event.preventDefault();
          alert('此操作不允许在嵌入页面中执行');
          return;
        }

        // 记录操作
        this.reportSecurity('critical-action-attempted', {
          action: button.dataset.criticalAction,
          timestamp: Date.now()
        });
      });
    });
  }

  monitorSuspiciousActivity() {
    // 监听鼠标移动（检测异常点击模式）
    let clickCount = 0;
    let lastClickTime = 0;

    document.addEventListener('click', (event) => {
      const now = Date.now();

      // 短时间内大量点击（可能是自动化攻击）
      if (now - lastClickTime < 100) {
        clickCount++;

        if (clickCount > 5) {
          console.warn('检测到异常点击行为');
          this.reportSecurity('suspicious-clicks', {
            count: clickCount,
            timestamp: now
          });
        }
      } else {
        clickCount = 1;
      }

      lastClickTime = now;
    });
  }

  reportSecurity(eventType, data) {
    // 上报安全事件
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/security/report', JSON.stringify({
        type: eventType,
        data,
        userAgent: navigator.userAgent,
        url: window.location.href
      }));
    }
  }
}

// 启动防御系统
const defense = new ClickjackingDefense();
```

下午 4 点，你完成了点击劫持防御体系的部署。新的防御措施包括：HTTP 响应头（X-Frame-Options + CSP）、JavaScript 检测与阻止、用户交互二次确认、后端验证与 CSRF 保护。你给技术总监发消息："点击劫持防御已部署，包含多层防护，用户账户安全得到保障。"

---

## 技术档案：点击劫持防御核心策略

**规则 1: 使用 X-Frame-Options 响应头**

设置 `X-Frame-Options` HTTP 响应头，控制页面是否允许被嵌入 iframe。这是最基础的防御措施。

```javascript
// 后端设置 X-Frame-Options（Node.js / Express 示例）
app.use((req, res, next) => {
  // DENY: 完全禁止被嵌入 iframe
  res.setHeader('X-Frame-Options', 'DENY');

  // SAMEORIGIN: 只允许同源页面嵌入
  // res.setHeader('X-Frame-Options', 'SAMEORIGIN');

  next();
});

// 针对特定路由设置
app.get('/user/profile', (req, res) => {
  res.setHeader('X-Frame-Options', 'DENY');
  res.render('profile');
});

// Nginx 配置示例
/*
server {
    location / {
        add_header X-Frame-Options "DENY" always;
    }
}
*/

// Apache 配置示例
/*
Header always set X-Frame-Options "DENY"
*/

// 三个选项的对比
// DENY: 任何页面都不能嵌入（最严格）
// SAMEORIGIN: 只有同源页面可以嵌入
// ALLOW-FROM uri: 只有指定 URL 可以嵌入（已废弃，不推荐）

// 实际应用：根据页面类型选择策略
app.use((req, res, next) => {
  const path = req.path;

  if (path.startsWith('/user/') || path.startsWith('/admin/')) {
    // 关键页面：完全禁止嵌入
    res.setHeader('X-Frame-Options', 'DENY');
  } else if (path.startsWith('/widget/')) {
    // 小部件页面：允许同源嵌入
    res.setHeader('X-Frame-Options', 'SAMEORIGIN');
  } else {
    // 其他页面：默认禁止
    res.setHeader('X-Frame-Options', 'DENY');
  }

  next();
});
```

**规则 2: 使用 Content-Security-Policy 的 frame-ancestors**

CSP 的 `frame-ancestors` 指令比 `X-Frame-Options` 更强大，支持多个域名白名单，是现代标准。

```javascript
// 设置 CSP 的 frame-ancestors 指令
app.use((req, res, next) => {
  // 完全禁止嵌入
  res.setHeader(
    'Content-Security-Policy',
    "frame-ancestors 'none'"
  );

  // 只允许同源嵌入
  // res.setHeader(
  //   'Content-Security-Policy',
  //   "frame-ancestors 'self'"
  // );

  // 允许特定域名嵌入（支持多个）
  // res.setHeader(
  //   'Content-Security-Policy',
  //   "frame-ancestors 'self' https://trusted1.com https://trusted2.com"
  // );

  next();
});

// 最佳实践：同时设置 X-Frame-Options 和 CSP
app.use((req, res, next) => {
  // 旧浏览器支持
  res.setHeader('X-Frame-Options', 'DENY');

  // 现代浏览器支持
  res.setHeader(
    'Content-Security-Policy',
    "frame-ancestors 'none'"
  );

  next();
});

// 完整的 CSP 策略示例
app.use((req, res, next) => {
  const csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'", 'https://cdn.example.com'],
    'style-src': ["'self'", "'unsafe-inline'"],
    'img-src': ["'self'", 'data:', 'https:'],
    'font-src': ["'self'", 'https://fonts.gstatic.com'],
    'connect-src': ["'self'", 'https://api.example.com'],
    'frame-ancestors': ["'none'"], // 点击劫持防御
    'base-uri': ["'self'"],
    'form-action': ["'self'"]
  };

  const cspString = Object.entries(csp)
    .map(([directive, sources]) => `${directive} ${sources.join(' ')}`)
    .join('; ');

  res.setHeader('Content-Security-Policy', cspString);

  next();
});

// 使用 Report-Only 模式测试 CSP
app.use((req, res, next) => {
  // 只报告违规，不阻止
  res.setHeader(
    'Content-Security-Policy-Report-Only',
    "frame-ancestors 'none'; report-uri /api/csp-report"
  );

  next();
});

// CSP 违规报告接收端点
app.post('/api/csp-report', express.json(), (req, res) => {
  console.log('CSP 违规报告:', req.body);
  res.status(204).end();
});
```

**规则 3: JavaScript Frame Busting 检测**

在客户端使用 JavaScript 检测页面是否在 iframe 中，如果是则跳出或阻止显示。注意：这是辅助手段，不能替代 HTTP 响应头。

```javascript
// 基本的 Frame Busting
(function() {
  if (window !== window.top) {
    // 页面在 iframe 中
    console.warn('检测到页面被嵌入 iframe');

    // 尝试跳出 iframe
    try {
      window.top.location = window.location;
    } catch (error) {
      // 跨域时会失败，采用其他方案
      document.body.style.display = 'none';

      document.body.innerHTML = `
        <div style="padding: 40px; text-align: center;">
          <h1>安全警告</h1>
          <p>此页面不允许在 iframe 中显示</p>
          <p><a href="${window.location.href}" target="_top">点击这里直接访问</a></p>
        </div>
      `;
    }
  }
})();

// 增强型 Frame Busting（防止攻击者禁用 JavaScript）
(function() {
  // 1. 默认隐藏页面（使用 CSS）
  const style = document.createElement('style');
  style.id = 'anticlickjack';
  style.textContent = 'body { display: none !important; }';

  // 尽早插入样式
  const firstScript = document.getElementsByTagName('script')[0];
  firstScript.parentNode.insertBefore(style, firstScript);

  // 2. 检查是否在顶层窗口
  if (window === window.top) {
    // 顶层窗口，移除隐藏样式
    const styleElement = document.getElementById('anticlickjack');
    if (styleElement) {
      styleElement.remove();
    }
  } else {
    // 在 iframe 中，显示警告
    document.addEventListener('DOMContentLoaded', () => {
      document.body.style.display = 'block';
      document.body.innerHTML = `
        <div class="security-warning">
          <h1>安全警告</h1>
          <p>此页面检测到可能的点击劫持攻击</p>
          <a href="${window.location.href}" target="_top">直接访问</a>
        </div>
      `;
    });
  }
})();

// 白名单方式（允许特定父页面）
(function() {
  if (window === window.top) {
    return; // 顶层窗口，允许
  }

  const allowedOrigins = [
    'https://trusted-partner.com',
    'https://our-subdomain.example.com'
  ];

  try {
    const parentOrigin = document.referrer
      ? new URL(document.referrer).origin
      : null;

    if (!allowedOrigins.includes(parentOrigin)) {
      blockPage('未授权的嵌入来源');
    }
  } catch (error) {
    blockPage('无法验证父页面来源');
  }

  function blockPage(reason) {
    document.body.innerHTML = `
      <div style="padding: 40px; text-align: center;">
        <h1>访问被拒绝</h1>
        <p>${reason}</p>
        <a href="${window.location.href}" target="_top">直接访问</a>
      </div>
    `;
  }
})();
```

**规则 4: 关键操作需要二次确认**

对于敏感操作（关注、删除、支付等），增加用户确认步骤，提高攻击难度。

```javascript
// 关键操作保护类
class CriticalActionProtection {
  constructor() {
    this.init();
  }

  init() {
    // 为所有关键操作按钮添加保护
    document.querySelectorAll('[data-critical-action]').forEach(button => {
      button.addEventListener('click', (event) => {
        event.preventDefault();
        this.handleCriticalAction(button);
      });
    });
  }

  handleCriticalAction(button) {
    const action = button.dataset.criticalAction;
    const actionUrl = button.dataset.actionUrl;

    // 检查是否在 iframe 中
    if (window !== window.top) {
      alert('此操作不允许在嵌入页面中执行');
      return;
    }

    // 显示确认对话框
    this.showConfirmDialog(action, () => {
      this.executeAction(actionUrl, action);
    });
  }

  showConfirmDialog(action, onConfirm) {
    const dialog = document.createElement('div');
    dialog.className = 'confirm-dialog-overlay';
    dialog.innerHTML = `
      <div class="confirm-dialog">
        <h3>确认操作</h3>
        <p>你确定要执行"${action}"操作吗？</p>
        <div class="dialog-buttons">
          <button class="btn-cancel">取消</button>
          <button class="btn-confirm">确认</button>
        </div>
      </div>
    `;

    document.body.appendChild(dialog);

    dialog.querySelector('.btn-cancel').addEventListener('click', () => {
      dialog.remove();
    });

    dialog.querySelector('.btn-confirm').addEventListener('click', () => {
      dialog.remove();
      onConfirm();
    });

    // 点击遮罩关闭
    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) {
        dialog.remove();
      }
    });
  }

  async executeAction(url, action) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ action })
      });

      const data = await response.json();

      if (data.success) {
        this.showToast('操作成功', 'success');
      } else {
        this.showToast('操作失败: ' + data.error, 'error');
      }
    } catch (error) {
      this.showToast('网络错误: ' + error.message, 'error');
    }
  }

  showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('show');
    }, 10);

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
}

// 初始化保护
new CriticalActionProtection();

// HTML 示例
/*
<button
  data-critical-action="关注用户"
  data-action-url="/api/user/follow"
  class="btn-follow"
>
  关注
</button>
*/
```

**规则 5: 后端验证与 CSRF 保护**

前端防御可以被绕过，必须在后端实施验证。结合 CSRF Token 和 Referer 检查实现多层防护。

```javascript
// 后端验证中间件（Node.js / Express）
const csrf = require('csurf');
const csrfProtection = csrf({ cookie: true });

// 关键操作路由
app.post('/api/user/follow', csrfProtection, async (req, res) => {
  try {
    // 验证 1: 检查 Referer 头
    const referer = req.headers.referer || req.headers.referrer;

    if (!referer || !referer.startsWith(process.env.SITE_URL)) {
      return res.status(403).json({
        error: '无效的请求来源'
      });
    }

    // 验证 2: 检查 X-Requested-With 头
    const requestedWith = req.headers['x-requested-with'];

    if (requestedWith !== 'XMLHttpRequest') {
      return res.status(403).json({
        error: '只接受 AJAX 请求'
      });
    }

    // 验证 3: CSRF Token（由 csurf 中间件自动验证）

    // 验证 4: 用户会话
    if (!req.session.userId) {
      return res.status(401).json({
        error: '未登录'
      });
    }

    // 验证 5: 检查用户是否已关注
    const targetUserId = req.body.targetUserId;
    const isFollowing = await checkIsFollowing(req.session.userId, targetUserId);

    if (isFollowing) {
      return res.status(400).json({
        error: '已经关注过了'
      });
    }

    // 执行关注操作
    await followUser(req.session.userId, targetUserId);

    res.json({ success: true });
  } catch (error) {
    console.error('关注操作失败:', error);
    res.status(500).json({
      error: '服务器错误'
    });
  }
});

// CSRF Token 生成端点
app.get('/api/csrf-token', csrfProtection, (req, res) => {
  res.json({
    csrfToken: req.csrfToken()
  });
});

// 前端获取并使用 CSRF Token
/*
// 页面加载时获取 Token
const csrfToken = await fetch('/api/csrf-token')
  .then(res => res.json())
  .then(data => data.csrfToken);

// 发送请求时携带 Token
fetch('/api/user/follow', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrfToken,
    'X-Requested-With': 'XMLHttpRequest'
  },
  body: JSON.stringify({ targetUserId: '123' })
});
*/
```

**规则 6: 完整的防御体系清单**

综合使用多层防御策略，形成完整的点击劫持防御体系。任何单一措施都可能被绕过，多层防护提供纵深防御。

```javascript
// 点击劫持防御检查清单
const defenseChecklist = {
  // 1. 服务器端防御（必须）
  server: {
    xFrameOptions: true,           // ✅ 设置 X-Frame-Options
    cspFrameAncestors: true,       // ✅ 设置 CSP frame-ancestors
    refererCheck: true,            // ✅ 验证 Referer 头
    csrfProtection: true,          // ✅ CSRF Token 保护
    xRequestedWithCheck: true      // ✅ 检查 X-Requested-With
  },

  // 2. 客户端防御（辅助）
  client: {
    frameDetection: true,          // ✅ JavaScript 检测 iframe
    criticalActionConfirm: true,   // ✅ 关键操作二次确认
    whitelist: ['trusted.com']     // ✅ 允许的父页面白名单
  },

  // 3. 监控与响应（推荐）
  monitoring: {
    securityReporting: true,       // ✅ 安全事件上报
    userActivityMonitor: true,     // ✅ 可疑活动监控
    anomalyDetection: true         // ✅ 异常行为检测
  }
};

// 防御体系实施示例
class ClickjackingDefenseSystem {
  constructor(config) {
    this.config = config;
    this.init();
  }

  init() {
    // 客户端检测
    if (this.config.client.frameDetection) {
      this.checkFraming();
    }

    // 关键操作保护
    if (this.config.client.criticalActionConfirm) {
      this.protectCriticalActions();
    }

    // 监控系统
    if (this.config.monitoring.userActivityMonitor) {
      this.startMonitoring();
    }
  }

  checkFraming() {
    if (window !== window.top) {
      const allowed = this.isAllowedParent();

      if (!allowed) {
        this.blockPage();
        this.reportSecurity('unauthorized-framing');
      }
    }
  }

  isAllowedParent() {
    const whitelist = this.config.client.whitelist || [];

    try {
      const parentOrigin = document.referrer
        ? new URL(document.referrer).origin
        : null;

      return whitelist.includes(parentOrigin);
    } catch (error) {
      return false;
    }
  }

  blockPage() {
    document.body.innerHTML = `
      <div class="security-block">
        <h1>安全警告</h1>
        <p>此页面检测到可能的安全威胁</p>
        <a href="${window.location.href}" target="_top">直接访问</a>
      </div>
    `;
  }

  protectCriticalActions() {
    // 实现关键操作保护
  }

  startMonitoring() {
    // 实现活动监控
  }

  reportSecurity(eventType, data = {}) {
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/security/report', JSON.stringify({
        type: eventType,
        data,
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        url: window.location.href
      }));
    }
  }
}

// 启动防御系统
const defenseSystem = new ClickjackingDefenseSystem(defenseChecklist);
```

---

**记录者注**:

点击劫持（Clickjacking）是一种界面伪装攻击，攻击者将目标网站嵌入透明或不可见的 iframe，诱导用户点击看似无害的按钮，实际上点击的是 iframe 中的敏感操作按钮。防御点击劫持需要多层策略的配合。

关键在于理解防御的多层性：服务器端设置 `X-Frame-Options` 和 CSP `frame-ancestors` 是核心防御，JavaScript Frame Busting 是辅助检测，关键操作二次确认提高攻击难度，后端验证 Referer 和 CSRF Token 是最后防线。任何单一防御措施都可能被绕过，只有综合运用多层防护才能有效抵御点击劫持攻击。

记住：**设置 X-Frame-Options 和 CSP frame-ancestors 响应头；JavaScript 检测 iframe 并阻止显示；关键操作需要用户二次确认；后端验证 Referer、X-Requested-With 和 CSRF Token；实施安全监控和异常检测；采用纵深防御策略形成完整防护体系**。点击劫持防御是 Web 应用安全的重要组成部分。
