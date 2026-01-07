《第 154 次记录: 周一早上的离线灾难 —— Service Worker 缓存失控》

---

## 紧急故障

周一早上 8 点 47 分, 你刚到公司, 手机就响了。

是运营总监老王的电话, 语气急促: "你们的 PWA 离线功能炸了! 昨晚更新后, 所有用户打开 App 都看到白屏, 客服电话都被打爆了。现在在线用户数掉了 70%, 你们技术部门什么时候能修好?"

你还没来得及放下背包, 立刻打开笔记本连上公司 Wi-Fi。浏览器打开生产环境 —— 果然, 白屏。

控制台里满屏红色错误:

```
Failed to load resource: net::ERR_FAILED
Service Worker installation failed
Uncaught (in promise) TypeError: Failed to fetch
```

你的心一沉。上周五下午你们刚上线了新版本, 更新了 Service Worker 的缓存策略, 当时测试环境一切正常。但现在...

你快速切换到公司内网监控系统, 数据让你倒吸一口冷气:

```
错误率统计 (过去 12 小时):
- 页面加载失败: 89.7%
- Service Worker 激活失败: 100%
- 离线缓存命中率: 0%

影响范围:
- 受影响用户: 247,532 人
- 投诉工单: 1,847 个
- 平均响应时间: 超时 (120s+)
```

你的 Slack 频道已经炸了:

```
[8:42] 运营部-小李: PWA 完全打不开了, 用户疯狂投诉
[8:43] 客服部-张主管: 电话都接不过来, 什么时候能恢复?
[8:45] CTO: @前端团队 这是 P0 事故, 立即处理
[8:46] 产品经理: 上周五的更新出问题了吗?
```

你快速回复: "正在排查, 30 分钟内给结论。"

但你心里清楚, 这可能是 Service Worker 缓存策略的问题。上周五你修改了缓存逻辑, 增加了版本号管理... 难道是那里出了问题?

---

## 压力排查

8 点 52 分, 你打开 Chrome DevTools 的 Application 面板。

首先检查 Service Worker 状态:

```
Service Workers
- https://app.example.com
  Status: ⚠️ Activated (installed 3 days ago)
  Running: Yes
  Version: sw-v1.2.3 (旧版本!)
```

"什么?" 你愣住了。"为什么还是旧版本? 昨晚明明部署了 v1.2.4..."

你点开 Cache Storage 查看缓存内容:

```
Cache Storage
├─ static-v1.2.3
│  ├─ /index.html (3 days ago)
│  ├─ /app.js (3 days ago)
│  └─ /style.css (3 days ago)
└─ api-cache-v1
   └─ (空)
```

"缓存的都是旧版本文件!" 你快速理解了问题的严重性。

现在的情况是:
1. 新版本的代码已经部署到服务器
2. 但 Service Worker 还在用旧版本的缓存
3. 旧版本的 HTML/JS 与新版本的 API 不兼容
4. 所有请求都失败了

你立刻查看上周五部署的 Service Worker 代码:

```javascript
// sw.js (v1.2.4 - 上周五部署的版本)
const CACHE_VERSION = 'static-v1.2.4';
const API_CACHE = 'api-cache-v1';

self.addEventListener('install', (event) => {
    console.log('Service Worker: 安装中...');

    event.waitUntil(
        caches.open(CACHE_VERSION).then((cache) => {
            return cache.addAll([
                '/',
                '/index.html',
                '/app.js',
                '/style.css',
                '/manifest.json'
            ]);
        })
    );

    // ❌ 问题 1: 没有调用 skipWaiting()
    // 新版本 Service Worker 安装后处于等待状态
});

self.addEventListener('activate', (event) => {
    console.log('Service Worker: 激活中...');

    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // ❌ 问题 2: 删除缓存的条件错误
                    if (cacheName !== CACHE_VERSION) {
                        console.log('删除旧缓存:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );

    // ❌ 问题 3: 没有调用 clients.claim()
    // 激活后不会立即控制已打开的页面
});

self.addEventListener('fetch', (event) => {
    // ❌ 问题 4: 缓存策略过于激进
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            // 优先返回缓存, 永远不更新
            if (cachedResponse) {
                return cachedResponse;
            }

            return fetch(event.request).then((networkResponse) => {
                // 网络请求成功后缓存
                if (event.request.url.startsWith(self.location.origin)) {
                    const cache = caches.open(CACHE_VERSION);
                    cache.then(c => c.put(event.request, networkResponse.clone()));
                }
                return networkResponse;
            });
        })
    );
});
```

"找到了!" 你恍然大悟。问题有 4 个:

