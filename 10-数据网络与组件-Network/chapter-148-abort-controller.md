《第 148 次记录: 下班前两分钟的请求风暴 —— AbortController 的生死时速》

---

## 下班前的系统崩溃

周五下午五点二十八分, 距离下班还有两分钟。

你已经收拾好背包, 准备关掉电脑, 开始周末。今天是个愉快的周五——项目按时交付, 代码审查通过, 没有紧急任务。你甚至已经在手机上查好了晚上的电影场次。

然后, 你的电脑风扇突然开始狂转。

Chrome 浏览器的标签页变成了 "页面无响应", 任务管理器显示浏览器进程占用了 8GB 内存, 而且还在持续增长。你打开的测试页面完全卡死, 鼠标点击没有任何反应。

"什么情况?" 你皱起眉头, 强制刷新页面。

页面重新加载, 但几秒钟后, 又卡死了。这次更严重——整个浏览器都失去响应, 你不得不强制关闭进程。

你重新打开 Chrome, 小心翼翼地打开测试页面。这次你打开了 Network 面板, 想看看发生了什么。

然后你愣住了。

Network 面板里密密麻麻全是红色的请求——几百个 pending 状态的 API 请求, 每一个都显示 "Pending", 没有完成, 也没有失败, 就这样一直挂着。而且数量还在疯狂增长: 200 个... 300 个... 500 个...

你的心沉了下去。这不是简单的 bug, 这是生产环境的灾难。今天下午刚上线的搜索功能, 正在疯狂地发送请求, 而且没有任何中止机制。

你看了一眼时间——5 点 31 分。周五晚上, 运维团队已经下班了, 产品经理也在回家路上。但如果不立刻解决, 周末用户访问高峰时, 服务器会被这些请求彻底压垮。

周末计划瞬间蒸发。你放下背包, 打开编辑器。

---

## 追踪失控的请求

你快速定位到搜索功能的代码——这是前端小张今天下午新上线的实时搜索功能:

```javascript
// 实时搜索实现
const searchInput = document.querySelector('#search');

searchInput.addEventListener('input', async (e) => {
    const keyword = e.target.value;

    if (keyword.length < 2) {
        return;  // 少于 2 个字符不搜索
    }

    // 发送搜索请求
    const response = await fetch(`/api/search?q=${encodeURIComponent(keyword)}`);
    const results = await response.json();

    displayResults(results);
});
```

"看起来没问题啊..." 你喃喃自语, 但直觉告诉你问题就在这里。

你在测试页面输入 "javascript", 观察 Network 面板:

```
输入 'j'  → 1 个请求 pending
输入 'a'  → 2 个请求 pending
输入 'v'  → 3 个请求 pending
输入 'a'  → 4 个请求 pending
...
```

"天哪," 你倒吸一口凉气, "每输入一个字符就发一个请求, 而且之前的请求从来没有被取消!"

问题的严重性瞬间清晰了:

1. 用户快速输入 10 个字符 → 发送 10 个请求
2. 这 10 个请求都在等待服务器响应
3. 服务器搜索很慢 (3-5 秒才返回)
4. 用户看到没反应, 又删除重新输入 → 又发送 10 个请求
5. 现在有 20 个请求同时 pending
6. 浏览器连接池耗尽, 页面其他功能也卡死

你快速检查服务器日志, 情况比想象的更糟:

```
[17:25:33] GET /api/search?q=j - 正在执行 (用时 2.3s)
[17:25:33] GET /api/search?q=ja - 正在执行 (用时 2.2s)
[17:25:33] GET /api/search?q=jav - 正在执行 (用时 2.1s)
[17:25:34] GET /api/search?q=java - 正在执行 (用时 2.0s)
...
[17:25:40] 数据库连接池耗尽 (50/50 连接被占用)
[17:25:41] 新请求被阻塞, 等待队列长度: 156
```

服务器的数据库连接池也被这些请求耗尽了! 每个搜索请求都占用一个数据库连接, 而这些连接因为客户端没有取消请求而一直挂着。

你的手开始冒汗。这不仅仅是前端问题, 整个服务都在崩溃边缘。

---

## AbortController 救场

你想起了 AbortController——Fetch API 的请求中止机制。

"必须立刻修复," 你打开编辑器, 开始重写搜索逻辑:

