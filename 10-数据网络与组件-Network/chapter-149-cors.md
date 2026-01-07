《第 149 次记录: 幽灵般的跨域错误 —— CORS 的间歇性谜案》

---

## 谜题现场

周三上午九点二十分, 你收到测试团队的 Bug 报告。

"用户信息接口有时候能调通, 有时候报 CORS 错误," QA 小林在 Slack 上说, "而且没有规律, 刷新几次就好了, 再刷新又不行了。"

你皱起眉头。CORS 错误应该是稳定复现的——要么配置对了, 要么配置错了, 怎么会间歇性出现?

你打开测试环境的页面, 尝试登录。第一次, 成功了。你刷新页面重新登录, 还是成功。再刷新一次——

```
Access to fetch at 'https://api.example.com/user/profile' from origin 'https://app.example.com'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

"出现了," 你盯着红色的错误信息。你再刷新一次, 这次又成功了。

这太诡异了。同一个请求, 同一个浏览器, 同一个环境, 结果却在成功和失败之间随机切换。

你打开 Network 面板, 仔细观察每一次请求。成功的请求看起来很正常:

```
Request URL: https://api.example.com/user/profile
Request Method: GET
Status Code: 200 OK

Response Headers:
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
Content-Type: application/json
```

但失败的请求...等等, 失败的请求根本没有响应头! 或者说, 浏览器拦截了响应, 你看不到服务器返回的内容。

你快速检查后端代码, CORS 配置看起来完全正确:

```javascript
// 后端 CORS 中间件
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', 'https://app.example.com');
    res.header('Access-Control-Allow-Credentials', 'true');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    next();
});
```

"配置没问题啊..." 你喃喃自语。但为什么会间歇性失败?

---

## 线索收集

上午十点, 你决定系统地收集线索。

你创建了一个测试页面, 连续发送 20 个相同的请求, 观察成功率:

```javascript
// 测试脚本
async function testCORS() {
    const results = [];

    for (let i = 0; i < 20; i++) {
        try {
            const response = await fetch('https://api.example.com/user/profile', {
                credentials: 'include'
            });

            results.push({
                attempt: i + 1,
                status: 'success',
                statusCode: response.status
            });

        } catch (error) {
            results.push({
                attempt: i + 1,
                status: 'failed',
                error: error.message
            });
        }

        await new Promise(resolve => setTimeout(resolve, 100));  // 间隔 100ms
    }

    console.table(results);
}
```

测试结果让你更加困惑:

```
Attempt | Status  | StatusCode | Error
--------|---------|------------|-------
1       | success | 200        |
2       | success | 200        |
3       | success | 200        |
4       | failed  |            | CORS error
5       | success | 200        |
6       | success | 200        |
7       | success | 200        |
8       | failed  |            | CORS error
...
```

20 次请求中, 有 6 次失败, 成功率 70%。而且失败的时机看起来完全随机。

"难道是服务器有多个实例, 配置不一致?" 你想到一个可能性。

你检查了服务器的负载均衡配置, 确实有 3 个后端实例在运行。你登录到每个实例, 检查 CORS 配置——完全一致。

"排除服务器配置问题," 你在笔记本上记录。

---

## 假设验证

中午十二点, 你吃着外卖, 继续思考这个问题。

你想起了 HTTP 缓存——会不会是浏览器缓存了某些 CORS 预检请求的结果?

你清空了浏览器缓存, 重新测试。问题依然存在。

"不是缓存," 你又在笔记本上划掉一条线索。

下午一点半, 你决定从另一个角度入手——仔细观察 Network 面板中成功和失败请求的细节。

你慢动作刷新页面, 盯着 Network 面板。突然, 你注意到一个奇怪的现象:

**成功的请求:**
```
Request Method: GET
Request Headers:
  Cookie: session_id=abc123
  Accept: application/json
```

**失败的请求前会先出现一个 OPTIONS 请求:**
```
Request Method: OPTIONS  <-- 这是什么?
Request Headers:
  Access-Control-Request-Method: GET
  Access-Control-Request-Headers: authorization
  Origin: https://app.example.com
```

"OPTIONS 请求?" 你愣住了。为什么有些请求会先发送 OPTIONS, 有些不会?

你快速搜索文档, 发现了关键信息: **CORS 预检请求 (Preflight Request)**。

当浏览器发送跨域请求时, 如果请求不是 "简单请求", 浏览器会先发送一个 OPTIONS 预检请求, 询问服务器是否允许真正的请求。

"简单请求?" 你继续查阅文档, 发现了 "简单请求" 的定义:

1. 请求方法是 GET, POST, 或 HEAD
2. 请求头只包含安全的头部 (如 Accept, Content-Type 等)
3. Content-Type 只能是 `application/x-www-form-urlencoded`, `multipart/form-data`, 或 `text/plain`

你回头检查前端代码:

```javascript
// 登录请求
async function login(username, password) {
    const response = await fetch('https://api.example.com/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'  // ✅ 简单请求
        },
        body: JSON.stringify({ username, password })
    });

    return response.json();
}