**问题 1: 没有 skipWaiting()**
- 新版本 Service Worker 安装后, 会进入 "waiting" 状态
- 只有当所有使用旧版本的标签页关闭后, 新版本才会激活
- 用户通常不会关闭标签页, 所以一直用的是旧版本

**问题 2: 缓存清理条件错误**
- API_CACHE 不等于 CACHE_VERSION, 所以也被删除了
- 但删除时机不对, 导致新旧缓存共存

**问题 3: 没有 clients.claim()**
- 即使 Service Worker 激活了, 也不会立即控制已打开的页面
- 用户需要刷新页面才能使用新的 Service Worker

**问题 4: 缓存策略过于激进**
- Cache First 策略导致永远返回旧缓存
- 即使服务器有新版本, 用户也看不到

你看了一眼时间: 9 点 03 分。距离你承诺的 30 分钟还有 24 分钟。

---

## 紧急修复

9 点 05 分, 你打开代码编辑器, 开始修复 Service Worker。

你知道必须立即解决两个问题:
1. **短期**: 让现有用户能用上新版本 (紧急修复)
2. **长期**: 改进缓存策略, 避免类似问题 (架构优化)

### 短期修复 (9:05-9:15)

你创建了紧急修复版本 `sw.js v1.2.5`:

```javascript
// sw.js (v1.2.5 - 紧急修复版本)
const CACHE_VERSION = 'static-v1.2.5';
const API_CACHE = 'api-cache-v2';
const OFFLINE_PAGE = '/offline.html';

// ✅ 修复 1: install 时强制激活
self.addEventListener('install', (event) => {
    console.log(`Service Worker v${CACHE_VERSION}: 安装中...`);

    event.waitUntil(
        caches.open(CACHE_VERSION).then((cache) => {
            return cache.addAll([
                '/',
                '/index.html',
                '/app.js',
                '/style.css',
                '/manifest.json',
                OFFLINE_PAGE  // 添加离线页面
            ]);
        }).then(() => {
            // ✅ 立即跳过等待, 激活新版本
            return self.skipWaiting();
        })
    );
});

// ✅ 修复 2: activate 时正确清理旧缓存
self.addEventListener('activate', (event) => {
    console.log(`Service Worker v${CACHE_VERSION}: 激活中...`);

    event.waitUntil(
        Promise.all([
            // 清理旧的静态资源缓存
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter(cacheName => {
                            // 只删除旧版本的 static 缓存
                            return cacheName.startsWith('static-') &&
                                   cacheName !== CACHE_VERSION;
                        })
                        .map(cacheName => {
                            console.log('删除旧缓存:', cacheName);
                            return caches.delete(cacheName);
                        })
                );
            }),

            // ✅ 立即接管所有页面
            self.clients.claim()
        ])
    );
});

// ✅ 修复 3: 改进缓存策略
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // 不同类型的资源使用不同策略
    if (request.url.includes('/api/')) {
        // API 请求: Network First (网络优先)
        event.respondWith(networkFirst(request));
    } else if (request.destination === 'document') {
        // HTML 页面: Stale While Revalidate (先返回缓存, 后台更新)
        event.respondWith(staleWhileRevalidate(request));
    } else {
        // 静态资源: Cache First (缓存优先)
        event.respondWith(cacheFirst(request));
    }
});

// 缓存策略 1: Network First (网络优先, 失败时用缓存)
async function networkFirst(request) {
    const cache = await caches.open(API_CACHE);

    try {
        // 先尝试网络请求
        const networkResponse = await fetch(request, {
            timeout: 5000  // 5 秒超时
        });

        // 成功后更新缓存
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;

    } catch (error) {
        // 网络失败, 返回缓存
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            console.log('网络失败, 使用缓存:', request.url);
            return cachedResponse;
        }

        // 缓存也没有, 返回离线页面
        return caches.match(OFFLINE_PAGE);
    }
}

// 缓存策略 2: Stale While Revalidate (先用缓存, 后台更新)
async function staleWhileRevalidate(request) {
    const cache = await caches.open(CACHE_VERSION);

    // 立即返回缓存 (如果有)
    const cachedResponse = await cache.match(request);

    // 同时发起网络请求更新缓存
    const fetchPromise = fetch(request).then((networkResponse) => {
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    });

    // 如果有缓存, 立即返回; 否则等待网络
    return cachedResponse || fetchPromise;
}

// 缓存策略 3: Cache First (缓存优先, 没有才请求网络)
async function cacheFirst(request) {
    const cache = await caches.open(CACHE_VERSION);

    // 先查缓存
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }

    // 缓存未命中, 请求网络
    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;

    } catch (error) {
        // 网络也失败了, 返回离线页面
        return caches.match(OFFLINE_PAGE);
    }
}
```

9 点 16 分, 你将修复版本部署到生产环境。