```javascript
// 修复后的实时搜索实现
const searchInput = document.querySelector('#search');
let currentController = null;  // 保存当前的 AbortController

searchInput.addEventListener('input', async (e) => {
    const keyword = e.target.value;

    // 1. 取消之前的请求
    if (currentController) {
        currentController.abort();  // ✅ 中止之前的请求
    }

    if (keyword.length < 2) {
        clearResults();
        return;
    }

    // 2. 创建新的 AbortController
    currentController = new AbortController();

    try {
        // 3. 使用 signal 发送请求
        const response = await fetch(
            `/api/search?q=${encodeURIComponent(keyword)}`,
            {
                signal: currentController.signal  // ✅ 关联 signal
            }
        );

        const results = await response.json();
        displayResults(results);

    } catch (error) {
        if (error.name === 'AbortError') {
            // 请求被中止, 这是正常的
            console.log('搜索已取消');
        } else {
            // 其他错误
            console.error('搜索失败:', error);
            showError('搜索失败, 请重试');
        }
    }
});
```

你快速部署修复代码, 刷新测试页面, 再次输入 "javascript":

```
输入 'j'  → 1 个请求 pending
输入 'a'  → 第 1 个请求被中止 (cancelled), 1 个新请求 pending
输入 'v'  → 第 2 个请求被中止 (cancelled), 1 个新请求 pending
输入 'a'  → 第 3 个请求被中止 (cancelled), 1 个新请求 pending
...
```

"成功了!" Network 面板显示, 之前的请求都被标记为 `cancelled`, 同时只有最新的一个请求在 pending。

你监控服务器日志:

```
[17:38:12] GET /api/search?q=j - 客户端中止 (0.2s)
[17:38:12] GET /api/search?q=ja - 客户端中止 (0.1s)
[17:38:12] GET /api/search?q=jav - 客户端中止 (0.1s)
[17:38:13] GET /api/search?q=javascript - 完成 (2.8s)
[17:38:15] 数据库连接池状态: 3/50 连接被占用 ✅
```

数据库连接池恢复正常了! 被中止的请求立即释放了数据库连接。

你松了一口气, 但立刻意识到还有更多问题需要解决。

---

## 深度理解与优化

你创建了一个完整的测试文件, 系统地验证 AbortController 的特性:

```javascript
// 测试 1: AbortController 的基本使用
const controller = new AbortController();
const signal = controller.signal;

// 监听中止事件
signal.addEventListener('abort', () => {
    console.log('请求被中止');
    console.log('中止原因:', signal.reason);
});

// 发送请求
fetch('/api/data', { signal })
    .then(response => response.json())
    .then(data => console.log('成功:', data))
    .catch(error => {
        if (error.name === 'AbortError') {
            console.log('捕获到中止错误');
        }
    });

// 3 秒后中止请求
setTimeout(() => {
    controller.abort('超时');  // 可以传递中止原因
}, 3000);
```

你发现了 AbortController 的几个关键特性:

```javascript
// 特性 1: signal.aborted 属性
const controller = new AbortController();
console.log(controller.signal.aborted);  // false

controller.abort();
console.log(controller.signal.aborted);  // true

// 特性 2: 一个 AbortController 只能中止一次
const controller = new AbortController();
controller.abort('第一次');
controller.abort('第二次');  // 无效, 已经中止过了

console.log(controller.signal.reason);  // '第一次' (保留第一次的原因)

// 特性 3: signal 可以被多个请求共享
const controller = new AbortController();
const signal = controller.signal;

// 三个请求共享同一个 signal
fetch('/api/data1', { signal });
fetch('/api/data2', { signal });
fetch('/api/data3', { signal });

// 一次 abort() 中止所有三个请求
controller.abort();

// 特性 4: 已经中止的 signal 立即触发错误
const controller = new AbortController();
controller.abort();

fetch('/api/data', { signal: controller.signal })
    .catch(error => {
        console.log('立即失败:', error.name);  // 'AbortError'
    });
// 请求甚至不会发送到服务器
```

你又测试了超时控制的优雅实现:

```javascript
// 方法 1: 使用 AbortSignal.timeout() (现代浏览器)
const response = await fetch('/api/data', {
    signal: AbortSignal.timeout(5000)  // 5 秒超时
});

// 方法 2: 手动实现超时
function fetchWithTimeout(url, options = {}, timeout = 5000) {
    const controller = new AbortController();

    const timeoutId = setTimeout(() => {
        controller.abort('请求超时');
    }, timeout);

    return fetch(url, {
        ...options,
        signal: controller.signal
    }).finally(() => {
        clearTimeout(timeoutId);  // 清除定时器
    });
}

// 使用
try {
    const response = await fetchWithTimeout('/api/data', {}, 5000);
    const data = await response.json();
    console.log(data);
} catch (error) {
    if (error.name === 'AbortError') {
        console.log('请求超时或被取消');
    }
}
```

---

## 完整的请求管理方案

你整理了一套完整的请求管理工具类:

```javascript
// 请求管理器: 自动取消过期请求
class RequestManager {
    constructor() {
        this.controllers = new Map();  // 存储所有 controller
    }

    // 创建可取消的请求
    fetch(key, url, options = {}) {
        // 取消同 key 的旧请求
        this.cancel(key);

        // 创建新 controller
        const controller = new AbortController();
        this.controllers.set(key, controller);

        // 发送请求
        return fetch(url, {
            ...options,
            signal: controller.signal
        }).finally(() => {
            // 请求完成后自动清理
            this.controllers.delete(key);
        });
    }

    // 取消指定 key 的请求
    cancel(key, reason = '请求被取消') {
        const controller = this.controllers.get(key);
        if (controller) {
            controller.abort(reason);
            this.controllers.delete(key);
        }
    }

    // 取消所有请求
    cancelAll(reason = '批量取消') {
        for (const [key, controller] of this.controllers.entries()) {
            controller.abort(reason);
        }
        this.controllers.clear();
    }

    // 获取当前 pending 的请求数量
    getPendingCount() {
        return this.controllers.size;
    }
}

// 使用示例
const manager = new RequestManager();

// 搜索功能: 每次新搜索自动取消旧搜索
searchInput.addEventListener('input', async (e) => {
    const keyword = e.target.value;

    if (keyword.length < 2) {
        return;
    }

    try {
        const response = await manager.fetch(
            'search',  // key: 相同 key 会自动取消
            `/api/search?q=${encodeURIComponent(keyword)}`
        );

        const results = await response.json();
        displayResults(results);

    } catch (error) {
        if (error.name === 'AbortError') {
            // 被新搜索取消, 不处理
        } else {
            console.error('搜索失败:', error);
        }
    }
});

// 页面卸载时取消所有请求
window.addEventListener('beforeunload', () => {
    manager.cancelAll('页面关闭');
});
```

你又实现了带超时的请求管理:

```javascript
// 增强版: 支持超时控制
class TimeoutRequestManager extends RequestManager {
    fetch(key, url, options = {}) {
        const { timeout, ...fetchOptions } = options;

        // 取消旧请求
        this.cancel(key);

        // 创建 controller
        const controller = new AbortController();
        this.controllers.set(key, {
            controller,
            timeoutId: null
        });

        // 设置超时
        if (timeout) {
            const timeoutId = setTimeout(() => {
                controller.abort(`请求超时 (${timeout}ms)`);
            }, timeout);

            this.controllers.get(key).timeoutId = timeoutId;
        }

        // 发送请求
        return fetch(url, {
            ...fetchOptions,
            signal: controller.signal
        }).finally(() => {
            // 清理
            const entry = this.controllers.get(key);
            if (entry && entry.timeoutId) {
                clearTimeout(entry.timeoutId);
            }
            this.controllers.delete(key);
        });
    }
}

// 使用
const manager = new TimeoutRequestManager();

await manager.fetch('data', '/api/data', {
    timeout: 5000,  // 5 秒超时
    method: 'POST',
    body: JSON.stringify({ id: 123 })
});
```

你还实现了请求优先级管理:

```javascript
// 请求优先级队列
class PriorityRequestManager {
    constructor(maxConcurrent = 6) {
        this.maxConcurrent = maxConcurrent;
        this.running = new Map();  // 正在运行的请求
        this.queue = [];  // 等待队列
    }

    async fetch(key, url, options = {}) {
        const { priority = 0, ...fetchOptions } = options;

        // 取消同 key 的旧请求
        this.cancel(key);

        // 创建请求任务
        const task = {
            key,
            url,
            options: fetchOptions,
            priority,
            controller: new AbortController()
        };

        // 如果达到并发上限, 加入队列
        if (this.running.size >= this.maxConcurrent) {
            this.queue.push(task);
            this.queue.sort((a, b) => b.priority - a.priority);  // 按优先级排序
            return this.waitForSlot(task);
        }

        // 立即执行
        return this.execute(task);
    }

    async waitForSlot(task) {
        return new Promise((resolve, reject) => {
            task.resolve = resolve;
            task.reject = reject;
        });
    }

    async execute(task) {
        this.running.set(task.key, task);

        try {
            const response = await fetch(task.url, {
                ...task.options,
                signal: task.controller.signal
            });

            const result = await response.json();

            if (task.resolve) {
                task.resolve(result);
            }

            return result;

        } catch (error) {
            if (task.reject) {
                task.reject(error);
            }
            throw error;

        } finally {
            this.running.delete(task.key);
            this.processQueue();
        }
    }

    processQueue() {
        while (this.queue.length > 0 && this.running.size < this.maxConcurrent) {
            const task = this.queue.shift();
            this.execute(task);
        }
    }

    cancel(key, reason = '请求被取消') {
        // 取消运行中的请求
        const running = this.running.get(key);
        if (running) {
            running.controller.abort(reason);
            this.running.delete(key);
        }

        // 从队列中移除
        const index = this.queue.findIndex(task => task.key === key);
        if (index !== -1) {
            const task = this.queue.splice(index, 1)[0];
            if (task.reject) {
                task.reject(new DOMException(reason, 'AbortError'));
            }
        }
    }
}

// 使用示例
const manager = new PriorityRequestManager(3);  // 最多 3 个并发

// 高优先级: 用户点击的请求
manager.fetch('user-action', '/api/important', {
    priority: 10
});

// 低优先级: 预加载的请求
manager.fetch('prefetch-1', '/api/prefetch/1', {
    priority: 1
});

manager.fetch('prefetch-2', '/api/prefetch/2', {
    priority: 1
});
```

