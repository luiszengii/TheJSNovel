《第 145 次记录: API 请求的突然失败 —— Fetch 的网络真相》

---

## 深夜告警

周日晚上十点二十三分，你的手机震动了。

这是生产环境监控系统发来的紧急告警："API 请求失败率突增至 45%，用户登录、支付、数据加载全部受影响。请立即处理。"

你从床上坐起来，打开笔记本。监控面板上的图表触目惊心——从晚上九点半开始，API 请求成功率从 99.8% 暴跌到 55%，而且还在持续下降。

"到底发生了什么？" 你快速查看错误日志，发现了大量相同的报错信息：

```
TypeError: Failed to fetch
Network request failed
Request timeout
```

你点开详细日志，发现所有失败的请求都来自前端应用，后端服务器状态正常。更诡异的是，这些失败请求没有任何规律——同一个用户，同一个接口，有时成功，有时失败。

"这不像是服务器宕机，" 你想，"更像是网络层面的问题。但为什么突然爆发？"

你查看了最近的部署记录。周五下午，你们上线了一个新功能——实时数据同步。前端使用 Fetch API 每 10 秒轮询一次服务器获取最新数据。

"难道是轮询导致的？" 你打开代码仓库，找到了那段代码：

```javascript
// 实时数据同步功能
function syncData() {
    fetch('/api/sync')
        .then(response => response.json())
        .then(data => {
            updateUI(data);
        });
}

// 每 10 秒同步一次
setInterval(syncData, 10000);
```

"代码看起来没问题啊，" 你困惑，"就是一个简单的 Fetch 请求。"

但用户投诉越来越多。Slack 上的客服频道已经炸开了，客服主管发来消息："现在有 500+ 用户无法正常使用，必须马上修复！"

"必须在一小时内找到根因，" 你深吸一口气，开始了这场深夜调试。

---

## 快速定位

晚上十点四十分，你开始系统地排查问题。

你首先在本地环境复现了实时同步功能。打开 Chrome DevTools 的 Network 面板，观察 Fetch 请求的行为。

第一次请求：成功，200 OK，响应时间 50ms。
第二次请求：成功，200 OK，响应时间 55ms。
第三次请求：失败，状态显示 "(failed)"，错误信息 "net::ERR_FAILED"。

"果然能复现，" 你说，"但为什么会失败？"

你点开失败请求的详细信息，发现 Timing 标签页显示请求在 "Stalled" 阶段就停止了，连 DNS 查询都没有开始。

"这说明请求连发送都没发送出去，" 你分析，"被浏览器拦截了？"

你又注意到一个诡异的现象：每次刷新页面后，前几个请求总是成功的，但随着时间推移，失败率越来越高。大约 30 秒后，几乎所有请求都会失败。

"30 秒...这个时间点很可疑，" 你想起了某个 HTTP 特性。

你打开浏览器的 "chrome://net-internals/#sockets" 页面，查看当前的网络连接状态。果然，你看到了大量处于 "TIME_WAIT" 状态的连接。

"连接没有被正确复用！" 你恍然大悟，"每次 Fetch 请求都创建了新的 TCP 连接，而连接关闭后会进入 TIME_WAIT 状态，大约持续 30-120 秒。短时间内创建太多连接，浏览器就会拒绝新的请求！"

但这还不能解释为什么失败率这么高。你继续深入调查。

---

## 根因分析

晚上十一点十分，你开始分析 Fetch API 的网络行为。

你写了一个测试脚本，模拟高频请求：

```javascript
async function testFetch() {
    const startTime = Date.now();
    const results = [];

    for (let i = 0; i < 100; i++) {
        try {
            const response = await fetch('/api/test');
            results.push({ index: i, status: 'success', time: Date.now() - startTime });
        } catch (error) {
            results.push({ index: i, status: 'failed', error: error.message, time: Date.now() - startTime });
        }
    }

    // 分析结果
    const successCount = results.filter(r => r.status === 'success').length;
    const failedCount = results.filter(r => r.status === 'failed').length;

    console.log(`成功: ${successCount}, 失败: ${failedCount}`);
    console.log('失败分布:', results.filter(r => r.status === 'failed'));
}

testFetch();
```

