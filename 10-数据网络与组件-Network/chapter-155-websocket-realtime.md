《第 155 次记录: 周四下午的技术选型 —— WebSocket 实时通信方案》

---

## 技术选型会议

周四下午三点, 会议室的白板上写满了需求。

"我们需要实时推送功能," 产品经理小王指着原型图, "用户发送消息后, 其他在线用户要立即看到, 不能有延迟。类似微信那样的体验。"

你坐在会议桌前, 打开笔记本。这不是第一次讨论实时通信方案了——上周五的技术评审会上, 大家提出了三个候选方案: 轮询、Server-Sent Events (SSE)、WebSocket。

技术总监老李看向你: "你调研得怎么样了? 这三个方案各有什么优缺点?"

你打开准备好的对比文档:

```
实时通信方案对比:

方案 1: 短轮询 (Short Polling)
- 客户端每隔 N 秒请求一次服务器
- 实现简单, 但效率极低
- 大量无效请求, 服务器压力大

方案 2: 长轮询 (Long Polling)
- 客户端请求后, 服务器挂起连接直到有新消息
- 比短轮询好, 但仍有大量 HTTP 开销
- 连接频繁断开重连

方案 3: Server-Sent Events (SSE)
- 服务器单向推送到客户端
- 基于 HTTP, 实现简单
- 只能服务器推送, 客户端发送仍需 HTTP 请求

方案 4: WebSocket
- 全双工通信, 双向实时
- 持久连接, 开销小
- 需要专门的服务器支持
```

"我们的需求是双向实时通信," 后端老张说, "用户既要发送消息, 也要接收消息。SSE 只能单向推送, 不够。"

"那就是 WebSocket 了," 小王说, "但是 WebSocket 复杂吗? 我听说连接管理很麻烦。"

"确实有些挑战," 你点头, "WebSocket 虽然强大, 但需要处理断线重连、心跳检测、消息队列等问题。不过我准备了一套完整的方案。"

你切换到技术架构图:

```
WebSocket 架构设计:

客户端:
- WebSocket 连接管理类
- 自动重连机制 (指数退避)
- 心跳检测 (30 秒间隔)
- 消息队列 (断线期间缓存)
- 事件驱动架构

服务端:
- WebSocket 服务器 (Node.js + ws 库)
- 连接池管理
- 消息广播
- 用户认证
```

老李看着架构图: "看起来方案很完整。但有个关键问题——如果用户网络不稳定, 频繁断线重连怎么办?"

"这正是我要重点解决的问题," 你说, "我设计了一套智能重连策略, 结合指数退避和消息队列, 确保消息不丢失。"

"好," 老李拍板, "那就用 WebSocket。你先做个技术验证, 下周一给我看 Demo。"

会议结束后, 你回到工位, 开始深入研究 WebSocket 的技术细节。

---

## WebSocket 协议基础

你打开 MDN 文档, 从最基础的概念开始。

**WebSocket 是什么?**

WebSocket 是一个在单个 TCP 连接上进行全双工通信的协议。它允许服务器主动向客户端推送数据, 而不需要客户端不断轮询。

你在笔记中记录核心特点:

```
WebSocket 核心特性:

1. 全双工通信:
   - 客户端和服务器可以同时发送数据
   - 不像 HTTP 的请求-响应模式

2. 持久连接:
   - 一次握手, 长期保持
   - 避免重复建立连接的开销

3. 低延迟:
   - 没有 HTTP 请求头的开销
   - 消息帧格式简单高效

4. 二进制和文本支持:
   - 可以发送文本 (UTF-8)
   - 可以发送二进制数据 (ArrayBuffer, Blob)

5. 跨域支持:
   - 通过 origin 验证控制
   - 比 CORS 更灵活
```

**WebSocket URL 格式:**

WebSocket 使用特殊的 URL 协议:

```javascript
// 非加密连接
const ws = new WebSocket('ws://localhost:8080');

// 加密连接 (生产环境必须用)
const wss = new WebSocket('wss://api.example.com/chat');

// 可以带路径和查询参数
const ws = new WebSocket('wss://api.example.com/chat?userId=123&token=abc');
```

你注意到一个重要细节: 生产环境必须使用 `wss://` (WebSocket Secure), 就像 HTTPS 一样。

**WebSocket 连接生命周期:**

你在白板上画出状态转换图:

```
连接生命周期:

CONNECTING (0)  → 正在建立连接
    ↓
OPEN (1)        → 连接已建立, 可以通信
    ↓
CLOSING (2)     → 连接正在关闭
    ↓
CLOSED (3)      → 连接已关闭
```

每个状态对应 `readyState` 属性的一个值:

```javascript
const ws = new WebSocket('wss://api.example.com');

console.log(ws.readyState);  // 0 (CONNECTING)

ws.addEventListener('open', () => {
    console.log(ws.readyState);  // 1 (OPEN)
});

ws.addEventListener('close', () => {
    console.log(ws.readyState);  // 3 (CLOSED)
});
```

**WebSocket 握手过程:**

WebSocket 连接以 HTTP 请求开始, 然后升级为 WebSocket 协议:

```
客户端发送升级请求:

GET /chat HTTP/1.1
Host: api.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13

服务器响应:

HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

握手成功后, 连接从 HTTP 升级为 WebSocket, 之后的所有通信都使用 WebSocket 协议。

---

## 基础实现与初步问题

你决定先实现一个最简单的 WebSocket 客户端:

```javascript
// 最简单的 WebSocket 客户端
const ws = new WebSocket('wss://api.example.com/chat');

// 连接建立
ws.addEventListener('open', (event) => {
    console.log('WebSocket 连接已建立');

    // 发送消息
    ws.send('Hello Server!');

    // 发送 JSON 数据
    ws.send(JSON.stringify({
        type: 'message',
        content: 'Hello from client'
    }));
});

// 接收消息
ws.addEventListener('message', (event) => {
    console.log('收到消息:', event.data);

    // 如果是 JSON, 解析它
    try {
        const data = JSON.parse(event.data);
        console.log('解析后的数据:', data);
    } catch (e) {
        // 纯文本消息
        console.log('文本消息:', event.data);
    }
});

// 连接关闭
ws.addEventListener('close', (event) => {
    console.log('连接已关闭');
    console.log('关闭码:', event.code);
    console.log('关闭原因:', event.reason);
    console.log('是否正常关闭:', event.wasClean);
});

// 连接错误
ws.addEventListener('error', (event) => {
    console.error('WebSocket 错误:', event);
});
```

你在本地测试环境运行这段代码。一开始很顺利——连接建立、消息收发都正常。

但当你关闭 WiFi 模拟断网时, 问题出现了:

```
WebSocket 连接已建立
收到消息: {"type":"welcome","message":"Welcome to chat"}
发送消息: Hello Server!