---

## 常见陷阱与最佳实践

你整理了使用 AbortController 的常见错误:

```javascript
// ❌ 错误 1: 忘记检查 AbortError
async function badFetch() {
    const controller = new AbortController();

    setTimeout(() => controller.abort(), 1000);

    const response = await fetch('/api/data', {
        signal: controller.signal
    });
    // ❌ 如果请求被中止, 这里会抛出 AbortError
    // 但没有 try-catch 捕获

    return response.json();
}

// ✅ 正确: 总是捕获并检查 AbortError
async function goodFetch() {
    const controller = new AbortController();

    setTimeout(() => controller.abort(), 1000);

    try {
        const response = await fetch('/api/data', {
            signal: controller.signal
        });

        return await response.json();

    } catch (error) {
        if (error.name === 'AbortError') {
            console.log('请求被中止, 这是预期行为');
            return null;  // 或者其他默认值
        }
        throw error;  // 其他错误继续抛出
    }
}

// ❌ 错误 2: 重复使用同一个 controller
const controller = new AbortController();

fetch('/api/data1', { signal: controller.signal });

// ❌ controller 已经用过了, 不能重复使用
fetch('/api/data2', { signal: controller.signal });

// ✅ 正确: 每个请求序列使用新的 controller
let currentController = null;

function makeRequest() {
    // 取消旧请求
    if (currentController) {
        currentController.abort();
    }

    // 创建新 controller
    currentController = new AbortController();

    return fetch('/api/data', {
        signal: currentController.signal
    });
}

// ❌ 错误 3: 忘记清理定时器
function badTimeout() {
    const controller = new AbortController();

    const timeoutId = setTimeout(() => {
        controller.abort();
    }, 5000);

    fetch('/api/data', { signal: controller.signal })
        .then(response => response.json());
    // ❌ 如果请求在 5 秒内完成, 定时器仍然会触发
}

// ✅ 正确: 请求完成后清理定时器
function goodTimeout() {
    const controller = new AbortController();

    const timeoutId = setTimeout(() => {
        controller.abort('超时');
    }, 5000);

    return fetch('/api/data', { signal: controller.signal })
        .finally(() => {
            clearTimeout(timeoutId);  // ✅ 清理定时器
        })
        .then(response => response.json());
}

// ❌ 错误 4: 在已中止的 signal 上添加监听器
const controller = new AbortController();
controller.abort();

controller.signal.addEventListener('abort', () => {
    console.log('这个监听器永远不会触发');
    // ❌ signal 已经中止, 不会再触发 abort 事件
});

// ✅ 正确: 检查 aborted 状态
const controller = new AbortController();
controller.abort();

if (controller.signal.aborted) {
    console.log('signal 已经中止');
} else {
    controller.signal.addEventListener('abort', () => {
        console.log('signal 被中止');
    });
}

// ❌ 错误 5: 假设 abort() 是同步的
const controller = new AbortController();

fetch('/api/data', { signal: controller.signal })
    .catch(error => {
        console.log('捕获错误:', error.name);
    });

controller.abort();
console.log('abort 调用完成');

// 输出顺序:
// "abort 调用完成"
// "捕获错误: AbortError"
// ✅ abort() 是同步的, 但 Promise rejection 是异步的

// ✅ 正确: 理解异步行为
const controller = new AbortController();

const promise = fetch('/api/data', { signal: controller.signal })
    .catch(error => {
        if (error.name === 'AbortError') {
            console.log('请求被中止');
        }
    });

controller.abort();  // 立即中止请求

await promise;  // 等待 Promise 完成
console.log('Promise 已解决');
```

你创建了一套最佳实践模板:

```javascript
// ✅ 最佳实践 1: 实时搜索防抖 + 取消
class SearchBox {
    constructor(input, onResults) {
        this.input = input;
        this.onResults = onResults;
        this.controller = null;
        this.debounceTimer = null;

        this.input.addEventListener('input', (e) => {
            this.handleInput(e.target.value);
        });
    }

    handleInput(keyword) {
        // 防抖: 延迟 300ms
        clearTimeout(this.debounceTimer);

        this.debounceTimer = setTimeout(() => {
            this.search(keyword);
        }, 300);
    }

    async search(keyword) {
        // 取消之前的请求
        if (this.controller) {
            this.controller.abort();
        }

        if (keyword.length < 2) {
            this.onResults([]);
            return;
        }

        // 创建新 controller
        this.controller = new AbortController();

        try {
            const response = await fetch(
                `/api/search?q=${encodeURIComponent(keyword)}`,
                {
                    signal: this.controller.signal,
                    // AbortSignal.timeout() 在支持的浏览器中
                    // signal: AbortSignal.timeout(5000)
                }
            );

            const results = await response.json();
            this.onResults(results);

        } catch (error) {
            if (error.name === 'AbortError') {
                // 被新搜索取消, 忽略
            } else {
                console.error('搜索失败:', error);
                this.onResults([]);
            }
        }
    }

    destroy() {
        clearTimeout(this.debounceTimer);
        if (this.controller) {
            this.controller.abort();
        }
    }
}

// ✅ 最佳实践 2: 页面切换时取消请求
class Page {
    constructor() {
        this.controller = new AbortController();
    }

    async loadData() {
        try {
            const [users, posts, comments] = await Promise.all([
                fetch('/api/users', { signal: this.controller.signal }),
                fetch('/api/posts', { signal: this.controller.signal }),
                fetch('/api/comments', { signal: this.controller.signal })
            ]);

            // 处理数据...

        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('页面切换, 请求已取消');
            } else {
                console.error('加载失败:', error);
            }
        }
    }

    destroy() {
        // 页面销毁时取消所有请求
        this.controller.abort('页面销毁');
    }
}

// ✅ 最佳实践 3: React Hook 集成
function useFetch(url, options = {}) {
    const [data, setData] = React.useState(null);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);

    React.useEffect(() => {
        const controller = new AbortController();

        (async () => {
            try {
                setLoading(true);

                const response = await fetch(url, {
                    ...options,
                    signal: controller.signal
                });

                const result = await response.json();
                setData(result);
                setError(null);

            } catch (err) {
                if (err.name === 'AbortError') {
                    // 组件卸载导致的中止, 不更新状态
                } else {
                    setError(err);
                }
            } finally {
                setLoading(false);
            }
        })();

        // 清理函数: 组件卸载时取消请求
        return () => {
            controller.abort();
        };
    }, [url]);

    return { data, loading, error };
}

// 使用
function UserProfile({ userId }) {
    const { data, loading, error } = useFetch(`/api/users/${userId}`);

    if (loading) return <div>加载中...</div>;
    if (error) return <div>错误: {error.message}</div>;
    return <div>{data.name}</div>;
}

// ✅ 最佳实践 4: 带重试的请求
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
    const { timeout = 5000, ...fetchOptions } = options;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        const controller = new AbortController();

        const timeoutId = setTimeout(() => {
            controller.abort('超时');
        }, timeout);

        try {
            const response = await fetch(url, {
                ...fetchOptions,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                console.warn(`请求超时 (尝试 ${attempt + 1}/${maxRetries + 1})`);
            } else {
                console.warn(`请求失败: ${error.message} (尝试 ${attempt + 1}/${maxRetries + 1})`);
            }

            if (attempt === maxRetries) {
                throw error;  // 达到最大重试次数
            }

            // 指数退避
            const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
}

// ✅ 最佳实践 5: 组合多个 signal
function combineSignals(...signals) {
    const controller = new AbortController();

    for (const signal of signals) {
        if (signal.aborted) {
            controller.abort(signal.reason);
            break;
        }

        signal.addEventListener('abort', () => {
            controller.abort(signal.reason);
        }, { once: true });
    }

    return controller.signal;
}

// 使用: 同时响应超时和用户取消
const timeoutSignal = AbortSignal.timeout(5000);
const userController = new AbortController();

const combinedSignal = combineSignals(timeoutSignal, userController.signal);

fetch('/api/data', { signal: combinedSignal });

// 用户可以手动取消
document.querySelector('#cancel').addEventListener('click', () => {
    userController.abort('用户取消');
});
```

---

## 知识总结: AbortController 的核心原理

**规则 1: AbortController 与 AbortSignal 的分离设计**

