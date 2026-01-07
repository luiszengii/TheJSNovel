《第 139 次记录：窗口之间的呼唤 —— 跨窗口通信与数据同步》

## 第三方支付窗口失联事件

周二下午 3 点 12 分，你正在测试新开发的支付流程。按照产品需求，用户点击"支付"按钮后，系统会弹出一个新窗口跳转到第三方支付平台。支付完成后，新窗口应该通知主窗口刷新订单状态，然后自动关闭。

你写的代码看起来很简单：

```javascript
// 主窗口代码
const payButton = document.querySelector('.pay-btn');

payButton.addEventListener('click', () => {
  const paymentWindow = window.open(
    'https://payment.example.com/pay?orderId=12345',
    'payment',
    'width=800,height=600'
  );

  // 等待支付窗口通知
  window.addEventListener('message', (event) => {
    if (event.data === 'payment-success') {
      console.log('支付成功，刷新订单状态');
      refreshOrderStatus();
      paymentWindow.close();
    }
  });
});
```

测试环境运行正常。但上线第一天，客服就收到大量投诉："支付完成后页面没反应，我不知道有没有支付成功！"

你立刻打开线上页面测试。点击支付按钮，新窗口弹出，跳转到支付平台，输入密码完成支付。然后你等待... 5 秒、10 秒、30 秒。主窗口毫无反应，订单状态仍然显示"待支付"，而支付窗口也没有自动关闭。

"消息没有传回来？" 你困惑地想，"还是根本没发送？"

你打开主窗口的控制台，没有任何 `console.log` 输出。你切换到支付窗口，查看它的控制台 —— 空白的，没有任何错误。你检查了支付平台的回调代码，发现它确实调用了 `window.opener.postMessage('payment-success', '*')`。

"那为什么主窗口收不到消息？" 你盯着代码，突然意识到一个问题：支付平台的域名是 `payment.example.com`，而你的网站是 `shop.yoursite.com`。会不会是跨域问题？

前端架构师老李走过来："你遇到跨窗口通信的经典问题了。window.open 打开的窗口和父窗口之间确实可以通信，但前提是你得正确配置。"

## 跨窗口通信的正确姿势

老李展示了跨窗口通信的完整方案：

```javascript
// 主窗口（父窗口）
class PaymentWindowManager {
  constructor() {
    this.paymentWindow = null;
    this.init();
  }

  init() {
    // 监听来自支付窗口的消息
    window.addEventListener('message', (event) => {
      // 严格验证消息来源
      if (event.origin !== 'https://payment.example.com') {
        console.warn('拒绝来自未授权源的消息:', event.origin);
        return;
      }

      this.handlePaymentMessage(event.data);
    });
  }

  openPaymentWindow(orderId) {
    const url = `https://payment.example.com/pay?orderId=${orderId}`;

    // 打开支付窗口
    this.paymentWindow = window.open(
      url,
      'payment',
      'width=800,height=600,resizable=yes,scrollbars=yes'
    );

    // 检查窗口是否成功打开
    if (!this.paymentWindow) {
      alert('弹窗被浏览器阻止，请允许弹窗后重试');
      return;
    }

    // 窗口关闭检测
    this.startWindowCheck();
  }

  startWindowCheck() {
    const checkInterval = setInterval(() => {
      if (this.paymentWindow && this.paymentWindow.closed) {
        clearInterval(checkInterval);
        console.log('支付窗口已关闭');
        this.onWindowClosed();
      }
    }, 1000);
  }

  handlePaymentMessage(data) {
    console.log('收到支付窗口消息:', data);

    if (data.type === 'payment-success') {
      console.log('支付成功:', data.orderId);
      this.refreshOrderStatus(data.orderId);
      this.closePaymentWindow();
    } else if (data.type === 'payment-cancel') {
      console.log('用户取消支付');
      this.closePaymentWindow();
    }
  }

  closePaymentWindow() {
    if (this.paymentWindow && !this.paymentWindow.closed) {
      this.paymentWindow.close();
    }
  }

  refreshOrderStatus(orderId) {
    // 刷新订单状态
    fetch(`/api/orders/${orderId}`)
      .then(res => res.json())
      .then(order => {
        console.log('订单状态已更新:', order.status);
        this.showSuccessMessage();
      });
  }

  onWindowClosed() {
    // 窗口关闭时的处理
    console.log('支付窗口已关闭，检查订单状态');
    this.checkOrderStatus();
  }

  showSuccessMessage() {
    const message = document.createElement('div');
    message.className = 'success-message';
    message.textContent = '支付成功！';
    document.body.appendChild(message);

    setTimeout(() => message.remove(), 3000);
  }

  checkOrderStatus() {
    // 窗口关闭后的兜底检查
    console.log('执行兜底检查');
  }
}