[断网]

WebSocket 错误: Event {isTrusted: true}
连接已关闭
关闭码: 1006
关闭原因:
是否正常关闭: false
```

连接断开了, 但代码没有尝试重连。用户界面显示 "连接断开", 但什么也不做。

"这就是问题所在," 你在笔记中写道, "基础的 WebSocket API 不会自动重连。断线后, 连接就彻底断了。"

你又测试了另一个场景: 在连接断开时发送消息:

```javascript
// 连接断开后尝试发送消息
ws.addEventListener('close', () => {
    console.log('连接已关闭');

    // 尝试发送消息
    try {
        ws.send('This will fail');
    } catch (error) {
        console.error('发送失败:', error);
        // InvalidStateError: The connection is not open
    }
});
```

果然, 直接报错。如果用户在断网期间发送消息, 消息会丢失。

你列出了需要解决的问题:

```
问题清单:

1. ❌ 断线后不会自动重连
   - 用户需要刷新页面

2. ❌ 断线期间发送的消息会丢失
   - 没有消息队列缓存

3. ❌ 无法检测连接是否真正活跃
   - 网络可能卡住但连接未关闭

4. ❌ 重连时机不合理
   - 应该用指数退避避免服务器压力

5. ❌ 没有连接状态管理
   - UI 不知道当前连接状态
```

"需要一个完整的 WebSocket 管理类," 你决定, "封装这些复杂的逻辑。"

---

## 自动重连机制

你开始实现第一个重要特性: 自动重连。

```javascript
// 带自动重连的 WebSocket 客户端
class WebSocketClient {
    constructor(url, options = {}) {
        this.url = url;
        this.ws = null;

        // 重连配置
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 1000;  // 基础延迟 1 秒
        this.maxReconnectDelay = options.maxReconnectDelay || 30000;  // 最大延迟 30 秒

        // 事件处理器
        this.listeners = {
            open: [],
            message: [],
            close: [],
            error: [],
            reconnect: []
        };
    }

    // 连接到服务器
    connect() {
        console.log(`连接到 ${this.url}...`);

        this.ws = new WebSocket(this.url);

        // 连接建立
        this.ws.addEventListener('open', (event) => {
            console.log('WebSocket 连接成功');
            this.reconnectAttempts = 0;  // 重置重连次数

            // 触发 open 事件
            this.listeners.open.forEach(handler => handler(event));
        });

        // 接收消息
        this.ws.addEventListener('message', (event) => {
            this.listeners.message.forEach(handler => handler(event));
        });

        // 连接关闭
        this.ws.addEventListener('close', (event) => {
            console.log('WebSocket 连接关闭');

            // 触发 close 事件
            this.listeners.close.forEach(handler => handler(event));

            // 尝试重连
            this.handleReconnect();
        });

        // 连接错误
        this.ws.addEventListener('error', (event) => {
            console.error('WebSocket 错误');
            this.listeners.error.forEach(handler => handler(event));
        });
    }