// 获取用户信息 (登录后)
async function getUserProfile() {
    const response = await fetch('https://api.example.com/user/profile', {
        credentials: 'include',
        headers: {
            'Authorization': `Bearer ${getToken()}`  // ❌ 触发预检请求!
        }
    });

    return response.json();
}
```

"找到了!" 你惊呼。

登录请求是简单请求, 不需要预检。但获取用户信息的请求包含了自定义的 `Authorization` 头, 不是简单请求, 所以触发了预检!

你快速验证这个假设——去掉 `Authorization` 头, 改用 Cookie 传递 token:

```javascript
async function getUserProfile() {
    const response = await fetch('https://api.example.com/user/profile', {
        credentials: 'include'  // 只用 Cookie, 不用 Authorization 头
    });

    return response.json();
}
```

测试 20 次——全部成功! CORS 错误消失了。

"所以问题不在 GET 请求, 而在预检请求," 你总结。但为什么预检请求会间歇性失败?

---

## 真相浮现

下午三点, 你回到后端代码, 这次专门查看 OPTIONS 请求的处理。

你发现了一个微妙的问题:

```javascript
// 后端路由
app.use((req, res, next) => {
    // 设置 CORS 头
    res.header('Access-Control-Allow-Origin', 'https://app.example.com');
    res.header('Access-Control-Allow-Credentials', 'true');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    next();  // ⚠️ 继续执行后续中间件
});

// 身份验证中间件
app.use((req, res, next) => {
    if (req.path.startsWith('/user')) {
        const token = req.cookies.session_id;
        if (!token) {
            return res.status(401).json({ error: 'Unauthorized' });  // ❌ 预检请求被拦截!
        }
    }
    next();
});

// 用户路由
app.get('/user/profile', (req, res) => {
    res.json({ name: 'Alice', email: 'alice@example.com' });
});
```

"问题在这里!" 你看到了根本原因。

当浏览器发送 OPTIONS 预检请求时:
1. CORS 中间件设置了正确的响应头
2. 但 `next()` 继续执行
3. 身份验证中间件检查 Cookie
4. 预检请求通常不带 Cookie! (浏览器行为)
5. 身份验证失败, 返回 401
6. 预检失败, 真正的 GET 请求不会发送
7. 浏览器报告 CORS 错误

但为什么是间歇性的? 你继续调查, 发现了第二个关键线索:

```javascript
// 浏览器的预检缓存机制
// 预检请求成功后, 浏览器会缓存结果一段时间 (默认 5 秒)
// 在缓存期间, 相同的请求不会再发送预检

// 场景 1: 首次请求
// 1. 浏览器发送 OPTIONS 预检 → 被身份验证中间件拦截 → 401 → CORS 失败

// 场景 2: 登录后立即请求 (Cookie 还在)
// 1. 浏览器发送 OPTIONS 预检 → 身份验证通过 → 200 → 缓存预检结果
// 2. 浏览器发送真正的 GET 请求 → 成功
// 3. 后续请求使用缓存的预检结果 → 持续成功

// 场景 3: 预检缓存过期后
// 1. 浏览器重新发送 OPTIONS 预检 → 可能被拦截 → 间歇性失败
```

"完全理解了," 你在白板上画出完整的流程图:

```
用户刷新页面:
├─ 情况 A: 之前有成功的预检缓存 (5 秒内)
│  └─ 直接发送 GET 请求 (跳过预检) → 成功 ✅
│
├─ 情况 B: 预检缓存已过期, 且此时正好有有效 Cookie
│  ├─ 发送 OPTIONS 预检 → 身份验证通过 → 200
│  ├─ 缓存预检结果
│  └─ 发送 GET 请求 → 成功 ✅
│
└─ 情况 C: 预检缓存已过期, 且 Cookie 无效或不存在
   ├─ 发送 OPTIONS 预检 → 身份验证失败 → 401
   └─ 浏览器报告 CORS 错误 ❌
```

"间歇性的原因找到了," 你终于松了一口气。

---

## 根因修复

下午四点半, 你开始编写修复方案。

**核心原则: OPTIONS 预检请求应该在身份验证之前响应**

```javascript
// ✅ 修复后的代码
app.use((req, res, next) => {
    // 1. 设置 CORS 头
    res.header('Access-Control-Allow-Origin', 'https://app.example.com');
    res.header('Access-Control-Allow-Credentials', 'true');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    // 2. 如果是 OPTIONS 预检请求, 立即返回 200
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);  // ✅ 不继续执行后续中间件
    }

    next();  // 其他请求继续执行
});