// 使用示例
const paymentManager = new PaymentWindowManager();

document.querySelector('.pay-btn').addEventListener('click', () => {
  const orderId = document.querySelector('.order-id').textContent;
  paymentManager.openPaymentWindow(orderId);
});
```

老李解释道："关键在于几点：第一，使用 `postMessage` 进行跨窗口通信，支持跨域；第二，严格验证 `event.origin` 确保消息来源可信；第三，检测窗口关闭状态作为兜底方案。"

你立刻问："那支付窗口那边的代码应该怎么写？"

老李展示了支付窗口的代码：

```javascript
// 支付窗口（子窗口）
class PaymentNotifier {
  constructor() {
    this.parentOrigin = 'https://shop.yoursite.com';
    this.init();
  }

  init() {
    // 检查是否有父窗口
    if (!window.opener) {
      console.warn('没有检测到父窗口');
      return;
    }

    // 检查父窗口是否仍然存在
    if (window.opener.closed) {
      console.warn('父窗口已关闭');
      return;
    }

    // 监听支付完成事件
    this.listenForPaymentComplete();
  }

  listenForPaymentComplete() {
    // 假设支付平台有一个回调
    window.addEventListener('payment-complete', (event) => {
      const { orderId, success } = event.detail;

      if (success) {
        this.notifyParent({
          type: 'payment-success',
          orderId: orderId,
          timestamp: Date.now()
        });
      }
    });
  }

  notifyParent(data) {
    if (!window.opener || window.opener.closed) {
      console.error('父窗口不可访问');
      return;
    }

    try {
      // 向父窗口发送消息
      window.opener.postMessage(data, this.parentOrigin);
      console.log('已通知父窗口:', data);
    } catch (error) {
      console.error('通知父窗口失败:', error);
    }
  }

  // 用户点击"完成"按钮
  handleDoneClick() {
    this.notifyParent({
      type: 'payment-success',
      orderId: this.getOrderId(),
      timestamp: Date.now()
    });

    // 延迟关闭窗口，确保消息发送
    setTimeout(() => {
      window.close();
    }, 100);
  }

  // 用户点击"取消"按钮
  handleCancelClick() {
    this.notifyParent({
      type: 'payment-cancel',
      timestamp: Date.now()
    });

    setTimeout(() => {
      window.close();
    }, 100);
  }

  getOrderId() {
    const params = new URLSearchParams(window.location.search);
    return params.get('orderId');
  }
}

// 初始化
const notifier = new PaymentNotifier();

// 绑定按钮事件
document.querySelector('.done-btn')?.addEventListener('click', () => {
  notifier.handleDoneClick();
});

document.querySelector('.cancel-btn')?.addEventListener('click', () => {
  notifier.handleCancelClick();
});
```

你测试了新的代码，支付窗口终于能够正确通知主窗口了。但老李说："还不够稳定。你需要处理更多边界情况。"

## 双向通信与心跳检测

老李展示了更健壮的双向通信方案：

```javascript
// 双向通信管理器（可用于父窗口或子窗口）
class CrossWindowMessenger {
  constructor(targetWindow, targetOrigin) {
    this.targetWindow = targetWindow; // window.opener 或 子窗口引用
    this.targetOrigin = targetOrigin;
    this.handlers = new Map();
    this.pendingRequests = new Map();
    this.requestId = 0;
    this.connected = false;
    this.heartbeatInterval = null;
    this.init();
  }