但还有个问题: 如何让已打开页面的用户立即更新?

你在前端代码中添加了 Service Worker 更新检测:

```javascript
// app.js - Service Worker 注册与更新检测
if ('serviceWorker' in navigator) {
    // 注册 Service Worker
    navigator.serviceWorker.register('/sw.js').then((registration) => {
        console.log('Service Worker 注册成功');

        // ✅ 定期检查更新 (每 60 秒)
        setInterval(() => {
            registration.update();
        }, 60 * 1000);

        // ✅ 监听新版本安装完成
        registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;

            newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'activated') {
                    // 新版本已激活, 提示用户刷新
                    if (confirm('发现新版本, 是否立即更新?')) {
                        window.location.reload();
                    }
                }
            });
        });
    });

    // ✅ 监听 Service Worker 控制权变化
    let refreshing = false;
    navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (refreshing) return;
        refreshing = true;
        window.location.reload();
    });
}
```

9 点 22 分, 你再次部署前端代码。

---

## 效果验证

9 点 25 分, 你刷新监控系统。

数据开始好转:

```
实时错误率 (过去 5 分钟):
- 页面加载失败: 12.3% (↓ 77.4%)
- Service Worker 激活成功: 88.7%
- 离线缓存命中率: 67.8%

恢复统计:
- 成功刷新用户: 182,456 人 (73.7%)
- 待刷新用户: 65,076 人 (26.3%)
- 平均响应时间: 1.2s (正常)
```

你松了一口气, 但知道问题还没完全解决。还有 26% 的用户没刷新页面, 仍然使用旧版本。

9 点 28 分, 老王的电话又来了: "错误率下降了, 但还有部分用户反馈有问题, 什么情况?"

"还有些用户没刷新页面," 你解释, "需要他们手动刷新一次。我们已经在页面上加了自动更新提示, 应该很快就能全部恢复。"

"那就好," 老王说, "中午前必须恢复到 95% 以上。"

你挂断电话, 继续监控数据。每过几分钟, 成功率就提升一点:

```
9:30 - 76.8% 用户恢复
9:35 - 82.4% 用户恢复
9:40 - 89.1% 用户恢复
9:45 - 94.3% 用户恢复
9:50 - 97.8% 用户恢复 ✅
```

10 点整, 你在 Slack 频道发布了故障报告:

```
【故障报告】Service Worker 缓存失控事件

故障时间: 2024-01-15 00:00 - 09:50
影响范围: 247,532 用户 (89.7% 错误率)
根本原因: Service Worker 更新机制缺陷

问题分析:
1. 新版本 SW 未调用 skipWaiting(), 处于等待状态
2. 未调用 clients.claim(), 已打开页面未受控
3. 缓存策略过于激进, Cache First 导致永远用旧版本
4. 缺少自动更新检测机制

修复措施:
1. 紧急: 添加 skipWaiting() 和 clients.claim()
2. 紧急: 改进缓存策略 (Network First + Stale While Revalidate)
3. 紧急: 添加前端自动更新检测
4. 长期: 完善 Service Worker 版本管理体系

当前状态: ✅ 已恢复 (97.8% 用户正常)
```

---

## 架构改进

下午 2 点, 你开始整理长期改进方案。

你创建了一套完整的 Service Worker 管理体系:

### 1. 版本管理策略

```javascript
// sw-config.js - 统一版本管理
const SW_CONFIG = {
    version: '1.3.0',  // 语义化版本号

    caches: {
        static: `static-v1.3.0`,
        api: `api-v1.3.0`,
        images: `images-v1.3.0`
    },

    // 静态资源清单
    staticAssets: [
        '/',
        '/index.html',
        '/app.js',
        '/style.css',
        '/manifest.json',
        '/offline.html'
    ],

    // 缓存策略配置
    strategies: {
        document: 'stale-while-revalidate',
        api: 'network-first',
        static: 'cache-first',
        image: 'cache-first'
    },

    // 超时配置
    timeouts: {
        network: 5000,  // 网络请求超时 5 秒
        cache: 1000     // 缓存查询超时 1 秒
    }
};

export default SW_CONFIG;
```

### 2. 健壮的生命周期管理

