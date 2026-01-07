《第 151 次记录: 遗留代码的两周改造 —— XMLHttpRequest 的告别之旅》

---

## 技术债务的发现

周一上午十点, 你打开了那个存在三年的 `api.js` 文件。

这是季度代码审查的一部分。技术总监在会议上说: "我们要逐步清理技术债务, 提升代码质量。" 你被分配审查网络请求模块——这个模块自从 2020 年项目启动就没有大改过。

你滚动着代码, 看到了熟悉但陈旧的模式:

```javascript
// api.js - 三年前的代码
function request(url, options) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    resolve(JSON.parse(xhr.responseText));
                } catch (e) {
                    reject(new Error('Invalid JSON'));
                }
            } else {
                reject(new Error(`HTTP ${xhr.status}`));
            }
        };

        xhr.onerror = function() {
            reject(new Error('Network error'));
        };

        xhr.open(options.method || 'GET', url);

        if (options.headers) {
            Object.keys(options.headers).forEach(key => {
                xhr.setRequestHeader(key, options.headers[key]);
            });
        }

        xhr.send(options.body);
    });
}
```

"这还是 XMLHttpRequest..." 你喃喃自语。代码能用, 但你知道有更好的方式。

你快速搜索了项目, 发现这个 `request` 函数被 47 个文件调用, 涉及 156 个调用点。如果直接改用 Fetch API, 可能会影响很多地方。

"不能一次性重写," 你在审查报告里写道, "但可以渐进式迁移。"

---

## 迁移策略的设计

周一下午, 你召集了小组会议。

"我们的网络请求模块还在用 XMLHttpRequest," 你在白板上画出当前架构, "这个 API 已经被 Fetch 替代五年了。"

前端小李说: "但是改动太大了吧? 有 156 个调用点..."

"所以我们不是一次性替换," 你解释, "而是渐进式迁移。我的计划是这样的:"

**第一阶段 (第 1 周)**: 创建新的 Fetch 包装层, 保持 API 兼容
**第二阶段 (第 2 周)**: 逐步迁移调用点, 分模块验证
**第三阶段 (未来)**: 移除旧代码, 完全切换到 Fetch

"关键是新包装层要保持相同的接口," 你在白板上写下:

```javascript
// 目标: 保持相同的调用方式
request('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Alice' })
})
```

小李点头: "这样就不用改调用代码了。"

"对," 你说, "但内部实现用 Fetch。不过有个问题——上传进度。"

你在白板上列出对比:

```
XMLHttpRequest 优势:
✅ 上传进度监听 (xhr.upload.onprogress)
✅ 请求中止 (xhr.abort)

Fetch 优势:
✅ Promise 原生支持
✅ 更简洁的 API
✅ 支持 Request/Response 对象
✅ 更好的错误处理

Fetch 劣势:
❌ 无法监听上传进度 (只能监听下载)
```

后端老张提醒: "文件上传功能怎么办? 用户需要看进度条。"

"文件上传保留 XMLHttpRequest," 你说, "其他请求迁移到 Fetch。这就是渐进式迁移的好处——可以针对不同场景选择最优方案。"

---

## 第一周: 包装层实现

周二到周四, 你实现了新的 Fetch 包装层:

```javascript
// api-fetch.js - 新的 Fetch 包装层
class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    // 核心请求方法
    async request(url, options = {}) {
        const {
            method = 'GET',
            headers = {},
            body,
            timeout = 30000,
            signal,
            ...otherOptions
        } = options;

        // 1. 处理超时
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        const finalSignal = signal || controller.signal;

        try {
            // 2. 构建完整 URL
            const fullURL = url.startsWith('http') ? url : `${this.baseURL}${url}`;

            // 3. 发送 Fetch 请求
            const response = await fetch(fullURL, {
                method,
                headers: {
                    ...this.defaultHeaders,
                    ...headers
                },
                body: body ? (typeof body === 'string' ? body : JSON.stringify(body)) : undefined,
                signal: finalSignal,
                ...otherOptions
            });

            clearTimeout(timeoutId);

            // 4. 处理响应
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // 5. 解析 JSON
            const contentType = response.headers.get('Content-Type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }

            return await response.text();

        } catch (error) {
            clearTimeout(timeoutId);

            // 6. 统一错误处理
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }

            throw error;
        }
    }

    // 便捷方法
    get(url, options) {
        return this.request(url, { ...options, method: 'GET' });
    }

    post(url, body, options) {
        return this.request(url, { ...options, method: 'POST', body });
    }

    put(url, body, options) {
        return this.request(url, { ...options, method: 'PUT', body });
    }

    delete(url, options) {
        return this.request(url, { ...options, method: 'DELETE' });
    }
}

// 创建单例
export const api = new APIClient('/api');
```

周五上午, 你开始第一批迁移——用户管理模块。你创建了一个测试文件, 对比新旧实现:

```javascript
// 测试: 新旧实现对比
import { request as oldRequest } from './api.js';  // 旧的 XHR
import { api as newAPI } from './api-fetch.js';    // 新的 Fetch

async function testMigration() {
    const testCases = [
        { name: 'GET 请求', url: '/users', method: 'GET' },
        { name: 'POST 请求', url: '/users', method: 'POST', body: { name: 'Test' } },
        { name: '错误处理', url: '/404', method: 'GET' }
    ];

    for (const test of testCases) {
        console.log(`\n测试: ${test.name}`);

        try {
            const oldResult = await oldRequest(test.url, test);
            const newResult = await newAPI.request(test.url, test);

            console.log('✅ 新旧结果一致:', JSON.stringify(oldResult) === JSON.stringify(newResult));
        } catch (error) {
            console.log('❌ 错误:', error.message);
        }
    }
}
```

测试通过了。你松了一口气, 开始修改用户模块的代码:

```javascript
// users.js - 迁移前
import { request } from './api.js';

export async function getUsers() {
    return request('/users', { method: 'GET' });
}

// users.js - 迁移后
import { api } from './api-fetch.js';

export async function getUsers() {
    return api.get('/users');  // 更简洁了
}
```

周五下午, 你部署到测试环境。用户模块的所有功能正常工作。

---

## 第二周: 全面迁移

第二周, 你按模块逐个迁移:

**周一**: 商品模块 (23 个调用点) → ✅ 迁移成功
**周二**: 订单模块 (34 个调用点) → ✅ 迁移成功
**周三**: 评论模块 (18 个调用点) → ✅ 迁移成功

但周四遇到了问题——文件上传模块。

```javascript
// upload.js - 使用了上传进度
function uploadFile(file, onProgress) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        // ✅ XMLHttpRequest 支持上传进度
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
                reject(new Error(`Upload failed: ${xhr.status}`));
            }
        };

        xhr.onerror = () => reject(new Error('Network error'));

        const formData = new FormData();
        formData.append('file', file);

        xhr.open('POST', '/api/upload');
        xhr.send(formData);
    });
}
```

"Fetch 无法监听上传进度," 你在代码审查会上解释, "所以文件上传模块保留 XMLHttpRequest。"

小李问: "那不是还有旧代码吗?"

"对," 你说, "但这是合理的技术选择。我们创建一个专门的上传模块, 使用 XHR, 其他地方用 Fetch。这叫'混合策略'。"

你重构了上传模块:

```javascript
// upload.js - 保留 XHR 用于上传进度
export class FileUploader {
    uploadWithProgress(file, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    onProgress((e.loaded / e.total) * 100, e.loaded, e.total);
                }
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        resolve(JSON.parse(xhr.responseText));
                    } catch (e) {
                        reject(new Error('Invalid response'));
                    }
                } else {
                    reject(new Error(`Upload failed: ${xhr.status}`));
                }
            };

            xhr.onerror = () => reject(new Error('Network error'));
            xhr.ontimeout = () => reject(new Error('Upload timeout'));

            xhr.timeout = 60000;  // 60 秒超时

            const formData = new FormData();
            formData.append('file', file);

            xhr.open('POST', '/api/upload');
            xhr.send(formData);
        });
    }
}

export const uploader = new FileUploader();
```