// 身份验证中间件 (只对非 OPTIONS 请求执行)
app.use((req, res, next) => {
    if (req.path.startsWith('/user')) {
        const token = req.cookies.session_id;
        if (!token) {
            return res.status(401).json({ error: 'Unauthorized' });
        }
    }
    next();
});
```

你部署修复代码, 重新测试 100 次——全部成功! 间歇性 CORS 错误彻底消失了。

你又测试了预检缓存的行为:

```javascript
// 测试预检缓存
async function testPreflightCache() {
    console.log('第 1 次请求 (会发送预检):');
    await fetch('https://api.example.com/user/profile', {
        credentials: 'include',
        headers: { 'Authorization': 'Bearer token123' }
    });

    console.log('第 2 次请求 (3 秒后, 使用缓存的预检):');
    await new Promise(resolve => setTimeout(resolve, 3000));
    await fetch('https://api.example.com/user/profile', {
        credentials: 'include',
        headers: { 'Authorization': 'Bearer token123' }
    });

    console.log('第 3 次请求 (10 秒后, 预检缓存已过期):');
    await new Promise(resolve => setTimeout(resolve, 10000));
    await fetch('https://api.example.com/user/profile', {
        credentials: 'include',
        headers: { 'Authorization': 'Bearer token123' }
    });
}
```

Network 面板显示:
```
请求 1: OPTIONS (预检) + GET (实际请求)  ← 两个请求
请求 2: GET (实际请求)  ← 只有一个请求 (预检被缓存)
请求 3: OPTIONS (预检) + GET (实际请求)  ← 预检缓存过期, 重新预检
```

---

## 深度理解 CORS

你创建了一个完整的 CORS 测试套件:

```javascript
// CORS 测试: 简单请求 vs 预检请求

// ✅ 简单请求 (不触发预检)
async function simpleRequest() {
    // 条件 1: 方法是 GET, POST, HEAD
    // 条件 2: 只包含安全头部
    // 条件 3: Content-Type 是特定值

    await fetch('https://api.example.com/data', {
        method: 'GET',  // ✅ 简单方法
        credentials: 'include',
        headers: {
            'Accept': 'application/json'  // ✅ 安全头部
        }
    });
    // 浏览器直接发送请求, 不预检
}

// ❌ 复杂请求 (触发预检)
async function preflightRequest() {
    // 以下任一条件都会触发预检:

    // 原因 1: 自定义头部
    await fetch('https://api.example.com/data', {
        headers: {
            'X-Custom-Header': 'value'  // ❌ 触发预检
        }
    });

    // 原因 2: Authorization 头
    await fetch('https://api.example.com/data', {
        headers: {
            'Authorization': 'Bearer token'  // ❌ 触发预检
        }
    });

    // 原因 3: Content-Type 不是简单值
    await fetch('https://api.example.com/data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'  // ✅ 这个是安全的
        },
        body: JSON.stringify({ data: 'test' })
    });

    // 但如果是其他 Content-Type:
    await fetch('https://api.example.com/data', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/xml'  // ❌ 触发预检
        },
        body: '<data>test</data>'
    });

    // 原因 4: PUT, DELETE, PATCH 等方法
    await fetch('https://api.example.com/data', {
        method: 'PUT'  // ❌ 触发预检
    });

    // 原因 5: ReadableStream body
    await fetch('https://api.example.com/upload', {
        method: 'POST',
        body: new ReadableStream()  // ❌ 触发预检
    });
}
```

你又测试了预检请求的完整流程:

```javascript
// 预检请求详解
async function demonstratePreflight() {
    // 1. 浏览器发送 OPTIONS 预检请求
    // OPTIONS https://api.example.com/user/profile
    //
    // Request Headers:
    // Access-Control-Request-Method: GET
    // Access-Control-Request-Headers: authorization
    // Origin: https://app.example.com

    // 2. 服务器响应预检请求
    // HTTP/1.1 200 OK
    //
    // Response Headers:
    // Access-Control-Allow-Origin: https://app.example.com
    // Access-Control-Allow-Methods: GET, POST, PUT, DELETE
    // Access-Control-Allow-Headers: authorization, content-type
    // Access-Control-Allow-Credentials: true
    // Access-Control-Max-Age: 86400  ← 预检缓存时间 (24 小时)

    // 3. 浏览器检查预检响应
    if (preflightPassed) {
        // 4. 发送实际请求
        // GET https://api.example.com/user/profile
        //
        // Request Headers:
        // Authorization: Bearer token123
        // Origin: https://app.example.com
        // Cookie: session_id=abc123

        // 5. 服务器响应实际请求
        // HTTP/1.1 200 OK
        //
        // Response Headers:
        // Access-Control-Allow-Origin: https://app.example.com
        // Access-Control-Allow-Credentials: true
        // Content-Type: application/json
    } else {
        // 预检失败, 浏览器报告 CORS 错误, 不发送实际请求
        throw new Error('CORS preflight failed');
    }
}
```

你整理了 CORS 响应头的完整列表:

```javascript
// CORS 响应头完整指南