```javascript
// sw.js - 改进后的完整版本
import SW_CONFIG from './sw-config.js';

// ===== Install 阶段 =====
self.addEventListener('install', (event) => {
    console.log(`[SW v${SW_CONFIG.version}] 安装中...`);

    event.waitUntil(
        Promise.all([
            // 预缓存静态资源
            caches.open(SW_CONFIG.caches.static).then((cache) => {
                return cache.addAll(SW_CONFIG.staticAssets);
            }),

            // 创建其他缓存空间 (空的)
            caches.open(SW_CONFIG.caches.api),
            caches.open(SW_CONFIG.caches.images)

        ]).then(() => {
            console.log(`[SW v${SW_CONFIG.version}] 安装完成`);

            // ✅ 立即激活新版本
            return self.skipWaiting();
        }).catch((error) => {
            console.error(`[SW v${SW_CONFIG.version}] 安装失败:`, error);
            throw error;
        })
    );
});

// ===== Activate 阶段 =====
self.addEventListener('activate', (event) => {
    console.log(`[SW v${SW_CONFIG.version}] 激活中...`);

    event.waitUntil(
        Promise.all([
            // 清理旧版本缓存
            cleanupOldCaches(),

            // ✅ 立即接管所有客户端
            self.clients.claim(),

            // 通知所有客户端: 新版本已激活
            notifyClients({
                type: 'SW_UPDATED',
                version: SW_CONFIG.version
            })

        ]).then(() => {
            console.log(`[SW v${SW_CONFIG.version}] 激活完成`);
        })
    );
});

// 清理旧缓存
async function cleanupOldCaches() {
    const cacheNames = await caches.keys();
    const currentCaches = Object.values(SW_CONFIG.caches);

    const deletePromises = cacheNames
        .filter(cacheName => !currentCaches.includes(cacheName))
        .map(cacheName => {
            console.log(`[SW] 删除旧缓存: ${cacheName}`);
            return caches.delete(cacheName);
        });

    return Promise.all(deletePromises);
}

// 通知所有客户端
async function notifyClients(message) {
    const clients = await self.clients.matchAll({ type: 'window' });

    clients.forEach(client => {
        client.postMessage(message);
    });
}

// ===== Fetch 阶段 =====
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // 跳过非同源请求
    if (url.origin !== self.location.origin) {
        return;
    }

    // 跳过 POST/PUT/DELETE 等修改性请求
    if (request.method !== 'GET') {
        return;
    }

    // 根据资源类型选择策略
    let strategy;

    if (request.url.includes('/api/')) {
        strategy = networkFirst;
    } else if (request.destination === 'document') {
        strategy = staleWhileRevalidate;
    } else if (request.destination === 'image') {
        strategy = cacheFirst;
    } else {
        strategy = cacheFirst;
    }

    event.respondWith(strategy(request));
});

// ===== 缓存策略实现 =====

// Strategy 1: Network First (网络优先)
async function networkFirst(request) {
    const cacheName = SW_CONFIG.caches.api;
    const cache = await caches.open(cacheName);

    try {
        // 带超时的网络请求
        const networkResponse = await fetchWithTimeout(
            request,
            SW_CONFIG.timeouts.network
        );

        // 成功后更新缓存
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;

    } catch (error) {
        console.log('[SW] 网络请求失败, 尝试缓存:', request.url);

        // 网络失败, 返回缓存
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        // 缓存也没有, 返回离线页面
        return caches.match('/offline.html');
    }
}

// Strategy 2: Stale While Revalidate (先缓存后更新)
async function staleWhileRevalidate(request) {
    const cacheName = SW_CONFIG.caches.static;
    const cache = await caches.open(cacheName);

    // 立即返回缓存 (如果有)
    const cachedResponse = await cache.match(request);

    // 同时发起网络请求更新缓存 (不等待)
    const fetchPromise = fetch(request)
        .then((networkResponse) => {
            if (networkResponse.ok) {
                cache.put(request, networkResponse.clone());
            }
            return networkResponse;
        })
        .catch(() => null);

    // 如果有缓存, 立即返回; 否则等待网络
    return cachedResponse || fetchPromise || caches.match('/offline.html');
}

// Strategy 3: Cache First (缓存优先)
async function cacheFirst(request) {
    const cacheName = request.destination === 'image'
        ? SW_CONFIG.caches.images
        : SW_CONFIG.caches.static;

    const cache = await caches.open(cacheName);

    // 先查缓存
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }

    // 缓存未命中, 请求网络
    try {
        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;

    } catch (error) {
        return caches.match('/offline.html');
    }
}

// 带超时的 fetch
function fetchWithTimeout(request, timeout) {
    return Promise.race([
        fetch(request),
        new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Request timeout')), timeout);
        })
    ]);
}
```

### 3. 前端完善的更新检测