周五, 迁移完成。你统计了迁移结果:

```
迁移统计:
- 总调用点: 156 个
- 已迁移到 Fetch: 138 个 (88.5%)
- 保留 XHR (上传): 18 个 (11.5%)
- 测试通过率: 100%
- 性能提升: 平均响应时间减少 15%
```

---

## 迁移收获与反思

两周后, 你在技术分享会上总结了这次迁移:

**迁移前后对比**:

**旧代码 (XMLHttpRequest)**:
```javascript
function request(url, options) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    resolve(JSON.parse(xhr.responseText));
                } catch (e) {
                    reject(new Error('Invalid JSON'));
                }
            } else {
                reject(new Error(`HTTP ${xhr.status}`));
            }
        };

        xhr.onerror = function() {
            reject(new Error('Network error'));
        };

        xhr.open(options.method || 'GET', url);

        if (options.headers) {
            Object.keys(options.headers).forEach(key => {
                xhr.setRequestHeader(key, options.headers[key]);
            });
        }

        xhr.send(options.body);
    });
}

// 调用
request('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Alice' })
})
.then(data => console.log(data))
.catch(error => console.error(error));
```

**新代码 (Fetch)**:
```javascript
class APIClient {
    async request(url, options = {}) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), options.timeout || 30000);

        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    }
}

// 调用 (更简洁)
await api.post('/users', { name: 'Alice' });
```

**优势对比**:

| 维度 | XMLHttpRequest | Fetch API |
|------|----------------|-----------|
| 代码简洁度 | 30+ 行 | 10-15 行 |
| Promise 支持 | 需要手动包装 | ✅ 原生支持 |
| 错误处理 | 复杂 (多个回调) | ✅ 统一 try-catch |
| 超时控制 | xhr.timeout | ✅ AbortSignal |
| 上传进度 | ✅ xhr.upload.onprogress | ❌ 不支持 |
| 下载进度 | xhr.onprogress | ✅ response.body 流 |
| 现代特性 | ❌ 遗留 API | ✅ 标准化 |

你在总结里写道:

> "渐进式迁移的核心是: 不求一步到位, 但求持续改进。保留 XHR 用于上传进度不是妥协, 而是务实的技术选择。未来如果 Fetch 支持上传进度, 我们再迁移这部分。"

---

## 知识档案: XMLHttpRequest 与 Fetch 迁移指南

**规则 1: XMLHttpRequest 是遗留 API, 但仍有存在价值**

XMLHttpRequest 诞生于 1999 年 (IE5), 曾是 AJAX 革命的核心。2015 年 Fetch API 标准化后, XHR 进入维护模式, 但并未废弃。

**保留 XHR 的唯一合理场景: 上传进度监听**

```javascript
// ✅ 唯一合理使用 XHR 的场景
function uploadWithProgress(file, onProgress) {
    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            onProgress(e.loaded, e.total);
        }
    };

    xhr.open('POST', '/upload');
    xhr.send(file);
}
```

为什么 Fetch 不支持上传进度:
- **设计哲学**: Fetch 聚焦于简洁的 Promise 接口
- **异步模型**: `await fetch()` 返回时上传已完成
- **流式设计**: `response.body` 是响应流, 不是请求流

---

**规则 2: Fetch 的核心优势是 Promise 原生支持和更好的错误处理**

XMLHttpRequest 错误处理的痛点:

```javascript
// ❌ XHR 错误处理: 多个回调, 难以维护
const xhr = new XMLHttpRequest();

xhr.onload = function() {
    if (xhr.status >= 200 && xhr.status < 300) {
        try {
            const data = JSON.parse(xhr.responseText);
            // 成功逻辑
        } catch (e) {
            // JSON 解析错误
        }
    } else {
        // HTTP 错误
    }
};

xhr.onerror = function() {
    // 网络错误
};

xhr.ontimeout = function() {
    // 超时错误
};
```