// 1. Access-Control-Allow-Origin (必需)
res.header('Access-Control-Allow-Origin', 'https://app.example.com');
// 或者允许所有域 (不推荐, 尤其是使用 credentials 时):
// res.header('Access-Control-Allow-Origin', '*');

// 2. Access-Control-Allow-Credentials (可选)
res.header('Access-Control-Allow-Credentials', 'true');
// ⚠️ 如果设置为 true, Allow-Origin 不能是 '*'

// 3. Access-Control-Allow-Methods (预检需要)
res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH');

// 4. Access-Control-Allow-Headers (预检需要)
res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Custom-Header');
// 或者允许所有请求头:
// res.header('Access-Control-Allow-Headers', req.headers['access-control-request-headers']);

// 5. Access-Control-Max-Age (预检缓存时间)
res.header('Access-Control-Max-Age', '86400');  // 24 小时 (秒)
// 注意: 浏览器有最大缓存时间限制 (Chrome: 2 小时, Firefox: 24 小时)

// 6. Access-Control-Expose-Headers (可选)
res.header('Access-Control-Expose-Headers', 'X-Total-Count, X-Page-Number');
// 默认情况下, 浏览器只能访问 7 个安全响应头:
// Cache-Control, Content-Language, Content-Type, Expires, Last-Modified, Pragma, Content-Length
// 自定义响应头需要显式暴露

// 7. Vary (重要)
res.header('Vary', 'Origin');
// 告诉缓存代理: 根据 Origin 头缓存不同的响应
```

---

## 完整的 CORS 解决方案

你编写了一个生产级的 CORS 中间件:

```javascript
// 生产级 CORS 中间件
function corsMiddleware(options = {}) {
    const {
        allowedOrigins = [],  // 允许的源列表
        allowCredentials = true,
        allowedMethods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
        allowedHeaders = ['Content-Type', 'Authorization'],
        exposedHeaders = [],
        maxAge = 86400  // 24 小时
    } = options;

    return (req, res, next) => {
        const origin = req.headers.origin;

        // 1. 检查 Origin 是否在白名单中
        const isAllowed = allowedOrigins.includes(origin) ||
                         allowedOrigins.includes('*');

        if (isAllowed) {
            // 2. 设置 Allow-Origin
            if (allowedOrigins.includes('*') && !allowCredentials) {
                res.header('Access-Control-Allow-Origin', '*');
            } else {
                res.header('Access-Control-Allow-Origin', origin);
                res.header('Vary', 'Origin');  // 重要!
            }

            // 3. 设置 Credentials
            if (allowCredentials) {
                res.header('Access-Control-Allow-Credentials', 'true');
            }

            // 4. 暴露自定义响应头
            if (exposedHeaders.length > 0) {
                res.header('Access-Control-Expose-Headers', exposedHeaders.join(', '));
            }
        }

        // 5. 处理预检请求
        if (req.method === 'OPTIONS') {
            if (isAllowed) {
                res.header('Access-Control-Allow-Methods', allowedMethods.join(', '));
                res.header('Access-Control-Allow-Headers', allowedHeaders.join(', '));
                res.header('Access-Control-Max-Age', maxAge);
                return res.sendStatus(200);  // ✅ 立即返回, 不继续执行
            } else {
                return res.sendStatus(403);  // Origin 不在白名单中
            }
        }

        // 6. 实际请求: 如果 Origin 不在白名单, 拒绝请求
        if (!isAllowed) {
            return res.status(403).json({
                error: 'CORS policy: Origin not allowed'
            });
        }

        next();
    };
}

// 使用示例
app.use(corsMiddleware({
    allowedOrigins: [
        'https://app.example.com',
        'https://app.staging.example.com',
        'http://localhost:3000'  // 开发环境
    ],
    allowCredentials: true,
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
    exposedHeaders: ['X-Total-Count', 'X-Page-Number'],
    maxAge: 86400
}));
```

你又实现了动态 Origin 验证:

```javascript
// 高级: 动态 Origin 验证
function advancedCorsMiddleware(options = {}) {
    const {
        originValidator = null,  // 自定义验证函数
        ...otherOptions
    } = options;

    return (req, res, next) => {
        const origin = req.headers.origin;

        // 动态验证 Origin
        let isAllowed = false;

        if (typeof originValidator === 'function') {
            isAllowed = originValidator(origin, req);
        } else if (Array.isArray(otherOptions.allowedOrigins)) {
            isAllowed = otherOptions.allowedOrigins.includes(origin);
        }

        // 其余逻辑同上...
        if (isAllowed) {
            res.header('Access-Control-Allow-Origin', origin);
            res.header('Vary', 'Origin');
            // ...
        }

        if (req.method === 'OPTIONS') {
            return isAllowed ? res.sendStatus(200) : res.sendStatus(403);
        }

        if (!isAllowed) {
            return res.status(403).json({ error: 'CORS policy: Origin not allowed' });
        }

        next();
    };
}

