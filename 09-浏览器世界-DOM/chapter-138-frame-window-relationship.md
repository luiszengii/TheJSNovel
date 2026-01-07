《第 138 次记录：窗口的迷宫 —— Frame 与 window 的层级关系》

## iframe 内容无法访问之谜

周一上午 10 点 12 分，你正在开发一个新功能：在主页面中嵌入一个第三方支付表单的 iframe，用户填写完成后需要获取表单数据并提交到自己的服务器。

HTML 结构很简单：

```html
<div class="payment-container">
  <iframe id="payment-form" src="https://payment.example.com/form.html"></iframe>
  <button id="submit-btn">提交支付</button>
</div>
```

你写了 JavaScript 代码来获取 iframe 内的表单数据：

```javascript
const submitBtn = document.querySelector('#submit-btn');
const iframe = document.querySelector('#payment-form');

submitBtn.addEventListener('click', () => {
  // 获取 iframe 内的 document
  const iframeDoc = iframe.contentDocument;
  const formData = new FormData(iframeDoc.querySelector('form'));

  console.log('表单数据:', Object.fromEntries(formData));
});
```

测试环境运行正常。但上线后，你收到了错误报告："点击提交按钮时控制台报错。" 你打开线上页面，点击提交按钮，控制台立刻显示：

```
Uncaught DOMException: Blocked a frame with origin "https://yoursite.com" from accessing a cross-origin frame.
```

"`contentDocument` 是 `null`！" 你困惑地想，"为什么测试环境可以访问，线上却不行？"

你检查了测试环境的 iframe 地址：`http://localhost:3001/form.html`。原来测试环境的 iframe 和主页面都在本地，是同源的。但线上环境的 iframe 地址 `https://payment.example.com` 和主站 `https://yoursite.com` 不同源，浏览器阻止了访问。

前端架构师老王走过来："你遇到了跨域问题。iframe 有一套复杂的同源策略和通信机制，我们需要系统地理解 window、frame 的层级关系。"

## window 的层级关系

老王在白板上画出了 window 对象的层级结构：

```
┌─────────────────────────────────────────┐
│          window (顶层窗口)                │
│          self === window (true)          │
│          top === window (true)           │
│          parent === window (true)        │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │   iframe1 (子窗口)                  │ │
│  │   self !== window (false)          │ │
│  │   top === 顶层 window               │ │
│  │   parent === window                 │ │
│  │                                     │ │
│  │  ┌──────────────────────────────┐  │ │
│  │  │  iframe1-1 (孙窗口)          │  │ │
│  │  │  top === 顶层 window          │  │ │
│  │  │  parent === iframe1           │  │ │
│  │  │  window.frameElement !== null│  │ │
│  │  └──────────────────────────────┘  │ │
│  └────────────────────────────────────┘ │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │   iframe2 (子窗口)                  │ │
│  │   self !== window (false)          │ │
│  │   top === 顶层 window               │ │
│  │   parent === window                 │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

老王解释道："浏览器中的 window 对象有几个关键属性：
- `window`：当前窗口对象
- `self`：等同于 `window`，当前窗口的引用
- `top`：最顶层窗口（根窗口）
- `parent`：父窗口
- `frames`：子窗口集合
- `frameElement`：当前窗口在父页面中的 iframe 元素（顶层窗口中为 `null`）"

你立刻写了一个测试页面：

```html
<!-- parent.html -->
<!DOCTYPE html>
<html>
<head>
  <title>父页面</title>
</head>
<body>
  <h1>父页面</h1>
  <iframe id="child1" src="child1.html"></iframe>
  <iframe id="child2" src="child2.html"></iframe>

  <script>
    console.log('=== 父页面 ===');
    console.log('window === self:', window === self); // true
    console.log('window === top:', window === top);   // true
    console.log('window === parent:', window === parent); // true
    console.log('frameElement:', window.frameElement); // null
    console.log('frames.length:', window.frames.length); // 2

    // 访问子 iframe
    setTimeout(() => {
      const child1 = document.getElementById('child1').contentWindow;
      console.log('child1.parent === window:', child1.parent === window); // true
    }, 100);
  </script>
</body>
</html>
```

```html
<!-- child1.html -->
<!DOCTYPE html>
<html>
<head>
  <title>子页面 1</title>