  init() {
    // 监听消息
    window.addEventListener('message', (event) => {
      // 验证来源
      if (event.origin !== this.targetOrigin) {
        console.warn('拒绝来自未授权源的消息:', event.origin);
        return;
      }

      this.handleMessage(event.data);
    });

    // 启动心跳检测
    this.startHeartbeat();
  }

  handleMessage(message) {
    // 处理心跳响应
    if (message.type === 'heartbeat') {
      this.connected = true;
      return;
    }

    if (message.type === 'heartbeat-response') {
      this.connected = true;
      return;
    }

    // 处理请求响应
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

    // 处理普通消息
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
  }

  // 注册消息处理器
  on(type, handler) {
    this.handlers.set(type, handler);
  }

  // 发送单向消息
  send(type, data) {
    if (!this.isWindowAlive()) {
      console.error('目标窗口不可访问');
      return false;
    }

    try {
      this.targetWindow.postMessage({
        type,
        data,
        timestamp: Date.now()
      }, this.targetOrigin);
      return true;
    } catch (error) {
      console.error('发送消息失败:', error);
      return false;
    }
  }

  // 发送请求并等待响应
  request(type, data, timeout = 5000) {
    return new Promise((resolve, reject) => {
      if (!this.isWindowAlive()) {
        reject(new Error('目标窗口不可访问'));
        return;
      }

      const requestId = ++this.requestId;

      this.pendingRequests.set(requestId, { resolve, reject });

      try {
        this.targetWindow.postMessage({
          type,
          data,
          requestId,
          timestamp: Date.now()
        }, this.targetOrigin);
      } catch (error) {
        this.pendingRequests.delete(requestId);
        reject(error);
        return;
      }

      // 设置超时
      setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          reject(new Error('请求超时'));
        }
      }, timeout);
    });
  }

  // 发送响应
  sendResponse(requestId, data, error = null) {
    if (!this.isWindowAlive()) {
      return;
    }

    try {
      this.targetWindow.postMessage({
        responseId: requestId,
        data,
        error,
        timestamp: Date.now()
      }, this.targetOrigin);
    } catch (err) {
      console.error('发送响应失败:', err);
    }
  }

  // 心跳检测
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.isWindowAlive()) {
        this.send('heartbeat', {});
      } else {
        this.connected = false;
        console.warn('目标窗口已关闭');
        this.stopHeartbeat();
      }
    }, 3000);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // 检查窗口是否存在
  isWindowAlive() {
    try {
      return this.targetWindow && !this.targetWindow.closed;
    } catch (error) {
      return false;
    }
  }

  // 关闭连接
  close() {
    this.stopHeartbeat();
    this.handlers.clear();
    this.pendingRequests.clear();
  }
}

// 父窗口使用示例
const paymentWindow = window.open(
  'https://payment.example.com/pay',
  'payment',
  'width=800,height=600'
);

if (paymentWindow) {
  const messenger = new CrossWindowMessenger(
    paymentWindow,
    'https://payment.example.com'
  );

  // 监听支付结果
  messenger.on('payment-result', (data) => {
    console.log('支付结果:', data);

    if (data.success) {
      showSuccessMessage();
      refreshOrder(data.orderId);
    }
  });

  // 发送初始化数据
  messenger.send('init', {
    orderId: '12345',
    amount: 99.00,
    userId: 'user123'
  });

  // 请求支付状态
  messenger.request('get-status', {}).then(status => {
    console.log('当前状态:', status);
  });
}

