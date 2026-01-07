《第 150 次记录: 2000 人围观的直播翻车 —— URL 解析的陷阱》

---

## 直播开始

周四晚上七点整, 你坐在电脑前, 深吸一口气。

屏幕右侧显示着直播间的观众数：2247 人在线。这是公司的技术分享会, 你负责展示刚上线的"智能链接分享"功能——用户可以一键生成美化的分享链接, 包含预览图、标题、描述等元数据。

"大家好," 你对着麦克风说, "今天我来分享一个很实用的功能。相信大家都遇到过这样的场景：分享一个链接到社交媒体, 但显示的信息很丑, 没有图片, 标题也不对。我们的新功能可以自动优化这些..."

直播间的评论区滚动着：
```
用户A: 期待!
用户B: 终于有这个功能了
用户C: 之前确实很难用
```

你打开演示页面, 界面简洁优雅。输入框提示："输入任意 URL, 一键生成美化链接"。

"我们先测试一个简单的例子," 你说着, 在输入框输入 `https://example.com/blog/post-123`。

点击"生成链接"按钮。

页面加载了一秒, 然后显示结果:
```
✅ 生成成功!
原始链接: https://example.com/blog/post-123
分享链接: https://share.oursite.com/s/abc123def

预览:
[精美的卡片展示：标题、描述、缩略图]
```

"看, 很简单吧," 你满意地说, "生成的短链接不仅简洁, 而且包含丰富的预览信息。"

评论区一片好评:
```
用户D: 很酷!
用户E: 终于不用手动编辑了
```

"接下来我演示一个更复杂的例子," 你继续, "带查询参数和锚点的 URL。"

你输入: `https://example.com/search?q=javascript&sort=date#results`

点击"生成链接"。

然后, 屏幕上出现了红色的错误提示:
```
❌ 错误: 无效的 URL 格式
```

你愣了一下。"呃...这个链接应该是有效的啊..."

你又试了一次, 同样的错误。评论区开始出现疑问:
```
用户F: 什么情况?
用户G: 带参数的 URL 不支持吗?
用户H: 这是 bug 吧
```

你的手心开始冒汗。2000 多人在看着你翻车。

---

## 现场调试

"让我检查一下," 你强装镇定, 打开浏览器的开发者工具。

你快速查看 Network 面板——请求返回了 400 Bad Request, 响应内容是:
```json
{
  "error": "Invalid URL: Cannot parse query parameters"
}
```

"查询参数解析失败?" 你小声嘀咕, 然后意识到麦克风还开着。

评论区更热闹了:
```
用户I: URL 解析出问题了?
用户J: 应该用 URLSearchParams
用户K: 可能是编码问题
```

你快速切换到代码编辑器, 找到链接处理的代码:

```javascript
// 前端: 生成分享链接
async function generateShareLink(originalUrl) {
    try {
        // 验证 URL 格式
        const url = new URL(originalUrl);

        // 提取 URL 信息
        const urlInfo = {
            protocol: url.protocol,
            host: url.host,
            pathname: url.pathname,
            query: url.search,  // 这里有问题?
            hash: url.hash
        };

        // 发送到后端
        const response = await fetch('/api/share/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: originalUrl, info: urlInfo })
        });

        if (!response.ok) {
            throw new Error('生成失败');
        }

        return await response.json();

    } catch (error) {
        console.error('错误:', error);
        showError('无效的 URL 格式');
    }
}
```

你又快速检查了后端代码:

```javascript
// 后端: 处理分享链接创建
app.post('/api/share/create', (req, res) => {
    const { url, info } = req.body;

    // 验证 URL
    try {
        const parsedUrl = new URL(url);

        // 解析查询参数
        const params = {};
        const queryString = info.query.substring(1);  // 去掉开头的 '?'

        // ❌ 这里有问题!
        queryString.split('&').forEach(pair => {
            const [key, value] = pair.split('=');
            params[key] = value;  // 没有解码!
        });

        // 生成短链接
        const shortId = generateShortId();
        saveToDatabase(shortId, {
            originalUrl: url,
            params: params,
            ...info
        });

        res.json({
            success: true,
            shortUrl: `https://share.oursite.com/s/${shortId}`
        });

    } catch (error) {
        res.status(400).json({
            error: `Invalid URL: ${error.message}`
        });
    }
});
```

"我觉得可能是..." 你开始解释, 但突然停住了。

你注意到后端代码在手动解析查询参数, 而不是使用标准的 URLSearchParams API。而且, 当 URL 没有查询参数时, `info.query` 是空字符串, `substring(1)` 会返回空字符串, 然后 `split('&')` 会得到一个包含空字符串的数组...

但更大的问题是, 你输入的测试 URL `https://example.com/search?q=javascript&sort=date#results` 在你的本地环境测试时是工作的, 为什么现在失败了?

---

## 真相发现

你决定直接在浏览器控制台测试 URL 解析:

```javascript
const url = new URL('https://example.com/search?q=javascript&sort=date#results');
console.log(url.search);
// "?q=javascript&sort=date"

console.log(url.searchParams.get('q'));
// "javascript"

console.log(url.searchParams.get('sort'));
// "date"
```