    // 处理重连
    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error(`重连失败: 已达到最大重连次数 (${this.maxReconnectAttempts})`);
            return;
        }

        // 计算延迟 (指数退避)
        const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
            this.maxReconnectDelay
        );

        // 添加随机抖动 (±25%)
        const jitter = delay * (0.75 + Math.random() * 0.5);

        console.log(`${jitter.toFixed(0)}ms 后重连 (尝试 ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);

        this.reconnectAttempts++;

        // 触发 reconnect 事件
        this.listeners.reconnect.forEach(handler => handler({
            attempt: this.reconnectAttempts,
            maxAttempts: this.maxReconnectAttempts,
            delay: jitter
        }));

        // 延迟后重连
        setTimeout(() => {
            this.connect();
        }, jitter);
    }

    // 发送消息
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(data);
        } else {
            console.warn('连接未建立, 无法发送消息');
        }
    }

    // 关闭连接
    close() {
        this.reconnectAttempts = this.maxReconnectAttempts;  // 阻止自动重连
        if (this.ws) {
            this.ws.close();
        }
    }

    // 添加事件监听
    on(event, handler) {
        if (this.listeners[event]) {
            this.listeners[event].push(handler);
        }
    }
}
```

你测试这个新实现:

```javascript
// 测试: 自动重连
const client = new WebSocketClient('wss://api.example.com/chat', {
    maxReconnectAttempts: 5,
    reconnectDelay: 1000,
    maxReconnectDelay: 30000
});

client.on('open', () => {
    console.log('[应用] 连接已建立');
});

client.on('message', (event) => {
    console.log('[应用] 收到消息:', event.data);
});

client.on('reconnect', (info) => {
    console.log(`[应用] 正在重连 (${info.attempt}/${info.maxAttempts})...`);
});

client.connect();
```

测试结果:

```
连接到 wss://api.example.com/chat...
WebSocket 连接成功
[应用] 连接已建立

[模拟断网]

WebSocket 连接关闭
1024ms 后重连 (尝试 1/5)
[应用] 正在重连 (1/5)...
连接到 wss://api.example.com/chat...
WebSocket 连接成功
[应用] 连接已建立
```

"太好了!" 你满意地点头, "指数退避让重连更智能了。"

但你马上意识到还有一个问题——断线期间发送的消息怎么办?

---

## 消息队列与离线缓存

你决定添加消息队列机制:

```javascript
// 增强版: 支持消息队列
class WebSocketClientWithQueue extends WebSocketClient {
    constructor(url, options = {}) {
        super(url, options);

        // 消息队列
        this.messageQueue = [];
        this.maxQueueSize = options.maxQueueSize || 100;
    }

    // 连接建立后的处理
    connect() {
        super.connect();

        // 重写 open 事件处理
        const originalOpen = this.ws.addEventListener;
        this.ws.addEventListener('open', (event) => {
            // 清空消息队列
            this.flushMessageQueue();
        });
    }

    // 发送消息 (带队列)
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            // 连接正常, 直接发送
            this.ws.send(data);
            console.log('消息已发送:', data);

        } else {
            // 连接断开, 加入队列
            if (this.messageQueue.length >= this.maxQueueSize) {
                console.warn('消息队列已满, 丢弃最旧的消息');
                this.messageQueue.shift();
            }

            this.messageQueue.push({
                data: data,
                timestamp: Date.now()
            });

            console.log(`消息已加入队列 (队列长度: ${this.messageQueue.length})`);
        }
    }

    // 清空消息队列
    flushMessageQueue() {
        if (this.messageQueue.length === 0) {
            return;
        }

        console.log(`发送队列中的 ${this.messageQueue.length} 条消息...`);

        while (this.messageQueue.length > 0) {
            const message = this.messageQueue.shift();

            // 检查消息是否过期 (超过 5 分钟)
            const age = Date.now() - message.timestamp;
            if (age > 5 * 60 * 1000) {
                console.warn('消息已过期, 跳过:', message.data);
                continue;
            }

            // 发送消息
            try {
                this.ws.send(message.data);
                console.log('队列消息已发送:', message.data);
            } catch (error) {
                console.error('发送队列消息失败:', error);
                // 重新加入队列
                this.messageQueue.unshift(message);
                break;
            }
        }

        console.log('消息队列已清空');
    }

    // 获取队列状态
    getQueueStatus() {
        return {
            length: this.messageQueue.length,
            maxSize: this.maxQueueSize,
            messages: this.messageQueue
        };
    }
}
```

测试消息队列:

```javascript
// 测试: 消息队列
const client = new WebSocketClientWithQueue('wss://api.example.com/chat', {
    maxReconnectAttempts: 5,
    maxQueueSize: 50
});

client.on('open', () => {
    console.log('[应用] 连接已建立');
});

client.connect();

// 等待连接建立
setTimeout(() => {
    client.send(JSON.stringify({ message: '消息 1' }));  // 正常发送
}, 2000);

// 模拟断网
setTimeout(() => {
    console.log('[测试] 模拟断网');
    // 在断网期间发送消息
    client.send(JSON.stringify({ message: '消息 2' }));  // 加入队列
    client.send(JSON.stringify({ message: '消息 3' }));  // 加入队列
    client.send(JSON.stringify({ message: '消息 4' }));  // 加入队列
}, 5000);
```

测试结果:

```
连接到 wss://api.example.com/chat...
WebSocket 连接成功
[应用] 连接已建立
消息已发送: {"message":"消息 1"}

[测试] 模拟断网
消息已加入队列 (队列长度: 1)
消息已加入队列 (队列长度: 2)
消息已加入队列 (队列长度: 3)

1024ms 后重连 (尝试 1/5)...
连接到 wss://api.example.com/chat...
WebSocket 连接成功
[应用] 连接已建立

发送队列中的 3 条消息...
队列消息已发送: {"message":"消息 2"}
队列消息已发送: {"message":"消息 3"}
队列消息已发送: {"message":"消息 4"}
消息队列已清空
```

"完美!" 你兴奋地说, "断线期间的消息不会丢失了。"

---

## 心跳机制与连接健康检测

接下来你要解决一个更微妙的问题: 如何检测连接是否真正活跃?

有时网络会卡住——TCP 连接没有关闭, 但数据无法传输。这种情况下, `readyState` 仍然是 `OPEN`, 但实际上连接已经不可用了。

"需要心跳机制," 你在笔记中写道, "定期发送 ping, 如果收不到 pong, 就认为连接失效。"

```javascript
// 完整版: 支持心跳检测
class WebSocketClientWithHeartbeat extends WebSocketClientWithQueue {
    constructor(url, options = {}) {
        super(url, options);

        // 心跳配置
        this.heartbeatInterval = options.heartbeatInterval || 30000;  // 30 秒
        this.pongTimeout = options.pongTimeout || 5000;  // 5 秒超时

        this.heartbeatTimer = null;
        this.pongTimeoutTimer = null;
        this.lastPongTime = null;
    }

    // 连接建立
    connect() {
        super.connect();

        // 监听 open 事件
        this.ws.addEventListener('open', () => {
            this.startHeartbeat();
        });

        // 监听 message 事件 (接收 pong)
        this.ws.addEventListener('message', (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'pong') {
                    this.handlePong();
                }
            } catch (e) {
                // 不是 JSON 或不是 pong 消息, 忽略
            }
        });

        // 监听 close 事件
        this.ws.addEventListener('close', () => {
            this.stopHeartbeat();
        });
    }

    // 启动心跳
    startHeartbeat() {
        console.log('启动心跳检测');

        // 清除旧的定时器
        this.stopHeartbeat();

        // 定期发送 ping
        this.heartbeatTimer = setInterval(() => {
            this.sendPing();
        }, this.heartbeatInterval);

        // 立即发送一次 ping
        this.sendPing();
    }

    // 停止心跳
    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }

        if (this.pongTimeoutTimer) {
            clearTimeout(this.pongTimeoutTimer);
            this.pongTimeoutTimer = null;
        }
    }

    // 发送 ping
    sendPing() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const ping = JSON.stringify({
                type: 'ping',
                timestamp: Date.now()
            });

            this.ws.send(ping);
            console.log('[心跳] 发送 ping');

            // 启动 pong 超时检测
            this.pongTimeoutTimer = setTimeout(() => {
                console.warn('[心跳] pong 超时, 关闭连接');
                this.ws.close();
            }, this.pongTimeout);
        }
    }

    // 处理 pong
    handlePong() {
        console.log('[心跳] 收到 pong');

        // 清除超时定时器
        if (this.pongTimeoutTimer) {
            clearTimeout(this.pongTimeoutTimer);
            this.pongTimeoutTimer = null;
        }

        // 记录最后一次 pong 时间
        this.lastPongTime = Date.now();
    }

    // 获取心跳状态
    getHeartbeatStatus() {
        const now = Date.now();
        const timeSinceLastPong = this.lastPongTime ? now - this.lastPongTime : null;

        return {
            active: this.heartbeatTimer !== null,
            interval: this.heartbeatInterval,
            lastPongTime: this.lastPongTime,
            timeSinceLastPong: timeSinceLastPong,
            healthy: timeSinceLastPong === null || timeSinceLastPong < this.heartbeatInterval * 2
        };
    }
}
```

你模拟了一个心跳超时场景:

```javascript
// 测试: 心跳检测
const client = new WebSocketClientWithHeartbeat('wss://api.example.com/chat', {
    heartbeatInterval: 10000,  // 10 秒
    pongTimeout: 3000  // 3 秒超时
});

client.on('open', () => {
    console.log('[应用] 连接已建立');

    // 检查心跳状态
    setInterval(() => {
        const status = client.getHeartbeatStatus();
        console.log('[应用] 心跳状态:', status);
    }, 5000);
});

client.connect();
```

测试结果:

```
连接到 wss://api.example.com/chat...
WebSocket 连接成功
[应用] 连接已建立
启动心跳检测
[心跳] 发送 ping
[心跳] 收到 pong

[应用] 心跳状态: {
  active: true,
  interval: 10000,
  lastPongTime: 1705478234567,
  timeSinceLastPong: 2341,
  healthy: true
}

[心跳] 发送 ping
[心跳] 收到 pong

[模拟服务器无响应]

[心跳] 发送 ping
[心跳] pong 超时, 关闭连接
WebSocket 连接关闭
1024ms 后重连 (尝试 1/5)...
```

"非常好," 你满意地点头, "心跳机制可以及时发现连接失效, 触发重连。"

---

## 完整的 WebSocket 管理类

你整合了所有功能, 创建了一个完整的生产级 WebSocket 管理类:

```javascript
// 生产级 WebSocket 客户端
class WebSocketManager {
    constructor(url, options = {}) {
        this.url = url;
        this.ws = null;

        // 连接配置
        this.protocols = options.protocols || [];

        // 重连配置
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 1000;
        this.maxReconnectDelay = options.maxReconnectDelay || 30000;

        // 消息队列配置
        this.messageQueue = [];
        this.maxQueueSize = options.maxQueueSize || 100;
        this.messageExpiry = options.messageExpiry || 5 * 60 * 1000;  // 5 分钟

        // 心跳配置
        this.heartbeatInterval = options.heartbeatInterval || 30000;
        this.pongTimeout = options.pongTimeout || 5000;
        this.heartbeatTimer = null;
        this.pongTimeoutTimer = null;
        this.lastPongTime = null;

        // 状态
        this.manualClose = false;
        this.connectionState = 'disconnected';  // disconnected, connecting, connected, reconnecting

        // 事件处理器
        this.eventHandlers = {
            open: [],
            message: [],
            close: [],
            error: [],
            reconnect: [],
            stateChange: []
        };

        // 统计信息
        this.stats = {
            messagesReceived: 0,
            messagesSent: 0,
            reconnectCount: 0,
            totalConnectTime: 0,
            lastConnectTime: null
        };
    }

    // ========== 连接管理 ==========

    connect() {
        if (this.connectionState === 'connecting' || this.connectionState === 'connected') {
            console.warn('连接已存在');
            return;
        }

        this.manualClose = false;
        this.updateState('connecting');

        console.log(`连接到 ${this.url}...`);

        try {
            this.ws = new WebSocket(this.url, this.protocols);

            this.ws.addEventListener('open', this.handleOpen.bind(this));
            this.ws.addEventListener('message', this.handleMessage.bind(this));
            this.ws.addEventListener('close', this.handleClose.bind(this));
            this.ws.addEventListener('error', this.handleError.bind(this));

        } catch (error) {
            console.error('创建 WebSocket 失败:', error);
            this.updateState('disconnected');
            this.scheduleReconnect();
        }
    }

    disconnect() {
        console.log('主动断开连接');
        this.manualClose = true;
        this.stopHeartbeat();

        if (this.ws) {
            this.ws.close(1000, 'Client closing');
        }

        this.updateState('disconnected');
    }

    // ========== 事件处理 ==========

    handleOpen(event) {
        console.log('WebSocket 连接成功');

        this.reconnectAttempts = 0;
        this.stats.lastConnectTime = Date.now();
        this.updateState('connected');

        // 启动心跳
        this.startHeartbeat();

        // 清空消息队列
        this.flushMessageQueue();

        // 触发 open 事件
        this.emit('open', event);
    }

    handleMessage(event) {
        this.stats.messagesReceived++;

        // 尝试解析为 JSON
        let data;
        try {
            data = JSON.parse(event.data);

            // 处理心跳消息
            if (data.type === 'pong') {
                this.handlePong();
                return;
            }

        } catch (e) {
            // 不是 JSON, 使用原始数据
            data = event.data;
        }

        // 触发 message 事件
        this.emit('message', { data: data, raw: event.data });
    }

    handleClose(event) {
        console.log('WebSocket 连接关闭');
        console.log('关闭码:', event.code);
        console.log('关闭原因:', event.reason);

        // 更新统计
        if (this.stats.lastConnectTime) {
            const duration = Date.now() - this.stats.lastConnectTime;
            this.stats.totalConnectTime += duration;
        }

        this.stopHeartbeat();
        this.updateState('disconnected');

        // 触发 close 事件
        this.emit('close', event);

        // 如果不是主动关闭, 尝试重连
        if (!this.manualClose) {
            this.scheduleReconnect();
        }
    }

    handleError(event) {
        console.error('WebSocket 错误');
        this.emit('error', event);
    }

    // ========== 重连机制 ==========

    scheduleReconnect() {
        if (this.manualClose) {
            return;
        }

        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error(`重连失败: 已达到最大重连次数 (${this.maxReconnectAttempts})`);
            this.updateState('disconnected');
            return;
        }

        // 计算延迟 (指数退避 + 随机抖动)
        const baseDelay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
            this.maxReconnectDelay
        );
        const jitter = baseDelay * (0.75 + Math.random() * 0.5);

        console.log(`${jitter.toFixed(0)}ms 后重连 (尝试 ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);

        this.reconnectAttempts++;
        this.stats.reconnectCount++;
        this.updateState('reconnecting');

        // 触发 reconnect 事件
        this.emit('reconnect', {
            attempt: this.reconnectAttempts,
            maxAttempts: this.maxReconnectAttempts,
            delay: jitter
        });

        setTimeout(() => {
            this.connect();
        }, jitter);
    }

    // ========== 心跳机制 ==========

    startHeartbeat() {
        console.log('[心跳] 启动心跳检测');

        this.stopHeartbeat();

        this.heartbeatTimer = setInterval(() => {
            this.sendPing();
        }, this.heartbeatInterval);

        // 立即发送一次 ping
        this.sendPing();
    }

    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }

        if (this.pongTimeoutTimer) {
            clearTimeout(this.pongTimeoutTimer);
            this.pongTimeoutTimer = null;
        }
    }

    sendPing() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            const ping = JSON.stringify({
                type: 'ping',
                timestamp: Date.now()
            });

            this.ws.send(ping);
            console.log('[心跳] 发送 ping');

            // 启动 pong 超时检测
            this.pongTimeoutTimer = setTimeout(() => {
                console.warn('[心跳] pong 超时, 关闭连接');
                if (this.ws) {
                    this.ws.close();
                }
            }, this.pongTimeout);
        }
    }

    handlePong() {
        console.log('[心跳] 收到 pong');

        if (this.pongTimeoutTimer) {
            clearTimeout(this.pongTimeoutTimer);
            this.pongTimeoutTimer = null;
        }

        this.lastPongTime = Date.now();
    }

    // ========== 消息队列 ==========

    send(data) {
        const message = typeof data === 'string' ? data : JSON.stringify(data);

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            // 连接正常, 直接发送
            try {
                this.ws.send(message);
                this.stats.messagesSent++;
                console.log('消息已发送');
                return true;

            } catch (error) {
                console.error('发送消息失败:', error);
                this.queueMessage(message);
                return false;
            }

        } else {
            // 连接断开, 加入队列
            this.queueMessage(message);
            return false;
        }
    }

    queueMessage(message) {
        if (this.messageQueue.length >= this.maxQueueSize) {
            console.warn('消息队列已满, 丢弃最旧的消息');
            this.messageQueue.shift();
        }

        this.messageQueue.push({
            data: message,
            timestamp: Date.now()
        });

        console.log(`消息已加入队列 (队列长度: ${this.messageQueue.length})`);
    }

    flushMessageQueue() {
        if (this.messageQueue.length === 0) {
            return;
        }

        console.log(`发送队列中的 ${this.messageQueue.length} 条消息...`);

        const now = Date.now();
        let sent = 0;

        while (this.messageQueue.length > 0) {
            const message = this.messageQueue[0];

            // 检查消息是否过期
            if (now - message.timestamp > this.messageExpiry) {
                console.warn('消息已过期, 跳过');
                this.messageQueue.shift();
                continue;
            }

            // 发送消息
            try {
                this.ws.send(message.data);
                this.stats.messagesSent++;
                this.messageQueue.shift();
                sent++;

            } catch (error) {
                console.error('发送队列消息失败:', error);
                break;
            }
        }

        console.log(`已发送 ${sent} 条队列消息, 剩余 ${this.messageQueue.length} 条`);
    }

    // ========== 状态管理 ==========

    updateState(newState) {
        const oldState = this.connectionState;
        this.connectionState = newState;

        console.log(`状态变化: ${oldState} → ${newState}`);

        this.emit('stateChange', {
            oldState: oldState,
            newState: newState,
            timestamp: Date.now()
        });
    }

    getState() {
        return {
            connectionState: this.connectionState,
            readyState: this.ws ? this.ws.readyState : null,
            reconnectAttempts: this.reconnectAttempts,
            queueLength: this.messageQueue.length,
            lastPongTime: this.lastPongTime,
            stats: this.stats
        };
    }

    // ========== 事件系统 ==========

    on(event, handler) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].push(handler);
        }
    }

    off(event, handler) {
        if (this.eventHandlers[event]) {
            const index = this.eventHandlers[event].indexOf(handler);
            if (index !== -1) {
                this.eventHandlers[event].splice(index, 1);
            }
        }
    }

    emit(event, data) {
        if (this.eventHandlers[event]) {
            this.eventHandlers[event].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`事件处理器错误 (${event}):`, error);
                }
            });
        }
    }

    // ========== 工具方法 ==========

    isConnected() {
        return this.connectionState === 'connected' &&
               this.ws &&
               this.ws.readyState === WebSocket.OPEN;
    }

    getStats() {
        return {
            ...this.stats,
            currentState: this.connectionState,
            queueLength: this.messageQueue.length,
            uptime: this.stats.lastConnectTime ? Date.now() - this.stats.lastConnectTime : 0
        };
    }
}
```

你创建了一个测试页面来验证所有功能:

```javascript
// 完整测试
const wsManager = new WebSocketManager('wss://api.example.com/chat', {
    maxReconnectAttempts: 5,
    reconnectDelay: 1000,
    maxReconnectDelay: 30000,
    heartbeatInterval: 30000,
    pongTimeout: 5000,
    maxQueueSize: 50
});