// 子窗口使用示例
if (window.opener) {
  const messenger = new CrossWindowMessenger(
    window.opener,
    'https://shop.yoursite.com'
  );

  // 监听初始化数据
  messenger.on('init', (data) => {
    console.log('收到初始化数据:', data);
    initPaymentForm(data);
  });

  // 响应状态查询
  messenger.on('get-status', () => {
    return {
      status: 'processing',
      progress: 50
    };
  });

  // 支付完成后通知父窗口
  function onPaymentComplete(result) {
    messenger.send('payment-result', {
      success: true,
      orderId: result.orderId,
      transactionId: result.transactionId
    });

    setTimeout(() => {
      window.close();
    }, 1000);
  }
}
```

## 多窗口协调与状态同步

老李展示了如何管理多个子窗口：

```javascript
// 多窗口管理器
class MultiWindowManager {
  constructor() {
    this.windows = new Map();
    this.messengers = new Map();
    this.init();
  }

  init() {
    // 监听来自所有子窗口的消息
    window.addEventListener('message', (event) => {
      // 查找消息来源的窗口
      for (const [windowId, messenger] of this.messengers) {
        if (messenger.targetOrigin === event.origin) {
          // 消息已由 messenger 处理
          return;
        }
      }
    });

    // 监听窗口关闭
    this.startWindowMonitor();
  }

  openWindow(url, name, options = {}) {
    const windowId = name || `window-${Date.now()}`;

    // 打开新窗口
    const newWindow = window.open(
      url,
      name,
      this.formatWindowOptions(options)
    );

    if (!newWindow) {
      throw new Error('窗口打开失败，可能被浏览器阻止');
    }

    // 保存窗口引用
    this.windows.set(windowId, newWindow);

    // 创建通信管理器
    const messenger = new CrossWindowMessenger(
      newWindow,
      new URL(url).origin
    );

    this.messengers.set(windowId, messenger);

    return { windowId, window: newWindow, messenger };
  }

  formatWindowOptions(options) {
    const defaults = {
      width: 800,
      height: 600,
      resizable: 'yes',
      scrollbars: 'yes'
    };

    const merged = { ...defaults, ...options };

    return Object.entries(merged)
      .map(([key, value]) => `${key}=${value}`)
      .join(',');
  }

  getWindow(windowId) {
    return this.windows.get(windowId);
  }

  getMessenger(windowId) {
    return this.messengers.get(windowId);
  }

  closeWindow(windowId) {
    const win = this.windows.get(windowId);
    const messenger = this.messengers.get(windowId);

    if (messenger) {
      messenger.close();
      this.messengers.delete(windowId);
    }

    if (win && !win.closed) {
      win.close();
    }

    this.windows.delete(windowId);
  }

  closeAllWindows() {
    for (const [windowId] of this.windows) {
      this.closeWindow(windowId);
    }
  }

  broadcastMessage(type, data) {
    for (const [windowId, messenger] of this.messengers) {
      messenger.send(type, data);
    }
  }

  startWindowMonitor() {
    setInterval(() => {
      for (const [windowId, win] of this.windows) {
        if (win.closed) {
          console.log('窗口已关闭:', windowId);
          this.closeWindow(windowId);
        }
      }
    }, 1000);
  }

  getOpenWindows() {
    const openWindows = [];

    for (const [windowId, win] of this.windows) {
      if (!win.closed) {
        openWindows.push(windowId);
      }
    }

    return openWindows;
  }
}

// 使用示例
const windowManager = new MultiWindowManager();

// 打开支付窗口
document.querySelector('.pay-btn').addEventListener('click', async () => {
  const { windowId, messenger } = windowManager.openWindow(
    'https://payment.example.com/pay',
    'payment',
    { width: 800, height: 600 }
  );

  messenger.on('payment-success', (data) => {
    console.log('支付成功:', data);
    windowManager.closeWindow(windowId);
  });

  messenger.send('init', { orderId: '12345' });
});