"看起来解析是正常的," 你对着直播间说。

然后你想到了一个可能——会不会是输入框的值有问题?

你在控制台输出了实际发送的数据:

```javascript
const input = document.querySelector('#url-input');
console.log('输入的值:', input.value);
console.log('实际长度:', input.value.length);

// 输出:
// "https://example.com/search?q=javascript&sort=date#results"
// 62
```

等等, 62 个字符? 你数了一下, 应该是 61 个字符才对。

你仔细检查输入框的值, 使用 `Array.from()` 查看每个字符:

```javascript
const chars = Array.from(input.value);
console.log(chars.length);  // 62

// 查看最后几个字符
console.log(chars.slice(-5));
// ["s", "u", "l", "t", "s", " "]  ← 最后有个空格!
```

"找到了!" 你惊呼, "输入框末尾有个不可见的空格!"

你快速检查输入框的配置:

```html
<input
    type="text"
    id="url-input"
    placeholder="输入任意 URL, 一键生成美化链接"
/>
```

没有 `trim()` 处理! 用户复制粘贴 URL 时, 很容易带上额外的空格。

你立即修复代码:

```javascript
async function generateShareLink(originalUrl) {
    // ✅ 修复: 去除首尾空格
    const trimmedUrl = originalUrl.trim();

    try {
        const url = new URL(trimmedUrl);
        // ...
    } catch (error) {
        // ...
    }
}
```

但问题还没完全解决。你意识到后端的查询参数解析也有问题——为什么要手动解析, 而不用标准 API?

你快速重构了后端代码:

```javascript
app.post('/api/share/create', (req, res) => {
    const { url } = req.body;

    try {
        // ✅ 使用标准 URL API
        const parsedUrl = new URL(url.trim());

        // ✅ 使用 URLSearchParams 解析查询参数
        const params = {};
        parsedUrl.searchParams.forEach((value, key) => {
            params[key] = value;  // 已自动解码
        });

        // 生成短链接
        const shortId = generateShortId();
        saveToDatabase(shortId, {
            originalUrl: url.trim(),
            protocol: parsedUrl.protocol,
            host: parsedUrl.host,
            pathname: parsedUrl.pathname,
            params: params,
            hash: parsedUrl.hash
        });

        res.json({
            success: true,
            shortUrl: `https://share.oursite.com/s/${shortId}`,
            preview: {
                title: extractTitle(url),
                description: extractDescription(url)
            }
        });

    } catch (error) {
        res.status(400).json({
            error: `Invalid URL: ${error.message}`
        });
    }
});
```

你快速部署修复代码, 刷新演示页面, 重新测试:

```
输入: https://example.com/search?q=javascript&sort=date#results
结果: ✅ 生成成功!
```

"好了, 现在可以正常工作了," 你松了一口气。

评论区的氛围也缓和了:
```
用户L: 修好了!
用户M: trim() 是个好习惯
用户N: 学到了, URL 解析要用标准 API
```

但你心里清楚, 这次翻车暴露了更深层的问题。

---

## 深度理解

直播结束后, 你创建了一个完整的 URL 测试套件:

```javascript
// URL 对象完整测试

// 测试 1: URL 构造函数的基本使用
try {
    const url = new URL('https://example.com:8080/path/to/page?name=Alice&age=25#section');

    console.log('完整 URL:', url.href);
    // "https://example.com:8080/path/to/page?name=Alice&age=25#section"

    console.log('协议:', url.protocol);    // "https:"
    console.log('主机名:', url.hostname);  // "example.com"
    console.log('端口:', url.port);        // "8080"
    console.log('主机:', url.host);        // "example.com:8080"
    console.log('路径:', url.pathname);    // "/path/to/page"
    console.log('查询:', url.search);      // "?name=Alice&age=25"
    console.log('锚点:', url.hash);        // "#section"
    console.log('源:', url.origin);        // "https://example.com:8080"

} catch (error) {
    console.error('无效的 URL:', error);
}

// 测试 2: 相对 URL 需要 base URL
try {
    const url = new URL('/api/users');  // ❌ 错误: 缺少 base URL
} catch (error) {
    console.error(error.message);  // "Failed to construct 'URL': Invalid URL"
}

// ✅ 正确: 提供 base URL
const url = new URL('/api/users', 'https://api.example.com');
console.log(url.href);  // "https://api.example.com/api/users"

// 测试 3: base URL 的智能解析
const base = 'https://example.com/blog/';

console.log(new URL('post-123', base).href);
// "https://example.com/blog/post-123"  ← 相对于 base

console.log(new URL('./post-123', base).href);
// "https://example.com/blog/post-123"  ← 相对于当前目录

console.log(new URL('../about', base).href);
// "https://example.com/about"  ← 上级目录

console.log(new URL('/api/data', base).href);
// "https://example.com/api/data"  ← 绝对路径 (忽略 base 的路径部分)

