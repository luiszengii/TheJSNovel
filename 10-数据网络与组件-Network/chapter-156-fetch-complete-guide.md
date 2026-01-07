《第 156 次记录: 周六上午的深度学习 —— Fetch API 完整指南》

---

## 咖啡厅的研究计划

周六上午十点, 你坐在常去的咖啡厅里, 打开笔记本。

窗外阳光正好, 咖啡的香气混合着轻柔的音乐。这是你最喜欢的学习时光——没有工作压力, 没有紧急任务, 可以完全沉浸在技术探索中。

上周在公司重构网络请求模块时, 你意识到虽然每天都在用 Fetch API, 但对它的理解还停留在表面。`fetch()` 看起来简单, 但当你需要处理复杂场景时——上传进度、请求取消、超时控制、CORS 问题——你总是要查文档或 Stack Overflow。

"是时候系统地学习一遍了, " 你在笔记本上写下标题: "Fetch API 深度研究"。

你列出了想要搞清楚的问题:

```
研究清单:
1. Fetch 的设计哲学是什么? 为什么要替代 XMLHttpRequest?
2. Request 和 Response 对象到底是什么?
3. Headers API 如何正确使用?
4. 各种 fetch 选项 (mode, credentials, cache) 的实际作用?
5. 如何处理流式响应?
6. CORS 跨域问题的本质是什么?
7. 错误处理的最佳实践?
8. 如何实现超时和取消?
```

你点开 MDN 文档, 新建了一个 `fetch-research.html` 测试文件, 开始系统地研究每一个问题。

---

## 基础概念的重新理解

你从最简单的例子开始:

```javascript
// 最简单的 GET 请求
fetch('https://api.github.com/users/github')
    .then(response => response.json())
    .then(data => console.log(data));
```

"看起来很简单, " 你喃喃自语, "但这背后发生了什么?"

你在笔记中记录:

```
Fetch 的第一个返回值是什么?
- 不是数据, 而是 Response 对象
- Response 是一个"响应的抽象", 包含状态、头部、主体流

为什么要分两步 .then()?
- 第一步: 等待 HTTP 响应头到达 (网络层面的响应)
- 第二步: 等待响应体解析完成 (数据层面的处理)
```

你写了一个更详细的版本来验证理解:

```javascript
// 详细版本: 观察 Fetch 的两阶段特性
async function detailedFetch(url) {
    console.log('1. 发起请求...');

    const response = await fetch(url);
    console.log('2. 收到响应头:');
    console.log('   - 状态码:', response.status);
    console.log('   - 状态文本:', response.statusText);
    console.log('   - Content-Type:', response.headers.get('Content-Type'));
    console.log('   - 响应体可读:', response.bodyUsed === false);

    console.log('3. 开始解析响应体...');
    const data = await response.json();
    console.log('4. 响应体解析完成:', data);
    console.log('   - 响应体已消费:', response.bodyUsed === true);

    return data;
}
```

测试结果让你豁然开朗:

```
1. 发起请求...
2. 收到响应头:
   - 状态码: 200
   - 状态文本: OK
   - Content-Type: application/json; charset=utf-8
   - 响应体可读: true
3. 开始解析响应体...
4. 响应体解析完成: { login: 'github', id: 9919, ... }
   - 响应体已消费: true
```

"原来 Response 对象是一次性的, " 你在笔记中标注, "`response.json()` 消费了响应体流, 之后就不能再读取了。"

你立刻验证这个发现:

```javascript
// 验证: 响应体只能读取一次
async function testBodyConsumption() {
    const response = await fetch('https://api.github.com/zen');

    const text1 = await response.text();
    console.log('第一次读取:', text1);

    try {
        const text2 = await response.text();
        console.log('第二次读取:', text2);
    } catch (error) {
        console.error('❌ 错误:', error.message);
        // TypeError: body stream already read
    }
}
```

"这解释了为什么有时候调用 `response.json()` 会报错, " 你恍然大悟, "因为在某个地方已经消费过响应体了。"

---

## Request 对象的深度探索

你继续研究 Request 对象。大部分时候你直接用字符串 URL 调用 `fetch()`, 但你好奇 Request 对象能做什么。

```javascript
// 创建 Request 对象
const request = new Request('https://api.example.com/data', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer token123'
    },
    body: JSON.stringify({ name: 'Alice', age: 25 })
});

// 检查 Request 对象的属性
console.log('URL:', request.url);
console.log('Method:', request.method);
console.log('Headers:', [...request.headers.entries()]);
console.log('Body Used:', request.bodyUsed);

// 使用 Request 对象发起请求
fetch(request)
    .then(response => response.json())
    .then(data => console.log(data));
```

"Request 对象可以预先构建请求配置, " 你在笔记中记录, "这在需要复用请求或拦截修改请求时很有用。"

你想到一个实际场景——给所有 API 请求添加认证 token:

```javascript
// 场景: 封装带认证的请求
class AuthAPI {
    constructor(baseURL, token) {
        this.baseURL = baseURL;
        this.token = token;
    }

    // 创建带认证头的 Request
    createRequest(path, options = {}) {
        const url = `${this.baseURL}${path}`;

        const headers = new Headers(options.headers || {});
        headers.set('Authorization', `Bearer ${this.token}`);
        headers.set('Content-Type', 'application/json');

        return new Request(url, {
            ...options,
            headers: headers
        });
    }

    // GET 请求
    async get(path) {
        const request = this.createRequest(path, { method: 'GET' });
        const response = await fetch(request);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return response.json();
    }

    // POST 请求
    async post(path, body) {
        const request = this.createRequest(path, {
            method: 'POST',
            body: JSON.stringify(body)
        });

        const response = await fetch(request);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
    }
}

// 使用
const api = new AuthAPI('https://api.example.com', 'your-token');
const users = await api.get('/users');
const newUser = await api.post('/users', { name: 'Bob' });
```

你测试了这个封装, 感觉很满意。"Request 对象让请求配置更加结构化, " 你总结道。

---

## Headers API 的精细控制

接下来你研究 Headers API。你发现它比直接用对象要强大得多。

```javascript
// 创建 Headers 对象
const headers = new Headers();

// 添加头部
headers.append('Content-Type', 'application/json');
headers.append('X-Custom-Header', 'value1');

// 可以添加相同名称的多个值
headers.append('X-Custom-Header', 'value2');

// 检查头部
console.log('Has Content-Type:', headers.has('Content-Type'));
console.log('Get Content-Type:', headers.get('Content-Type'));
console.log('Get X-Custom-Header:', headers.get('X-Custom-Header'));
// → "value1, value2" (逗号分隔的合并值)

// 遍历所有头部
for (const [key, value] of headers.entries()) {
    console.log(`${key}: ${value}`);
}

// 删除头部
headers.delete('X-Custom-Header');

// 设置头部 (覆盖已存在的值)
headers.set('Authorization', 'Bearer new-token');
```

你注意到一个重要细节:

```javascript
// append vs set 的区别
const headers1 = new Headers();
headers1.append('X-Tag', 'tag1');
headers1.append('X-Tag', 'tag2');
console.log(headers1.get('X-Tag'));  // "tag1, tag2"

const headers2 = new Headers();
headers2.set('X-Tag', 'tag1');
headers2.set('X-Tag', 'tag2');
console.log(headers2.get('X-Tag'));  // "tag2" (覆盖)
```

"原来 `append` 会合并相同名称的值, 而 `set` 会覆盖, " 你在笔记中强调。

然后你发现 Headers 的 Guard 机制:

```javascript
// Guard 机制: 某些头部在特定上下文中不可修改
async function testHeaderGuard() {
    const response = await fetch('https://api.github.com/zen');

    // Response 的 headers 是只读的 (guard: 'response')
    try {
        response.headers.set('X-Custom', 'value');
    } catch (error) {
        console.error('❌ 无法修改响应头:', error.message);
        // TypeError: Headers are immutable
    }

    // 可以创建新的 Headers 对象来修改
    const newHeaders = new Headers(response.headers);
    newHeaders.set('X-Custom', 'value');
    console.log('✅ 新 Headers 对象可修改');
}
```

"这是个安全机制, " 你理解了, "防止修改已经发送或接收的请求/响应头。"

---

## Fetch 选项的完整探索

你决定系统地测试所有 fetch 选项。你创建了一个测试表:

```javascript
// 完整的 fetch 选项
const options = {
    // 1. 请求方法
    method: 'POST',  // GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS

    // 2. 请求头
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer token'
    },

    // 3. 请求体
    body: JSON.stringify({ data: 'value' }),  // 字符串、FormData、Blob、ArrayBuffer

    // 4. 请求模式
    mode: 'cors',  // cors, no-cors, same-origin, navigate

    // 5. 凭证 (Cookie)
    credentials: 'same-origin',  // omit, same-origin, include

    // 6. 缓存策略
    cache: 'default',  // default, no-store, reload, no-cache, force-cache, only-if-cached

    // 7. 重定向策略
    redirect: 'follow',  // follow, error, manual

    // 8. Referrer 策略
    referrer: '',
    referrerPolicy: 'no-referrer',

    // 9. 完整性校验
    integrity: '',  // Subresource Integrity

    // 10. Keepalive (页面卸载后仍保持请求)
    keepalive: false,

    // 11. 中止信号
    signal: null  // AbortSignal
};
```

你开始逐个测试关键选项。

**测试 1: mode 选项**

```javascript
// mode: 'cors' - 默认, 允许跨域请求
async function testCorsMode() {
    try {
        const response = await fetch('https://api.github.com/zen', {
            mode: 'cors'
        });
        console.log('CORS mode:', await response.text());
    } catch (error) {
        console.error('CORS 失败:', error);
    }
}

// mode: 'no-cors' - 跨域请求但不读取响应
async function testNoCorsMode() {
    const response = await fetch('https://api.github.com/zen', {
        mode: 'no-cors'
    });

    console.log('No-CORS mode:');
    console.log('- Type:', response.type);  // 'opaque'
    console.log('- Status:', response.status);  // 0
    console.log('- Body:', await response.text());  // '' (空字符串)
}

// mode: 'same-origin' - 仅同源请求
async function testSameOriginMode() {
    try {
        const response = await fetch('https://api.github.com/zen', {
            mode: 'same-origin'
        });
    } catch (error) {
        console.error('Same-origin mode 失败:', error.message);
        // TypeError: Failed to fetch
    }
}
```

你运行测试后理解了:

```
mode 选项的作用:
- cors: 默认模式, 允许跨域, 可以读取响应
- no-cors: 跨域但响应不透明, 主要用于 Service Worker 缓存
- same-origin: 强制同源, 跨域会报错
- navigate: 用于导航请求 (浏览器内部使用)
```