测试结果让你震惊：

```
成功: 52, 失败: 48
失败分布: [
  { index: 6, status: 'failed', error: 'Failed to fetch', time: 312 },
  { index: 7, status: 'failed', error: 'Failed to fetch', time: 315 },
  { index: 8, status: 'failed', error: 'Failed to fetch', time: 318 },
  ...
]
```

"100 个请求，失败了 48 个！" 你说，"这个失败率太高了。"

你又注意到，失败的请求集中在第 6-15 个、第 30-40 个、第 60-80 个。

"这个分布有规律，" 你分析，"每隔一段时间就会出现一波失败。"

你突然想到，Fetch API 默认使用 HTTP/1.1 协议，而 HTTP/1.1 有一个重要的限制——**同一域名下，浏览器最多同时维持 6 个 TCP 连接**（Chrome/Firefox 的限制）。

"所以当第 7 个请求到来时，浏览器无法创建新连接，只能等待前面的连接释放！" 你恍然，"但如果前面的连接因为某种原因没有正确关闭，新请求就会失败！"

你检查了原始代码，发现了一个致命问题：

```javascript
function syncData() {
    fetch('/api/sync')
        .then(response => response.json())  // ❌ 没有检查 response.ok
        .then(data => {
            updateUI(data);
        });  // ❌ 没有错误处理
}
```

"这段代码有三个严重问题，" 你列举：

1. **没有检查响应状态**：即使服务器返回 404 或 500，也会尝试 `response.json()`
2. **没有错误处理**：网络错误或 JSON 解析失败都会被忽略
3. **没有中止机制**：无法取消正在进行的请求

你又发现了第二个问题——生产环境的 API 响应时间大约 200-300ms，但轮询间隔只有 10 秒。这意味着在高峰期，多个用户同时发起请求，每个用户每 10 秒发一次，短时间内就会产生大量并发请求。

"假设有 1000 个在线用户，" 你计算，"每 10 秒就有 1000 个请求，平均每秒 100 个请求。如果每个请求需要 300ms，那就需要同时维持 30 个连接。但浏览器只允许 6 个！剩下的 24 个请求都会排队或失败！"

---

## 紧急修复

晚上十一点四十分，你开始编写修复方案。

你首先重写了 `syncData` 函数，添加了完整的错误处理：

```javascript
// ❌ 旧代码：没有错误处理
function syncDataOld() {
    fetch('/api/sync')
        .then(response => response.json())
        .then(data => {
            updateUI(data);
        });
}

// ✅ 新代码：完整的错误处理
async function syncDataNew() {
    try {
        const response = await fetch('/api/sync', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            // 添加超时控制
            signal: AbortSignal.timeout(5000)  // 5 秒超时
        });

        // 检查响应状态
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        updateUI(data);

    } catch (error) {
        // 区分错误类型
        if (error.name === 'AbortError') {
            console.warn('请求超时');
        } else if (error.message.includes('Failed to fetch')) {
            console.warn('网络错误');
        } else {
            console.error('同步失败:', error);
        }

        // 错误时不更新 UI，等待下次同步
    }
}
```

你又添加了请求去重机制，避免多个请求同时进行：

```javascript
class DataSync {
    constructor() {
        this.syncing = false;  // 同步状态标志
        this.lastSyncTime = 0;  // 上次同步时间
        this.minInterval = 10000;  // 最小同步间隔 10 秒
    }

    async sync() {
        // 如果正在同步，跳过
        if (this.syncing) {
            console.log('同步进行中，跳过本次请求');
            return;
        }

        // 如果距离上次同步时间太短，跳过
        const now = Date.now();
        if (now - this.lastSyncTime < this.minInterval) {
            console.log('同步间隔太短，跳过本次请求');
            return;
        }

        this.syncing = true;

        try {
            const response = await fetch('/api/sync', {
                signal: AbortSignal.timeout(5000)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            updateUI(data);

            this.lastSyncTime = Date.now();

        } catch (error) {
            console.error('同步失败:', error);
        } finally {
            this.syncing = false;  // 无论成功或失败，都重置状态
        }
    }

    // 启动定时同步
    start() {
        this.intervalId = setInterval(() => this.sync(), 10000);
    }

    // 停止同步
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
}

// 使用
const dataSync = new DataSync();
dataSync.start();

// 页面卸载时停止
window.addEventListener('beforeunload', () => {
    dataSync.stop();
});
```