// 监听事件
wsManager.on('open', () => {
    console.log('[应用] 连接已建立');
    updateUI('connected');
});

wsManager.on('message', (event) => {
    console.log('[应用] 收到消息:', event.data);
    displayMessage(event.data);
});

wsManager.on('close', (event) => {
    console.log('[应用] 连接已关闭');
    updateUI('disconnected');
});

wsManager.on('error', (event) => {
    console.error('[应用] 连接错误');
});

wsManager.on('reconnect', (info) => {
    console.log(`[应用] 正在重连 (${info.attempt}/${info.maxAttempts})...`);
    updateUI('reconnecting');
});

wsManager.on('stateChange', (event) => {
    console.log(`[应用] 状态变化: ${event.oldState} → ${event.newState}`);
});

// 连接
wsManager.connect();

// 发送消息
function sendMessage(text) {
    const message = {
        type: 'chat',
        content: text,
        timestamp: Date.now()
    };

    wsManager.send(message);
}

// 查看状态
function checkStatus() {
    const state = wsManager.getState();
    console.log('当前状态:', state);

    const stats = wsManager.getStats();
    console.log('统计信息:', stats);
}

// 断开连接
function disconnect() {
    wsManager.disconnect();
}
```

---

## 实战应用场景

你开始思考 WebSocket 的实际应用场景。

### 场景 1: 实时聊天

```javascript
// 聊天应用
class ChatClient {
    constructor(userId, userName) {
        this.userId = userId;
        this.userName = userName;

        // 创建 WebSocket 连接
        this.ws = new WebSocketManager(`wss://api.example.com/chat?userId=${userId}`, {
            heartbeatInterval: 30000
        });

        // 监听消息
        this.ws.on('message', (event) => {
            this.handleMessage(event.data);
        });

        // 监听状态变化
        this.ws.on('stateChange', (event) => {
            this.updateConnectionStatus(event.newState);
        });

        this.ws.connect();
    }