// 打开帮助窗口
document.querySelector('.help-btn').addEventListener('click', () => {
  const { windowId, messenger } = windowManager.openWindow(
    'https://help.example.com',
    'help',
    { width: 600, height: 800 }
  );

  messenger.on('close-request', () => {
    windowManager.closeWindow(windowId);
  });
});

// 广播消息给所有子窗口
function notifyAllWindows(message) {
  windowManager.broadcastMessage('notification', message);
}

// 页面卸载时关闭所有窗口
window.addEventListener('beforeunload', () => {
  windowManager.closeAllWindows();
});
```

下午 5 点 30 分，你完成了跨窗口通信的完整重构。新的实现不仅修复了消息丢失问题，还增加了心跳检测、请求响应模式、多窗口管理等功能。你给产品经理发消息："支付流程已优化，支持稳定的跨窗口通信，用户体验更流畅。"

---

## 技术档案：跨窗口通信核心机制

**规则 1: window.open 返回子窗口引用**

父窗口调用 `window.open` 返回子窗口的引用，子窗口通过 `window.opener` 访问父窗口。两个窗口可以相互引用但受同源策略限制。

```javascript
// 父窗口打开子窗口
const childWindow = window.open(
  'https://example.com/page.html',
  'childWindow',
  'width=800,height=600'
);

// 检查窗口是否成功打开
if (!childWindow) {
  console.error('窗口被浏览器阻止');
  return;
}

// 检查窗口是否关闭
console.log('窗口是否关闭:', childWindow.closed);

// 关闭子窗口
childWindow.close();

// 子窗口访问父窗口
if (window.opener) {
  console.log('有父窗口');

  // 检查父窗口是否仍然存在
  if (window.opener.closed) {
    console.log('父窗口已关闭');
  }
}

// 同源窗口可以直接访问 DOM（不推荐）
// 如果子窗口同源
if (childWindow && !childWindow.closed) {
  // ⚠️ 仅同源时可用
  childWindow.document.title = '新标题';
}

// 跨域窗口只能访问有限属性
// ✅ 总是可用的属性
console.log(childWindow.closed);  // 是否关闭
childWindow.close();               // 关闭窗口
childWindow.focus();               // 聚焦窗口
childWindow.blur();                // 失焦
childWindow.postMessage({}, '*');  // 发送消息

// ❌ 跨域时不可访问
// childWindow.document         // SecurityError
// childWindow.location.href    // SecurityError (读取)
```

**规则 2: postMessage 实现跨域通信**

使用 `postMessage` 可以安全地在不同源的窗口之间传递消息。发送方指定目标源，接收方验证消息来源。

```javascript
// 发送消息的标准格式
targetWindow.postMessage(data, targetOrigin);

// 父窗口向子窗口发送消息
const childWindow = window.open('https://example.com/page');

childWindow.addEventListener('load', () => {
  // ✅ 明确指定目标源（推荐）
  childWindow.postMessage({
    type: 'greeting',
    message: 'Hello from parent'
  }, 'https://example.com');

  // ❌ 不推荐使用 '*'（任意源都可以接收）
  // childWindow.postMessage(data, '*');
});

// 子窗口向父窗口发送消息
if (window.opener) {
  window.opener.postMessage({
    type: 'ready',
    timestamp: Date.now()
  }, 'https://parent.com');
}

// 接收消息的标准处理
window.addEventListener('message', (event) => {
  // ✅ 第一步：严格验证来源
  const allowedOrigins = [
    'https://example.com',
    'https://trusted.com'
  ];

  if (!allowedOrigins.includes(event.origin)) {
    console.warn('拒绝来自未授权源的消息:', event.origin);
    return;
  }

  // ✅ 第二步：验证数据格式
  if (typeof event.data !== 'object' || !event.data.type) {
    console.warn('无效的消息格式');
    return;
  }

  // ✅ 第三步：处理消息
  console.log('收到消息:', event.data);
  console.log('来源窗口:', event.source);
  console.log('来源域:', event.origin);

  // 回复消息
  if (event.source) {
    event.source.postMessage({
      type: 'response',
      received: true
    }, event.origin);
  }
});