AbortController 负责发起中止, AbortSignal 负责接收中止通知。

```javascript
// AbortController: 控制器 (发起方)
const controller = new AbortController();

// AbortSignal: 信号对象 (接收方)
const signal = controller.signal;

// 发起中止
controller.abort('原因');

// 检查是否已中止
console.log(signal.aborted);  // true
console.log(signal.reason);  // '原因'

// 监听中止事件
signal.addEventListener('abort', () => {
    console.log('收到中止信号');
});
```

分离的好处:
- **单向传递**: Controller 发送, Signal 接收, 职责清晰
- **多个接收者**: 一个 Signal 可以被多个请求共享
- **安全性**: 接收方只能监听, 不能修改或触发中止
- **组合性**: 可以组合多个 Signal 实现复杂逻辑

---

**规则 2: AbortController 只能中止一次**

一旦调用 `abort()`, AbortController 就进入已中止状态, 无法恢复。

```javascript
const controller = new AbortController();

console.log(controller.signal.aborted);  // false

controller.abort('第一次中止');
console.log(controller.signal.aborted);  // true
console.log(controller.signal.reason);  // '第一次中止'

controller.abort('第二次中止');  // 无效
console.log(controller.signal.reason);  // 仍然是 '第一次中止'

// 如果需要再次中止, 必须创建新的 controller
const newController = new AbortController();
```

为什么只能中止一次:
- **状态不可逆**: 防止混乱, 中止是终态
- **语义明确**: 一次中止代表一个决定
- **性能优化**: 浏览器可以立即释放资源
- **错误防护**: 防止意外的重复中止

---

**规则 3: signal.aborted 可以同步检查中止状态**

不需要等待 Promise, 可以立即检查 Signal 是否已中止。

```javascript
const controller = new AbortController();
const signal = controller.signal;

// 同步检查
console.log(signal.aborted);  // false

controller.abort();

// 立即变为 true
console.log(signal.aborted);  // true

// 已中止的 signal 立即导致请求失败
fetch('/api/data', { signal })
    .catch(error => {
        console.log(error.name);  // 'AbortError'
    });
// 请求甚至不会发送到网络
```

应用场景:
```javascript
// 场景 1: 避免无效的请求
async function loadData(signal) {
    if (signal.aborted) {
        console.log('已中止, 跳过请求');
        return null;
    }

    // 发送请求...
}

// 场景 2: 中止长时间计算
async function processData(data, signal) {
    for (let i = 0; i < data.length; i++) {
        if (signal.aborted) {
            console.log('计算被中止');
            return null;
        }

        // 处理每一项...
    }
}

// 场景 3: 条件执行
async function task(signal) {
    await step1();

    if (signal.aborted) return;

    await step2();

    if (signal.aborted) return;

    await step3();
}
```

---

**规则 4: abort 事件只触发一次**

当 `abort()` 被调用时, `abort` 事件触发一次, 之后不会再触发。

```javascript
const controller = new AbortController();
const signal = controller.signal;

// 添加监听器
signal.addEventListener('abort', () => {
    console.log('监听器 1');
});

signal.addEventListener('abort', () => {
    console.log('监听器 2');
});

// 第一次 abort
controller.abort();
// 输出:
// "监听器 1"
// "监听器 2"

// 再次 abort
controller.abort();
// (没有输出, 事件不会再次触发)

// 新添加的监听器也不会触发
signal.addEventListener('abort', () => {
    console.log('监听器 3');
});
// (没有输出)
```

正确的使用模式:
```javascript
// ✅ 正确: 添加监听器前检查状态
const controller = new AbortController();
const signal = controller.signal;

if (signal.aborted) {
    // 已经中止, 直接处理
    handleAbort();
} else {
    // 尚未中止, 添加监听器
    signal.addEventListener('abort', () => {
        handleAbort();
    });
}

function handleAbort() {
    console.log('处理中止逻辑');
}
```

---

**规则 5: 一个 Signal 可以中止多个操作**

AbortSignal 可以被多个 fetch 请求、定时器、自定义操作共享。

```javascript
const controller = new AbortController();
const signal = controller.signal;

// 同一个 signal 用于多个请求
const promise1 = fetch('/api/data1', { signal });
const promise2 = fetch('/api/data2', { signal });
const promise3 = fetch('/api/data3', { signal });

// 一次 abort() 中止所有三个请求
controller.abort();

// 所有 Promise 都会 reject
Promise.allSettled([promise1, promise2, promise3])
    .then(results => {
        results.forEach(result => {
            console.log(result.status);  // 'rejected'
            console.log(result.reason.name);  // 'AbortError'
        });
    });
```