    handleMessage(data) {
        switch (data.type) {
            case 'chat':
                // 显示聊天消息
                this.displayChatMessage(data);
                break;

            case 'user_joined':
                // 用户加入
                this.displaySystemMessage(`${data.userName} 加入了聊天室`);
                break;

            case 'user_left':
                // 用户离开
                this.displaySystemMessage(`${data.userName} 离开了聊天室`);
                break;

            case 'typing':
                // 正在输入提示
                this.showTypingIndicator(data.userId, data.userName);
                break;
        }
    }

    sendMessage(text) {
        this.ws.send({
            type: 'chat',
            userId: this.userId,
            userName: this.userName,
            content: text,
            timestamp: Date.now()
        });
    }

    sendTypingIndicator() {
        this.ws.send({
            type: 'typing',
            userId: this.userId,
            userName: this.userName
        });
    }

    displayChatMessage(data) {
        const messageElement = document.createElement('div');
        messageElement.className = 'chat-message';
        messageElement.innerHTML = `
            <span class="user-name">${data.userName}</span>:
            <span class="content">${data.content}</span>
            <span class="time">${new Date(data.timestamp).toLocaleTimeString()}</span>
        `;
        document.querySelector('#messages').appendChild(messageElement);
    }

    displaySystemMessage(text) {
        const messageElement = document.createElement('div');
        messageElement.className = 'system-message';
        messageElement.textContent = text;
        document.querySelector('#messages').appendChild(messageElement);
    }

    showTypingIndicator(userId, userName) {
        // 显示 "XXX 正在输入..." 提示
        // 3 秒后自动消失
    }

    updateConnectionStatus(state) {
        const statusElement = document.querySelector('#connection-status');
        statusElement.textContent = state;
        statusElement.className = `status-${state}`;
    }
}

// 使用
const chat = new ChatClient('user123', 'Alice');

// 发送消息
document.querySelector('#send-btn').addEventListener('click', () => {
    const input = document.querySelector('#message-input');
    chat.sendMessage(input.value);
    input.value = '';
});