Fetch 的统一错误处理:

```javascript
// ✅ Fetch: 统一的 try-catch
try {
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    // 成功逻辑

} catch (error) {
    // 所有错误统一处理: 网络错误、HTTP 错误、JSON 解析错误
    console.error('Request failed:', error);
}
```

---

**规则 3: 渐进式迁移策略: 包装层 → 逐模块替换 → 保留特殊场景**

迁移步骤:

**第 1 步: 创建 Fetch 包装层, 保持 API 兼容**

```javascript
class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
    }

    async request(url, options) {
        const response = await fetch(`${this.baseURL}${url}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return response.json();
    }

    get(url, options) {
        return this.request(url, { ...options, method: 'GET' });
    }

    post(url, body, options) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: JSON.stringify(body)
        });
    }
}
```

**第 2 步: 逐模块替换, 保持调用方式不变**

```javascript
// 迁移前
import { request } from './api-xhr.js';
const users = await request('/users', { method: 'GET' });

// 迁移后 (调用方式相同)
import { api } from './api-fetch.js';
const users = await api.get('/users');
```

**第 3 步: 保留 XHR 用于上传进度, 创建专门模块**

```javascript
// upload.js - 专门的上传模块
export class FileUploader {
    upload(file, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    onProgress(e.loaded / e.total);
                }
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(`Upload failed: ${xhr.status}`));
                }
            };

            xhr.onerror = () => reject(new Error('Network error'));

            const formData = new FormData();
            formData.append('file', file);

            xhr.open('POST', '/api/upload');
            xhr.send(formData);
        });
    }
}
```

---

**规则 4: 超时控制: XHR 用 timeout 属性, Fetch 用 AbortSignal**

XMLHttpRequest 超时:

```javascript
const xhr = new XMLHttpRequest();
xhr.timeout = 5000;  // 5 秒超时

xhr.ontimeout = function() {
    console.log('Request timeout');
};

xhr.open('GET', '/api/data');
xhr.send();
```

Fetch 超时 (需要 AbortController):

```javascript
// 方法 1: 手动实现超时
const controller = new AbortController();

const timeoutId = setTimeout(() => {
    controller.abort();
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
        console.log('Request timeout');
    }
}

// 方法 2: 使用 AbortSignal.timeout() (现代浏览器)
const response = await fetch('/api/data', {
    signal: AbortSignal.timeout(5000)
});
```

---

**规则 5: 请求中止: XHR 用 abort() 方法, Fetch 用 AbortController**

XMLHttpRequest 中止:

```javascript
const xhr = new XMLHttpRequest();

xhr.open('GET', '/api/data');
xhr.send();

// 用户取消
cancelButton.onclick = () => {
    xhr.abort();  // 中止请求
};
```

Fetch 中止 (需要 AbortController):

```javascript
const controller = new AbortController();