你又优化了并发控制，使用连接池限制同时进行的请求数量：

```javascript
class FetchPool {
    constructor(maxConcurrent = 6) {
        this.maxConcurrent = maxConcurrent;
        this.running = 0;
        this.queue = [];
    }

    async fetch(url, options = {}) {
        // 如果达到并发上限，加入队列等待
        if (this.running >= this.maxConcurrent) {
            await new Promise(resolve => this.queue.push(resolve));
        }

        this.running++;

        try {
            const response = await fetch(url, options);
            return response;
        } finally {
            this.running--;

            // 处理队列中的下一个请求
            if (this.queue.length > 0) {
                const resolve = this.queue.shift();
                resolve();
            }
        }
    }
}

// 使用
const fetchPool = new FetchPool(6);  // 最多 6 个并发请求

async function syncData() {
    try {
        const response = await fetchPool.fetch('/api/sync', {
            signal: AbortSignal.timeout(5000)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        updateUI(data);

    } catch (error) {
        console.error('同步失败:', error);
    }
}
```

---

## 部署验证

凌晨十二点三十分，你将修复代码部署到生产环境。

部署前的状态：
- API 请求成功率：55%
- 平均响应时间：1.2 秒（包含大量超时）
- 用户投诉：500+ 条

部署后 5 分钟：
- API 请求成功率：95%
- 平均响应时间：200ms
- 新增投诉：0

部署后 30 分钟：
- API 请求成功率：99.7%（恢复正常水平）
- 平均响应时间：180ms
- 用户开始反馈"问题解决了"

"终于修复了，" 你长舒一口气。

你又监控了一个小时，确保问题彻底解决。监控面板显示，所有指标都恢复到了正常水平。

凌晨一点三十分，你给团队发了一封总结邮件：

```
主题：生产事故复盘 - Fetch API 请求失败

事故时间：周日 21:30 - 00:30 (3 小时)
影响范围：所有前端用户，API 请求成功率降至 55%
根本原因：
1. 高频轮询 (10 秒/次) + 多用户并发，超过浏览器连接限制
2. 没有错误处理，导致失败的请求堆积
3. 没有超时控制，慢请求占用连接过久
4. 没有请求去重，多个请求可能同时进行

修复措施：
1. 添加完整的错误处理和超时控制 (5 秒)
2. 实现请求去重，避免并发请求
3. 使用连接池限制并发数量 (6 个)
4. 添加最小同步间隔检查

经验教训：
- Fetch API 不是简单的 "发送请求"，需要考虑网络层面的限制
- 高频请求必须有并发控制和错误处理
- 生产环境的并发量远超开发环境，必须做压力测试
```

---

## 深度理解

第二天上午，你召集团队进行技术分享。

你在白板上写下了 Fetch API 的核心特性：

### Fetch API 的本质

**本质 1: Fetch 返回 Promise**

Fetch API 是基于 Promise 的异步 API，返回的 Promise 只会在**网络错误**时 reject。

```javascript
// Fetch 的 Promise 行为
fetch('/api/data')
    .then(response => {
        // ✓ 进入 then，即使是 404 或 500
        console.log('请求完成，状态码:', response.status);

        if (!response.ok) {
            // ❌ 必须手动检查 response.ok
            throw new Error('HTTP error: ' + response.status);
        }

        return response.json();
    })
    .catch(error => {
        // ✓ 只有网络错误会进入 catch
        // - TypeError: Failed to fetch (网络断开)
        // - AbortError (请求被中止)
        // - TimeoutError (超时)
        console.error('网络错误:', error);
    });
```