</head>
<body>
  <h2>子页面 1</h2>

  <script>
    console.log('=== 子页面 1 ===');
    console.log('window === self:', window === self); // true
    console.log('window === top:', window === top);   // false
    console.log('window === parent:', window === parent); // false
    console.log('parent === top:', parent === top);   // true
    console.log('frameElement:', window.frameElement); // <iframe id="child1">

    // 访问父窗口
    console.log('父窗口标题:', parent.document.title); // "父页面"
  </script>
</body>
</html>
```

## 同源 iframe 的访问

老王展示了同源 iframe 的访问方式：

```javascript
// 父页面访问 iframe
const iframe = document.querySelector('#my-iframe');

// 方法 1: 通过 contentWindow 访问 iframe 的 window 对象
const iframeWindow = iframe.contentWindow;
console.log('iframe 的 URL:', iframeWindow.location.href);
console.log('iframe 的标题:', iframeWindow.document.title);

// 方法 2: 通过 contentDocument 访问 iframe 的 document 对象
const iframeDoc = iframe.contentDocument;
console.log('iframe 的 body:', iframeDoc.body);

// 方法 3: 通过 frames 集合访问
const iframeByIndex = window.frames[0];
const iframeByName = window.frames['my-iframe']; // iframe 需要有 name 属性

// 操作 iframe 内容
iframeDoc.body.style.backgroundColor = 'lightblue';
iframeWindow.alert('来自父页面的消息'); // 在 iframe 中显示 alert

// iframe 中调用父页面的函数
// 父页面定义函数
window.parentFunction = function(message) {
  console.log('父页面收到消息:', message);
};

// iframe 中调用
// parent.parentFunction('Hello from iframe');
```

```javascript
// iframe 内部访问父页面
console.log('父页面的标题:', parent.document.title);
console.log('顶层页面的 URL:', top.location.href);

// 判断是否在 iframe 中
function isInIframe() {
  return window !== window.top;
}

console.log('当前页面在 iframe 中:', isInIframe());

// 判断是否在顶层窗口
function isTopWindow() {
  return window === window.top;
}

// 获取 iframe 在父页面中的元素
const iframeElement = window.frameElement;
if (iframeElement) {
  console.log('iframe 的 ID:', iframeElement.id);
  console.log('iframe 的 src:', iframeElement.src);
}

// 向父页面发送消息（同源情况下也可以直接调用）
parent.postMessage({ type: 'greeting', message: 'Hello' }, '*');
```

## 跨域 iframe 的通信

老王展示了跨域情况下的通信方案：

```javascript
// 父页面：发送消息给 iframe
const iframe = document.querySelector('#payment-form');

iframe.addEventListener('load', () => {
  // 向 iframe 发送消息
  iframe.contentWindow.postMessage({
    type: 'init',
    data: {
      userId: '12345',
      amount: 100
    }
  }, 'https://payment.example.com'); // 指定目标域
});

// 父页面：监听 iframe 发来的消息
window.addEventListener('message', (event) => {
  // 安全检查：验证消息来源
  if (event.origin !== 'https://payment.example.com') {
    console.warn('收到来自未知源的消息:', event.origin);
    return;
  }

  console.log('收到 iframe 消息:', event.data);

  if (event.data.type === 'payment-success') {
    console.log('支付成功:', event.data.orderId);
    submitPayment(event.data);
  }
});
```

```javascript
// iframe 内部：监听父页面消息
window.addEventListener('message', (event) => {
  // 安全检查：验证消息来源
  if (event.origin !== 'https://yoursite.com') {
    return;
  }

  console.log('收到父页面消息:', event.data);

  if (event.data.type === 'init') {
    const { userId, amount } = event.data.data;
    initPaymentForm(userId, amount);
  }
});

// iframe 内部：发送消息给父页面
function sendPaymentResult(orderId) {
  parent.postMessage({
    type: 'payment-success',
    orderId: orderId,
    timestamp: Date.now()
  }, 'https://yoursite.com'); // 指定目标域
}

// 用户完成支付后
submitButton.addEventListener('click', () => {
  processPayment().then((orderId) => {
    sendPaymentResult(orderId);
  });
});
```

## 安全的跨域通信封装

老王帮你封装了一个安全的跨域通信类：

```javascript
class SecureFrameMessenger {
  constructor(targetFrame, targetOrigin) {
    this.targetFrame = targetFrame; // iframe 的 contentWindow 或 parent
    this.targetOrigin = targetOrigin; // 目标源
    this.handlers = new Map();
    this.pendingRequests = new Map();
    this.requestId = 0;
    this.init();
  }