console.log(new URL('https://other.com', base).href);
// "https://other.com"  ← 完整 URL (完全忽略 base)

// 测试 4: URLSearchParams 的强大功能
const url = new URL('https://example.com/search?q=javascript&lang=en&sort=date');

// 方式 1: 使用 searchParams 属性
console.log(url.searchParams.get('q'));       // "javascript"
console.log(url.searchParams.get('lang'));    // "en"
console.log(url.searchParams.get('sort'));    // "date"
console.log(url.searchParams.get('unknown')); // null

// 方式 2: 遍历所有参数
url.searchParams.forEach((value, key) => {
    console.log(`${key}: ${value}`);
});
// q: javascript
// lang: en
// sort: date

// 方式 3: 修改查询参数
url.searchParams.set('page', '2');        // 添加参数
url.searchParams.delete('sort');          // 删除参数
url.searchParams.append('tag', 'frontend');  // 添加重复参数
url.searchParams.append('tag', 'tutorial');

console.log(url.search);
// "?q=javascript&lang=en&page=2&tag=frontend&tag=tutorial"

// 方式 4: 获取所有同名参数
console.log(url.searchParams.getAll('tag'));
// ["frontend", "tutorial"]

// 方式 5: 检查参数是否存在
console.log(url.searchParams.has('q'));      // true
console.log(url.searchParams.has('unknown')); // false

// 方式 6: 转换为字符串
console.log(url.searchParams.toString());
// "q=javascript&lang=en&page=2&tag=frontend&tag=tutorial"
```

你又测试了 URL 编码和解码:

```javascript
// URL 编码测试

// 测试 1: URLSearchParams 自动编码
const params = new URLSearchParams();
params.set('name', '张三');          // 中文
params.set('query', 'a & b');        // 特殊字符
params.set('url', 'https://x.com');  // URL

console.log(params.toString());
// "name=%E5%BC%A0%E4%B8%89&query=a+%26+b&url=https%3A%2F%2Fx.com"

// 测试 2: 构造带编码参数的 URL
const url = new URL('https://example.com/search');
url.searchParams.set('q', '前端开发');
url.searchParams.set('filter', 'type:article & status:published');

console.log(url.href);
// "https://example.com/search?q=%E5%89%8D%E7%AB%AF%E5%BC%80%E5%8F%91&filter=type%3Aarticle+%26+status%3Apublished"

// 测试 3: 解码自动进行
const decodedQ = url.searchParams.get('q');
console.log(decodedQ);  // "前端开发"  ← 自动解码

// 测试 4: 手动编码和解码 (不推荐)
const encoded = encodeURIComponent('你好 world');
console.log(encoded);  // "%E4%BD%A0%E5%A5%BD%20world"

const decoded = decodeURIComponent(encoded);
console.log(decoded);  // "你好 world"

// ⚠️ 注意: encodeURI vs encodeURIComponent 的区别
console.log(encodeURI('https://example.com/path?q=你好'));
// "https://example.com/path?q=%E4%BD%A0%E5%A5%BD"  ← 保留 URL 结构字符

console.log(encodeURIComponent('https://example.com/path?q=你好'));
// "https%3A%2F%2Fexample.com%2Fpath%3Fq%3D%E4%BD%A0%E5%A5%BD"  ← 编码所有特殊字符
```

---

## 常见陷阱与最佳实践

你整理了 URL 处理的常见错误:

```javascript
// ❌ 错误 1: 忘记 trim() 空格
function parseUrl(input) {
    return new URL(input);  // ❌ 用户输入可能带空格
}

// ✅ 正确: 始终 trim
function parseUrl(input) {
    return new URL(input.trim());
}

// ❌ 错误 2: 假设所有 URL 都是绝对 URL
function getHostname(url) {
    const parsed = new URL(url);  // ❌ 相对 URL 会报错
    return parsed.hostname;
}

// ✅ 正确: 提供 base URL 处理相对 URL
function getHostname(url, base = window.location.href) {
    const parsed = new URL(url, base);
    return parsed.hostname;
}

// ❌ 错误 3: 手动解析查询参数
function getQueryParam(url, key) {
    const queryStart = url.indexOf('?');
    const queryString = url.substring(queryStart + 1);
    const pairs = queryString.split('&');

    for (const pair of pairs) {
        const [k, v] = pair.split('=');
        if (k === key) {
            return v;  // ❌ 没有解码, 没有处理重复参数
        }
    }

    return null;
}

// ✅ 正确: 使用 URLSearchParams
function getQueryParam(url, key) {
    const parsed = new URL(url);
    return parsed.searchParams.get(key);  // ✅ 自动解码
}

// ❌ 错误 4: 修改 URL 时直接拼接字符串
function addQueryParam(url, key, value) {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}${key}=${value}`;  // ❌ 没有编码, 忽略已有参数
}

// ✅ 正确: 使用 URL 对象
function addQueryParam(url, key, value) {
    const parsed = new URL(url);
    parsed.searchParams.set(key, value);  // ✅ 自动编码, 正确处理
    return parsed.href;
}

// ❌ 错误 5: 混淆 encodeURI 和 encodeURIComponent
function buildApiUrl(path, params) {
    const query = Object.entries(params)
        .map(([k, v]) => `${k}=${encodeURI(v)}`)  // ❌ 应该用 encodeURIComponent
        .join('&');

    return `https://api.example.com${path}?${query}`;
}