**本质 2: Response 对象是流式的**

Response.body 是一个 ReadableStream，只能读取一次。

```javascript
const response = await fetch('/api/data');

// 读取一次
const data1 = await response.json();

// ❌ 再次读取会失败
try {
    const data2 = await response.json();
} catch (error) {
    console.error('错误:', error.message);
    // TypeError: body stream already read
}
```

**本质 3: Fetch 没有内置超时机制**

必须使用 AbortController 或 AbortSignal.timeout 实现超时。

```javascript
// 方法 1: AbortController
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 5000);

try {
    const response = await fetch('/api/data', {
        signal: controller.signal
    });
    clearTimeout(timeoutId);
} catch (error) {
    if (error.name === 'AbortError') {
        console.log('请求超时');
    }
}

// 方法 2: AbortSignal.timeout (更简洁)
try {
    const response = await fetch('/api/data', {
        signal: AbortSignal.timeout(5000)
    });
} catch (error) {
    if (error.name === 'AbortError') {
        console.log('请求超时');
    }
}
```

**本质 4: Fetch 默认不发送 Cookies**

必须显式设置 `credentials` 选项。

```javascript
// ❌ 默认不发送 Cookies
fetch('/api/data');

// ✅ 同源请求发送 Cookies
fetch('/api/data', {
    credentials: 'same-origin'
});

// ✅ 跨域请求也发送 Cookies
fetch('https://api.example.com/data', {
    credentials: 'include'
});
```

**本质 5: Fetch 不支持上传进度**

无法监听请求体的上传进度（只能监听响应的下载进度）。

```javascript
// ❌ Fetch 无法监听上传进度
const response = await fetch('/api/upload', {
    method: 'POST',
    body: largeFile
});
// 没有办法知道上传进度

// ✅ 如果需要上传进度，使用 XMLHttpRequest
const xhr = new XMLHttpRequest();
xhr.upload.onprogress = (e) => {
    const percent = (e.loaded / e.total) * 100;
    console.log(`上传进度: ${percent}%`);
};
xhr.open('POST', '/api/upload');
xhr.send(largeFile);
```

---

## 最佳实践

你整理了一套 Fetch API 的最佳实践：

**实践 1: 封装通用的 Fetch 函数**

```javascript
async function fetchWithTimeout(url, options = {}) {
    // 默认超时 10 秒
    const timeout = options.timeout || 10000;

    // 创建超时控制器
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    // 合并 signal
    const signal = options.signal
        ? AbortSignal.any([options.signal, controller.signal])
        : controller.signal;

    try {
        const response = await fetch(url, {
            ...options,
            signal
        });

        clearTimeout(timeoutId);

        // 检查响应状态
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response;

    } catch (error) {
        clearTimeout(timeoutId);

        // 统一错误处理
        if (error.name === 'AbortError') {
            throw new Error('请求超时');
        } else if (error.message.includes('Failed to fetch')) {
            throw new Error('网络连接失败');
        } else {
            throw error;
        }
    }
}

// 使用
try {
    const response = await fetchWithTimeout('/api/data', {
        timeout: 5000
    });
    const data = await response.json();
} catch (error) {
    console.error(error.message);
}
```

**实践 2: 实现请求重试机制**

```javascript
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
    let lastError;

    for (let i = 0; i < maxRetries; i++) {
        try {
            const response = await fetchWithTimeout(url, options);
            return response;

        } catch (error) {
            lastError = error;

            // 如果是客户端错误 (4xx)，不重试
            if (error.message.includes('HTTP error! status: 4')) {
                throw error;
            }

            // 如果不是最后一次，等待后重试
            if (i < maxRetries - 1) {
                const delay = Math.pow(2, i) * 1000;  // 指数退避: 1s, 2s, 4s
                console.log(`请求失败，${delay}ms 后重试 (${i + 1}/${maxRetries})`);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }

    throw lastError;
}

// 使用
try {
    const response = await fetchWithRetry('/api/data', {}, 3);
    const data = await response.json();
} catch (error) {
    console.error('重试 3 次后仍然失败:', error);
}
```