  init() {
    window.addEventListener('message', (event) => {
      // 严格的源检查
      if (event.origin !== this.targetOrigin) {
        console.warn('拒绝来自未授权源的消息:', event.origin);
        return;
      }

      const message = event.data;

      // 处理响应
      if (message.responseId && this.pendingRequests.has(message.responseId)) {
        const { resolve, reject } = this.pendingRequests.get(message.responseId);
        this.pendingRequests.delete(message.responseId);

        if (message.error) {
          reject(new Error(message.error));
        } else {
          resolve(message.data);
        }
        return;
      }

      // 处理请求
      if (message.type && this.handlers.has(message.type)) {
        const handler = this.handlers.get(message.type);

        try {
          const result = handler(message.data);

          // 如果是请求，发送响应
          if (message.requestId) {
            this.sendResponse(message.requestId, result);
          }
        } catch (error) {
          if (message.requestId) {
            this.sendResponse(message.requestId, null, error.message);
          }
        }
      }
    });
  }

  // 注册消息处理器
  on(type, handler) {
    this.handlers.set(type, handler);
  }

  // 发送单向消息（不需要响应）
  send(type, data) {
    this.targetFrame.postMessage({
      type,
      data
    }, this.targetOrigin);
  }

  // 发送请求并等待响应
  request(type, data) {
    return new Promise((resolve, reject) => {
      const requestId = ++this.requestId;

      this.pendingRequests.set(requestId, { resolve, reject });

      this.targetFrame.postMessage({
        type,
        data,
        requestId
      }, this.targetOrigin);

      // 设置超时
      setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          reject(new Error('请求超时'));
        }
      }, 10000); // 10 秒超时
    });
  }

  // 发送响应
  sendResponse(requestId, data, error = null) {
    this.targetFrame.postMessage({
      responseId: requestId,
      data,
      error
    }, this.targetOrigin);
  }
}

// 父页面使用示例
const iframe = document.querySelector('#payment-form');

iframe.addEventListener('load', () => {
  const messenger = new SecureFrameMessenger(
    iframe.contentWindow,
    'https://payment.example.com'
  );

  // 监听 iframe 发来的消息
  messenger.on('payment-complete', (data) => {
    console.log('支付完成:', data);
    showSuccessMessage(data.orderId);
  });

  // 发送初始化数据
  messenger.send('init', {
    userId: '12345',
    amount: 100
  });

  // 发送请求并等待响应
  messenger.request('get-status', {}).then((status) => {
    console.log('支付状态:', status);
  });
});

// iframe 内部使用示例
const messenger = new SecureFrameMessenger(
  window.parent,
  'https://yoursite.com'
);

// 监听父页面的初始化消息
messenger.on('init', (data) => {
  console.log('收到初始化数据:', data);
  initForm(data.userId, data.amount);
});

// 处理状态查询请求
messenger.on('get-status', () => {
  return {
    status: 'ready',
    timestamp: Date.now()
  };
});

// 支付完成后通知父页面
submitButton.addEventListener('click', () => {
  processPayment().then((orderId) => {
    messenger.send('payment-complete', {
      orderId,
      timestamp: Date.now()
    });
  });
});
```

## iframe 的加载和生命周期

老王展示了如何处理 iframe 的加载和生命周期：

```javascript
// 创建和管理 iframe
class IframeManager {
  constructor(options) {
    this.options = options;
    this.iframe = null;
    this.loaded = false;
    this.loadPromise = null;
  }