// 消息事件对象的关键属性
// event.data: 消息内容（可以是任意可序列化的数据）
// event.origin: 消息来源的协议+域名+端口
// event.source: 发送消息的窗口引用
// event.ports: MessagePort 数组（高级用法）
```

**规则 3: 检测窗口状态和生命周期**

定期检测子窗口是否关闭，实现窗口关闭后的兜底处理。`window.closed` 属性总是可访问的，即使跨域。

```javascript
// 窗口状态检测
function isWindowAlive(win) {
  try {
    // closed 属性即使跨域也可以访问
    return win && !win.closed;
  } catch (error) {
    return false;
  }
}

// 定期检测窗口状态
const childWindow = window.open('https://example.com');

const checkInterval = setInterval(() => {
  if (!isWindowAlive(childWindow)) {
    console.log('子窗口已关闭');
    clearInterval(checkInterval);

    // 执行清理操作
    handleWindowClosed();
  }
}, 1000);

// 窗口关闭处理
function handleWindowClosed() {
  console.log('窗口关闭，执行兜底逻辑');

  // 例如：检查订单状态、刷新数据
  checkOrderStatus();
}

// 在子窗口关闭前通知父窗口
// 子窗口代码
window.addEventListener('beforeunload', () => {
  if (window.opener && !window.opener.closed) {
    window.opener.postMessage({
      type: 'window-closing',
      reason: 'user-action'
    }, 'https://parent.com');
  }
});

// 优雅关闭窗口
function closeWindowGracefully(childWindow, origin) {
  // 1. 先发送关闭通知
  if (isWindowAlive(childWindow)) {
    childWindow.postMessage({
      type: 'close-request'
    }, origin);
  }

  // 2. 延迟关闭，确保消息发送
  setTimeout(() => {
    if (isWindowAlive(childWindow)) {
      childWindow.close();
    }
  }, 100);
}

// 子窗口监听关闭请求
window.addEventListener('message', (event) => {
  if (event.origin !== 'https://parent.com') return;

  if (event.data.type === 'close-request') {
    // 执行清理操作
    cleanup();

    // 通知完成
    event.source.postMessage({
      type: 'close-acknowledged'
    }, event.origin);

    // 关闭窗口
    setTimeout(() => window.close(), 50);
  }
});
```

**规则 4: 实现请求-响应模式**

通过为消息添加唯一 ID，可以实现类似 HTTP 的请求-响应通信模式，支持异步等待响应。

```javascript
// 请求-响应通信封装
class WindowMessenger {
  constructor(targetWindow, targetOrigin) {
    this.targetWindow = targetWindow;
    this.targetOrigin = targetOrigin;
    this.pendingRequests = new Map();
    this.requestId = 0;
    this.init();
  }

  init() {
    window.addEventListener('message', (event) => {
      if (event.origin !== this.targetOrigin) return;

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
      }
    });
  }

  // 发送请求并等待响应
  request(type, data, timeout = 5000) {
    return new Promise((resolve, reject) => {
      const requestId = ++this.requestId;

      // 保存 promise 的 resolve/reject
      this.pendingRequests.set(requestId, { resolve, reject });

      // 发送请求
      this.targetWindow.postMessage({
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
      }, timeout);
    });
  }

  // 发送响应
  sendResponse(requestId, data, error = null) {
    this.targetWindow.postMessage({
      responseId: requestId,
      data,
      error
    }, this.targetOrigin);
  }
}

// 使用示例：父窗口
const messenger = new WindowMessenger(
  childWindow,
  'https://example.com'
);

// 发送请求
messenger.request('get-user-data', { userId: '123' })
  .then(userData => {
    console.log('收到用户数据:', userData);
  })
  .catch(error => {
    console.error('请求失败:', error);
  });