**实践 3: 实现请求缓存**

```javascript
class FetchCache {
    constructor(maxAge = 60000) {  // 默认缓存 60 秒
        this.cache = new Map();
        this.maxAge = maxAge;
    }

    async fetch(url, options = {}) {
        // 只缓存 GET 请求
        if (options.method && options.method !== 'GET') {
            return fetch(url, options);
        }

        const cacheKey = url + JSON.stringify(options);
        const cached = this.cache.get(cacheKey);

        // 检查缓存是否有效
        if (cached && Date.now() - cached.timestamp < this.maxAge) {
            console.log('使用缓存:', url);
            return cached.response.clone();  // 克隆 Response
        }

        // 发起新请求
        const response = await fetch(url, options);

        // 只缓存成功的响应
        if (response.ok) {
            this.cache.set(cacheKey, {
                response: response.clone(),  // 克隆 Response
                timestamp: Date.now()
            });
        }

        return response;
    }

    clear() {
        this.cache.clear();
    }
}

// 使用
const fetchCache = new FetchCache(60000);  // 缓存 60 秒

const response = await fetchCache.fetch('/api/data');
const data = await response.json();
```

**实践 4: 实现并发控制**

```javascript
class ConcurrentFetch {
    constructor(maxConcurrent = 6) {
        this.maxConcurrent = maxConcurrent;
        this.running = 0;
        this.queue = [];
    }

    async fetch(url, options = {}) {
        // 等待槽位
        while (this.running >= this.maxConcurrent) {
            await new Promise(resolve => this.queue.push(resolve));
        }

        this.running++;

        try {
            const response = await fetch(url, options);
            return response;

        } finally {
            this.running--;

            // 释放下一个等待的请求
            if (this.queue.length > 0) {
                const resolve = this.queue.shift();
                resolve();
            }
        }
    }
}

// 使用
const concurrentFetch = new ConcurrentFetch(6);

// 发起 100 个请求，但同时最多 6 个
const promises = [];
for (let i = 0; i < 100; i++) {
    promises.push(
        concurrentFetch.fetch(`/api/data/${i}`)
            .then(r => r.json())
    );
}

const results = await Promise.all(promises);
```

**实践 5: 完整的请求封装**

```javascript
class ApiClient {
    constructor(baseURL = '', options = {}) {
        this.baseURL = baseURL;
        this.defaultOptions = {
            timeout: 10000,
            maxRetries: 3,
            cacheMaxAge: 60000,
            maxConcurrent: 6,
            ...options
        };

        this.cache = new FetchCache(this.defaultOptions.cacheMaxAge);
        this.concurrent = new ConcurrentFetch(this.defaultOptions.maxConcurrent);
    }

    async request(url, options = {}) {
        const fullURL = this.baseURL + url;
        const mergedOptions = {
            ...this.defaultOptions,
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...this.defaultOptions.headers,
                ...options.headers
            }
        };

        // 应用并发控制
        const response = await this.concurrent.fetch(fullURL, mergedOptions);

        // 应用缓存
        // const response = await this.cache.fetch(fullURL, mergedOptions);

        // 应用重试
        // const response = await fetchWithRetry(fullURL, mergedOptions, this.defaultOptions.maxRetries);

        // 应用超时
        // const response = await fetchWithTimeout(fullURL, mergedOptions);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response;
    }

    async get(url, options = {}) {
        return this.request(url, { ...options, method: 'GET' });
    }

    async post(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(url, data, options = {}) {
        return this.request(url, {
            ...options,
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(url, options = {}) {
        return this.request(url, { ...options, method: 'DELETE' });
    }
}

// 使用
const api = new ApiClient('https://api.example.com');

try {
    const response = await api.get('/users');
    const users = await response.json();

    await api.post('/users', { name: 'Alice', email: 'alice@example.com' });

    await api.put('/users/1', { name: 'Alice Updated' });

    await api.delete('/users/1');

} catch (error) {
    console.error('API 请求失败:', error);
}
```