// ✅ 正确: 使用 URLSearchParams 避免混淆
function buildApiUrl(path, params) {
    const url = new URL(path, 'https://api.example.com');
    Object.entries(params).forEach(([k, v]) => {
        url.searchParams.set(k, v);  // ✅ 自动使用正确的编码
    });
    return url.href;
}

// ❌ 错误 6: 忽略 trailing slash 的影响
const url1 = new URL('api/users', 'https://example.com/v1');
console.log(url1.href);  // "https://example.com/api/users"  ← /v1 被覆盖!

const url2 = new URL('api/users', 'https://example.com/v1/');
console.log(url2.href);  // "https://example.com/v1/api/users"  ← 正确

// ✅ 正确: base URL 的路径部分应该以 / 结尾
function resolveUrl(relative, base) {
    // 确保 base 以 / 结尾
    const normalizedBase = base.endsWith('/') ? base : base + '/';
    return new URL(relative, normalizedBase).href;
}

// ❌ 错误 7: 没有验证 URL 格式
function fetchData(url) {
    return fetch(url);  // ❌ url 可能无效
}

// ✅ 正确: 验证 URL 格式
function fetchData(url) {
    try {
        const parsed = new URL(url);

        // 额外验证: 只允许 https
        if (parsed.protocol !== 'https:') {
            throw new Error('Only HTTPS is allowed');
        }

        return fetch(parsed.href);

    } catch (error) {
        throw new Error(`Invalid URL: ${error.message}`);
    }
}
```

你创建了一套实用的 URL 工具函数:

```javascript
// URL 工具库

class URLHelper {
    // 安全解析 URL
    static parse(input, base = undefined) {
        try {
            return new URL(input.trim(), base);
        } catch (error) {
            console.error('Invalid URL:', input, error);
            return null;
        }
    }

    // 验证 URL 格式
    static isValid(input, options = {}) {
        const {
            allowedProtocols = ['http:', 'https:'],
            requireHttps = false,
            allowedDomains = null
        } = options;

        try {
            const url = new URL(input.trim());

            // 检查协议
            if (requireHttps && url.protocol !== 'https:') {
                return false;
            }

            if (!allowedProtocols.includes(url.protocol)) {
                return false;
            }

            // 检查域名白名单
            if (allowedDomains && !allowedDomains.includes(url.hostname)) {
                return false;
            }

            return true;

        } catch (error) {
            return false;
        }
    }

    // 构建查询字符串
    static buildQuery(params) {
        const searchParams = new URLSearchParams();

        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                if (Array.isArray(value)) {
                    value.forEach(v => searchParams.append(key, v));
                } else {
                    searchParams.set(key, value);
                }
            }
        });

        return searchParams.toString();
    }

    // 解析查询字符串
    static parseQuery(queryString) {
        const params = {};
        const searchParams = new URLSearchParams(queryString);

        searchParams.forEach((value, key) => {
            if (params[key]) {
                // 已存在同名参数, 转换为数组
                if (Array.isArray(params[key])) {
                    params[key].push(value);
                } else {
                    params[key] = [params[key], value];
                }
            } else {
                params[key] = value;
            }
        });

        return params;
    }

    // 合并 URL 和查询参数
    static addParams(url, params) {
        const parsed = this.parse(url);
        if (!parsed) return url;

        Object.entries(params).forEach(([key, value]) => {
            parsed.searchParams.set(key, value);
        });

        return parsed.href;
    }

    // 移除指定查询参数
    static removeParams(url, keys) {
        const parsed = this.parse(url);
        if (!parsed) return url;

        keys.forEach(key => {
            parsed.searchParams.delete(key);
        });

        return parsed.href;
    }

    // 更新查询参数
    static updateParams(url, params) {
        const parsed = this.parse(url);
        if (!parsed) return url;

        Object.entries(params).forEach(([key, value]) => {
            if (value === null || value === undefined) {
                parsed.searchParams.delete(key);
            } else {
                parsed.searchParams.set(key, value);
            }
        });

        return parsed.href;
    }

    // 获取不带查询参数的 URL
    static getBaseUrl(url) {
        const parsed = this.parse(url);
        if (!parsed) return url;

        return `${parsed.origin}${parsed.pathname}`;
    }

    // 比较两个 URL 是否相同 (忽略查询参数顺序)
    static isSameUrl(url1, url2, options = {}) {
        const {
            ignoreProtocol = false,
            ignoreHash = false,
            ignoreQuery = false
        } = options;

        const parsed1 = this.parse(url1);
        const parsed2 = this.parse(url2);

        if (!parsed1 || !parsed2) return false;

        // 比较协议
        if (!ignoreProtocol && parsed1.protocol !== parsed2.protocol) {
            return false;
        }

        // 比较主机和路径
        if (parsed1.hostname !== parsed2.hostname || parsed1.pathname !== parsed2.pathname) {
            return false;
        }

        // 比较查询参数
        if (!ignoreQuery) {
            const params1 = Array.from(parsed1.searchParams.entries()).sort();
            const params2 = Array.from(parsed2.searchParams.entries()).sort();

            if (JSON.stringify(params1) !== JSON.stringify(params2)) {
                return false;
            }
        }

        // 比较 hash
        if (!ignoreHash && parsed1.hash !== parsed2.hash) {
            return false;
        }

        return true;
    }

    // 从 URL 中提取文件名
    static getFilename(url) {
        const parsed = this.parse(url);
        if (!parsed) return null;

        const pathname = parsed.pathname;
        const segments = pathname.split('/');
        return segments[segments.length - 1] || null;
    }

    // 从 URL 中提取文件扩展名
    static getExtension(url) {
        const filename = this.getFilename(url);
        if (!filename) return null;

        const dotIndex = filename.lastIndexOf('.');
        return dotIndex !== -1 ? filename.substring(dotIndex + 1) : null;
    }

    // 规范化 URL (统一格式)
    static normalize(url) {
        const parsed = this.parse(url);
        if (!parsed) return url;

        // 移除默认端口
        if ((parsed.protocol === 'http:' && parsed.port === '80') ||
            (parsed.protocol === 'https:' && parsed.port === '443')) {
            parsed.port = '';
        }

        // 移除 trailing slash (除非是根路径)
        if (parsed.pathname !== '/' && parsed.pathname.endsWith('/')) {
            parsed.pathname = parsed.pathname.slice(0, -1);
        }

        // 统一查询参数顺序
        const sortedParams = new URLSearchParams(
            Array.from(parsed.searchParams.entries()).sort()
        );

        const result = new URL(parsed.origin + parsed.pathname);
        result.search = sortedParams.toString();
        result.hash = parsed.hash;

        return result.href;
    }
}