// 使用示例: 只允许以 .example.com 结尾的域名
app.use(advancedCorsMiddleware({
    originValidator: (origin, req) => {
        // 白名单模式
        if (!origin) return false;

        // 允许 example.com 的所有子域名
        if (origin.endsWith('.example.com')) {
            return true;
        }

        // 允许 localhost (开发环境)
        if (origin.startsWith('http://localhost:')) {
            return true;
        }

        // 允许特定用户访问 (动态权限)
        if (req.user && req.user.role === 'admin') {
            return true;
        }

        return false;
    },
    allowCredentials: true
}));
```

你还实现了前端的 CORS 错误处理:

```javascript
// 前端: 优雅处理 CORS 错误
async function fetchWithCorsHandling(url, options = {}) {
    try {
        const response = await fetch(url, options);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();

    } catch (error) {
        // CORS 错误的特征: TypeError + 'Failed to fetch'
        if (error instanceof TypeError && error.message === 'Failed to fetch') {
            console.error('CORS 错误: 可能的原因:');
            console.error('1. 服务器未设置正确的 CORS 头');
            console.error('2. 请求使用了不安全的头部或方法, 触发预检失败');
            console.error('3. 服务器对 OPTIONS 预检请求处理不当');
            console.error('4. Origin 不在服务器白名单中');

            // 用户友好的错误提示
            throw new Error('无法连接到服务器, 请检查网络连接或联系管理员');
        }

        throw error;
    }
}

// 使用
fetchWithCorsHandling('https://api.example.com/data', {
    credentials: 'include',
    headers: {
        'Authorization': 'Bearer token123'
    }
})
.then(data => console.log(data))
.catch(error => showErrorToUser(error.message));
```

---

## 常见陷阱与调试技巧

你总结了 CORS 的常见错误:

```javascript
// ❌ 错误 1: Allow-Origin 设置为 * 且使用 credentials
res.header('Access-Control-Allow-Origin', '*');
res.header('Access-Control-Allow-Credentials', 'true');  // ❌ 冲突

fetch('https://api.example.com/data', {
    credentials: 'include'  // ❌ 浏览器报错
});

// ✅ 正确: 使用具体的 Origin
res.header('Access-Control-Allow-Origin', req.headers.origin);
res.header('Access-Control-Allow-Credentials', 'true');

// ❌ 错误 2: 预检请求返回错误状态码
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    next();
});

app.options('/api/data', (req, res) => {
    res.status(404).send('Not found');  // ❌ 预检失败
});

// ✅ 正确: 预检请求返回 200
app.options('/api/data', (req, res) => {
    res.sendStatus(200);  // ✅
});

// ❌ 错误 3: 忘记设置 Vary 头
res.header('Access-Control-Allow-Origin', req.headers.origin);
// ❌ 缺少 Vary, 缓存代理可能返回错误的响应

// ✅ 正确: 始终设置 Vary
res.header('Access-Control-Allow-Origin', req.headers.origin);
res.header('Vary', 'Origin');  // ✅

// ❌ 错误 4: Allow-Headers 与实际请求头不匹配
res.header('Access-Control-Allow-Headers', 'Content-Type');

fetch('/api/data', {
    headers: {
        'Authorization': 'Bearer token'  // ❌ 不在允许列表中
    }
});

// ✅ 正确: 允许所有请求的头部
res.header('Access-Control-Allow-Headers',
    req.headers['access-control-request-headers'] || 'Content-Type, Authorization'
);

// ❌ 错误 5: 预检请求执行了业务逻辑
app.use(authenticate);  // 身份验证中间件

app.options('/api/data', (req, res) => {
    // ❌ OPTIONS 请求也会执行 authenticate
    res.sendStatus(200);
});

// ✅ 正确: OPTIONS 请求在身份验证之前返回
app.use((req, res, next) => {
    if (req.method === 'OPTIONS') {
        // 设置 CORS 头
        res.header('Access-Control-Allow-Origin', origin);
        // ...
        return res.sendStatus(200);  // ✅ 立即返回
    }
    next();
});

app.use(authenticate);  // 只对非 OPTIONS 请求执行

// ❌ 错误 6: 前端忘记设置 credentials
fetch('https://api.example.com/data');  // ❌ 不发送 Cookie

// ✅ 正确: 跨域请求带上 Cookie
fetch('https://api.example.com/data', {
    credentials: 'include'  // ✅
});

// ❌ 错误 7: 响应头没有在实际请求中设置
app.options('/api/data', (req, res) => {
    res.header('Access-Control-Allow-Origin', origin);
    res.sendStatus(200);
});

app.get('/api/data', (req, res) => {
    // ❌ 忘记设置 CORS 头
    res.json({ data: 'test' });
});

// ✅ 正确: 实际请求也要设置 CORS 头
app.get('/api/data', (req, res) => {
    res.header('Access-Control-Allow-Origin', origin);
    res.header('Access-Control-Allow-Credentials', 'true');
    res.json({ data: 'test' });
});
```

你创建了一个 CORS 调试清单:

```javascript
// CORS 调试清单