---

## 知识总结

**规则 1: Fetch 返回的 Promise 特殊行为**

Fetch 返回的 Promise 只在**网络错误**时 reject，HTTP 错误状态码 (如 404, 500) 不会导致 reject。

```javascript
// Fetch 的 Promise 行为
try {
    const response = await fetch('/api/not-found');

    // ✓ 即使是 404，也会进入这里
    console.log('Status:', response.status);  // 404

    if (!response.ok) {
        // ❌ 必须手动检查并抛出错误
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

} catch (error) {
    // ✓ 只有这些情况会进入 catch:
    // 1. 网络错误 (TypeError: Failed to fetch)
    // 2. 请求被中止 (AbortError)
    // 3. 手动抛出的错误 (如上面的 HTTP error)
    console.error(error);
}
```

关键点：
- **resolve**: 只要收到 HTTP 响应（无论状态码），Promise 就会 resolve
- **reject**: 只有网络层面的错误（无法连接、请求被中止）才会 reject
- **必须检查 response.ok**: 判断 HTTP 状态码是否为 200-299

---

**规则 2: Response 对象的流式特性**

Response.body 是 ReadableStream，只能读取一次。

```javascript
const response = await fetch('/api/data');

// 读取方法 1: response.json() (读取并解析 JSON)
const data1 = await response.json();

// ❌ 再次读取会失败
try {
    const data2 = await response.json();
} catch (error) {
    console.error(error.message);
    // TypeError: body stream already read
}

// ✅ 如果需要多次读取，使用 response.clone()
const response = await fetch('/api/data');
const clone = response.clone();

const data1 = await response.json();  // 读取原始 response
const data2 = await clone.json();  // 读取克隆的 response
```

读取 Response 的方法：
- **response.json()**: 解析为 JSON 对象
- **response.text()**: 读取为文本字符串
- **response.blob()**: 读取为 Blob 对象
- **response.arrayBuffer()**: 读取为 ArrayBuffer
- **response.formData()**: 读取为 FormData

注意：
- 所有读取方法都返回 Promise
- 只能调用一次，第二次会抛出错误
- 如果需要多次读取，使用 `response.clone()`

---

**规则 3: Fetch 的超时控制**

Fetch API 没有内置超时机制，必须使用 AbortSignal。

```javascript
// 方法 1: 使用 AbortController (手动控制)
const controller = new AbortController();
const timeoutId = setTimeout(() => {
    controller.abort();  // 超时后中止请求
}, 5000);

try {
    const response = await fetch('/api/data', {
        signal: controller.signal
    });
    clearTimeout(timeoutId);

    const data = await response.json();

} catch (error) {
    clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
        console.log('请求超时');
    } else {
        console.error('请求失败:', error);
    }
}

// 方法 2: 使用 AbortSignal.timeout (更简洁)
try {
    const response = await fetch('/api/data', {
        signal: AbortSignal.timeout(5000)  // 5 秒超时
    });

    const data = await response.json();

} catch (error) {
    if (error.name === 'AbortError' || error.name === 'TimeoutError') {
        console.log('请求超时');
    } else {
        console.error('请求失败:', error);
    }
}

// 方法 3: 组合多个 AbortSignal
const userController = new AbortController();
const timeoutSignal = AbortSignal.timeout(5000);

const combinedSignal = AbortSignal.any([
    userController.signal,
    timeoutSignal
]);

try {
    const response = await fetch('/api/data', {
        signal: combinedSignal
    });
} catch (error) {
    // 可能是用户中止，也可能是超时
}

// 用户主动中止
document.querySelector('#cancel').onclick = () => {
    userController.abort();
};
```

---

**规则 4: Fetch 的 Credentials 选项**

Fetch 默认不发送 Cookies，需要显式设置 `credentials` 选项。