  create() {
    this.iframe = document.createElement('iframe');

    // 设置基本属性
    this.iframe.src = this.options.src;
    this.iframe.id = this.options.id || `iframe-${Date.now()}`;

    // 设置安全属性
    if (this.options.sandbox) {
      // sandbox 限制 iframe 的权限
      // allow-scripts: 允许运行脚本
      // allow-same-origin: 允许同源访问（谨慎使用）
      // allow-forms: 允许提交表单
      // allow-popups: 允许弹窗
      this.iframe.sandbox = this.options.sandbox;
    }

    // 设置样式
    if (this.options.style) {
      Object.assign(this.iframe.style, this.options.style);
    }

    // 监听加载事件
    this.loadPromise = new Promise((resolve, reject) => {
      this.iframe.addEventListener('load', () => {
        console.log('iframe 加载完成:', this.iframe.src);
        this.loaded = true;
        resolve(this.iframe);
      });

      this.iframe.addEventListener('error', (error) => {
        console.error('iframe 加载失败:', error);
        reject(error);
      });
    });

    // 插入到页面
    const container = this.options.container || document.body;
    container.appendChild(this.iframe);

    return this.loadPromise;
  }

  async waitForLoad() {
    if (this.loaded) return this.iframe;
    return this.loadPromise;
  }

  // 刷新 iframe
  reload() {
    if (this.iframe) {
      this.iframe.src = this.iframe.src;
    }
  }

  // 销毁 iframe
  destroy() {
    if (this.iframe && this.iframe.parentElement) {
      this.iframe.parentElement.removeChild(this.iframe);
      this.iframe = null;
      this.loaded = false;
    }
  }

  // 更改 iframe 的 src
  navigate(url) {
    if (this.iframe) {
      this.loaded = false;
      this.iframe.src = url;
      return this.waitForLoad();
    }
  }
}

// 使用示例
const iframeManager = new IframeManager({
  src: 'https://example.com/page.html',
  id: 'my-iframe',
  container: document.querySelector('.iframe-container'),
  sandbox: 'allow-scripts allow-forms',
  style: {
    width: '100%',
    height: '600px',
    border: 'none'
  }
});

iframeManager.create().then((iframe) => {
  console.log('iframe 创建并加载完成');

  // 设置通信
  const messenger = new SecureFrameMessenger(
    iframe.contentWindow,
    'https://example.com'
  );

  messenger.send('init', { userId: '12345' });
});

// 5 秒后切换到另一个页面
setTimeout(() => {
  iframeManager.navigate('https://example.com/another-page.html');
}, 5000);

// 10 秒后销毁 iframe
setTimeout(() => {
  iframeManager.destroy();
}, 10000);
```

## iframe 的安全策略

老王强调了 iframe 的安全问题：

```javascript
// 1. sandbox 属性限制权限
const iframe = document.createElement('iframe');
iframe.src = 'https://untrusted.com/content.html';

// 不添加 sandbox：iframe 拥有完整权限（危险）
// iframe.sandbox = ''; // 空字符串：最严格限制

// 添加必要的权限
iframe.sandbox = 'allow-scripts allow-forms';
// allow-scripts: 允许运行 JavaScript
// allow-same-origin: 允许同源访问（谨慎！）
// allow-forms: 允许表单提交
// allow-popups: 允许打开弹窗
// allow-modals: 允许 alert/confirm/prompt
// allow-top-navigation: 允许修改顶层窗口 location

document.body.appendChild(iframe);

// 2. X-Frame-Options 响应头（服务端设置）
// 防止自己的页面被嵌入到其他站点的 iframe 中

// 服务端设置：
// X-Frame-Options: DENY  // 禁止任何页面嵌入
// X-Frame-Options: SAMEORIGIN  // 只允许同源页面嵌入
// X-Frame-Options: ALLOW-FROM https://trusted.com  // 只允许特定源嵌入

// 3. Content-Security-Policy (CSP)
// 更现代的方式替代 X-Frame-Options

// 服务端设置：
// Content-Security-Policy: frame-ancestors 'none'  // 禁止嵌入
// Content-Security-Policy: frame-ancestors 'self'  // 只允许同源
// Content-Security-Policy: frame-ancestors https://trusted.com  // 只允许特定源

// 4. JavaScript 检测并阻止嵌入（客户端防御）
function preventFraming() {
  if (window !== window.top) {
    // 当前页面在 iframe 中
    console.warn('检测到页面被嵌入 iframe，阻止显示');

    // 方案 1: 跳出 iframe
    window.top.location = window.location;

    // 方案 2: 隐藏内容
    document.body.style.display = 'none';

    // 方案 3: 显示警告
    document.body.innerHTML = '<h1>此页面不允许在 iframe 中显示</h1>';
  }
}

preventFraming();