// 1. 确认请求是否跨域
const apiOrigin = new URL('https://api.example.com').origin;
const pageOrigin = window.location.origin;
console.log('是否跨域:', apiOrigin !== pageOrigin);

// 2. 检查是否触发预检
function willTriggerPreflight(url, options) {
    const method = options.method || 'GET';
    const headers = options.headers || {};

    // 检查方法
    if (!['GET', 'POST', 'HEAD'].includes(method)) {
        return true;
    }

    // 检查头部
    const safeHeaders = ['accept', 'accept-language', 'content-language', 'content-type'];
    for (const header of Object.keys(headers)) {
        if (!safeHeaders.includes(header.toLowerCase())) {
            return true;
        }
    }

    // 检查 Content-Type
    const contentType = headers['Content-Type'] || headers['content-type'];
    if (contentType) {
        const simpleTypes = [
            'application/x-www-form-urlencoded',
            'multipart/form-data',
            'text/plain'
        ];
        if (!simpleTypes.includes(contentType)) {
            return true;
        }
    }

    return false;
}

// 3. 查看预检请求
// Chrome DevTools → Network → Filter: OPTIONS
// 检查预检请求和响应的头部

// 4. 验证服务器响应
async function debugCors(url, options) {
    try {
        const response = await fetch(url, options);
        console.log('请求成功');
        console.log('响应头:', Object.fromEntries(response.headers.entries()));

    } catch (error) {
        console.error('CORS 错误');
        console.log('错误信息:', error.message);
        console.log('检查项:');
        console.log('1. 服务器是否设置 Access-Control-Allow-Origin?');
        console.log('2. 是否触发预检? 服务器是否正确处理 OPTIONS?');
        console.log('3. 是否使用 credentials? 服务器是否允许?');
        console.log('4. 自定义头部是否在 Allow-Headers 中?');
    }
}

// 5. 测试不同场景
async function testCorsScenarios() {
    const url = 'https://api.example.com/data';

    // 场景 1: 简单请求
    console.log('=== 测试简单请求 ===');
    await debugCors(url, {
        method: 'GET',
        credentials: 'include'
    });

    // 场景 2: 带自定义头的请求 (触发预检)
    console.log('=== 测试预检请求 ===');
    await debugCors(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
            'Authorization': 'Bearer token'
        }
    });

    // 场景 3: PUT 请求 (触发预检)
    console.log('=== 测试 PUT 请求 ===');
    await debugCors(url, {
        method: 'PUT',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ data: 'test' })
    });
}
```

---

## 知识总结: CORS 的核心机制

**规则 1: 同源策略是浏览器的安全基石**

同源策略 (Same-Origin Policy) 限制一个源的脚本如何与另一个源的资源交互。

```javascript
// 同源的定义: 协议 + 域名 + 端口 完全相同

// 同源示例
https://example.com/page1
https://example.com/page2
// ✅ 同源 (协议, 域名, 端口都相同)

// 跨域示例
https://example.com      → http://example.com       // ❌ 协议不同
https://example.com      → https://api.example.com  // ❌ 域名不同
https://example.com:443  → https://example.com:8080 // ❌ 端口不同
https://example.com      → https://sub.example.com  // ❌ 子域名不同

// 同源策略限制的操作
// 1. 读取其他源的 Cookie, LocalStorage, IndexedDB
// 2. 操作其他源的 DOM
// 3. 发送 AJAX 请求到其他源 (可以发送, 但浏览器拦截响应)
```

为什么需要同源策略:
- **安全隔离**: 防止恶意网站读取敏感数据
- **Cookie 保护**: 防止 CSRF 攻击
- **DOM 隔离**: 防止 XSS 攻击扩散
- **数据隔离**: 保护用户隐私

---

**规则 2: CORS 是同源策略的安全放宽机制**

CORS (Cross-Origin Resource Sharing) 允许服务器声明哪些源可以访问其资源。

```javascript
// CORS 工作流程

// 步骤 1: 浏览器发送请求 (带上 Origin 头)
fetch('https://api.example.com/data', {
    // ...
});

// Request Headers:
// Origin: https://app.example.com

// 步骤 2: 服务器检查 Origin 并设置响应头
res.header('Access-Control-Allow-Origin', 'https://app.example.com');

// 步骤 3: 浏览器检查响应头
if (allowedOrigin === currentOrigin) {
    // ✅ 允许 JavaScript 访问响应
    const data = await response.json();
} else {
    // ❌ 拦截响应, 报告 CORS 错误
    throw new TypeError('Failed to fetch');
}
```

CORS 的关键点:
- **服务器控制**: 服务器决定谁可以访问
- **浏览器执行**: 浏览器负责检查和拦截
- **请求已发送**: CORS 错误时请求已到达服务器
- **响应被拦截**: JavaScript 无法访问响应内容

---

**规则 3: 简单请求不触发预检, 复杂请求触发预检**

浏览器根据请求特征决定是否发送预检请求。

```javascript
// ✅ 简单请求 (不触发预检)
// 满足所有条件:
// 1. 方法是 GET, POST, HEAD 之一
// 2. 头部只包含安全头部
// 3. Content-Type 是特定值