```javascript
// 选项 1: 'omit' - 从不发送 Cookies (默认行为)
fetch('/api/data', {
    credentials: 'omit'
});

// 选项 2: 'same-origin' - 同源请求发送 Cookies
fetch('/api/data', {
    credentials: 'same-origin'  // 常用
});

// 选项 3: 'include' - 跨域请求也发送 Cookies
fetch('https://api.example.com/data', {
    credentials: 'include',
    mode: 'cors'  // 跨域请求需要 CORS
});
```

注意：
- 如果服务器需要 Cookie 认证，必须设置 `credentials: 'same-origin'` 或 `'include'`
- 跨域请求使用 `credentials: 'include'` 时，服务器必须返回 `Access-Control-Allow-Credentials: true`

---

**规则 5: Fetch 的请求模式 (mode)**

Fetch 的 `mode` 选项控制跨域行为。

```javascript
// 模式 1: 'cors' - 允许跨域 (默认)
fetch('https://api.example.com/data', {
    mode: 'cors',  // 必须服务器支持 CORS
    credentials: 'include'
});

// 模式 2: 'no-cors' - 不透明响应 (opaque response)
// 只能用于简单请求，无法读取响应内容
const response = await fetch('https://api.example.com/data', {
    mode: 'no-cors'
});
console.log(response.status);  // 0 (无法读取)
console.log(response.ok);  // false

// 模式 3: 'same-origin' - 只允许同源请求
fetch('/api/data', {
    mode: 'same-origin'  // 跨域请求会直接失败
});

// 模式 4: 'navigate' - 用于页面导航 (很少使用)
```

选择原则：
- **同源请求**: 使用 `same-origin` (更安全)
- **跨域 API**: 使用 `cors` (默认)
- **跨域资源** (如图片): 使用 `no-cors` (但无法读取内容)

---

**规则 6: Fetch 的并发限制**

浏览器对同一域名的并发连接数有限制 (HTTP/1.1: 6 个, HTTP/2: 更多)。

```javascript
// ❌ 问题：100 个并发请求
const promises = [];
for (let i = 0; i < 100; i++) {
    promises.push(fetch(`/api/data/${i}`));
}
await Promise.all(promises);  // 可能导致部分请求失败

// ✅ 解决方案 1: 控制并发数量
async function fetchWithLimit(urls, limit = 6) {
    const results = [];
    const executing = [];

    for (const url of urls) {
        const promise = fetch(url).then(r => r.json());
        results.push(promise);

        if (limit <= urls.length) {
            const e = promise.then(() => {
                executing.splice(executing.indexOf(e), 1);
            });
            executing.push(e);

            if (executing.length >= limit) {
                await Promise.race(executing);
            }
        }
    }

    return Promise.all(results);
}

const urls = Array.from({ length: 100 }, (_, i) => `/api/data/${i}`);
const data = await fetchWithLimit(urls, 6);

// ✅ 解决方案 2: 使用队列
class RequestQueue {
    constructor(maxConcurrent = 6) {
        this.maxConcurrent = maxConcurrent;
        this.running = 0;
        this.queue = [];
    }

    async add(url, options) {
        while (this.running >= this.maxConcurrent) {
            await new Promise(resolve => this.queue.push(resolve));
        }

        this.running++;

        try {
            return await fetch(url, options);
        } finally {
            this.running--;
            const next = this.queue.shift();
            if (next) next();
        }
    }
}
```

---

**规则 7: Fetch 的错误处理最佳实践**

完整的错误处理应该区分不同类型的错误。