// 输入时发送 typing 提示
let typingTimer;
document.querySelector('#message-input').addEventListener('input', () => {
    clearTimeout(typingTimer);
    chat.sendTypingIndicator();

    typingTimer = setTimeout(() => {
        // 停止输入 3 秒后不再发送 typing
    }, 3000);
});
```

### 场景 2: 实时通知

```javascript
// 通知系统
class NotificationClient {
    constructor(userId) {
        this.userId = userId;

        this.ws = new WebSocketManager(`wss://api.example.com/notifications?userId=${userId}`, {
            heartbeatInterval: 60000  // 通知系统心跳间隔可以长一些
        });

        this.ws.on('message', (event) => {
            this.handleNotification(event.data);
        });

        this.ws.connect();
    }

    handleNotification(data) {
        switch (data.type) {
            case 'order_update':
                this.showNotification('订单更新', data.message);
                break;

            case 'payment_success':
                this.showNotification('支付成功', data.message);
                break;

            case 'system_alert':
                this.showNotification('系统通知', data.message, 'warning');
                break;
        }
    }

    showNotification(title, message, level = 'info') {
        // 显示浏览器通知
        if (Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: '/icon.png'
            });
        }

        // 显示页面内通知
        const notification = document.createElement('div');
        notification.className = `notification notification-${level}`;
        notification.innerHTML = `
            <h4>${title}</h4>
            <p>${message}</p>
        `;
        document.body.appendChild(notification);

        // 5 秒后自动消失
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// 使用
const notifications = new NotificationClient('user123');
```

### 场景 3: 实时协作编辑

```javascript
// 协作编辑
class CollaborativeEditor {
    constructor(documentId, userId) {
        this.documentId = documentId;
        this.userId = userId;

        this.ws = new WebSocketManager(`wss://api.example.com/collab?docId=${documentId}&userId=${userId}`);

        this.editor = document.querySelector('#editor');
        this.cursors = new Map();  // 其他用户的光标位置

        // 监听消息
        this.ws.on('message', (event) => {
            this.handleMessage(event.data);
        });

        // 监听编辑器变化
        this.editor.addEventListener('input', () => {
            this.handleLocalEdit();
        });

        this.ws.connect();
    }

    handleMessage(data) {
        switch (data.type) {
            case 'edit':
                // 应用其他用户的编辑
                this.applyRemoteEdit(data);
                break;

            case 'cursor':
                // 更新其他用户的光标位置
                this.updateRemoteCursor(data.userId, data.position);
                break;

            case 'user_joined':
                this.showUserJoined(data.userId, data.userName);
                break;

            case 'user_left':
                this.showUserLeft(data.userId);
                break;
        }
    }

    handleLocalEdit() {
        // 获取编辑内容
        const content = this.editor.value;
        const cursorPosition = this.editor.selectionStart;

        // 发送编辑操作
        this.ws.send({
            type: 'edit',
            userId: this.userId,
            content: content,
            cursorPosition: cursorPosition,
            timestamp: Date.now()
        });
    }

    applyRemoteEdit(data) {
        // 保存当前光标位置
        const currentPosition = this.editor.selectionStart;

        // 应用编辑
        this.editor.value = data.content;

        // 恢复光标位置 (需要根据编辑内容调整)
        this.editor.selectionStart = currentPosition;
        this.editor.selectionEnd = currentPosition;
    }

    updateRemoteCursor(userId, position) {
        // 显示其他用户的光标 (通常用不同颜色)
        let cursor = this.cursors.get(userId);

        if (!cursor) {
            cursor = document.createElement('div');
            cursor.className = 'remote-cursor';
            document.body.appendChild(cursor);
            this.cursors.set(userId, cursor);
        }

        // 更新光标位置
        // (实际实现需要计算文本位置对应的屏幕坐标)
    }

    showUserJoined(userId, userName) {
        console.log(`${userName} 加入了协作编辑`);
    }

    showUserLeft(userId) {
        // 移除该用户的光标
        const cursor = this.cursors.get(userId);
        if (cursor) {
            cursor.remove();
            this.cursors.delete(userId);
        }
    }
}

// 使用
const editor = new CollaborativeEditor('doc-123', 'user-456');
```

---

## 知识档案: WebSocket 实时通信的八个核心机制

**规则 1: WebSocket 是全双工通信协议, 连接建立后双方可随时发送数据**

WebSocket 不同于 HTTP 的请求-响应模式, 连接建立后客户端和服务器都可以主动发送数据。

```javascript
// HTTP 模式: 必须先请求才能响应
fetch('/api/data')
    .then(response => response.json());

// WebSocket 模式: 服务器可以主动推送
const ws = new WebSocket('wss://api.example.com');

ws.addEventListener('open', () => {
    // 客户端主动发送
    ws.send('Hello');
});

ws.addEventListener('message', (event) => {
    // 服务器主动推送
    console.log('服务器推送:', event.data);
});
```

全双工通信的优势:
- **实时性**: 服务器有新数据时立即推送, 无需轮询
- **低延迟**: 消息直接传输, 没有 HTTP 请求头开销
- **高效**: 一次握手, 长期复用, 节省连接建立成本

WebSocket vs HTTP:

| 特性 | HTTP | WebSocket |
|------|------|-----------|
| 通信模式 | 单向 (请求-响应) | 双向 (全双工) |
| 连接持久性 | 短连接 (HTTP/1.1 Keep-Alive 有限) | 长连接 |
| 服务器推送 | 不支持 (除非用 HTTP/2 Server Push) | ✅ 原生支持 |
| 消息开销 | HTTP 头 (几百字节) | 帧头 (2-14 字节) |
| 实时性 | 需要轮询 | ✅ 即时推送 |

---

**规则 2: WebSocket 连接以 HTTP 握手开始, 然后升级为 WebSocket 协议**

WebSocket 使用 HTTP Upgrade 机制从 HTTP 升级到 WebSocket。

```javascript
// 客户端发起握手
GET /chat HTTP/1.1
Host: api.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Origin: https://example.com

// 服务器响应
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

握手流程:
1. **客户端发送 HTTP 请求**: 包含 `Upgrade: websocket` 头, 请求升级协议
2. **服务器验证**: 检查 `Sec-WebSocket-Key`, 计算 `Sec-WebSocket-Accept`
3. **返回 101 状态码**: `101 Switching Protocols` 表示协议切换成功
4. **连接升级**: 从 HTTP 升级为 WebSocket, 开始全双工通信

WebSocket URL:
- `ws://`: 非加密连接 (对应 HTTP)
- `wss://`: 加密连接 (对应 HTTPS, 生产环境必须用)

```javascript
// ✅ 生产环境: 使用加密连接
const ws = new WebSocket('wss://api.example.com/chat');

// ❌ 开发环境: 可以用非加密 (仅限本地测试)
const ws = new WebSocket('ws://localhost:8080/chat');
```