// 5. postMessage 的安全检查
window.addEventListener('message', (event) => {
  // ❌ 危险：不检查来源
  // const data = event.data;
  // processData(data);

  // ✅ 安全：严格检查来源
  const allowedOrigins = [
    'https://trusted1.com',
    'https://trusted2.com'
  ];

  if (!allowedOrigins.includes(event.origin)) {
    console.warn('拒绝来自未授权源的消息:', event.origin);
    return;
  }

  // 验证数据格式
  if (typeof event.data !== 'object' || !event.data.type) {
    console.warn('无效的消息格式');
    return;
  }

  // 处理消息
  processMessage(event.data);
});
```

## 修复支付功能

老王帮你重构了支付功能，使用安全的跨域通信：

```javascript
// 父页面：初始化支付 iframe
class PaymentIntegration {
  constructor(options) {
    this.options = options;
    this.iframe = null;
    this.messenger = null;
    this.init();
  }

  async init() {
    // 创建 iframe
    this.iframe = document.createElement('iframe');
    this.iframe.src = 'https://payment.example.com/form.html';
    this.iframe.id = 'payment-form';
    this.iframe.style.cssText = 'width: 100%; height: 600px; border: none;';

    // 安全设置
    this.iframe.sandbox = 'allow-scripts allow-forms allow-same-origin';

    document.querySelector('.payment-container').appendChild(this.iframe);

    // 等待 iframe 加载
    await new Promise((resolve) => {
      this.iframe.addEventListener('load', resolve);
    });

    // 设置通信
    this.messenger = new SecureFrameMessenger(
      this.iframe.contentWindow,
      'https://payment.example.com'
    );

    this.setupMessageHandlers();
    this.sendInitData();
  }

  setupMessageHandlers() {
    // 监听支付完成
    this.messenger.on('payment-complete', (data) => {
      console.log('支付完成:', data);
      this.onPaymentComplete(data);
    });

    // 监听支付失败
    this.messenger.on('payment-error', (error) => {
      console.error('支付失败:', error);
      this.onPaymentError(error);
    });

    // 监听表单验证
    this.messenger.on('form-valid', (isValid) => {
      this.submitButton.disabled = !isValid;
    });
  }

  sendInitData() {
    this.messenger.send('init', {
      userId: this.options.userId,
      amount: this.options.amount,
      orderId: this.options.orderId
    });
  }

  async submitPayment() {
    try {
      // 请求 iframe 提交支付
      const result = await this.messenger.request('submit-payment', {});
      console.log('支付结果:', result);
      return result;
    } catch (error) {
      console.error('支付请求失败:', error);
      throw error;
    }
  }

  onPaymentComplete(data) {
    // 支付成功后的处理
    showSuccessMessage('支付成功！');
    window.location.href = `/order/success?orderId=${data.orderId}`;
  }

  onPaymentError(error) {
    // 支付失败后的处理
    showErrorMessage(`支付失败：${error.message}`);
  }
}

// 使用支付集成
const payment = new PaymentIntegration({
  userId: '12345',
  amount: 100,
  orderId: 'ORDER-2024-001'
});

document.querySelector('#submit-btn').addEventListener('click', async () => {
  try {
    await payment.submitPayment();
  } catch (error) {
    console.error('提交失败:', error);
  }
});
```

下午 3 点，你完成了支付功能的重构。新的实现使用安全的 postMessage 通信，完全符合跨域安全策略。你部署到测试环境，所有功能正常工作。你给产品经理发消息："支付功能已修复，使用标准的跨域通信方案，安全可靠。"

---

## 技术档案：Frame 与 window 层级关系

**规则 1: 理解 window 的层级关系属性**

window 对象提供了多个属性来访问窗口层级关系：`window`、`self`、`top`、`parent`、`frames`、`frameElement`。

```javascript
// 在顶层窗口中：
console.log(window === self);   // true（window 和 self 都指向当前窗口）
console.log(window === top);    // true（当前窗口就是顶层窗口）
console.log(window === parent); // true（没有父窗口）
console.log(window.frameElement); // null（顶层窗口不在 iframe 中）
console.log(window.frames.length); // 子 iframe 数量

// 在 iframe 中：
console.log(window === self);   // true（仍然指向当前窗口）
console.log(window === top);    // false（当前窗口不是顶层）
console.log(window === parent); // false（有父窗口）
console.log(window.frameElement); // <iframe> 元素
console.log(parent !== window); // true（可以访问父窗口）
console.log(top !== window);    // true（可以访问顶层窗口）