// 使用示例
console.log(URLHelper.isValid('https://example.com', { requireHttps: true }));  // true

const query = URLHelper.buildQuery({
    name: 'Alice',
    tags: ['frontend', 'javascript'],
    page: 1
});
console.log(query);  // "name=Alice&tags=frontend&tags=javascript&page=1"

const newUrl = URLHelper.addParams('https://example.com/search', {
    q: 'javascript',
    lang: 'en'
});
console.log(newUrl);  // "https://example.com/search?q=javascript&lang=en"

console.log(URLHelper.isSameUrl(
    'https://example.com/page?a=1&b=2',
    'https://example.com/page?b=2&a=1'  // 参数顺序不同
));  // true

console.log(URLHelper.getFilename('https://example.com/downloads/file.pdf'));  // "file.pdf"

console.log(URLHelper.normalize('http://example.com:80/path/?b=2&a=1#section'));
// "http://example.com/path?a=1&b=2#section"  ← 移除默认端口, 排序参数
```

---

## 前端路由与 URL 管理

你还实现了单页应用的 URL 管理:

```javascript
// SPA 路由管理

class Router {
    constructor() {
        this.routes = new Map();
        this.currentRoute = null;

        // 监听浏览器前进/后退
        window.addEventListener('popstate', (e) => {
            this.handleRouteChange(window.location.href, e.state);
        });
    }

    // 注册路由
    on(path, handler) {
        this.routes.set(path, handler);
    }

    // 导航到指定路由
    navigate(path, state = {}) {
        const url = new URL(path, window.location.origin);

        // 更新浏览器历史
        window.history.pushState(state, '', url.href);

        // 处理路由变化
        this.handleRouteChange(url.href, state);
    }

    // 替换当前路由
    replace(path, state = {}) {
        const url = new URL(path, window.location.origin);

        window.history.replaceState(state, '', url.href);

        this.handleRouteChange(url.href, state);
    }

    // 处理路由变化
    handleRouteChange(href, state) {
        const url = new URL(href);
        const pathname = url.pathname;

        // 查找匹配的路由
        const handler = this.routes.get(pathname) || this.routes.get('*');

        if (handler) {
            this.currentRoute = {
                path: pathname,
                query: Object.fromEntries(url.searchParams.entries()),
                hash: url.hash,
                state: state
            };

            handler(this.currentRoute);
        } else {
            console.warn('No route handler found for:', pathname);
        }
    }

    // 获取当前查询参数
    getQueryParams() {
        const url = new URL(window.location.href);
        return Object.fromEntries(url.searchParams.entries());
    }

    // 更新查询参数 (不刷新页面)
    setQueryParams(params, replace = false) {
        const url = new URL(window.location.href);

        Object.entries(params).forEach(([key, value]) => {
            if (value === null || value === undefined) {
                url.searchParams.delete(key);
            } else {
                url.searchParams.set(key, value);
            }
        });

        if (replace) {
            window.history.replaceState({}, '', url.href);
        } else {
            window.history.pushState({}, '', url.href);
        }

        // 触发路由变化
        this.handleRouteChange(url.href, {});
    }