---

**规则 3: WebSocket 有 4 个连接状态, 通过 readyState 属性查询**

WebSocket 连接生命周期包含 4 个状态:

```javascript
// 4 种连接状态
WebSocket.CONNECTING  // 0 - 正在连接
WebSocket.OPEN        // 1 - 连接已建立, 可以通信
WebSocket.CLOSING     // 2 - 连接正在关闭
WebSocket.CLOSED      // 3 - 连接已关闭

// 查询当前状态
const ws = new WebSocket('wss://api.example.com');
console.log(ws.readyState);  // 0 (CONNECTING)

ws.addEventListener('open', () => {
    console.log(ws.readyState);  // 1 (OPEN)
});

ws.close();
console.log(ws.readyState);  // 2 (CLOSING)

ws.addEventListener('close', () => {
    console.log(ws.readyState);  // 3 (CLOSED)
});
```

状态转换规则:
- **CONNECTING → OPEN**: 握手成功
- **OPEN → CLOSING**: 调用 `close()` 方法
- **CLOSING → CLOSED**: 关闭完成
- **CONNECTING → CLOSED**: 连接失败 (跳过 OPEN)

发送消息前必须检查状态:

```javascript
// ✅ 正确: 检查状态
if (ws.readyState === WebSocket.OPEN) {
    ws.send('Hello');
} else {
    console.warn('连接未建立, 无法发送消息');
}

// ❌ 错误: 不检查状态直接发送
ws.send('Hello');  // 可能抛出 InvalidStateError
```

---

**规则 4: 断线后 WebSocket 不会自动重连, 需要手动实现重连逻辑**

原生 WebSocket API 不提供自动重连功能, 连接关闭后必须手动重新连接。

```javascript
// ❌ 原生 WebSocket: 断线后不会重连
const ws = new WebSocket('wss://api.example.com');

ws.addEventListener('close', () => {
    console.log('连接已关闭');
    // 什么也不做, 连接彻底断开
});

// ✅ 正确: 实现自动重连
class WebSocketWithReconnect {
    constructor(url, options = {}) {
        this.url = url;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectDelay = options.reconnectDelay || 1000;
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.addEventListener('close', () => {
            this.handleReconnect();
        });
    }

    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('重连失败: 已达到最大重连次数');
            return;
        }

        // 指数退避: 1s → 2s → 4s → 8s → 16s
        const delay = Math.min(
            this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
            30000  // 最大延迟 30 秒
        );

        // 添加随机抖动 (±25%)
        const jitter = delay * (0.75 + Math.random() * 0.5);

        console.log(`${jitter.toFixed(0)}ms 后重连 (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);

        this.reconnectAttempts++;

        setTimeout(() => {
            this.connect();
        }, jitter);
    }
}
```

重连策略最佳实践:
- **指数退避**: 避免服务器过载, 延迟逐渐增加
- **随机抖动**: 避免大量客户端同时重连 (雷鸣群效应)
- **最大延迟**: 设置上限 (如 30 秒), 避免无限增长
- **最大次数**: 达到上限后停止重连, 避免死循环

---

**规则 5: 心跳机制检测连接健康, 及时发现连接失效**

TCP 连接可能处于 "半开" 状态——连接未关闭, 但数据无法传输。`readyState` 仍然是 `OPEN`, 但实际上连接已失效。

```javascript
// ❌ 问题: 连接卡住但 readyState 仍为 OPEN
const ws = new WebSocket('wss://api.example.com');

ws.addEventListener('open', () => {
    console.log(ws.readyState);  // 1 (OPEN)

    // [网络卡住, 但 TCP 连接未断]

    setTimeout(() => {
        console.log(ws.readyState);  // 仍然是 1 (OPEN)
        // 但实际上无法通信
    }, 60000);
});
```

心跳机制解决方案:

```javascript
// ✅ 正确: 实现心跳检测
class WebSocketWithHeartbeat {
    constructor(url, options = {}) {
        this.url = url;
        this.heartbeatInterval = options.heartbeatInterval || 30000;  // 30 秒
        this.pongTimeout = options.pongTimeout || 5000;  // 5 秒超时
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.addEventListener('open', () => {
            this.startHeartbeat();
        });

        this.ws.addEventListener('message', (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'pong') {
                this.handlePong();
            }
        });
    }

    startHeartbeat() {
        // 定期发送 ping
        this.heartbeatTimer = setInterval(() => {
            this.sendPing();
        }, this.heartbeatInterval);
    }

    sendPing() {
        this.ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));

        // 等待 pong 响应
        this.pongTimer = setTimeout(() => {
            console.warn('心跳超时, 关闭连接');
            this.ws.close();  // 触发重连
        }, this.pongTimeout);
    }

    handlePong() {
        clearTimeout(this.pongTimer);
        console.log('心跳正常');
    }
}
```

心跳机制原理:
1. **定期发送 ping**: 每隔一定时间 (如 30 秒) 发送心跳消息
2. **等待 pong 响应**: 服务器收到 ping 后应返回 pong
3. **超时检测**: 如果在规定时间内 (如 5 秒) 未收到 pong, 认为连接失效
4. **主动关闭**: 关闭失效连接, 触发重连机制

---

**规则 6: 断线期间发送的消息需要缓存到队列, 重连后重发**

连接断开时, 调用 `send()` 会抛出异常。需要消息队列缓存断线期间的消息。

```javascript
// ❌ 问题: 断线期间消息丢失
const ws = new WebSocket('wss://api.example.com');

ws.send('Message 1');  // ✅ 成功

// [连接断开]

ws.send('Message 2');  // ❌ 抛出 InvalidStateError

// [重连成功]

ws.send('Message 3');  // ✅ 成功
// Message 2 丢失了!
```

消息队列解决方案:

```javascript
// ✅ 正确: 实现消息队列
class WebSocketWithQueue {
    constructor(url, options = {}) {
        this.url = url;
        this.messageQueue = [];
        this.maxQueueSize = options.maxQueueSize || 100;
        this.messageExpiry = options.messageExpiry || 5 * 60 * 1000;  // 5 分钟
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            // 连接正常, 直接发送
            this.ws.send(data);

        } else {
            // 连接断开, 加入队列
            if (this.messageQueue.length >= this.maxQueueSize) {
                console.warn('队列已满, 丢弃最旧的消息');
                this.messageQueue.shift();
            }

            this.messageQueue.push({
                data: data,
                timestamp: Date.now()
            });

            console.log(`消息已加入队列 (${this.messageQueue.length}/${this.maxQueueSize})`);
        }
    }

    flushQueue() {
        const now = Date.now();

        while (this.messageQueue.length > 0) {
            const message = this.messageQueue[0];

            // 检查消息是否过期
            if (now - message.timestamp > this.messageExpiry) {
                console.warn('消息已过期, 跳过');
                this.messageQueue.shift();
                continue;
            }

            // 发送消息
            try {
                this.ws.send(message.data);
                this.messageQueue.shift();
            } catch (error) {
                console.error('发送队列消息失败');
                break;
            }
        }
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.addEventListener('open', () => {
            // 连接建立后清空队列
            this.flushQueue();
        });
    }
}
```

消息队列策略:
- **队列大小限制**: 防止内存溢出 (如 100 条)
- **消息过期时间**: 过期消息不再发送 (如 5 分钟)
- **FIFO 顺序**: 先进先出, 保证消息顺序
- **重连后自动发送**: 连接建立后立即清空队列

---

**规则 7: WebSocket 支持文本和二进制数据, 需要正确处理数据类型**

WebSocket 可以发送文本 (UTF-8 字符串) 和二进制数据 (`ArrayBuffer` 或 `Blob`)。

```javascript
const ws = new WebSocket('wss://api.example.com');