fetch('https://api.example.com/data', {
    method: 'GET',
    credentials: 'include',
    headers: {
        'Accept': 'application/json',
        'Accept-Language': 'zh-CN',
        'Content-Language': 'zh-CN'
    }
});
// 浏览器直接发送请求

// ❌ 复杂请求 (触发预检)
// 不满足简单请求条件:

// 原因 1: 自定义头部
fetch('https://api.example.com/data', {
    headers: {
        'X-Custom': 'value'
    }
});

// 原因 2: Content-Type 不是简单值
fetch('https://api.example.com/data', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'  // ⚠️ 注意: 这个实际上是简单值!
    },
    body: JSON.stringify({})
});

// 正确的复杂 Content-Type:
fetch('https://api.example.com/data', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/xml'  // ❌ 触发预检
    }
});

// 原因 3: 方法是 PUT, DELETE, PATCH
fetch('https://api.example.com/data', {
    method: 'PUT'  // ❌ 触发预检
});

// 原因 4: 使用 ReadableStream
fetch('https://api.example.com/upload', {
    method: 'POST',
    body: new ReadableStream()  // ❌ 触发预检
});
```

简单请求的完整定义:
- **方法**: GET, POST, HEAD
- **安全头部**: Accept, Accept-Language, Content-Language, Content-Type (特定值), Range (特定值)
- **Content-Type**: `application/x-www-form-urlencoded`, `multipart/form-data`, `text/plain`
- **无自定义头**: 不包含 Authorization, X-* 等自定义头

---

**规则 4: 预检请求是 OPTIONS 方法的独立请求**

预检请求 (Preflight Request) 询问服务器是否允许实际请求。

```javascript
// 实际代码
fetch('https://api.example.com/user/profile', {
    method: 'GET',
    credentials: 'include',
    headers: {
        'Authorization': 'Bearer token123'
    }
});

// 浏览器实际发送两个请求:

// 请求 1: OPTIONS 预检请求
/*
OPTIONS /user/profile HTTP/1.1
Host: api.example.com
Origin: https://app.example.com
Access-Control-Request-Method: GET
Access-Control-Request-Headers: authorization
*/

// 服务器响应预检
/*
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: authorization, content-type
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 86400
*/

// 请求 2: 实际 GET 请求 (预检通过后)
/*
GET /user/profile HTTP/1.1
Host: api.example.com
Origin: https://app.example.com
Authorization: Bearer token123
Cookie: session_id=abc123
*/

// 服务器响应实际请求
/*
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true
Content-Type: application/json

{"name": "Alice", "email": "alice@example.com"}
*/
```

预检请求的特点:
- **独立请求**: 预检是完全独立的 HTTP 请求
- **OPTIONS 方法**: 始终使用 OPTIONS 方法
- **询问权限**: 通过特殊头部询问服务器
- **可缓存**: 服务器可设置缓存时间 (Max-Age)
- **失败即停**: 预检失败则不发送实际请求

---

**规则 5: 预检请求应在业务逻辑之前响应**

OPTIONS 预检请求不应该执行身份验证等业务逻辑。

```javascript
// ❌ 错误: 预检请求执行业务逻辑
app.use(authenticate);  // 身份验证

app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', origin);
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    next();
});
// OPTIONS 请求会先执行 authenticate, 可能失败

// ✅ 正确: 预检请求在业务逻辑之前响应
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', origin);

    if (req.method === 'OPTIONS') {
        res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
        res.header('Access-Control-Allow-Headers', 'Authorization, Content-Type');
        res.header('Access-Control-Max-Age', '86400');
        return res.sendStatus(200);  // ✅ 立即返回
    }

    next();
});

app.use(authenticate);  // 只对实际请求执行
```

为什么预检不应执行业务逻辑:
- **OPTIONS 无状态**: 预检请求不应该携带认证信息
- **避免副作用**: 预检不应该修改数据或状态
- **性能考虑**: 预检应该快速响应
- **安全隔离**: 预检和实际请求的安全要求不同

---

**规则 6: Access-Control-Max-Age 控制预检缓存时间**

预检响应可以被浏览器缓存, 避免重复预检。

```javascript
// 服务器设置预检缓存
res.header('Access-Control-Max-Age', '86400');  // 24 小时 (秒)

// 浏览器行为
// 第 1 次请求: 发送预检 → 缓存结果 (24 小时)
// 第 2-N 次请求: 使用缓存, 跳过预检
// 24 小时后: 预检缓存过期, 重新发送预检