// 判断当前页面是否在 iframe 中
function isInIframe() {
  return window !== window.top;
}

// 判断当前页面是否是顶层窗口
function isTopWindow() {
  return window === window.top;
}

// 获取嵌套层级
function getFrameDepth() {
  let depth = 0;
  let currentWindow = window;

  while (currentWindow !== currentWindow.parent) {
    depth++;
    currentWindow = currentWindow.parent;
  }

  return depth;
}

console.log('iframe 嵌套层级:', getFrameDepth());
```

**规则 2: 同源 iframe 可以直接访问，跨域 iframe 受限**

同源的 iframe 可以通过 `contentWindow` 或 `contentDocument` 直接访问，跨域 iframe 只能通过 postMessage 通信。

```javascript
// 同源 iframe（例如：父页面和 iframe 都在 https://example.com）

const iframe = document.querySelector('#my-iframe');

// ✅ 可以访问 iframe 的 window 对象
const iframeWindow = iframe.contentWindow;
console.log('iframe 标题:', iframeWindow.document.title);

// ✅ 可以访问 iframe 的 document 对象
const iframeDoc = iframe.contentDocument;
iframeDoc.body.style.backgroundColor = 'lightblue';

// ✅ 可以调用 iframe 中的函数
iframeWindow.someFunction();

// ✅ iframe 可以访问父页面
// 在 iframe 中：
console.log('父页面标题:', parent.document.title);
parent.someParentFunction();

// 跨域 iframe（父页面 https://site1.com，iframe https://site2.com）

const crossOriginIframe = document.querySelector('#cross-origin-iframe');

// ❌ 无法访问 contentDocument（会返回 null 或抛出错误）
console.log(crossOriginIframe.contentDocument); // null 或 SecurityError

// ❌ 无法访问 contentWindow 的大部分属性
// crossOriginIframe.contentWindow.document.title; // SecurityError

// ✅ 只能通过 postMessage 通信
crossOriginIframe.contentWindow.postMessage({ type: 'greeting' }, 'https://site2.com');

// 安全边界检查
function canAccessIframe(iframe) {
  try {
    const doc = iframe.contentDocument;
    return doc !== null;
  } catch (error) {
    return false;
  }
}
```

**规则 3: 使用 postMessage 实现安全的跨域通信**

postMessage 是跨域通信的标准方式，发送时指定目标域，接收时验证来源域，确保安全。

```javascript
// 父页面：发送消息给 iframe
const iframe = document.querySelector('#my-iframe');

iframe.addEventListener('load', () => {
  // 发送消息，指定目标域
  iframe.contentWindow.postMessage({
    type: 'init',
    data: { userId: '123', token: 'abc' }
  }, 'https://iframe-site.com'); // ✅ 明确指定目标域

  // ❌ 不要使用 '*'，除非确实需要
  // iframe.contentWindow.postMessage(data, '*');
});

// 父页面：接收 iframe 的消息
window.addEventListener('message', (event) => {
  // ✅ 严格验证来源
  if (event.origin !== 'https://iframe-site.com') {
    console.warn('拒绝来自未授权源的消息:', event.origin);
    return;
  }

  // ✅ 验证数据格式
  if (typeof event.data !== 'object' || !event.data.type) {
    console.warn('无效的消息格式');
    return;
  }

  // 处理消息
  console.log('收到消息:', event.data);

  if (event.data.type === 'ready') {
    console.log('iframe 已准备好');
  }
});

// iframe 内部：发送消息给父页面
window.addEventListener('load', () => {
  parent.postMessage({
    type: 'ready',
    timestamp: Date.now()
  }, 'https://parent-site.com'); // ✅ 指定目标域
});

// iframe 内部：接收父页面的消息
window.addEventListener('message', (event) => {
  // ✅ 验证来源
  if (event.origin !== 'https://parent-site.com') {
    return;
  }

  console.log('收到父页面消息:', event.data);

  if (event.data.type === 'init') {
    initWithData(event.data.data);
  }
});