ws.addEventListener('open', () => {
    // 发送文本消息
    ws.send('Hello Server');

    // 发送 JSON 数据
    ws.send(JSON.stringify({
        type: 'chat',
        message: 'Hello'
    }));

    // 发送二进制数据 (ArrayBuffer)
    const buffer = new ArrayBuffer(8);
    const view = new DataView(buffer);
    view.setInt32(0, 42);
    ws.send(buffer);

    // 发送二进制数据 (Blob)
    const blob = new Blob(['Binary data'], { type: 'application/octet-stream' });
    ws.send(blob);
});

// 接收消息
ws.addEventListener('message', (event) => {
    if (typeof event.data === 'string') {
        // 文本消息
        console.log('文本:', event.data);

        // 尝试解析 JSON
        try {
            const data = JSON.parse(event.data);
            console.log('JSON:', data);
        } catch (e) {
            // 不是 JSON, 纯文本
        }

    } else if (event.data instanceof ArrayBuffer) {
        // 二进制消息 (ArrayBuffer)
        console.log('ArrayBuffer:', event.data);

    } else if (event.data instanceof Blob) {
        // 二进制消息 (Blob)
        console.log('Blob:', event.data);

        // 读取 Blob 内容
        event.data.arrayBuffer().then(buffer => {
            console.log('Blob 内容:', buffer);
        });
    }
});
```

设置接收数据类型:

```javascript
// 设置接收二进制数据的格式
ws.binaryType = 'arraybuffer';  // 默认
// 或
ws.binaryType = 'blob';

ws.addEventListener('message', (event) => {
    if (ws.binaryType === 'arraybuffer') {
        // event.data 是 ArrayBuffer
    } else {
        // event.data 是 Blob
    }
});
```

数据类型处理最佳实践:
- **文本消息**: 使用 JSON 格式, 便于解析和扩展
- **二进制消息**: 根据场景选择 `ArrayBuffer` (性能优先) 或 `Blob` (大文件)
- **类型检测**: 接收消息时检查类型, 分别处理
- **编码一致性**: 文本消息统一使用 UTF-8 编码

---

**规则 8: WebSocket 连接关闭有状态码和原因, 需要根据不同情况处理**

WebSocket 关闭时会返回关闭码 (`code`) 和关闭原因 (`reason`)。

```javascript
const ws = new WebSocket('wss://api.example.com');

ws.addEventListener('close', (event) => {
    console.log('关闭码:', event.code);
    console.log('关闭原因:', event.reason);
    console.log('是否正常关闭:', event.wasClean);

    // 根据关闭码处理
    switch (event.code) {
        case 1000:
            console.log('正常关闭');
            break;

        case 1001:
            console.log('端点离开 (如关闭页面)');
            break;

        case 1006:
            console.log('连接异常关闭 (如网络断开)');
            // 应该重连
            break;

        case 1008:
            console.log('策略违规 (如认证失败)');
            // 不应该重连
            break;

        case 1009:
            console.log('消息过大');
            break;

        case 1011:
            console.log('服务器错误');
            // 应该重连
            break;

        default:
            console.log('其他错误:', event.code);
    }
});

// 主动关闭连接 (指定关闭码和原因)
ws.close(1000, 'User logout');
```

常见关闭码:

| 关闭码 | 含义 | 是否重连 |
|-------|------|---------|
| 1000 | 正常关闭 | ❌ 不需要 |
| 1001 | 端点离开 | ❌ 不需要 |
| 1002 | 协议错误 | ❌ 不需要 |
| 1003 | 不支持的数据类型 | ❌ 不需要 |
| 1006 | 连接异常关闭 | ✅ 应该重连 |
| 1007 | 数据格式错误 | ❌ 不需要 |
| 1008 | 策略违规 | ❌ 不需要 |
| 1009 | 消息过大 | ⚠️ 视情况 |
| 1011 | 服务器错误 | ✅ 应该重连 |
| 1015 | TLS 握手失败 | ✅ 应该重连 |

关闭处理策略:

```javascript
function shouldReconnect(code) {
    // 这些情况应该重连
    const reconnectCodes = [1006, 1011, 1012, 1013, 1014, 1015];
    return reconnectCodes.includes(code);
}

ws.addEventListener('close', (event) => {
    if (shouldReconnect(event.code)) {
        console.log('连接异常, 尝试重连...');
        reconnect();
    } else {
        console.log('正常关闭或不可恢复错误, 不重连');
    }
});
```

---

**事故档案编号**: NETWORK-2024-1955
**影响范围**: WebSocket 连接管理, 实时通信, 心跳机制, 自动重连, 消息队列
**根本原因**: 原生 WebSocket API 不提供自动重连、心跳检测、消息队列等生产环境必需功能, 需要完整的管理层封装
**学习成本**: 高 (需深入理解 WebSocket 协议、连接生命周期、网络异常处理、指数退避算法)

这是 JavaScript 世界第 155 次被记录的网络与数据事故。WebSocket 提供全双工实时通信, 连接建立后双方可随时发送数据。连接以 HTTP 握手开始, 然后升级为 WebSocket 协议。WebSocket 有 4 个连接状态 (CONNECTING, OPEN, CLOSING, CLOSED), 通过 `readyState` 属性查询。断线后不会自动重连, 需要手动实现重连逻辑, 使用指数退避和随机抖动避免服务器过载。心跳机制通过定期 ping-pong 检测连接健康, 及时发现连接失效。断线期间发送的消息需要缓存到队列, 重连后重发, 防止消息丢失。WebSocket 支持文本 (UTF-8) 和二进制数据 (ArrayBuffer, Blob), 需要正确处理数据类型。连接关闭有状态码和原因, 根据不同情况决定是否重连。理解 WebSocket 的完整生命周期管理、心跳机制、消息队列、错误恢复是构建可靠实时通信系统的基础。

---