**测试 2: credentials 选项**

```javascript
// credentials: 控制是否发送 Cookie
async function testCredentials() {
    // 'omit': 不发送 Cookie
    await fetch('/api/data', { credentials: 'omit' });

    // 'same-origin': 同源时发送 Cookie (默认)
    await fetch('/api/data', { credentials: 'same-origin' });

    // 'include': 始终发送 Cookie (包括跨域)
    await fetch('https://api.example.com/data', {
        credentials: 'include'
    });
}
```

"这解释了为什么有时候跨域请求不带 Cookie, " 你恍然大悟, "需要显式设置 `credentials: 'include'`, 并且服务器要返回 `Access-Control-Allow-Credentials: true`。"

**测试 3: cache 选项**

```javascript
// cache: 控制缓存策略
async function testCacheOptions() {
    // 'default': 使用浏览器缓存策略
    await fetch('/api/data', { cache: 'default' });

    // 'no-store': 不使用缓存, 也不更新缓存
    await fetch('/api/data', { cache: 'no-store' });

    // 'reload': 忽略缓存, 发起请求并更新缓存
    await fetch('/api/data', { cache: 'reload' });

    // 'no-cache': 验证缓存是否有效, 有效则使用
    await fetch('/api/data', { cache: 'no-cache' });

    // 'force-cache': 强制使用缓存 (即使过期)
    await fetch('/api/data', { cache: 'force-cache' });

    // 'only-if-cached': 仅使用缓存 (无缓存则失败)
    await fetch('/api/data', {
        cache: 'only-if-cached',
        mode: 'same-origin'  // 必须配合 same-origin
    });
}
```

你画了一个图表对比缓存策略:

```
缓存策略对比:
| 策略           | 检查缓存 | 发起请求 | 更新缓存 | 适用场景           |
|----------------|----------|----------|----------|--------------------|
| default        | ✅       | 视情况   | ✅       | 正常请求           |
| no-store       | ❌       | ✅       | ❌       | 敏感数据           |
| reload         | ❌       | ✅       | ✅       | 强制刷新           |
| no-cache       | ✅       | ✅       | ✅       | 验证缓存有效性     |
| force-cache    | ✅       | 视情况   | ❌       | 优先使用缓存       |
| only-if-cached | ✅       | ❌       | ❌       | 离线模式           |
```

---

## 流式响应的实战

你想起上周研究过 ReadableStream, 现在可以结合 Fetch 使用了。

```javascript
// 场景: 下载大文件并显示进度
async function downloadWithProgress(url, onProgress) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    // 获取文件大小
    const contentLength = response.headers.get('Content-Length');
    const total = parseInt(contentLength, 10);

    let loaded = 0;
    const chunks = [];

    // 获取 ReadableStream reader
    const reader = response.body.getReader();

    while (true) {
        const { done, value } = await reader.read();

        if (done) {
            break;
        }

        chunks.push(value);
        loaded += value.length;

        // 实时进度回调
        onProgress({
            loaded,
            total,
            percentage: (loaded / total) * 100
        });
    }

    // 合并所有 chunk
    const blob = new Blob(chunks);
    return blob;
}

// 测试
const blob = await downloadWithProgress(
    'https://example.com/large-file.zip',
    (progress) => {
        console.log(`下载进度: ${progress.percentage.toFixed(2)}%`);
    }
);

console.log('下载完成:', blob.size, '字节');
```

你运行测试, 看到实时的进度输出:

```
下载进度: 12.34%
下载进度: 28.56%
下载进度: 45.78%
下载进度: 67.89%
下载进度: 89.12%
下载进度: 100.00%
下载完成: 10485760 字节
```

"这比 XMLHttpRequest 的 `onprogress` 更灵活, " 你在笔记中记录, "因为可以对流数据进行任意处理。"

你又实现了一个流式 JSON 解析的例子:

```javascript
// 场景: 流式解析 JSONL (每行一个 JSON 对象)
async function streamParseJSONL(url) {
    const response = await fetch(url);
    const reader = response.body
        .pipeThrough(new TextDecoderStream())  // 字节流 → 文本流
        .getReader();

    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();

        if (done) {
            // 处理最后一行
            if (buffer.trim()) {
                const obj = JSON.parse(buffer);
                console.log('解析对象:', obj);
            }
            break;
        }

        buffer += value;

        // 按行分割
        const lines = buffer.split('\n');
        buffer = lines.pop();  // 保留不完整的最后一行

        // 解析完整的行
        for (const line of lines) {
            if (line.trim()) {
                try {
                    const obj = JSON.parse(line);
                    console.log('解析对象:', obj);
                } catch (error) {
                    console.error('解析失败:', line);
                }
            }
        }
    }
}
```

---

## CORS 跨域的深度理解

你决定彻底搞清楚 CORS 的工作原理。你在本地启动了两个服务器来测试。