应用场景:
```javascript
// 场景 1: 页面加载时的多个请求
class PageLoader {
    constructor() {
        this.controller = new AbortController();
    }

    async load() {
        const signal = this.controller.signal;

        try {
            const [header, sidebar, content, footer] = await Promise.all([
                fetch('/api/header', { signal }),
                fetch('/api/sidebar', { signal }),
                fetch('/api/content', { signal }),
                fetch('/api/footer', { signal })
            ]);

            // 渲染页面...

        } catch (error) {
            if (error.name === 'AbortError') {
                console.log('页面加载被取消');
            }
        }
    }

    cancel() {
        // 一次取消所有请求
        this.controller.abort('用户取消');
    }
}

// 场景 2: 可中止的定时任务
function abortableSetTimeout(callback, delay, signal) {
    if (signal.aborted) {
        return Promise.reject(new DOMException('Aborted', 'AbortError'));
    }

    return new Promise((resolve, reject) => {
        const timeoutId = setTimeout(() => {
            resolve(callback());
        }, delay);

        signal.addEventListener('abort', () => {
            clearTimeout(timeoutId);
            reject(new DOMException('Aborted', 'AbortError'));
        }, { once: true });
    });
}

// 使用
const controller = new AbortController();

abortableSetTimeout(() => {
    console.log('延迟执行');
}, 5000, controller.signal);

// 可以随时取消
controller.abort();
```

---

**规则 6: AbortSignal.timeout() 提供便捷的超时控制**

现代浏览器支持 `AbortSignal.timeout()` 创建自动超时的 Signal。

```javascript
// 方式 1: 使用 AbortSignal.timeout() (推荐)
try {
    const response = await fetch('/api/data', {
        signal: AbortSignal.timeout(5000)  // 5 秒超时
    });

    const data = await response.json();
    console.log(data);

} catch (error) {
    if (error.name === 'TimeoutError') {  // 注意是 TimeoutError
        console.log('请求超时');
    }
}

// 方式 2: 手动实现超时 (兼容旧浏览器)
const controller = new AbortController();

const timeoutId = setTimeout(() => {
    controller.abort('请求超时');
}, 5000);

try {
    const response = await fetch('/api/data', {
        signal: controller.signal
    });

    clearTimeout(timeoutId);

    const data = await response.json();
    console.log(data);

} catch (error) {
    clearTimeout(timeoutId);

    if (error.name === 'AbortError') {
        console.log('请求超时或被取消');
    }
}

// 方式 3: 组合超时和手动取消
const controller = new AbortController();
const timeoutSignal = AbortSignal.timeout(5000);

// 组合两个 signal
const combinedSignal = AbortSignal.any([
    controller.signal,
    timeoutSignal
]);

fetch('/api/data', { signal: combinedSignal });

// 用户可以手动取消
document.querySelector('#cancel').onclick = () => {
    controller.abort('用户取消');
};
```

浏览器兼容性:
- `AbortSignal.timeout()`: Chrome 103+, Firefox 100+, Safari 16+
- `AbortSignal.any()`: Chrome 116+, Firefox 115+, Safari 16.4+
- 旧浏览器需要 polyfill 或手动实现

---

**规则 7: 自定义操作也可以支持 AbortSignal**

任何异步操作都可以接受 AbortSignal 参数实现可中止。

```javascript
// 可中止的延迟函数
function delay(ms, signal) {
    return new Promise((resolve, reject) => {
        if (signal?.aborted) {
            return reject(new DOMException('Aborted', 'AbortError'));
        }

        const timeoutId = setTimeout(resolve, ms);

        signal?.addEventListener('abort', () => {
            clearTimeout(timeoutId);
            reject(new DOMException('Aborted', 'AbortError'));
        }, { once: true });
    });
}

// 使用
const controller = new AbortController();

delay(5000, controller.signal)
    .then(() => console.log('延迟完成'))
    .catch(error => {
        if (error.name === 'AbortError') {
            console.log('延迟被中止');
        }
    });

// 可以随时取消
controller.abort();

// 可中止的文件读取
function readFileAbortable(file, signal) {
    return new Promise((resolve, reject) => {
        if (signal?.aborted) {
            return reject(new DOMException('Aborted', 'AbortError'));
        }

        const reader = new FileReader();

        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(e.target.error);

        signal?.addEventListener('abort', () => {
            reader.abort();
            reject(new DOMException('Aborted', 'AbortError'));
        }, { once: true });

        reader.readAsText(file);
    });
}

// 可中止的动画
function animateAbortable(element, keyframes, options, signal) {
    if (signal?.aborted) {
        return Promise.reject(new DOMException('Aborted', 'AbortError'));
    }

    const animation = element.animate(keyframes, options);

    signal?.addEventListener('abort', () => {
        animation.cancel();
    }, { once: true });

    return animation.finished;
}
```