```javascript
async function safeFetch(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            signal: AbortSignal.timeout(10000)  // 10 秒超时
        });

        // 检查 HTTP 状态
        if (!response.ok) {
            const error = new Error(`HTTP error! status: ${response.status}`);
            error.response = response;
            error.status = response.status;

            // 区分客户端错误和服务器错误
            if (response.status >= 400 && response.status < 500) {
                error.type = 'client_error';  // 4xx: 客户端错误
            } else if (response.status >= 500) {
                error.type = 'server_error';  // 5xx: 服务器错误
            }

            throw error;
        }

        return response;

    } catch (error) {
        // 区分错误类型
        if (error.name === 'AbortError' || error.name === 'TimeoutError') {
            error.type = 'timeout';
            console.error('请求超时:', url);

        } else if (error.message.includes('Failed to fetch')) {
            error.type = 'network';
            console.error('网络错误:', url);

        } else if (error.type === 'client_error') {
            console.error('客户端错误:', error.status, url);

        } else if (error.type === 'server_error') {
            console.error('服务器错误:', error.status, url);

        } else {
            console.error('未知错误:', error);
        }

        throw error;
    }
}

// 使用
try {
    const response = await safeFetch('/api/data');
    const data = await response.json();

} catch (error) {
    switch (error.type) {
        case 'timeout':
            showMessage('请求超时，请稍后重试');
            break;
        case 'network':
            showMessage('网络连接失败，请检查网络');
            break;
        case 'client_error':
            showMessage('请求错误: ' + error.status);
            break;
        case 'server_error':
            showMessage('服务器错误，请联系管理员');
            break;
        default:
            showMessage('未知错误');
    }
}
```

---

**规则 8: Fetch 与 XMLHttpRequest 的选择**

Fetch 是现代 API，但某些场景仍需 XMLHttpRequest。

```javascript
// Fetch 的优势
// ✓ 基于 Promise，代码更简洁
// ✓ 支持 Request/Response 对象
// ✓ 支持 Service Worker
// ✓ 更现代的 API 设计

// Fetch 的不足
// ✗ 无法监听上传进度
// ✗ 无法中止已发送的请求体
// ✗ 无法设置请求超时 (需要 AbortSignal)
// ✗ 默认不发送 Cookies

// XMLHttpRequest 的优势
// ✓ 支持上传进度监听
// ✓ 支持请求超时设置
// ✓ 更好的浏览器兼容性
// ✓ 默认发送 Cookies

// 选择原则
// - 普通 GET/POST 请求 → Fetch
// - 需要上传进度 → XMLHttpRequest
// - 需要下载进度 → Fetch (支持)
// - Service Worker → Fetch (必须)
// - 旧浏览器兼容 → XMLHttpRequest

// 上传进度示例 (必须用 XMLHttpRequest)
function uploadWithProgress(file, onProgress) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                onProgress(percent);
            }
        };

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(new Error(`HTTP ${xhr.status}`));
            }
        };

        xhr.onerror = () => reject(new Error('Network error'));

        xhr.open('POST', '/api/upload');
        xhr.send(file);
    });
}

// 使用
await uploadWithProgress(file, (percent) => {
    console.log(`上传进度: ${percent}%`);
});
```

---

**事故档案编号**: NETWORK-2024-1945
**影响范围**: Fetch API, HTTP 并发限制, 网络请求, 高频轮询
**根本原因**: 高频请求 + 无错误处理 + 无超时控制 + 无并发限制，超过浏览器连接数限制
**学习成本**: 中 (需理解 HTTP 协议和浏览器网络层限制)

这是 JavaScript 世界第 145 次被记录的网络与数据事故。Fetch API 是基于 Promise 的现代网络请求 API，但它的 Promise 只在**网络错误**时 reject，HTTP 错误状态码 (404, 500) 不会导致 reject，必须手动检查 `response.ok`。Response 对象是流式的，body 只能读取一次，第二次会报错。Fetch 没有内置超时机制，必须使用 `AbortSignal.timeout()` 实现超时控制。浏览器对同一域名的并发连接数有限制 (HTTP/1.1: 6 个)，高频请求必须实现并发控制，否则会导致请求失败。Fetch 默认不发送 Cookies，需要设置 `credentials: 'same-origin'`。完整的 Fetch 使用必须包含：错误处理、超时控制、重试机制、并发限制、请求去重。理解 Fetch 的异步特性和浏览器网络层限制是避免生产事故的关键。

---