    // 返回上一页
    back() {
        window.history.back();
    }

    // 前进下一页
    forward() {
        window.history.forward();
    }
}

// 使用示例
const router = new Router();

// 注册路由
router.on('/home', (route) => {
    console.log('Home page', route);
    document.title = 'Home';
});

router.on('/search', (route) => {
    console.log('Search page', route.query);
    const query = route.query.q || '';
    document.title = `Search: ${query}`;
    performSearch(query);
});

router.on('/post/:id', (route) => {
    console.log('Post page', route);
    const postId = route.params.id;
    loadPost(postId);
});

// 导航
router.navigate('/search?q=javascript&lang=en');

// 更新查询参数
router.setQueryParams({ page: 2 }, true);  // replace = true, 不增加历史记录
```

---

## 知识总结: URL 对象的核心机制

**规则 1: URL 构造函数需要有效的绝对 URL 或 base URL**

URL 构造函数可以接受两个参数: `url` 和可选的 `base`。

```javascript
// ✅ 绝对 URL (不需要 base)
const url1 = new URL('https://example.com/path');
console.log(url1.href);  // "https://example.com/path"

// ✅ 相对 URL + base URL
const url2 = new URL('/api/users', 'https://example.com');
console.log(url2.href);  // "https://example.com/api/users"

// ❌ 相对 URL 没有 base (报错)
try {
    const url3 = new URL('/api/users');
} catch (error) {
    console.error(error.message);  // "Failed to construct 'URL': Invalid URL"
}

// ✅ 使用当前页面作为 base
const url4 = new URL('/api/users', window.location.href);
console.log(url4.href);  // "https://[current-domain]/api/users"
```

相对 URL 的解析规则:
- **以 `/` 开头**: 相对于 origin (协议 + 域名 + 端口)
- **不以 `/` 开头**: 相对于 base 的完整路径
- **以 `./` 开头**: 相对于 base 的当前目录
- **以 `../` 开头**: 相对于 base 的上级目录

---

**规则 2: URL 对象的属性都是可读写的**

修改 URL 对象的属性会自动更新 `href`。

```javascript
const url = new URL('https://example.com:8080/path?q=test#section');

// 修改协议
url.protocol = 'http:';
console.log(url.href);  // "http://example.com:8080/path?q=test#section"

// 修改主机名
url.hostname = 'api.example.com';
console.log(url.href);  // "http://api.example.com:8080/path?q=test#section"

// 修改端口
url.port = '3000';
console.log(url.href);  // "http://api.example.com:3000/path?q=test#section"

// 修改路径
url.pathname = '/api/data';
console.log(url.href);  // "http://api.example.com:3000/api/data?q=test#section"

// 修改查询参数
url.search = '?page=2&limit=10';
console.log(url.href);  // "http://api.example.com:3000/api/data?page=2&limit=10#section"

// 修改 hash
url.hash = '#results';
console.log(url.href);  // "http://api.example.com:3000/api/data?page=2&limit=10#results"
```

只读属性:
- `url.origin`: 协议 + 域名 + 端口 (只读)
- `url.searchParams`: URLSearchParams 对象 (可通过其方法修改)

---

**规则 3: URLSearchParams 自动处理编码和解码**

URLSearchParams 是操作查询参数的标准 API, 自动处理 URL 编码。

```javascript
const params = new URLSearchParams();

// 设置参数 (自动编码)
params.set('name', '张三');        // 中文
params.set('query', 'a & b');      // 特殊字符
params.set('url', 'https://x.com'); // URL

console.log(params.toString());
// "name=%E5%BC%A0%E4%B8%89&query=a+%26+b&url=https%3A%2F%2Fx.com"

// 获取参数 (自动解码)
console.log(params.get('name'));   // "张三"  ← 自动解码
console.log(params.get('query'));  // "a & b"

// 从字符串创建
const params2 = new URLSearchParams('?name=%E5%BC%A0%E4%B8%89&age=25');
console.log(params2.get('name'));  // "张三"  ← 自动解码

// 从对象创建
const params3 = new URLSearchParams({
    name: '李四',
    age: 30
});
console.log(params3.toString());  // "name=%E6%9D%8E%E5%9B%9B&age=30"

// 从数组创建
const params4 = new URLSearchParams([
    ['name', '王五'],
    ['tag', 'frontend'],
    ['tag', 'javascript']  // 重复参数
]);
console.log(params4.getAll('tag'));  // ["frontend", "javascript"]
```

URLSearchParams 的方法:
- `get(key)`: 获取单个值
- `getAll(key)`: 获取所有同名参数的值
- `set(key, value)`: 设置参数 (覆盖已有)
- `append(key, value)`: 添加参数 (保留已有)
- `delete(key)`: 删除参数
- `has(key)`: 检查参数是否存在
- `forEach(callback)`: 遍历参数
- `entries()`, `keys()`, `values()`: 迭代器

---

**规则 4: 用户输入的 URL 必须 trim() 处理**

用户复制粘贴 URL 时常带有不可见的空格, 必须先 trim()。

```javascript
// ❌ 常见错误: 不处理空格
function parseUrl(input) {
    return new URL(input);  // 可能报错或解析错误
}