最佳实践:
```javascript
// 设计可中止的 API
class AsyncTask {
    constructor(signal) {
        this.signal = signal;
        this.checkAborted();
    }

    checkAborted() {
        if (this.signal?.aborted) {
            throw new DOMException('Task aborted', 'AbortError');
        }
    }

    async step1() {
        this.checkAborted();
        // 执行步骤 1...
    }

    async step2() {
        this.checkAborted();
        // 执行步骤 2...
    }

    async execute() {
        await this.step1();
        await this.step2();
        // ...
    }
}

// 使用
const controller = new AbortController();
const task = new AsyncTask(controller.signal);

task.execute().catch(error => {
    if (error.name === 'AbortError') {
        console.log('任务被中止');
    }
});

// 可以随时中止
controller.abort();
```

---

**规则 8: 请求取消会立即释放资源**

当请求被 `abort()` 时, 浏览器和服务器都会立即释放相关资源。

```javascript
// 前端: 浏览器立即释放资源
const controller = new AbortController();

fetch('/api/large-download', { signal: controller.signal })
    .then(response => response.blob())
    .then(blob => {
        // 处理大文件...
    })
    .catch(error => {
        if (error.name === 'AbortError') {
            console.log('下载被取消');
            // ✅ 浏览器立即停止接收数据
            // ✅ 已接收的数据被丢弃
            // ✅ 网络连接被关闭
            // ✅ 内存被释放
        }
    });

// 用户取消下载
controller.abort();

// 后端: 服务器感知客户端中止 (Node.js 示例)
app.get('/api/large-download', (req, res) => {
    // 监听客户端断开
    req.on('close', () => {
        if (!res.writableEnded) {
            console.log('客户端中止了请求');
            // ✅ 停止读取文件
            // ✅ 关闭文件句柄
            // ✅ 释放数据库连接
            // ✅ 取消正在进行的计算
            stream.destroy();
            db.release();
        }
    });

    // 读取大文件...
    const stream = fs.createReadStream('/path/to/large-file.zip');
    stream.pipe(res);
});
```

资源释放的重要性:
```javascript
// 场景 1: 防止内存泄漏
class DataFetcher {
    constructor() {
        this.cache = new Map();
        this.controllers = new Map();
    }

    async fetch(key, url) {
        // 取消旧请求并释放资源
        this.cancel(key);

        const controller = new AbortController();
        this.controllers.set(key, controller);

        try {
            const response = await fetch(url, {
                signal: controller.signal
            });

            const data = await response.json();
            this.cache.set(key, data);
            return data;

        } finally {
            // 请求完成后移除 controller
            this.controllers.delete(key);
        }
    }

    cancel(key) {
        const controller = this.controllers.get(key);
        if (controller) {
            controller.abort();  // ✅ 立即释放网络资源
            this.controllers.delete(key);  // ✅ 释放内存引用
        }
    }

    destroy() {
        // 清理所有资源
        for (const controller of this.controllers.values()) {
            controller.abort();
        }
        this.controllers.clear();
        this.cache.clear();
    }
}

// 场景 2: 页面卸载时清理
window.addEventListener('beforeunload', () => {
    // ✅ 取消所有 pending 的请求
    globalRequestManager.cancelAll();
    // 避免浏览器等待请求完成
});
```

---

**事故档案编号**: NETWORK-2024-1948
**影响范围**: AbortController, AbortSignal, 请求取消, 超时控制, 资源管理
**根本原因**: 实时搜索功能未实现请求取消机制, 导致大量 pending 请求堆积, 耗尽浏览器连接池和服务器资源
**学习成本**: 中 (需理解 Controller-Signal 分离设计和异步资源管理)

这是 JavaScript 世界第 148 次被记录的网络与数据事故。AbortController 提供了标准的请求取消机制, 通过 Controller-Signal 分离设计实现职责清晰的中止控制。每个 AbortController 只能中止一次, 无法恢复或重复使用。AbortSignal 可以被多个操作共享, 实现一次中止多个请求。`signal.aborted` 属性可以同步检查中止状态, 避免无效操作。`AbortSignal.timeout()` 提供了便捷的超时控制。自定义异步操作也应该支持 AbortSignal 参数, 实现统一的取消机制。请求取消会立即释放浏览器和服务器资源, 防止内存泄漏和连接池耗尽。实时搜索、页面切换、组件卸载等场景必须正确使用 AbortController 取消过期请求。理解 AbortController 的设计哲学和使用模式是构建健壮网络应用的关键。

---