```javascript
// app.js - Service Worker 完整管理
class ServiceWorkerManager {
    constructor() {
        this.registration = null;
        this.updateCheckInterval = 60 * 1000;  // 60 秒检查一次
    }

    async init() {
        if (!('serviceWorker' in navigator)) {
            console.warn('浏览器不支持 Service Worker');
            return;
        }

        try {
            // 注册 Service Worker
            this.registration = await navigator.serviceWorker.register('/sw.js', {
                scope: '/'
            });

            console.log('Service Worker 注册成功');

            // 监听更新
            this.setupUpdateListener();

            // 定期检查更新
            this.startUpdateCheck();

            // 监听消息
            this.setupMessageListener();

        } catch (error) {
            console.error('Service Worker 注册失败:', error);
        }
    }

    // 监听更新
    setupUpdateListener() {
        this.registration.addEventListener('updatefound', () => {
            const newWorker = this.registration.installing;

            console.log('发现新版本 Service Worker');

            newWorker.addEventListener('statechange', () => {
                console.log('Service Worker 状态:', newWorker.state);

                if (newWorker.state === 'activated') {
                    this.handleUpdate();
                }
            });
        });

        // 监听控制权变化
        let refreshing = false;
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            if (refreshing) return;
            refreshing = true;

            console.log('Service Worker 控制权已切换, 刷新页面');
            window.location.reload();
        });
    }

    // 处理更新
    handleUpdate() {
        // 显示更新提示
        this.showUpdateNotification();
    }

    // 显示更新通知
    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'sw-update-notification';
        notification.innerHTML = `
            <p>发现新版本, 是否立即更新?</p>
            <button id="sw-update-btn">立即更新</button>
            <button id="sw-dismiss-btn">稍后</button>
        `;

        document.body.appendChild(notification);

        document.getElementById('sw-update-btn').onclick = () => {
            window.location.reload();
        };

        document.getElementById('sw-dismiss-btn').onclick = () => {
            notification.remove();
        };
    }

    // 定期检查更新
    startUpdateCheck() {
        setInterval(() => {
            if (this.registration) {
                this.registration.update();
            }
        }, this.updateCheckInterval);
    }

    // 监听来自 Service Worker 的消息
    setupMessageListener() {
        navigator.serviceWorker.addEventListener('message', (event) => {
            const { type, version } = event.data;

            if (type === 'SW_UPDATED') {
                console.log(`Service Worker 已更新到 v${version}`);
            }
        });
    }

    // 手动触发更新
    async checkForUpdate() {
        if (this.registration) {
            await this.registration.update();
        }
    }

    // 卸载 Service Worker
    async unregister() {
        if (this.registration) {
            await this.registration.unregister();
            console.log('Service Worker 已卸载');
        }
    }
}

// 初始化
const swManager = new ServiceWorkerManager();
swManager.init();
```

---

## 知识档案: Service Worker 离线缓存的八大核心机制

**规则 1: Service Worker 有独立的生命周期, 不受页面刷新影响**

Service Worker 是浏览器后台运行的独立线程, 生命周期与页面完全分离。

```javascript
// Service Worker 生命周期状态
// parsed → installing → installed (waiting) → activating → activated → redundant

self.addEventListener('install', (event) => {
    // installing 状态: 安装静态资源
    console.log('Service Worker: 安装中...');

    event.waitUntil(
        caches.open('static-v1').then((cache) => {
            return cache.addAll(['/index.html', '/app.js']);
        }).then(() => {
            // ✅ 跳过等待, 立即激活
            return self.skipWaiting();
        })
    );
});

self.addEventListener('activate', (event) => {
    // activating 状态: 清理旧缓存
    console.log('Service Worker: 激活中...');

    event.waitUntil(
        Promise.all([
            cleanupOldCaches(),

            // ✅ 立即接管所有页面
            self.clients.claim()
        ])
    );
});
```

生命周期关键点:
- **installed (waiting)**: 新版本安装完成, 但等待旧版本释放
- **skipWaiting()**: 跳过等待, 立即进入 activating 状态
- **clients.claim()**: 激活后立即控制所有页面
- **redundant**: 被新版本替换或安装失败

---

**规则 2: 新版本 Service Worker 默认不会立即激活, 需要显式调用 skipWaiting()**

浏览器的保守策略: 等待所有使用旧版本的标签页关闭后, 新版本才激活。

```javascript
// ❌ 默认行为: 新版本等待
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('static-v2').then((cache) => {
            return cache.addAll([...]);
        })
        // 安装完成后, 进入 waiting 状态
        // 用户需要关闭所有标签页, 新版本才激活
    );
});

// ✅ 立即激活: 调用 skipWaiting()
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('static-v2').then((cache) => {
            return cache.addAll([...]);
        }).then(() => {
            // 跳过等待, 立即激活
            return self.skipWaiting();
        })
    );
});

// ✅ 前端检测新版本
navigator.serviceWorker.register('/sw.js').then((registration) => {
    registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;

        newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // 新版本已安装, 提示用户刷新
                alert('发现新版本, 请刷新页面');
            }
        });
    });
});
```