```javascript
// 场景 1: 简单请求 (不触发预检)
async function simpleCorsRequest() {
    // 简单请求的条件:
    // - 方法: GET, POST, HEAD
    // - Content-Type: text/plain, application/x-www-form-urlencoded, multipart/form-data
    // - 无自定义头部

    const response = await fetch('http://localhost:3001/api/data', {
        method: 'GET'
    });

    // 服务器必须返回:
    // Access-Control-Allow-Origin: http://localhost:3000
    // 或
    // Access-Control-Allow-Origin: *

    const data = await response.json();
    console.log('简单请求成功:', data);
}

// 场景 2: 预检请求 (Preflight)
async function preflightCorsRequest() {
    // 以下情况触发预检:
    // - 方法: PUT, DELETE, PATCH, OPTIONS
    // - Content-Type: application/json
    // - 自定义头部

    const response = await fetch('http://localhost:3001/api/data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Custom-Header': 'value'
        },
        body: JSON.stringify({ name: 'Alice' })
    });

    // 浏览器会先发送 OPTIONS 请求:
    // OPTIONS /api/data HTTP/1.1
    // Origin: http://localhost:3000
    // Access-Control-Request-Method: POST
    // Access-Control-Request-Headers: content-type, x-custom-header

    // 服务器必须返回:
    // Access-Control-Allow-Origin: http://localhost:3000
    // Access-Control-Allow-Methods: POST, PUT, DELETE
    // Access-Control-Allow-Headers: content-type, x-custom-header
    // Access-Control-Max-Age: 86400  // 预检结果缓存时间

    const data = await response.json();
    console.log('预检请求成功:', data);
}

// 场景 3: 带凭证的跨域请求
async function corsWithCredentials() {
    const response = await fetch('http://localhost:3001/api/data', {
        method: 'GET',
        credentials: 'include'  // 发送 Cookie
    });

    // 服务器必须返回:
    // Access-Control-Allow-Origin: http://localhost:3000 (不能是 *)
    // Access-Control-Allow-Credentials: true

    const data = await response.json();
    console.log('带凭证请求成功:', data);
}
```

你画了一个 CORS 流程图:

```
CORS 请求流程:

简单请求:
Client → Server: GET /api/data
                 Origin: http://localhost:3000
Client ← Server: Access-Control-Allow-Origin: http://localhost:3000
                 Content-Type: application/json
                 Body: { data }

预检请求:
Client → Server: OPTIONS /api/data
                 Origin: http://localhost:3000
                 Access-Control-Request-Method: POST
                 Access-Control-Request-Headers: content-type
Client ← Server: Access-Control-Allow-Origin: http://localhost:3000
                 Access-Control-Allow-Methods: POST, PUT
                 Access-Control-Allow-Headers: content-type
                 Access-Control-Max-Age: 86400

Client → Server: POST /api/data
                 Origin: http://localhost:3000
                 Content-Type: application/json
                 Body: { data }
Client ← Server: Access-Control-Allow-Origin: http://localhost:3000
                 Content-Type: application/json
                 Body: { result }
```

"CORS 的本质是浏览器的安全机制, " 你总结, "服务器通过响应头告诉浏览器: 这个跨域请求是允许的。"

---

## 错误处理的最佳实践

你开始研究 Fetch 的错误处理。你发现一个让你惊讶的事实:

```javascript
// 错误处理的常见误区
async function commonMistake() {
    try {
        const response = await fetch('https://api.example.com/404');
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('❌ 捕获错误:', error.message);
    }
}

// 运行后你发现: 404 错误没有被 catch 捕获!
// 因为 Fetch 只在网络错误时才 reject Promise
```

"这是个陷阱, " 你在笔记中强调, "HTTP 错误状态码 (4xx, 5xx) 不会导致 Promise rejection!"

你写了一个完整的错误处理方案:

```javascript
// 完整的错误处理
async function robustFetch(url, options = {}) {
    try {
        // 1. 发起请求
        const response = await fetch(url, options);

        // 2. 检查 HTTP 状态码
        if (!response.ok) {
            // 尝试解析错误信息
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

            try {
                const errorData = await response.json();
                if (errorData.message) {
                    errorMessage = errorData.message;
                }
            } catch {
                // 无法解析 JSON, 使用默认错误消息
            }

            throw new Error(errorMessage);
        }

        // 3. 解析响应体
        const contentType = response.headers.get('Content-Type');

        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else if (contentType && contentType.includes('text/')) {
            return await response.text();
        } else {
            return await response.blob();
        }

    } catch (error) {
        // 4. 区分错误类型
        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
            // 网络错误 (无法连接、CORS 失败、DNS 错误等)
            throw new Error('网络错误: 无法连接到服务器');
        } else if (error.name === 'AbortError') {
            // 请求被取消
            throw new Error('请求已取消');
        } else {
            // HTTP 错误或其他错误
            throw error;
        }
    }
}

// 使用
try {
    const data = await robustFetch('https://api.example.com/data');
    console.log('成功:', data);
} catch (error) {
    console.error('失败:', error.message);
}
```

你列出了 Fetch 可能遇到的所有错误类型:

```
Fetch 错误分类:

1. 网络错误 (Promise rejection):
   - TypeError: Failed to fetch
   - 原因: 无法连接、DNS 错误、CORS 失败、证书错误

2. HTTP 错误 (不会 rejection, 需要手动检查):
   - 4xx: 客户端错误 (400, 401, 403, 404)
   - 5xx: 服务器错误 (500, 502, 503, 504)

3. 解析错误 (Promise rejection):
   - SyntaxError: JSON 解析失败
   - TypeError: 响应体已被消费

4. 中止错误 (Promise rejection):
   - AbortError: 请求被 AbortController 取消

5. 超时错误 (手动实现):
   - 通过 AbortController 实现超时逻辑
```