// postMessage 的关键点：
// 1. 发送时明确指定 targetOrigin（第二个参数）
// 2. 接收时验证 event.origin
// 3. 验证消息格式和内容
// 4. 不要使用 '*' 作为 targetOrigin（除非确实需要）
```

**规则 4: 使用 sandbox 属性限制 iframe 权限**

sandbox 属性为 iframe 设置安全沙箱，默认禁止所有危险操作，通过白名单逐个启用需要的权限。

```javascript
// 创建受限的 iframe
const iframe = document.createElement('iframe');
iframe.src = 'https://untrusted.com/content.html';

// 空 sandbox：最严格限制（禁止所有）
iframe.sandbox = '';

// 常用权限组合
iframe.sandbox = 'allow-scripts allow-forms';
// allow-scripts: 允许运行 JavaScript
// allow-forms: 允许提交表单
// allow-popups: 允许弹窗
// allow-same-origin: 允许同源访问（谨慎使用！）
// allow-top-navigation: 允许修改顶层窗口导航
// allow-modals: 允许 alert/confirm/prompt

document.body.appendChild(iframe);

// ⚠️ 不要同时使用 allow-scripts 和 allow-same-origin
// 这会让 iframe 可以移除自己的 sandbox 属性，失去限制
// ❌ 危险组合
iframe.sandbox = 'allow-scripts allow-same-origin';

// ✅ 安全组合（不同时启用）
iframe.sandbox = 'allow-scripts allow-forms';

// 实际应用：嵌入第三方内容
function embedUntrustedContent(url) {
  const iframe = document.createElement('iframe');
  iframe.src = url;

  // 严格的安全限制
  iframe.sandbox = 'allow-scripts'; // 只允许脚本，不允许其他
  iframe.style.cssText = 'width: 100%; height: 600px; border: none;';

  // 可选：设置 CSP
  iframe.setAttribute('csp', "default-src 'self'");

  return iframe;
}
```

**规则 5: 防止自己的页面被恶意嵌入**

使用 X-Frame-Options 或 CSP frame-ancestors 指令，以及 JavaScript 检测，防止页面被嵌入到恶意站点的 iframe 中。

```javascript
// 方法 1: 服务端设置 HTTP 响应头（最可靠）

// X-Frame-Options（旧标准，广泛支持）
// X-Frame-Options: DENY  // 禁止任何页面嵌入
// X-Frame-Options: SAMEORIGIN  // 只允许同源嵌入

// Content-Security-Policy（新标准，推荐）
// Content-Security-Policy: frame-ancestors 'none'  // 禁止嵌入
// Content-Security-Policy: frame-ancestors 'self'  // 只允许同源
// Content-Security-Policy: frame-ancestors https://trusted.com  // 允许特定域

// 方法 2: JavaScript 检测（客户端防御，辅助手段）

// 检测并阻止嵌入
function preventFraming() {
  if (window !== window.top) {
    console.warn('检测到页面被嵌入 iframe');

    // 方案 A: 跳出 iframe（破坏嵌入者的页面布局）
    try {
      window.top.location = window.location;
    } catch (e) {
      // 跨域时会失败，使用其他方案
    }

    // 方案 B: 隐藏内容
    document.body.style.display = 'none';

    // 方案 C: 显示警告
    document.body.innerHTML = '<h1>此页面不允许在 iframe 中显示</h1>';
  }
}

// 页面加载时立即执行
preventFraming();

// 方法 3: 白名单方式（允许特定父页面）

function checkFramingAllowed() {
  if (window === window.top) {
    // 顶层窗口，允许
    return;
  }

  const allowedOrigins = [
    'https://trusted-partner.com',
    'https://my-other-site.com'
  ];

  try {
    const parentOrigin = document.referrer
      ? new URL(document.referrer).origin
      : null;

    if (!allowedOrigins.includes(parentOrigin)) {
      blockPage('未授权的嵌入');
    }
  } catch (error) {
    // 跨域时可能无法获取 referrer
    blockPage('无法验证父页面');
  }
}

function blockPage(reason) {
  console.warn('阻止页面显示:', reason);
  document.body.innerHTML = `<h1>访问被拒绝</h1><p>${reason}</p>`;
}
```

**规则 6: 管理 iframe 的生命周期和资源**

正确创建、加载、更新和销毁 iframe，避免内存泄漏和性能问题。

```javascript
class IframeLifecycleManager {
  constructor(config) {
    this.config = config;
    this.iframe = null;
    this.loaded = false;
    this.messenger = null;
  }