为什么需要 skipWaiting():
- **用户体验**: 避免用户长时间使用旧版本
- **快速修复**: 紧急 bug 修复能立即生效
- **版本一致性**: 避免新旧版本共存导致的问题

⚠️ 注意: skipWaiting() 可能导致已加载的页面使用旧资源, 需配合 clients.claim() 和页面刷新机制。

---

**规则 3: clients.claim() 让激活的 Service Worker 立即控制所有页面**

默认情况下, Service Worker 激活后不会立即控制已打开的页面。

```javascript
// ❌ 默认行为: 激活后不控制已打开页面
self.addEventListener('activate', (event) => {
    console.log('Service Worker 已激活');
    // 但已打开的页面仍由旧版本 SW 控制
    // 用户需要刷新页面才能使用新版本
});

// ✅ 立即控制: 调用 clients.claim()
self.addEventListener('activate', (event) => {
    event.waitUntil(
        Promise.all([
            cleanupOldCaches(),

            // 立即接管所有页面
            self.clients.claim()
        ])
    );
});

// 前端监听控制权变化
navigator.serviceWorker.addEventListener('controllerchange', () => {
    console.log('Service Worker 控制权已切换');
    // 自动刷新页面
    window.location.reload();
});
```

clients.claim() 的作用:
- **立即生效**: 新版本 Service Worker 立即控制所有页面
- **无缝切换**: 配合 skipWaiting() 实现无缝更新
- **版本统一**: 确保所有页面使用相同版本的 Service Worker

典型更新流程:
```javascript
// 完整的立即更新流程
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('v2').then(cache => cache.addAll([...]))
            .then(() => self.skipWaiting())  // 步骤 1: 跳过等待
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        cleanupOldCaches()
            .then(() => self.clients.claim())  // 步骤 2: 立即接管
    );
});
```

---

**规则 4: 缓存策略决定了离线体验质量, 不同资源应使用不同策略**

常见的 5 种缓存策略, 适用于不同场景。

```javascript
// Strategy 1: Cache First (缓存优先)
// 适用: 静态资源 (JS/CSS/图片)
async function cacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) {
        return cached;  // 有缓存立即返回
    }

    const network = await fetch(request);
    const cache = await caches.open('static');
    cache.put(request, network.clone());
    return network;
}

// Strategy 2: Network First (网络优先)
// 适用: API 请求 (需要最新数据)
async function networkFirst(request) {
    try {
        const network = await fetch(request);
        const cache = await caches.open('api');
        cache.put(request, network.clone());
        return network;
    } catch (error) {
        const cached = await caches.match(request);
        return cached || caches.match('/offline.html');
    }
}

// Strategy 3: Stale While Revalidate (先缓存后更新)
// 适用: HTML 页面 (快速加载 + 保持更新)
async function staleWhileRevalidate(request) {
    const cached = await caches.match(request);

    const fetchPromise = fetch(request).then((network) => {
        const cache = caches.open('pages');
        cache.then(c => c.put(request, network.clone()));
        return network;
    });

    return cached || fetchPromise;
}

// Strategy 4: Network Only (仅网络)
// 适用: 实时性要求高的请求 (支付/验证码)
async function networkOnly(request) {
    return fetch(request);  // 不缓存
}

// Strategy 5: Cache Only (仅缓存)
// 适用: 预缓存的资源 (manifest/icons)
async function cacheOnly(request) {
    return caches.match(request);
}
```

策略选择原则:

| 资源类型 | 推荐策略 | 原因 |
|---------|---------|------|
| HTML 页面 | Stale While Revalidate | 快速加载 + 保持更新 |
| API 请求 | Network First | 数据实时性 |
| JS/CSS | Cache First | 静态资源, 版本化管理 |
| 图片 | Cache First | 不常变化 |
| 支付请求 | Network Only | 必须实时 |
| Manifest | Cache Only | 预缓存资源 |

---

**规则 5: Cache API 是 Service Worker 的持久化存储, 独立于 HTTP 缓存**

Cache API 与 HTTP 缓存是两套独立的系统。

```javascript
// Cache API 操作
self.addEventListener('install', (event) => {
    event.waitUntil(
        // 打开或创建缓存空间
        caches.open('static-v1').then((cache) => {
            // 批量添加资源
            return cache.addAll([
                '/',
                '/index.html',
                '/app.js',
                '/style.css'
            ]);
        })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                // ✅ 直接返回缓存, 不发送网络请求
                // 完全绕过 HTTP 缓存 (Cache-Control, ETag)
                return cachedResponse;
            }

            return fetch(event.request).then((networkResponse) => {
                // 缓存网络响应
                const cache = caches.open('static-v1');
                cache.then(c => c.put(event.request, networkResponse.clone()));
                return networkResponse;
            });
        })
    );
});

// 清理旧缓存
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter(name => name !== 'static-v1')
                    .map(name => caches.delete(name))
            );
        })
    );
});
```