---

## 超时和取消控制

你研究了 AbortController 的使用。这是 Fetch 提供的请求取消机制。

```javascript
// 基础: 请求取消
async function testAbort() {
    const controller = new AbortController();
    const signal = controller.signal;

    // 3 秒后取消请求
    setTimeout(() => {
        controller.abort();
        console.log('请求已取消');
    }, 3000);

    try {
        const response = await fetch('https://api.example.com/slow-api', {
            signal: signal
        });

        const data = await response.json();
        console.log('成功:', data);

    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('请求被用户取消');
        } else {
            console.error('其他错误:', error);
        }
    }
}

// 实现超时功能
function fetchWithTimeout(url, options = {}, timeout = 5000) {
    const controller = new AbortController();
    const signal = controller.signal;

    const timeoutId = setTimeout(() => {
        controller.abort();
    }, timeout);

    return fetch(url, { ...options, signal })
        .then(response => {
            clearTimeout(timeoutId);
            return response;
        })
        .catch(error => {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error(`请求超时 (${timeout}ms)`);
            }
            throw error;
        });
}

// 使用
try {
    const response = await fetchWithTimeout('https://api.example.com/data', {}, 3000);
    const data = await response.json();
    console.log('成功:', data);
} catch (error) {
    console.error('失败:', error.message);
}
```

你封装了一个支持超时和取消的 Fetch 包装器:

```javascript
// 完整的 Fetch 包装器
class FetchClient {
    constructor(baseURL = '', defaultTimeout = 30000) {
        this.baseURL = baseURL;
        this.defaultTimeout = defaultTimeout;
    }

    async request(url, options = {}) {
        const {
            timeout = this.defaultTimeout,
            signal,
            ...fetchOptions
        } = options;

        // 创建 AbortController
        const controller = new AbortController();
        const combinedSignal = signal || controller.signal;

        // 设置超时
        const timeoutId = setTimeout(() => {
            controller.abort();
        }, timeout);

        try {
            // 构建完整 URL
            const fullURL = url.startsWith('http') ? url : `${this.baseURL}${url}`;

            // 发起请求
            const response = await fetch(fullURL, {
                ...fetchOptions,
                signal: combinedSignal
            });

            clearTimeout(timeoutId);

            // 检查 HTTP 状态
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // 解析响应体
            const contentType = response.headers.get('Content-Type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }

            return await response.text();

        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                throw new Error('请求超时或被取消');
            }

            throw error;
        }
    }

    get(url, options) {
        return this.request(url, { ...options, method: 'GET' });
    }

    post(url, body, options) {
        return this.request(url, {
            ...options,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...options?.headers
            },
            body: JSON.stringify(body)
        });
    }

    put(url, body, options) {
        return this.request(url, {
            ...options,
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...options?.headers
            },
            body: JSON.stringify(body)
        });
    }

    delete(url, options) {
        return this.request(url, { ...options, method: 'DELETE' });
    }
}

// 使用
const client = new FetchClient('https://api.example.com', 5000);

// GET 请求
const users = await client.get('/users');

// POST 请求
const newUser = await client.post('/users', { name: 'Alice', age: 25 });

// 带超时的请求
const data = await client.get('/slow-api', { timeout: 3000 });

// 可取消的请求
const controller = new AbortController();
setTimeout(() => controller.abort(), 2000);
const result = await client.get('/data', { signal: controller.signal });
```

---

## 文件上传的多种方式

你测试了 Fetch 上传文件的不同方法。

```javascript
// 方法 1: 上传单个文件
async function uploadSingleFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('description', '用户上传的文件');

    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData  // 不要设置 Content-Type, 让浏览器自动设置
    });

    return await response.json();
}

// 方法 2: 上传多个文件
async function uploadMultipleFiles(files) {
    const formData = new FormData();

    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    const response = await fetch('/api/upload/multiple', {
        method: 'POST',
        body: formData
    });

    return await response.json();
}

// 方法 3: 上传 JSON 数据 + 文件
async function uploadWithMetadata(file, metadata) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));

    const response = await fetch('/api/upload/with-metadata', {
        method: 'POST',
        body: formData
    });

    return await response.json();
}

// 方法 4: 上传 Blob (如录音、截图)
async function uploadBlob(blob, filename) {
    const formData = new FormData();
    formData.append('file', blob, filename);

    const response = await fetch('/api/upload/blob', {
        method: 'POST',
        body: formData
    });

    return await response.json();
}

// 方法 5: 直接上传二进制数据
async function uploadBinary(arrayBuffer, filename) {
    const response = await fetch(`/api/upload/binary?filename=${filename}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/octet-stream'
        },
        body: arrayBuffer
    });

    return await response.json();
}
```

你创建了一个测试页面:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Fetch 文件上传测试</title>
</head>
<body>
    <input type="file" id="fileInput" multiple>
    <button onclick="upload()">上传</button>

    <script>
        async function upload() {
            const files = document.querySelector('#fileInput').files;

            if (files.length === 0) {
                alert('请选择文件');
                return;
            }

            const formData = new FormData();
            for (const file of files) {
                formData.append('files', file);
            }

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const result = await response.json();
                console.log('上传成功:', result);
                alert('上传成功!');

            } catch (error) {
                console.error('上传失败:', error);
                alert('上传失败: ' + error.message);
            }
        }
    </script>
</body>
</html>
```