  // 创建并加载 iframe
  async create() {
    this.iframe = document.createElement('iframe');
    this.iframe.src = this.config.src;
    this.iframe.id = this.config.id || `iframe-${Date.now()}`;

    // 安全设置
    if (this.config.sandbox) {
      this.iframe.sandbox = this.config.sandbox;
    }

    // 样式设置
    Object.assign(this.iframe.style, this.config.style || {});

    // 等待加载完成
    await new Promise((resolve, reject) => {
      this.iframe.addEventListener('load', () => {
        console.log('iframe 加载完成');
        this.loaded = true;
        resolve();
      });

      this.iframe.addEventListener('error', () => {
        console.error('iframe 加载失败');
        reject(new Error('加载失败'));
      });

      // 超时处理
      setTimeout(() => {
        if (!this.loaded) {
          reject(new Error('加载超时'));
        }
      }, 10000); // 10 秒超时

      // 插入 DOM
      const container = this.config.container || document.body;
      container.appendChild(this.iframe);
    });

    // 设置通信
    if (this.config.enableMessaging) {
      this.messenger = new SecureFrameMessenger(
        this.iframe.contentWindow,
        this.config.targetOrigin
      );
    }

    return this.iframe;
  }

  // 更新 iframe 内容
  async navigate(url) {
    if (!this.iframe) throw new Error('iframe 不存在');

    this.loaded = false;
    this.iframe.src = url;

    await new Promise((resolve) => {
      const handler = () => {
        this.loaded = true;
        this.iframe.removeEventListener('load', handler);
        resolve();
      };
      this.iframe.addEventListener('load', handler);
    });
  }

  // 刷新 iframe
  reload() {
    if (this.iframe) {
      this.iframe.src = this.iframe.src;
    }
  }

  // 销毁 iframe（清理资源）
  destroy() {
    if (this.iframe) {
      // 清除 src，停止加载资源
      this.iframe.src = 'about:blank';

      // 从 DOM 移除
      if (this.iframe.parentElement) {
        this.iframe.parentElement.removeChild(this.iframe);
      }

      // 清除引用
      this.iframe = null;
      this.messenger = null;
      this.loaded = false;
    }
  }

  // 发送消息
  send(type, data) {
    if (this.messenger) {
      this.messenger.send(type, data);
    }
  }

  // 请求-响应
  async request(type, data) {
    if (this.messenger) {
      return this.messenger.request(type, data);
    }
    throw new Error('消息通信未启用');
  }
}

// 使用示例
const manager = new IframeLifecycleManager({
  src: 'https://example.com/page.html',
  id: 'my-iframe',
  container: document.querySelector('.iframe-container'),
  sandbox: 'allow-scripts allow-forms',
  enableMessaging: true,
  targetOrigin: 'https://example.com',
  style: {
    width: '100%',
    height: '600px',
    border: 'none'
  }
});

// 创建 iframe
await manager.create();

// 发送消息
manager.send('init', { userId: '123' });

// 请求数据
const status = await manager.request('get-status', {});

// 切换页面
await manager.navigate('https://example.com/another.html');

// 销毁 iframe（重要！避免内存泄漏）
manager.destroy();
```

---

**记录者注**:

iframe 和 window 对象的层级关系是浏览器多窗口架构的核心。每个 iframe 都有独立的 window 对象，通过 `parent`、`top`、`frames` 等属性形成层级关系。同源的 iframe 可以直接通过 `contentWindow` 和 `contentDocument` 访问，跨域 iframe 受到同源策略限制，只能通过 postMessage 进行安全通信。

关键在于理解同源策略的边界、postMessage 的正确用法（明确指定目标域、验证来源域）、sandbox 属性的权限控制、以及防止自己的页面被恶意嵌入的措施（X-Frame-Options、CSP frame-ancestors、JavaScript 检测）。实际应用中需要正确管理 iframe 的生命周期，及时销毁不再使用的 iframe 以避免内存泄漏。

记住：**同源 iframe 可直接访问，跨域 iframe 用 postMessage；发送消息指定目标域，接收消息验证来源域；使用 sandbox 限制权限，使用 X-Frame-Options 防止被嵌入；正确管理生命周期避免内存泄漏**。掌握 iframe 和 window 的关系是构建复杂 Web 应用的必备技能。