// 使用示例：子窗口
window.addEventListener('message', (event) => {
  if (event.origin !== 'https://parent.com') return;

  const message = event.data;

  if (message.type === 'get-user-data' && message.requestId) {
    // 处理请求
    const userData = getUserData(message.data.userId);

    // 发送响应
    event.source.postMessage({
      responseId: message.requestId,
      data: userData
    }, event.origin);
  }
});
```

**规则 5: 心跳检测保持连接活性**

使用定时心跳消息检测窗口连接状态，及时发现窗口关闭或通信中断。

```javascript
// 心跳检测实现
class WindowConnection {
  constructor(targetWindow, targetOrigin) {
    this.targetWindow = targetWindow;
    this.targetOrigin = targetOrigin;
    this.connected = false;
    this.lastHeartbeat = Date.now();
    this.heartbeatInterval = null;
    this.heartbeatTimeout = 5000; // 5秒超时
    this.init();
  }

  init() {
    // 监听心跳响应
    window.addEventListener('message', (event) => {
      if (event.origin !== this.targetOrigin) return;

      if (event.data.type === 'heartbeat') {
        // 收到心跳请求，回复
        this.sendHeartbeatResponse(event.source, event.origin);
      } else if (event.data.type === 'heartbeat-response') {
        // 收到心跳响应
        this.onHeartbeatReceived();
      }
    });

    // 启动心跳
    this.startHeartbeat();
  }

  startHeartbeat() {
    // 每3秒发送一次心跳
    this.heartbeatInterval = setInterval(() => {
      if (this.isWindowAlive()) {
        this.sendHeartbeat();

        // 检查是否超时
        if (Date.now() - this.lastHeartbeat > this.heartbeatTimeout) {
          this.onConnectionLost();
        }
      } else {
        this.onWindowClosed();
      }
    }, 3000);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  sendHeartbeat() {
    try {
      this.targetWindow.postMessage({
        type: 'heartbeat',
        timestamp: Date.now()
      }, this.targetOrigin);
    } catch (error) {
      console.error('发送心跳失败:', error);
    }
  }

  sendHeartbeatResponse(source, origin) {
    try {
      source.postMessage({
        type: 'heartbeat-response',
        timestamp: Date.now()
      }, origin);
    } catch (error) {
      console.error('发送心跳响应失败:', error);
    }
  }

  onHeartbeatReceived() {
    this.connected = true;
    this.lastHeartbeat = Date.now();
  }

  onConnectionLost() {
    this.connected = false;
    console.warn('心跳超时，连接可能已断开');

    // 触发回调
    if (this.onDisconnect) {
      this.onDisconnect();
    }
  }

  onWindowClosed() {
    this.connected = false;
    this.stopHeartbeat();
    console.log('窗口已关闭');

    // 触发回调
    if (this.onClose) {
      this.onClose();
    }
  }

  isWindowAlive() {
    try {
      return this.targetWindow && !this.targetWindow.closed;
    } catch (error) {
      return false;
    }
  }

  close() {
    this.stopHeartbeat();
  }
}

// 使用示例
const connection = new WindowConnection(
  childWindow,
  'https://example.com'
);

connection.onDisconnect = () => {
  console.log('连接断开，尝试重连或清理资源');
};

connection.onClose = () => {
  console.log('窗口关闭，执行清理');
  cleanup();
};

// 页面卸载时关闭心跳
window.addEventListener('beforeunload', () => {
  connection.close();
});
```

**规则 6: 多窗口管理与广播**

管理多个子窗口时，需要跟踪所有窗口引用，支持批量通信和统一清理。

```javascript
// 多窗口管理器
class MultiWindowManager {
  constructor() {
    this.windows = new Map(); // windowId -> window引用
    this.origins = new Map(); // windowId -> origin
  }