fetch('/api/data', {
    signal: controller.signal
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => {
    if (error.name === 'AbortError') {
        console.log('Request cancelled');
    }
});

// 用户取消
cancelButton.onclick = () => {
    controller.abort();  // 中止请求
};
```

---

**规则 6: 响应类型处理: XHR 需要手动解析, Fetch 提供便捷方法**

XMLHttpRequest 响应处理:

```javascript
const xhr = new XMLHttpRequest();

xhr.onload = function() {
    // 需要手动判断内容类型和解析
    const contentType = xhr.getResponseHeader('Content-Type');

    if (contentType.includes('application/json')) {
        const data = JSON.parse(xhr.responseText);
    } else if (contentType.includes('text/html')) {
        const html = xhr.responseText;
    } else if (contentType.includes('image')) {
        const blob = xhr.response;  // 需要设置 responseType = 'blob'
    }
};

xhr.open('GET', '/api/data');
xhr.send();
```

Fetch 响应处理 (更优雅):

```javascript
const response = await fetch('/api/data');

// 根据内容类型选择解析方法
if (response.headers.get('Content-Type').includes('application/json')) {
    const data = await response.json();  // ✅ 自动解析 JSON
} else if (response.headers.get('Content-Type').includes('text')) {
    const text = await response.text();  // ✅ 文本
} else if (response.headers.get('Content-Type').includes('image')) {
    const blob = await response.blob();  // ✅ 二进制
}
```

---

**规则 7: 错误状态判断: XHR 需要检查 status, Fetch 提供 response.ok**

XMLHttpRequest 错误判断:

```javascript
xhr.onload = function() {
    // ❌ 需要手动检查状态码范围
    if (xhr.status >= 200 && xhr.status < 300) {
        // 成功
    } else if (xhr.status >= 400 && xhr.status < 500) {
        // 客户端错误
    } else if (xhr.status >= 500) {
        // 服务器错误
    }
};
```

Fetch 错误判断:

```javascript
const response = await fetch('/api/data');

// ✅ response.ok 自动判断 2xx 范围
if (response.ok) {
    // 成功 (200-299)
    const data = await response.json();
} else {
    // 失败 (>= 400)
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
}
```

---

**规则 8: 下载进度监听: XHR 用 onprogress, Fetch 用 ReadableStream**

XMLHttpRequest 下载进度:

```javascript
const xhr = new XMLHttpRequest();

xhr.onprogress = function(e) {
    if (e.lengthComputable) {
        const percent = (e.loaded / e.total) * 100;
        console.log(`下载进度: ${percent.toFixed(2)}%`);
    }
};

xhr.onload = function() {
    console.log('下载完成');
};

xhr.open('GET', '/api/large-file');
xhr.send();
```

Fetch 下载进度 (使用 ReadableStream):

```javascript
const response = await fetch('/api/large-file');

const contentLength = response.headers.get('Content-Length');
const total = parseInt(contentLength, 10);
let loaded = 0;

const reader = response.body.getReader();

while (true) {
    const { done, value } = await reader.read();

    if (done) {
        console.log('下载完成');
        break;
    }

    loaded += value.length;
    const percent = (loaded / total) * 100;
    console.log(`下载进度: ${percent.toFixed(2)}%`);
}
```

---

**事故档案编号**: NETWORK-2024-1951
**影响范围**: XMLHttpRequest, Fetch API, 渐进式迁移, API 重构, 技术债务管理
**根本原因**: 遗留代码使用 XMLHttpRequest, 需要渐进式迁移到现代 Fetch API, 但保留上传进度监听场景
**学习成本**: 中 (需理解两种 API 差异和迁移策略)

这是 JavaScript 世界第 151 次被记录的网络与数据事故。XMLHttpRequest 是诞生于 1999 年的遗留 API, 2015 年 Fetch API 标准化后成为现代首选。Fetch 的核心优势是 Promise 原生支持、统一的错误处理和更简洁的 API。但 Fetch 无法监听上传进度, 这是 XMLHttpRequest 仍有保留价值的唯一场景。渐进式迁移策略包括: 创建 Fetch 包装层保持 API 兼容、逐模块替换调用点、保留 XHR 用于特殊场景如文件上传进度。超时控制方面, XHR 使用 timeout 属性, Fetch 使用 AbortSignal。请求中止方面, XHR 使用 abort() 方法, Fetch 使用 AbortController。下载进度监听方面, XHR 使用 onprogress 事件, Fetch 使用 ReadableStream。响应处理方面, Fetch 提供 json()/text()/blob() 等便捷方法, XHR 需要手动解析。错误判断方面, Fetch 的 response.ok 属性自动判断 2xx 状态码范围。理解两种 API 的设计差异和适用场景, 制定务实的迁移策略是管理技术债务的关键。

---