"Fetch 上传文件比 XMLHttpRequest 简单多了, " 你感慨, "但缺点是无法监听上传进度。"

你在笔记中标注了这个限制:

```
Fetch 上传的限制:
✅ 支持: FormData, Blob, ArrayBuffer, String
✅ 简洁: 代码更清晰
❌ 缺点: 无法监听上传进度
❌ 缺点: 上传大文件时无法显示进度条

解决方案:
1. 小文件 (<10MB): 使用 Fetch
2. 大文件 (>10MB): 仍需使用 XMLHttpRequest 或分块上传
3. 或使用 Service Worker + Streams API (高级方案)
```

---

## 实战场景集合

下午三点, 你整理了一天的学习成果。你创建了一个 "Fetch 实战场景" 文档, 汇总常用模式。

**场景 1: 并发请求**

```javascript
// 并发请求多个 API
async function fetchMultiple(urls) {
    const promises = urls.map(url => fetch(url).then(r => r.json()));
    return Promise.all(promises);
}

// 使用
const [users, posts, comments] = await fetchMultiple([
    '/api/users',
    '/api/posts',
    '/api/comments'
]);
```

**场景 2: 串行请求**

```javascript
// 串行请求 (后一个依赖前一个的结果)
async function fetchSequential() {
    const user = await fetch('/api/user/1').then(r => r.json());
    const posts = await fetch(`/api/user/${user.id}/posts`).then(r => r.json());
    const comments = await fetch(`/api/posts/${posts[0].id}/comments`).then(r => r.json());

    return { user, posts, comments };
}
```

**场景 3: 重试机制**

```javascript
// 请求失败时自动重试
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
    let lastError;

    for (let i = 0; i < maxRetries; i++) {
        try {
            const response = await fetch(url, options);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            lastError = error;
            console.warn(`请求失败 (第 ${i + 1} 次尝试):`, error.message);

            if (i < maxRetries - 1) {
                // 指数退避: 1s, 2s, 4s
                const delay = Math.pow(2, i) * 1000;
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }

    throw new Error(`请求失败 (已重试 ${maxRetries} 次): ${lastError.message}`);
}
```

**场景 4: 请求节流**

```javascript
// 限制并发请求数量
class RequestQueue {
    constructor(maxConcurrent = 3) {
        this.maxConcurrent = maxConcurrent;
        this.current = 0;
        this.queue = [];
    }

    async add(url, options) {
        while (this.current >= this.maxConcurrent) {
            await new Promise(resolve => this.queue.push(resolve));
        }

        this.current++;

        try {
            const response = await fetch(url, options);
            return await response.json();
        } finally {
            this.current--;
            const resolve = this.queue.shift();
            if (resolve) resolve();
        }
    }
}

// 使用
const queue = new RequestQueue(3);

const urls = Array.from({ length: 20 }, (_, i) => `/api/data/${i}`);
const results = await Promise.all(urls.map(url => queue.add(url)));
```

**场景 5: 缓存包装**

```javascript
// 简单的缓存包装器
class CachedFetch {
    constructor(ttl = 60000) {
        this.cache = new Map();
        this.ttl = ttl;
    }

    async fetch(url, options = {}) {
        const key = `${url}:${JSON.stringify(options)}`;

        // 检查缓存
        if (this.cache.has(key)) {
            const { data, timestamp } = this.cache.get(key);
            if (Date.now() - timestamp < this.ttl) {
                console.log('使用缓存:', url);
                return data;
            }
        }

        // 发起请求
        console.log('发起请求:', url);
        const response = await fetch(url, options);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // 缓存结果
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });

        return data;
    }

    clear() {
        this.cache.clear();
    }
}

// 使用
const cachedFetch = new CachedFetch(60000);  // 缓存 60 秒

const data1 = await cachedFetch.fetch('/api/data');  // 发起请求
const data2 = await cachedFetch.fetch('/api/data');  // 使用缓存
```

**场景 6: GraphQL 请求**

```javascript
// GraphQL 查询
async function graphqlQuery(query, variables = {}) {
    const response = await fetch('/graphql', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query,
            variables
        })
    });

    const result = await response.json();

    if (result.errors) {
        throw new Error(result.errors[0].message);
    }

    return result.data;
}

// 使用
const data = await graphqlQuery(`
    query GetUser($id: ID!) {
        user(id: $id) {
            id
            name
            email
            posts {
                id
                title
            }
        }
    }
`, { id: '123' });
```

---

## 知识档案: Fetch API 的八个核心机制

**规则 1: Fetch 返回 Promise<Response>, 不直接返回数据**

Fetch API 采用两阶段设计: 第一阶段获取 Response 对象 (HTTP 响应头到达), 第二阶段解析响应体 (数据传输完成)。

```javascript
// 两阶段特性
const response = await fetch('/api/data');  // 第一阶段: 获取 Response 对象

console.log(response.status);    // 200
console.log(response.headers);   // Headers 对象
console.log(response.bodyUsed);  // false (响应体未读取)

const data = await response.json();  // 第二阶段: 解析响应体

console.log(response.bodyUsed);  // true (响应体已消费)
```