Cache API vs HTTP 缓存:

| 特性 | Cache API | HTTP 缓存 |
|------|----------|-----------|
| 控制权 | 完全由代码控制 | 由 HTTP 头控制 |
| 过期策略 | 手动管理 | Cache-Control, Expires |
| 存储位置 | 独立存储空间 | 浏览器缓存 |
| 优先级 | 高 (SW 拦截) | 低 (网络层) |
| 离线能力 | ✅ 完全离线 | ❌ 需要网络验证 |

Cache API 最佳实践:
- **版本化缓存**: 使用版本号作为缓存名 (`static-v1.2.3`)
- **及时清理**: activate 时删除旧版本缓存
- **分类存储**: 不同类型资源使用不同缓存空间 (`static`, `api`, `images`)
- **克隆响应**: `put()` 时使用 `response.clone()` 避免流消耗

---

**规则 6: event.waitUntil() 确保异步操作完成后才结束生命周期阶段**

Service Worker 的生命周期事件是短暂的, waitUntil() 延长其生命。

```javascript
// ❌ 错误: 异步操作未完成, SW 就进入下一阶段
self.addEventListener('install', (event) => {
    // 异步操作
    caches.open('static-v1').then((cache) => {
        return cache.addAll(['/index.html']);
    });

    // ❌ install 事件立即结束
    // cache.addAll() 可能还没完成
    // 导致缓存不完整
});

// ✅ 正确: 使用 waitUntil() 等待异步完成
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('static-v1').then((cache) => {
            return cache.addAll(['/index.html']);
        })
    );

    // ✅ 只有 cache.addAll() 完成后, install 才结束
});

// 复杂示例: 多个异步操作
self.addEventListener('activate', (event) => {
    event.waitUntil(
        Promise.all([
            // 操作 1: 清理旧缓存
            caches.keys().then((names) => {
                return Promise.all(
                    names
                        .filter(name => name !== 'current')
                        .map(name => caches.delete(name))
                );
            }),

            // 操作 2: 接管所有客户端
            self.clients.claim(),

            // 操作 3: 通知所有客户端
            notifyAllClients({ type: 'UPDATED' })
        ])
    );

    // ✅ 所有操作完成后, activate 才结束
});
```

waitUntil() 的作用:
- **延长生命周期**: 防止 SW 在异步操作完成前进入下一阶段
- **保证完整性**: 确保缓存资源、清理操作等全部完成
- **错误处理**: 如果 Promise 失败, 生命周期事件也失败

常见错误:
```javascript
// ❌ 错误 1: 忘记 return
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('static').then((cache) => {
            cache.addAll([...]);  // ❌ 没有 return
        })
    );
});

// ❌ 错误 2: 异步操作不在 waitUntil() 中
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('static')
    );

    // ❌ cache.addAll() 在 waitUntil() 外部
    caches.open('static').then(cache => cache.addAll([...]));
});

// ✅ 正确: 完整的 Promise 链
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('static').then((cache) => {
            return cache.addAll([...]);  // ✅ return
        })
    );
});
```

---

**规则 7: Service Worker 更新机制是增量的, 需要主动检查和清理旧版本**

浏览器自动检查 Service Worker 更新, 但开发者需要管理缓存版本。

```javascript
// 浏览器自动检查更新的时机:
// 1. 用户首次访问页面
// 2. 页面刷新且距上次检查超过 24 小时
// 3. 调用 registration.update()

// 前端: 手动触发更新检查
navigator.serviceWorker.register('/sw.js').then((registration) => {
    // 定期检查更新 (每 60 秒)
    setInterval(() => {
        registration.update();
    }, 60 * 1000);

    // 监听更新
    registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;

        newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // 新版本已安装 (处于 waiting 状态)
                console.log('新版本可用');
            }
        });
    });
});

// Service Worker: 清理旧版本缓存
const CURRENT_CACHES = {
    static: 'static-v1.3.0',
    api: 'api-v1.3.0',
    images: 'images-v1.3.0'
};

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter(cacheName => {
                        // 删除不在当前版本列表中的缓存
                        return !Object.values(CURRENT_CACHES).includes(cacheName);
                    })
                    .map(cacheName => {
                        console.log('删除旧缓存:', cacheName);
                        return caches.delete(cacheName);
                    })
            );
        })
    );
});
```

更新流程:

```
1. 浏览器检测到 sw.js 文件变化 (字节级对比)
   ↓
2. 下载新版本 sw.js, 执行 install 事件
   ↓
3. 新版本进入 waiting 状态 (如果有旧版本在运行)
   ↓
4. 用户关闭所有标签页, 或调用 skipWaiting()
   ↓
5. 新版本执行 activate 事件, 清理旧缓存
   ↓
6. 新版本接管所有页面 (如果调用了 clients.claim())
```

强制更新策略:
```javascript
// Service Worker: 立即更新
self.addEventListener('message', (event) => {
    if (event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

// 前端: 提示用户更新
navigator.serviceWorker.register('/sw.js').then((registration) => {
    registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing;

        newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                // 提示用户
                if (confirm('发现新版本, 是否立即更新?')) {
                    // 通知 Service Worker 跳过等待
                    newWorker.postMessage({ type: 'SKIP_WAITING' });
                }
            }
        });
    });
});
```

---

**规则 8: Service Worker 作用域 (scope) 决定了它能拦截哪些请求**

Service Worker 只能拦截其作用域内的请求。

```javascript
// 注册时指定 scope
navigator.serviceWorker.register('/sw.js', {
    scope: '/app/'  // 只拦截 /app/* 路径的请求
});

// ✅ 会被拦截: https://example.com/app/index.html
// ✅ 会被拦截: https://example.com/app/api/users
// ❌ 不会被拦截: https://example.com/about
// ❌ 不会被拦截: https://example.com/api/data

// 默认 scope 是 sw.js 所在的目录
navigator.serviceWorker.register('/sw.js');
// 默认 scope: '/' (拦截所有请求)

navigator.serviceWorker.register('/scripts/sw.js');
// 默认 scope: '/scripts/' (只拦截 /scripts/* 的请求)
```

作用域规则:
- **默认值**: Service Worker 文件所在目录
- **限制**: scope 不能超出 sw.js 所在目录
- **最大作用域**: 通过 HTTP 头 `Service-Worker-Allowed` 扩大范围

```javascript
// ❌ 错误: scope 超出 sw.js 所在目录
navigator.serviceWorker.register('/scripts/sw.js', {
    scope: '/'  // 错误! sw.js 在 /scripts/, scope 不能是 /
});

// ✅ 方法 1: 移动 sw.js 到根目录
navigator.serviceWorker.register('/sw.js', {
    scope: '/'  // 正确
});

// ✅ 方法 2: 服务器设置 HTTP 头扩大作用域
// HTTP Response Headers:
// Service-Worker-Allowed: /

navigator.serviceWorker.register('/scripts/sw.js', {
    scope: '/'  // 服务器允许, 可以这样做
});
```

fetch 事件作用域检查:
```javascript
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // 只处理同源且在 scope 内的请求
    if (url.origin === self.location.origin) {
        console.log('拦截请求:', url.pathname);

        event.respondWith(
            caches.match(event.request)
                .then(cached => cached || fetch(event.request))
        );
    }

    // 跨域请求不处理, 浏览器直接发送
});
```

多 Service Worker 共存:
```javascript
// App 1: 注册 scope 为 /app1/
navigator.serviceWorker.register('/app1/sw.js', {
    scope: '/app1/'
});

// App 2: 注册 scope 为 /app2/
navigator.serviceWorker.register('/app2/sw.js', {
    scope: '/app2/'
});

// ✅ 两个 Service Worker 可以共存
// /app1/* 的请求由 app1 的 SW 处理
// /app2/* 的请求由 app2 的 SW 处理
```

---

**事故档案编号**: NETWORK-2024-1954
**影响范围**: Service Worker 生命周期, 缓存策略, 离线功能, 版本管理, 更新机制
**根本原因**: Service Worker 更新机制缺陷导致新版本未激活, 缓存策略过于激进导致永远使用旧版本资源
**学习成本**: 高 (需深入理解浏览器缓存机制, Service Worker 生命周期, Promise 异步流程控制)

这是 JavaScript 世界第 154 次被记录的网络与数据事故。Service Worker 有独立的生命周期, 不受页面刷新影响。新版本 Service Worker 默认不会立即激活, 需要显式调用 skipWaiting() 跳过等待状态。clients.claim() 让激活的 Service Worker 立即控制所有页面。缓存策略决定了离线体验质量, 不同资源应使用不同策略 (Cache First, Network First, Stale While Revalidate)。Cache API 是 Service Worker 的持久化存储, 独立于 HTTP 缓存。event.waitUntil() 确保异步操作完成后才结束生命周期阶段。Service Worker 更新机制是增量的, 需要主动检查和清理旧版本缓存。Service Worker 作用域 (scope) 决定了它能拦截哪些请求。理解 Service Worker 的生命周期管理、缓存策略选择、版本更新机制是构建可靠 PWA 应用的基础。

---