  // 打开新窗口
  openWindow(url, name, features) {
    const win = window.open(url, name, features);

    if (!win) {
      throw new Error('窗口被阻止');
    }

    const windowId = name || `window-${Date.now()}`;
    const origin = new URL(url).origin;

    this.windows.set(windowId, win);
    this.origins.set(windowId, origin);

    // 监听窗口关闭
    this.monitorWindow(windowId);

    return windowId;
  }

  // 监听窗口关闭
  monitorWindow(windowId) {
    const checkInterval = setInterval(() => {
      const win = this.windows.get(windowId);

      if (!win || win.closed) {
        clearInterval(checkInterval);
        this.removeWindow(windowId);
      }
    }, 1000);
  }

  // 移除窗口
  removeWindow(windowId) {
    this.windows.delete(windowId);
    this.origins.delete(windowId);
    console.log('窗口已移除:', windowId);
  }

  // 向指定窗口发送消息
  sendToWindow(windowId, message) {
    const win = this.windows.get(windowId);
    const origin = this.origins.get(windowId);

    if (!win || win.closed) {
      console.warn('窗口不存在或已关闭:', windowId);
      return false;
    }

    try {
      win.postMessage(message, origin);
      return true;
    } catch (error) {
      console.error('发送消息失败:', error);
      return false;
    }
  }

  // 广播消息给所有窗口
  broadcast(message) {
    const results = {};

    for (const [windowId, win] of this.windows) {
      if (!win.closed) {
        results[windowId] = this.sendToWindow(windowId, message);
      }
    }

    return results;
  }

  // 关闭指定窗口
  closeWindow(windowId) {
    const win = this.windows.get(windowId);

    if (win && !win.closed) {
      win.close();
    }

    this.removeWindow(windowId);
  }

  // 关闭所有窗口
  closeAll() {
    for (const [windowId, win] of this.windows) {
      if (!win.closed) {
        win.close();
      }
    }

    this.windows.clear();
    this.origins.clear();
  }

  // 获取所有打开的窗口
  getOpenWindows() {
    const openWindows = [];

    for (const [windowId, win] of this.windows) {
      if (!win.closed) {
        openWindows.push(windowId);
      }
    }

    return openWindows;
  }
}

// 使用示例
const manager = new MultiWindowManager();

// 打开多个窗口
const paymentId = manager.openWindow(
  'https://payment.com',
  'payment',
  'width=800,height=600'
);

const helpId = manager.openWindow(
  'https://help.com',
  'help',
  'width=600,height=800'
);

// 向指定窗口发送消息
manager.sendToWindow(paymentId, {
  type: 'init',
  orderId: '12345'
});

// 广播消息给所有窗口
manager.broadcast({
  type: 'user-logged-out',
  timestamp: Date.now()
});

// 获取打开的窗口列表
console.log('打开的窗口:', manager.getOpenWindows());

// 页面卸载时关闭所有窗口
window.addEventListener('beforeunload', () => {
  manager.closeAll();
});
```

---

**记录者注**:

跨窗口通信是浏览器提供的强大能力，允许不同窗口（包括跨域）之间安全地传递消息。`window.open` 返回子窗口引用，子窗口通过 `window.opener` 访问父窗口，但跨域时只能使用 `postMessage` 进行通信。

关键在于理解 `postMessage` 的正确用法（明确指定目标源、严格验证来源源）、窗口状态检测（`window.closed` 属性）、请求-响应模式实现、心跳检测保持连接活性。实际应用中需要处理窗口被阻止、窗口意外关闭、消息超时等边界情况，实现健壮的跨窗口通信系统。

记住：**window.open 返回子窗口引用，window.opener 访问父窗口；使用 postMessage 实现跨域通信；发送时指定目标源，接收时验证来源源；检测窗口状态处理关闭事件；实现请求-响应模式支持异步调用；心跳检测保持连接活性；多窗口管理支持广播和统一清理**。掌握跨窗口通信是构建复杂 Web 应用的重要技能。