为什么要分两阶段:
- **即时反馈**: 收到响应头后立即知道请求状态, 无需等待数据下载
- **流式处理**: 可以在数据传输过程中进行处理
- **灵活解析**: 可以根据 Content-Type 选择不同的解析方式 (json, text, blob, arrayBuffer)

响应体只能读取一次:
```javascript
const response = await fetch('/api/data');
const data1 = await response.json();  // ✅ 成功
const data2 = await response.json();  // ❌ TypeError: body stream already read
```

---

**规则 2: HTTP 错误状态码不会导致 Promise rejection**

Fetch 只在网络错误时 reject Promise, HTTP 错误状态码 (4xx, 5xx) 仍然会 resolve Promise, 需要手动检查 `response.ok`。

```javascript
// ❌ 错误: 404 不会被 catch 捕获
try {
    const response = await fetch('/api/404');
    const data = await response.json();  // 代码会执行到这里
} catch (error) {
    console.log('不会执行');
}

// ✅ 正确: 检查 response.ok
try {
    const response = await fetch('/api/404');

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
} catch (error) {
    console.log('捕获错误:', error.message);
}
```

Fetch 错误分类:
- **网络错误** (Promise rejection): 无法连接、DNS 错误、CORS 失败、证书错误
- **HTTP 错误** (不会 rejection): 400, 401, 403, 404, 500, 502, 503, 504
- **解析错误** (Promise rejection): JSON 解析失败、响应体已消费
- **中止错误** (Promise rejection): AbortController 取消请求

---

**规则 3: Request 和 Response 对象是 Fetch API 的核心抽象**

Request 对象封装请求配置, Response 对象封装响应数据, 两者都是不可变的。

```javascript
// Request 对象
const request = new Request('https://api.example.com/data', {
    method: 'POST',
    headers: new Headers({
        'Content-Type': 'application/json',
        'Authorization': 'Bearer token'
    }),
    body: JSON.stringify({ name: 'Alice' })
});

console.log(request.url);        // "https://api.example.com/data"
console.log(request.method);     // "POST"
console.log(request.headers);    // Headers 对象
console.log(request.bodyUsed);   // false

// 使用 Request 对象
const response = await fetch(request);

// Response 对象
console.log(response.status);       // 200
console.log(response.statusText);   // "OK"
console.log(response.ok);           // true (status 200-299)
console.log(response.headers);      // Headers 对象
console.log(response.type);         // "cors"
console.log(response.url);          // 最终 URL (可能经过重定向)
```

Request/Response 的不可变性:
```javascript
// ❌ 无法修改已有对象
request.method = 'GET';  // 无效, 属性只读

// ✅ 创建新对象
const newRequest = new Request(request, { method: 'GET' });
```

---

**规则 4: Headers API 提供 append/set/get/delete 方法, 区分 append 和 set**

Headers 对象是 HTTP 头部的容器, 支持动态修改, `append` 会合并相同名称的值, `set` 会覆盖。

```javascript
const headers = new Headers();

// append: 添加值 (相同名称会合并)
headers.append('X-Tag', 'tag1');
headers.append('X-Tag', 'tag2');
console.log(headers.get('X-Tag'));  // "tag1, tag2"

// set: 设置值 (覆盖已存在的值)
headers.set('X-Tag', 'tag3');
console.log(headers.get('X-Tag'));  // "tag3"

// get: 获取值
console.log(headers.get('Content-Type'));  // "application/json"

// has: 检查是否存在
console.log(headers.has('Authorization'));  // true

// delete: 删除头部
headers.delete('X-Tag');

// 遍历所有头部
for (const [key, value] of headers.entries()) {
    console.log(`${key}: ${value}`);
}
```

Headers Guard 机制:
- **request**: Request 的 headers 可修改
- **response**: Response 的 headers 只读
- **immutable**: 完全不可修改

```javascript
const response = await fetch('/api/data');

// ❌ 响应头只读
response.headers.set('X-Custom', 'value');  // TypeError

// ✅ 创建新的 Headers 对象
const newHeaders = new Headers(response.headers);
newHeaders.set('X-Custom', 'value');  // 成功
```

---

**规则 5: credentials 选项控制 Cookie 发送策略, 跨域需显式设置 include**

credentials 决定请求是否携带 Cookie 和认证信息, 默认 `same-origin` (仅同源请求发送)。

```javascript
// 'omit': 不发送 Cookie
await fetch('/api/data', { credentials: 'omit' });

// 'same-origin': 同源请求发送 Cookie (默认)
await fetch('/api/data', { credentials: 'same-origin' });

// 'include': 始终发送 Cookie (包括跨域)
await fetch('https://api.example.com/data', {
    credentials: 'include'
});
```

跨域发送 Cookie 的完整要求:
1. **客户端**: `credentials: 'include'`
2. **服务器**: `Access-Control-Allow-Credentials: true`
3. **服务器**: `Access-Control-Allow-Origin` 不能是 `*`, 必须是具体域名

```javascript
// 跨域带 Cookie 请求
await fetch('https://api.example.com/data', {
    method: 'GET',
    credentials: 'include'
});

// 服务器必须返回:
// Access-Control-Allow-Origin: https://your-domain.com
// Access-Control-Allow-Credentials: true
```

---

**规则 6: mode 选项决定跨域策略, no-cors 返回不透明响应**

mode 选项控制请求的跨域行为, 影响是否允许跨域和响应的可读性。