// 用户输入: "https://example.com "  ← 末尾有空格
parseUrl('https://example.com ');  // ❌ 报错

// ✅ 正确: 始终 trim
function parseUrl(input) {
    return new URL(input.trim());
}

parseUrl('https://example.com ');  // ✅ 正常工作

// ✅ 更好: 封装安全的解析函数
function safeParseUrl(input, base = undefined) {
    if (!input || typeof input !== 'string') {
        return null;
    }

    try {
        return new URL(input.trim(), base);
    } catch (error) {
        console.warn('Invalid URL:', input, error);
        return null;
    }
}

// 使用
const url = safeParseUrl(userInput);
if (url) {
    // 解析成功
} else {
    // 无效 URL
}
```

为什么需要 trim():
- **复制粘贴**: 用户从其他地方复制时可能带上空格
- **手动输入**: 用户输入时可能不小心敲了空格
- **表单提交**: HTML 表单不会自动 trim
- **URL 验证**: 浏览器对 URL 格式要求严格

---

**规则 5: base URL 的 trailing slash 影响相对路径解析**

base URL 是否以 `/` 结尾会影响相对路径的解析结果。

```javascript
// 情况 1: base 没有 trailing slash
const base1 = 'https://example.com/api/v1';

console.log(new URL('users', base1).href);
// "https://example.com/api/users"  ← /v1 被替换!

console.log(new URL('/users', base1).href);
// "https://example.com/users"  ← 绝对路径, 忽略 base 的路径

// 情况 2: base 有 trailing slash
const base2 = 'https://example.com/api/v1/';

console.log(new URL('users', base2).href);
// "https://example.com/api/v1/users"  ← 正确拼接

console.log(new URL('./users', base2).href);
// "https://example.com/api/v1/users"  ← 相同结果

console.log(new URL('../v2/users', base2).href);
// "https://example.com/api/v2/users"  ← 上级目录

// ✅ 最佳实践: 确保 base 以 / 结尾
function normalizeBase(base) {
    return base.endsWith('/') ? base : base + '/';
}

function resolveUrl(relative, base) {
    return new URL(relative, normalizeBase(base)).href;
}

console.log(resolveUrl('users', 'https://example.com/api/v1'));
// "https://example.com/api/v1/users"  ← 符合预期
```

解析规则总结:
- `相对路径` + `base/`: 拼接到 base 路径后
- `相对路径` + `base` (无 /): 替换 base 的最后一段
- `/绝对路径` + `base`: 只使用 base 的 origin
- `完整URL` + `base`: 完全忽略 base

---

**规则 6: 不要手动拼接或解析 URL, 使用 URL API**

手动字符串操作容易出错, 应始终使用 URL API。

```javascript
// ❌ 错误 1: 手动拼接查询参数
function addQueryParam(url, key, value) {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}${key}=${value}`;
}

addQueryParam('https://example.com/search?q=test', 'page', '2 & 3');
// "https://example.com/search?q=test&page=2 & 3"  ← ❌ 没有编码

// ✅ 正确: 使用 URL API
function addQueryParam(url, key, value) {
    const parsed = new URL(url);
    parsed.searchParams.set(key, value);  // 自动编码
    return parsed.href;
}

addQueryParam('https://example.com/search?q=test', 'page', '2 & 3');
// "https://example.com/search?q=test&page=2+%26+3"  ← ✅ 正确编码

// ❌ 错误 2: 手动解析查询参数
function getQueryParam(url, key) {
    const parts = url.split('?');
    if (parts.length < 2) return null;

    const pairs = parts[1].split('&');
    for (const pair of pairs) {
        const [k, v] = pair.split('=');
        if (k === key) {
            return v;  // ❌ 没有解码
        }
    }
    return null;
}

getQueryParam('https://example.com?name=%E5%BC%A0%E4%B8%89', 'name');
// "%E5%BC%A0%E4%B8%89"  ← ❌ 应该是 "张三"

// ✅ 正确: 使用 URLSearchParams
function getQueryParam(url, key) {
    const parsed = new URL(url);
    return parsed.searchParams.get(key);  // 自动解码
}

getQueryParam('https://example.com?name=%E5%BC%A0%E4%B8%89', 'name');
// "张三"  ← ✅ 正确解码

// ❌ 错误 3: 手动修改域名
function changeHost(url, newHost) {
    return url.replace(/https?:\/\/[^\/]+/, `https://${newHost}`);
}

changeHost('https://example.com:8080/path', 'api.example.com');
// "https://api.example.com/path"  ← ❌ 丢失端口号!

// ✅ 正确: 使用 URL 属性
function changeHost(url, newHost) {
    const parsed = new URL(url);
    parsed.hostname = newHost;  // 保留端口
    return parsed.href;
}