// 浏览器的最大缓存时间限制
// Chrome: 7200 秒 (2 小时)
// Firefox: 86400 秒 (24 小时)
// Safari: 600 秒 (10 分钟)
```

预检缓存的影响:
```javascript
// 场景 1: 频繁相同请求
// 设置长缓存时间 (1 小时)
res.header('Access-Control-Max-Age', '3600');
// 优势: 减少预检请求, 提升性能
// 劣势: CORS 配置更新后, 客户端可能使用旧缓存

// 场景 2: 开发环境
// 设置短缓存时间 (10 秒)
res.header('Access-Control-Max-Age', '10');
// 优势: 配置更新快速生效
// 劣势: 预检请求较多, 性能略差

// 场景 3: 禁用预检缓存
res.header('Access-Control-Max-Age', '0');
// 每次请求都发送预检
```

---

**规则 7: credentials: 'include' 需要服务器明确允许**

跨域请求默认不发送 Cookie, 需要显式设置 `credentials: 'include'`。

```javascript
// 前端: 发送 Cookie
fetch('https://api.example.com/user', {
    credentials: 'include'  // ✅ 发送 Cookie
});

// 服务器: 允许 Credentials
res.header('Access-Control-Allow-Origin', 'https://app.example.com');
res.header('Access-Control-Allow-Credentials', 'true');  // ✅ 必需

// ⚠️ 重要限制: 使用 credentials 时, Allow-Origin 不能是 '*'
res.header('Access-Control-Allow-Origin', '*');
res.header('Access-Control-Allow-Credentials', 'true');
// ❌ 浏览器报错: "不能同时使用 '*' 和 credentials"
```

credentials 的三种模式:
```javascript
// same-origin (默认): 只在同源请求中发送 Cookie
fetch('/api/data', {
    credentials: 'same-origin'
});

// include: 始终发送 Cookie (跨域也发送)
fetch('https://api.example.com/data', {
    credentials: 'include'
});

// omit: 始终不发送 Cookie
fetch('https://api.example.com/data', {
    credentials: 'omit'
});
```

---

**规则 8: Vary: Origin 对缓存代理至关重要**

动态 CORS 响应必须设置 `Vary: Origin` 头。

```javascript
// 服务器: 动态 Allow-Origin
app.use((req, res, next) => {
    const origin = req.headers.origin;

    if (allowedOrigins.includes(origin)) {
        res.header('Access-Control-Allow-Origin', origin);  // 动态值
        res.header('Vary', 'Origin');  // ✅ 必须设置
    }

    next();
});

// 为什么需要 Vary: Origin?
//
// 场景: CDN 或反向代理缓存了 API 响应
//
// 请求 1: Origin: https://app1.example.com
// 响应 1: Access-Control-Allow-Origin: https://app1.example.com
// CDN 缓存了响应 1
//
// 请求 2: Origin: https://app2.example.com
// ❌ 没有 Vary: CDN 返回缓存的响应 1
// ❌ 浏览器看到 Allow-Origin: app1, 但当前 Origin 是 app2
// ❌ CORS 错误!
//
// ✅ 有 Vary: Origin: CDN 知道要根据 Origin 缓存不同的响应
// ✅ 请求 2 不使用缓存, 正确返回 Allow-Origin: app2
```

Vary 头的作用:
- **缓存控制**: 告诉缓存代理如何缓存不同的响应
- **动态响应**: 支持根据请求头返回不同内容
- **CORS 必需**: 动态 Allow-Origin 必须使用 Vary
- **性能优化**: 正确的缓存策略

---

**事故档案编号**: NETWORK-2024-1949
**影响范围**: CORS, Same-Origin Policy, 预检请求, 跨域认证, 预检缓存
**根本原因**: OPTIONS 预检请求被身份验证中间件拦截, 导致预检间歇性失败, 结合预检缓存机制形成间歇性 CORS 错误
**学习成本**: 高 (需深入理解浏览器安全策略和 HTTP 协议交互)

这是 JavaScript 世界第 149 次被记录的网络与数据事故。同源策略是浏览器安全的基石, CORS 提供了安全的跨域访问机制。简单请求直接发送, 复杂请求先发送 OPTIONS 预检请求询问服务器权限。预检请求应在业务逻辑之前响应, 避免身份验证等中间件拦截。`Access-Control-Max-Age` 控制预检缓存时间, 浏览器会缓存预检结果避免重复请求。使用 `credentials: 'include'` 发送跨域 Cookie 时, 服务器必须设置 `Allow-Credentials: true` 且 `Allow-Origin` 不能是 `*`。动态 CORS 响应必须设置 `Vary: Origin` 头防止缓存代理返回错误的响应。CORS 错误的本质是浏览器拦截了响应, 请求已到达服务器。理解简单请求 vs 预检请求的区别, 正确处理 OPTIONS 请求, 设置完整的 CORS 响应头是跨域开发的关键。

---