```javascript
// 'cors': 允许跨域, 可读取响应 (默认)
const response1 = await fetch('https://api.example.com/data', {
    mode: 'cors'
});
console.log(response1.type);  // "cors"
console.log(await response1.json());  // 可读取

// 'no-cors': 允许跨域, 但响应不透明
const response2 = await fetch('https://api.example.com/data', {
    mode: 'no-cors'
});
console.log(response2.type);    // "opaque"
console.log(response2.status);  // 0
console.log(await response2.text());  // "" (空, 无法读取)

// 'same-origin': 仅同源, 跨域会失败
const response3 = await fetch('https://api.example.com/data', {
    mode: 'same-origin'
});
// TypeError: Failed to fetch

// 'navigate': 用于导航请求 (浏览器内部使用)
```

no-cors 的使用场景:
- Service Worker 缓存跨域资源 (如 CDN 的 CSS/JS)
- 发送跨域日志 (不需要读取响应)
- 预加载跨域资源

---

**规则 7: AbortController 提供请求取消和超时功能**

Fetch API 原生不支持超时, 需要通过 AbortController 实现取消和超时控制。

```javascript
// 基础用法: 手动取消请求
const controller = new AbortController();
const signal = controller.signal;

fetch('/api/data', { signal })
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => {
        if (error.name === 'AbortError') {
            console.log('请求被取消');
        }
    });

// 3 秒后取消
setTimeout(() => controller.abort(), 3000);
```

实现超时功能:
```javascript
function fetchWithTimeout(url, options = {}, timeout = 5000) {
    const controller = new AbortController();
    const signal = controller.signal;

    const timeoutId = setTimeout(() => {
        controller.abort();
    }, timeout);

    return fetch(url, { ...options, signal })
        .then(response => {
            clearTimeout(timeoutId);
            return response;
        })
        .catch(error => {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error(`请求超时 (${timeout}ms)`);
            }
            throw error;
        });
}

// 使用
await fetchWithTimeout('/api/slow', {}, 3000);
```

一个 AbortController 可以控制多个请求:
```javascript
const controller = new AbortController();
const signal = controller.signal;

Promise.all([
    fetch('/api/users', { signal }),
    fetch('/api/posts', { signal }),
    fetch('/api/comments', { signal })
])
.then(responses => Promise.all(responses.map(r => r.json())))
.then(data => console.log(data))
.catch(error => {
    if (error.name === 'AbortError') {
        console.log('所有请求被取消');
    }
});

// 取消所有请求
controller.abort();
```

---

**规则 8: 流式响应通过 response.body 访问 ReadableStream**

Response.body 是 ReadableStream 实例, 支持流式读取大文件或实时数据, 而不需要等待整个响应下载完成。

```javascript
// 下载大文件并显示进度
async function downloadWithProgress(url, onProgress) {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const contentLength = response.headers.get('Content-Length');
    const total = parseInt(contentLength, 10);

    let loaded = 0;
    const chunks = [];

    const reader = response.body.getReader();

    while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        chunks.push(value);
        loaded += value.length;

        onProgress({
            loaded,
            total,
            percentage: (loaded / total) * 100
        });
    }

    return new Blob(chunks);
}

// 使用
const blob = await downloadWithProgress('/large-file.zip', (progress) => {
    console.log(`下载进度: ${progress.percentage.toFixed(2)}%`);
});
```

流式解析 JSON Lines:
```javascript
async function streamParseJSONL(url) {
    const response = await fetch(url);
    const reader = response.body
        .pipeThrough(new TextDecoderStream())
        .getReader();

    let buffer = '';

    while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += value;
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
            if (line.trim()) {
                const obj = JSON.parse(line);
                console.log('解析对象:', obj);
            }
        }
    }
}
```

流式处理优势:
- **内存效率**: 不需要一次性加载整个响应到内存
- **实时性**: 数据到达即可处理, 无需等待完整下载
- **灵活性**: 可以对数据流进行任意转换和过滤

---

**事故档案编号**: NETWORK-2024-1956
**影响范围**: Fetch API, Request/Response 对象, Headers API, 跨域请求, 流式响应, 请求取消
**根本原因**: Fetch API 采用现代 Promise 设计, 提供 Request/Response 抽象, 支持流式处理, 但需要理解两阶段响应、HTTP 错误处理、CORS 策略、流式读取机制
**学习成本**: 中高 (需理解 Promise, Stream, CORS, AbortController, Headers Guard 机制)

这是 JavaScript 世界第 156 次被记录的网络与数据事故。Fetch API 采用两阶段设计: 第一阶段获取 Response 对象 (HTTP 响应头), 第二阶段解析响应体 (数据)。HTTP 错误状态码不会导致 Promise rejection, 需要手动检查 `response.ok`。Request 和 Response 对象是不可变的核心抽象, 封装请求和响应的完整信息。Headers API 提供 append/set/get/delete 方法, append 合并值, set 覆盖值。credentials 选项控制 Cookie 发送策略, 跨域需显式设置 `include` 并配合服务器 CORS 头。mode 选项决定跨域策略, `no-cors` 返回不透明响应仅用于缓存和日志。AbortController 提供请求取消和超时功能, 一个控制器可管理多个请求。流式响应通过 `response.body` 访问 ReadableStream, 支持渐进式处理大文件和实时数据。理解 Fetch API 的完整生命周期、错误处理模式、跨域机制、流式特性是构建现代网络应用的基础。

---