changeHost('https://example.com:8080/path', 'api.example.com');
// "https://api.example.com:8080/path"  ← ✅ 保留端口
```

为什么不要手动操作:
- **编码问题**: 容易忘记编码/解码
- **边界情况**: 难以处理所有边界情况
- **维护困难**: 正则表达式难以维护
- **性能**: 浏览器的原生 API 更快

---

**规则 7: URL 验证应该明确要求和限制**

不同场景对 URL 的要求不同, 验证时应明确约束。

```javascript
// 完整的 URL 验证函数
function validateUrl(input, options = {}) {
    const {
        requireProtocol = true,
        allowedProtocols = ['http:', 'https:'],
        requireHttps = false,
        allowedDomains = null,  // null 表示允许所有域名
        allowLocalhost = true,
        requirePath = false
    } = options;

    // 1. 基本格式验证
    let url;
    try {
        url = new URL(input.trim());
    } catch (error) {
        return {
            valid: false,
            error: 'Invalid URL format'
        };
    }

    // 2. 协议验证
    if (!allowedProtocols.includes(url.protocol)) {
        return {
            valid: false,
            error: `Protocol must be one of: ${allowedProtocols.join(', ')}`
        };
    }

    if (requireHttps && url.protocol !== 'https:') {
        return {
            valid: false,
            error: 'HTTPS is required'
        };
    }

    // 3. 域名验证
    if (!allowLocalhost && (url.hostname === 'localhost' || url.hostname === '127.0.0.1')) {
        return {
            valid: false,
            error: 'Localhost is not allowed'
        };
    }

    if (allowedDomains && !allowedDomains.includes(url.hostname)) {
        return {
            valid: false,
            error: `Domain must be one of: ${allowedDomains.join(', ')}`
        };
    }

    // 4. 路径验证
    if (requirePath && url.pathname === '/') {
        return {
            valid: false,
            error: 'URL must have a path'
        };
    }

    return {
        valid: true,
        url: url
    };
}

// 使用示例

// 场景 1: API 接口 (必须 HTTPS)
const result1 = validateUrl('https://api.example.com/users', {
    requireHttps: true,
    allowedDomains: ['api.example.com']
});

// 场景 2: 用户分享链接 (允许 HTTP 和 HTTPS)
const result2 = validateUrl('http://blog.example.com/post-123', {
    requireHttps: false
});

// 场景 3: 外部资源 (不允许 localhost)
const result3 = validateUrl('https://localhost:3000/image.png', {
    allowLocalhost: false
});

// 场景 4: 文件下载 (必须有路径)
const result4 = validateUrl('https://cdn.example.com', {
    requirePath: true
});
```

---

**规则 8: origin 是只读的, 由 protocol + hostname + port 组成**

`url.origin` 是只读属性, 不能直接修改, 必须分别修改组成部分。

```javascript
const url = new URL('https://example.com:8080/path');

// ❌ 不能直接修改 origin
try {
    url.origin = 'https://api.example.com:3000';
} catch (error) {
    console.error('origin is read-only');
}

console.log(url.origin);  // "https://example.com:8080"

// ✅ 正确: 分别修改 protocol, hostname, port
url.protocol = 'http:';
url.hostname = 'api.example.com';
url.port = '3000';

console.log(url.origin);  // "http://api.example.com:3000"
console.log(url.href);    // "http://api.example.com:3000/path"

// origin 的组成规则
console.log(new URL('https://example.com').origin);
// "https://example.com"  ← 默认端口 443 不显示

console.log(new URL('http://example.com').origin);
// "http://example.com"  ← 默认端口 80 不显示

console.log(new URL('https://example.com:443').origin);
// "https://example.com"  ← 默认端口被省略

console.log(new URL('https://example.com:8080').origin);
// "https://example.com:8080"  ← 非默认端口显示
```

origin 的用途:
- **同源策略**: 判断两个 URL 是否同源
- **CORS**: Access-Control-Allow-Origin 头
- **安全验证**: 验证请求来源
- **API 基础路径**: 构建 API 端点

---

**事故档案编号**: NETWORK-2024-1950
**影响范围**: URL, URLSearchParams, URL 解析, 查询参数编码, 相对 URL 解析
**根本原因**: 用户输入 URL 末尾带空格导致解析失败, 后端手动解析查询参数而非使用标准 API
**学习成本**: 中 (需理解 URL 结构和编码规则)

这是 JavaScript 世界第 150 次被记录的网络与数据事故。URL 构造函数需要有效的绝对 URL 或提供 base URL。URL 对象的所有属性都是可读写的, 修改属性会自动更新 href。URLSearchParams 是操作查询参数的标准 API, 自动处理编码和解码。用户输入的 URL 必须 trim() 处理, 避免不可见空格导致解析失败。base URL 的 trailing slash 会影响相对路径的解析结果。不要手动拼接或解析 URL, 应始终使用 URL API 避免编码问题和边界情况。URL 验证应该明确要求和限制, 针对不同场景设置不同的验证规则。`url.origin` 是只读属性, 由 `protocol + hostname + port` 组成。理解 URL 的标准解析机制和 API 使用是正确处理链接的基础。

---
