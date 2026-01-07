《第 157 次记录: 存储方案的技术选型 —— localStorage、sessionStorage 与 IndexedDB 的权衡》

---

## 技术选型会议

周二下午三点, 会议室的投影屏幕上显示着四个候选方案。

产品经理小王指着原型图: "我们需要离线编辑功能。用户在地铁上写文档, 没网络也要能保存草稿。回到办公室打开电脑, 数据要能同步。"

技术总监老李看向你: "前端存储方案你调研得怎么样了?"

你打开准备好的对比文档:

```
前端存储方案对比:

方案 1: Cookie
- 容量: 4KB
- 每次请求自动发送
- 主要用于身份认证

方案 2: localStorage
- 容量: 5-10MB
- 持久化存储
- 同步 API

方案 3: sessionStorage
- 容量: 5-10MB
- 会话级存储
- 同步 API

方案 4: IndexedDB
- 容量: 无限制 (受磁盘限制)
- 异步 API
- 支持索引和事务
```

后端老张皱眉: "localStorage 不是有 5MB 限制吗? 用户的文档如果很大怎么办?"

"这正是我要讨论的问题, " 你说, "每个方案都有适用场景和限制。Cookie 太小, localStorage 同步阻塞, IndexedDB 复杂度高。我们需要根据实际需求选择。"

小王问: "那用户编辑文档时, 应该用哪个?"

"这取决于文档大小、编辑频率、离线时长, " 你解释, "我这两天做了详细的测试和对比。"

老李点头: "好, 那就从最基础的 Cookie 开始, 逐个分析。"

---

## Cookie: 早期存储方案

你切换到第一页 PPT: "Cookie 诞生于 1994 年, 最初是为了解决 HTTP 无状态问题。"

### 基础特性

你打开控制台演示:

```javascript
// 设置 Cookie
document.cookie = "username=Alice";
document.cookie = "theme=dark";

// 读取 Cookie
console.log(document.cookie);
// "username=Alice; theme=dark"

// Cookie 的完整语法
document.cookie = "sessionId=abc123; max-age=3600; path=/; secure; samesite=strict";
```

"Cookie 的 API 设计很奇怪, " 你说, "读写都是通过 `document.cookie` 字符串操作, 不是结构化的对象。"

小陈 (前端新人) 问: "为什么每次赋值都要写完整的字符串?"

"因为 Cookie 是浏览器维护的, 不是 JavaScript 直接管理, " 你解释, "每次赋值实际上是告诉浏览器: 请设置或更新这个 Cookie。"

你展示了 Cookie 的完整选项:

```javascript
// Cookie 选项详解
function setCookie(name, value, options = {}) {
    let cookieString = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`;

    // max-age: 过期时间 (秒)
    if (options.maxAge) {
        cookieString += `; max-age=${options.maxAge}`;
    }

    // expires: 过期日期
    if (options.expires) {
        cookieString += `; expires=${options.expires.toUTCString()}`;
    }

    // path: 作用路径
    cookieString += `; path=${options.path || '/'}`;

    // domain: 作用域名
    if (options.domain) {
        cookieString += `; domain=${options.domain}`;
    }

    // secure: 仅 HTTPS
    if (options.secure) {
        cookieString += `; secure`;
    }

    // samesite: 跨站策略
    if (options.sameSite) {
        cookieString += `; samesite=${options.sameSite}`;
    }

    // httpOnly: 无法通过 JavaScript 访问 (需服务器设置)

    document.cookie = cookieString;
}

// 使用
setCookie('userId', '12345', {
    maxAge: 7 * 24 * 60 * 60,  // 7 天
    path: '/',
    secure: true,
    sameSite: 'strict'
});
```

老张问: "为什么 httpOnly 无法通过 JavaScript 设置?"

"安全原因, " 你回答, "httpOnly 的 Cookie 只能在服务器端设置, JavaScript 无法读取。这是为了防止 XSS 攻击窃取敏感 Cookie。"

### Cookie 的读取和解析

你展示了完整的 Cookie 管理类:

```javascript
// Cookie 管理类
class CookieManager {
    // 获取单个 Cookie
    static get(name) {
        const cookies = document.cookie.split('; ');

        for (const cookie of cookies) {
            const [key, value] = cookie.split('=');
            if (decodeURIComponent(key) === name) {
                return decodeURIComponent(value);
            }
        }

        return null;
    }

    // 获取所有 Cookie
    static getAll() {
        const cookies = {};
        const cookieStrings = document.cookie.split('; ');

        for (const cookie of cookieStrings) {
            if (!cookie) continue;

            const [key, value] = cookie.split('=');
            cookies[decodeURIComponent(key)] = decodeURIComponent(value);
        }

        return cookies;
    }

    // 设置 Cookie
    static set(name, value, options = {}) {
        let cookieString = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`;

        if (options.maxAge) {
            cookieString += `; max-age=${options.maxAge}`;
        }

        if (options.expires) {
            cookieString += `; expires=${options.expires.toUTCString()}`;
        }

        cookieString += `; path=${options.path || '/'}`;

        if (options.domain) {
            cookieString += `; domain=${options.domain}`;
        }

        if (options.secure) {
            cookieString += `; secure`;
        }

        if (options.sameSite) {
            cookieString += `; samesite=${options.sameSite}`;
        }

        document.cookie = cookieString;
    }

    // 删除 Cookie
    static delete(name, options = {}) {
        this.set(name, '', {
            ...options,
            maxAge: -1  // 设置为过期
        });
    }

    // 检查 Cookie 是否存在
    static has(name) {
        return this.get(name) !== null;
    }
}

// 使用示例
CookieManager.set('theme', 'dark', { maxAge: 30 * 24 * 60 * 60 });
console.log(CookieManager.get('theme'));  // "dark"
console.log(CookieManager.getAll());      // { theme: "dark", ... }
CookieManager.delete('theme');
```

### Cookie 的限制

你总结了 Cookie 的主要限制:

```
Cookie 的限制:

1. 容量限制:
   - 单个 Cookie: 4KB
   - 每个域名: 约 50 个 Cookie
   - 总容量: 约 200KB

2. 性能影响:
   - 每次 HTTP 请求自动携带
   - 增加请求大小和网络开销
   - 同源所有请求都会带上

3. API 限制:
   - 字符串操作, 不支持结构化数据
   - 同步 API, 可能阻塞
   - 无法存储复杂对象

4. 安全问题:
   - XSS 攻击可窃取 Cookie
   - CSRF 攻击可利用 Cookie
   - 需要 httpOnly 和 secure 保护
```

"所以 Cookie 不适合存储大量数据, " 你总结, "它的设计初衷是轻量级的会话标识, 不是客户端数据库。"

---

## localStorage: 持久化存储

你切换到第二页 PPT: "localStorage 在 HTML5 中引入, 提供了简单的键值对存储。"

### 基础 API

你演示基本操作:

```javascript
// 存储数据
localStorage.setItem('username', 'Alice');
localStorage.setItem('age', '25');

// 读取数据
console.log(localStorage.getItem('username'));  // "Alice"

// 删除数据
localStorage.removeItem('age');

// 清空所有数据
localStorage.clear();

// 获取键名
console.log(localStorage.key(0));  // 第一个键名

// 获取数量
console.log(localStorage.length);  // 键值对数量
```

"注意, " 你强调, "localStorage 只能存储字符串。如果存储对象, 必须先序列化。"

```javascript
// 存储对象
const user = { name: 'Alice', age: 25 };

// ❌ 错误: 直接存储对象会变成 "[object Object]"
localStorage.setItem('user', user);
console.log(localStorage.getItem('user'));  // "[object Object]"

// ✅ 正确: 先序列化
localStorage.setItem('user', JSON.stringify(user));
const retrieved = JSON.parse(localStorage.getItem('user'));
console.log(retrieved);  // { name: 'Alice', age: 25 }
```

### 封装工具类

你展示了一个实用的 localStorage 封装:

```javascript
// localStorage 工具类
class LocalStorage {
    // 设置数据
    static set(key, value, expires = null) {
        const data = {
            value: value,
            timestamp: Date.now(),
            expires: expires  // 过期时间 (毫秒)
        };

        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('localStorage.setItem 失败:', error);
            return false;
        }
    }

    // 获取数据
    static get(key) {
        try {
            const item = localStorage.getItem(key);
            if (!item) return null;

            const data = JSON.parse(item);

            // 检查是否过期
            if (data.expires && Date.now() - data.timestamp > data.expires) {
                this.remove(key);
                return null;
            }

            return data.value;
        } catch (error) {
            console.error('localStorage.getItem 失败:', error);
            return null;
        }
    }

    // 删除数据
    static remove(key) {
        localStorage.removeItem(key);
    }

    // 清空所有数据
    static clear() {
        localStorage.clear();
    }

    // 获取所有键
    static keys() {
        return Object.keys(localStorage);
    }

    // 获取所有数据
    static getAll() {
        const result = {};
        const keys = this.keys();

        for (const key of keys) {
            result[key] = this.get(key);
        }

        return result;
    }

    // 检查容量
    static getSize() {
        let total = 0;
        const keys = this.keys();

        for (const key of keys) {
            const value = localStorage.getItem(key);
            total += key.length + value.length;
        }

        return {
            bytes: total,
            kilobytes: (total / 1024).toFixed(2),
            megabytes: (total / 1024 / 1024).toFixed(2)
        };
    }
}

// 使用示例
LocalStorage.set('user', { name: 'Alice', age: 25 });
LocalStorage.set('tempData', 'value', 60 * 1000);  // 60 秒后过期

console.log(LocalStorage.get('user'));      // { name: 'Alice', age: 25 }
console.log(LocalStorage.getSize());        // { bytes: 123, kilobytes: "0.12", ... }
```

### 容量测试

小王问: "localStorage 真的有 5MB 限制吗?"

"我测试过了, " 你展示测试代码:

```javascript
// 测试 localStorage 容量限制
function testLocalStorageCapacity() {
    const testKey = 'capacity_test';
    let size = 0;
    const chunkSize = 1024 * 100;  // 100KB

    try {
        while (true) {
            const data = 'x'.repeat(chunkSize);
            localStorage.setItem(testKey, data.repeat(size + 1));
            size++;

            if (size % 10 === 0) {
                console.log(`已存储: ${(size * chunkSize / 1024 / 1024).toFixed(2)}MB`);
            }
        }
    } catch (error) {
        console.log(`容量上限: ${(size * chunkSize / 1024 / 1024).toFixed(2)}MB`);
        console.error('错误:', error.message);
    } finally {
        localStorage.removeItem(testKey);
    }
}

// 测试结果 (Chrome):
// 已存储: 1.00MB
// 已存储: 2.00MB
// 已存储: 3.00MB
// 已存储: 4.00MB
// 已存储: 5.00MB
// 容量上限: 5.00MB
// 错误: QuotaExceededError: Failed to execute 'setItem' on 'Storage'
```

"实测结果, " 你说, "Chrome 的 localStorage 限制是 5MB, Firefox 是 10MB, Safari 是 5MB。超出限制会抛出 `QuotaExceededError`。"

### 跨标签页通信

你展示了 localStorage 的一个特殊能力:

```javascript
// 跨标签页通信
// 标签页 A: 监听存储变化
window.addEventListener('storage', (event) => {
    console.log('存储变化:');
    console.log('- 键:', event.key);
    console.log('- 旧值:', event.oldValue);
    console.log('- 新值:', event.newValue);
    console.log('- URL:', event.url);
    console.log('- 存储对象:', event.storageArea);
});

// 标签页 B: 修改存储
localStorage.setItem('message', 'Hello from Tab B');

// 标签页 A 会收到 storage 事件
```

"注意, " 你提醒, "storage 事件只在**其他**标签页触发, 当前标签页不会收到自己修改的事件。"

### localStorage 的限制

你总结了 localStorage 的问题:

```
localStorage 的限制:

1. 容量限制:
   - Chrome/Safari: 5MB
   - Firefox: 10MB
   - 超出抛出 QuotaExceededError

2. 同步 API:
   - 读写操作阻塞主线程
   - 大量数据会导致卡顿
   - 不适合高频读写

3. 数据类型:
   - 只能存储字符串
   - 对象需要 JSON.stringify/parse
   - 无法存储 Blob、ArrayBuffer

4. 安全问题:
   - 同源任何脚本都可访问
   - XSS 攻击可窃取数据
   - 不适合存储敏感信息

5. 持久化问题:
   - 用户清理浏览器数据会丢失
   - 隐私模式下可能被限制
   - 无法保证数据永久存在
```

---

## sessionStorage: 会话级存储

"sessionStorage 和 localStorage API 完全相同, " 你说, "唯一的区别是生命周期。"

### 基础特性

你演示对比:

```javascript
// localStorage: 持久化存储
localStorage.setItem('persistent', 'value');
// → 关闭浏览器后仍然存在

// sessionStorage: 会话级存储
sessionStorage.setItem('temporary', 'value');
// → 关闭标签页后丢失
```

"sessionStorage 的生命周期是**浏览器标签页**, " 你解释, "关闭标签页, 数据就丢失了。"

小陈问: "那刷新页面呢?"

"刷新页面数据还在, " 你回答, "只有**关闭标签页**或**浏览器**才会清空。"

### 会话级存储的应用

你展示了 sessionStorage 的典型用例:

```javascript
// 用例 1: 表单草稿 (页面刷新不丢失)
class FormDraft {
    constructor(formId) {
        this.formId = formId;
        this.key = `form_draft_${formId}`;
    }

    // 保存草稿
    save(data) {
        sessionStorage.setItem(this.key, JSON.stringify(data));
    }

    // 加载草稿
    load() {
        const saved = sessionStorage.getItem(this.key);
        return saved ? JSON.parse(saved) : null;
    }

    // 清除草稿
    clear() {
        sessionStorage.removeItem(this.key);
    }
}

// 使用
const draft = new FormDraft('contact-form');

// 页面加载时恢复草稿
const savedData = draft.load();
if (savedData) {
    document.querySelector('#name').value = savedData.name;
    document.querySelector('#email').value = savedData.email;
}

// 输入时自动保存
document.querySelector('#contact-form').addEventListener('input', () => {
    draft.save({
        name: document.querySelector('#name').value,
        email: document.querySelector('#email').value
    });
});

// 提交后清除草稿
document.querySelector('#contact-form').addEventListener('submit', () => {
    draft.clear();
});
```

```javascript
// 用例 2: 多步骤表单
class MultiStepForm {
    constructor(formId) {
        this.formId = formId;
        this.key = `multi_step_${formId}`;
    }

    // 保存当前步骤
    saveStep(step, data) {
        const allData = this.loadAll() || {};
        allData[step] = data;
        sessionStorage.setItem(this.key, JSON.stringify(allData));
    }

    // 加载所有步骤
    loadAll() {
        const saved = sessionStorage.getItem(this.key);
        return saved ? JSON.parse(saved) : null;
    }

    // 加载特定步骤
    loadStep(step) {
        const allData = this.loadAll();
        return allData ? allData[step] : null;
    }

    // 提交后清除
    clear() {
        sessionStorage.removeItem(this.key);
    }
}

// 使用
const multiForm = new MultiStepForm('registration');

// 步骤 1: 保存基本信息
document.querySelector('#step1-next').addEventListener('click', () => {
    multiForm.saveStep('step1', {
        username: document.querySelector('#username').value,
        email: document.querySelector('#email').value
    });
});

// 步骤 2: 保存详细信息
document.querySelector('#step2-next').addEventListener('click', () => {
    multiForm.saveStep('step2', {
        address: document.querySelector('#address').value,
        phone: document.querySelector('#phone').value
    });
});

// 最终提交
document.querySelector('#submit').addEventListener('click', () => {
    const allData = multiForm.loadAll();
    console.log('提交数据:', allData);
    multiForm.clear();
});
```

```javascript
// 用例 3: 页面状态保存 (返回时恢复)
class PageState {
    static save(key, state) {
        sessionStorage.setItem(`page_state_${key}`, JSON.stringify(state));
    }

    static load(key) {
        const saved = sessionStorage.getItem(`page_state_${key}`);
        return saved ? JSON.parse(saved) : null;
    }

    static clear(key) {
        sessionStorage.removeItem(`page_state_${key}`);
    }
}

// 列表页: 保存滚动位置和筛选条件
window.addEventListener('beforeunload', () => {
    PageState.save('product-list', {
        scrollY: window.scrollY,
        filters: {
            category: document.querySelector('#category').value,
            priceRange: document.querySelector('#price').value
        }
    });
});

// 返回列表页时恢复
window.addEventListener('load', () => {
    const state = PageState.load('product-list');
    if (state) {
        window.scrollTo(0, state.scrollY);
        document.querySelector('#category').value = state.filters.category;
        document.querySelector('#price').value = state.filters.priceRange;
    }
});
```

### localStorage vs sessionStorage

你总结了两者的对比:

```
localStorage vs sessionStorage:

特性              | localStorage    | sessionStorage
-----------------|-----------------|----------------
生命周期          | 永久 (除非手动删除) | 标签页会话
作用域            | 同源所有标签页    | 当前标签页
刷新页面          | 保留             | 保留
新标签页打开同 URL | 共享             | 独立
关闭标签页        | 保留             | 清空
容量限制          | 5-10MB          | 5-10MB
API              | 完全相同         | 完全相同

适用场景:
- localStorage: 用户设置、主题、token、离线数据
- sessionStorage: 表单草稿、多步骤表单、临时状态
```

---

## IndexedDB: 浏览器数据库

"如果需要存储大量结构化数据, " 你说, "IndexedDB 是唯一的选择。"

### IndexedDB 特性

你列出了 IndexedDB 的核心特性:

```
IndexedDB 核心特性:

1. 容量:
   - 无固定限制 (受磁盘空间限制)
   - Chrome: 可用磁盘空间的 60%
   - 超出容量浏览器会提示用户

2. 数据类型:
   - 支持几乎所有 JavaScript 类型
   - 对象、数组、Blob、File、ArrayBuffer
   - 使用结构化克隆算法

3. 异步 API:
   - 所有操作都是异步的
   - 不阻塞主线程
   - 基于事件或 Promise

4. 索引:
   - 支持多个索引
   - 快速查询和范围查找
   - 支持唯一索引

5. 事务:
   - 所有操作必须在事务中
   - 支持 readonly/readwrite 模式
   - 原子性保证

6. 同源策略:
   - 每个源有独立的数据库
   - 跨域无法访问
```

### 基础操作

你展示了 IndexedDB 的基本使用:

```javascript
// 打开数据库
function openDatabase() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('MyDatabase', 1);

        // 首次创建或版本升级时触发
        request.onupgradeneeded = (event) => {
            const db = event.target.result;

            // 创建对象仓库 (类似表)
            if (!db.objectStoreNames.contains('users')) {
                const objectStore = db.createObjectStore('users', {
                    keyPath: 'id',      // 主键
                    autoIncrement: true // 自动递增
                });

                // 创建索引
                objectStore.createIndex('email', 'email', { unique: true });
                objectStore.createIndex('age', 'age', { unique: false });
            }
        };

        request.onsuccess = (event) => {
            resolve(event.target.result);
        };

        request.onerror = (event) => {
            reject(event.target.error);
        };
    });
}

// 添加数据
async function addUser(user) {
    const db = await openDatabase();

    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['users'], 'readwrite');
        const objectStore = transaction.objectStore('users');

        const request = objectStore.add(user);

        request.onsuccess = () => {
            resolve(request.result);  // 返回自动生成的 id
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}

// 读取数据
async function getUser(id) {
    const db = await openDatabase();

    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['users'], 'readonly');
        const objectStore = transaction.objectStore('users');

        const request = objectStore.get(id);

        request.onsuccess = () => {
            resolve(request.result);
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}

// 更新数据
async function updateUser(user) {
    const db = await openDatabase();

    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['users'], 'readwrite');
        const objectStore = transaction.objectStore('users');

        const request = objectStore.put(user);

        request.onsuccess = () => {
            resolve(request.result);
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}

// 删除数据
async function deleteUser(id) {
    const db = await openDatabase();

    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['users'], 'readwrite');
        const objectStore = transaction.objectStore('users');

        const request = objectStore.delete(id);

        request.onsuccess = () => {
            resolve();
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}

// 查询所有数据
async function getAllUsers() {
    const db = await openDatabase();

    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['users'], 'readonly');
        const objectStore = transaction.objectStore('users');

        const request = objectStore.getAll();

        request.onsuccess = () => {
            resolve(request.result);
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}

// 使用索引查询
async function getUserByEmail(email) {
    const db = await openDatabase();

    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['users'], 'readonly');
        const objectStore = transaction.objectStore('users');
        const index = objectStore.index('email');

        const request = index.get(email);

        request.onsuccess = () => {
            resolve(request.result);
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}

// 范围查询
async function getUsersByAgeRange(minAge, maxAge) {
    const db = await openDatabase();

    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['users'], 'readonly');
        const objectStore = transaction.objectStore('users');
        const index = objectStore.index('age');

        const range = IDBKeyRange.bound(minAge, maxAge);
        const request = index.getAll(range);

        request.onsuccess = () => {
            resolve(request.result);
        };

        request.onerror = () => {
            reject(request.error);
        };
    });
}
```

### 封装工具类

"IndexedDB 的 API 太繁琐了, " 小陈抱怨。

"所以我封装了一个工具类, " 你展示:

```javascript
// IndexedDB 工具类
class IndexedDBHelper {
    constructor(dbName, version = 1) {
        this.dbName = dbName;
        this.version = version;
        this.db = null;
    }

    // 打开数据库
    async open(stores = []) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.version);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // 创建对象仓库
                for (const store of stores) {
                    if (!db.objectStoreNames.contains(store.name)) {
                        const objectStore = db.createObjectStore(store.name, {
                            keyPath: store.keyPath || 'id',
                            autoIncrement: store.autoIncrement !== false
                        });

                        // 创建索引
                        if (store.indexes) {
                            for (const index of store.indexes) {
                                objectStore.createIndex(
                                    index.name,
                                    index.keyPath || index.name,
                                    {
                                        unique: index.unique || false,
                                        multiEntry: index.multiEntry || false
                                    }
                                );
                            }
                        }
                    }
                }
            };

            request.onsuccess = (event) => {
                this.db = event.target.result;
                resolve(this.db);
            };

            request.onerror = (event) => {
                reject(event.target.error);
            };
        });
    }

    // 添加数据
    async add(storeName, data) {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const objectStore = transaction.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const request = objectStore.add(data);

            request.onsuccess = () => {
                resolve(request.result);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    // 批量添加
    async addAll(storeName, dataArray) {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const objectStore = transaction.objectStore(storeName);

        const promises = dataArray.map(data => {
            return new Promise((resolve, reject) => {
                const request = objectStore.add(data);
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
        });

        return Promise.all(promises);
    }

    // 获取数据
    async get(storeName, key) {
        const transaction = this.db.transaction([storeName], 'readonly');
        const objectStore = transaction.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const request = objectStore.get(key);

            request.onsuccess = () => {
                resolve(request.result);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    // 获取所有数据
    async getAll(storeName) {
        const transaction = this.db.transaction([storeName], 'readonly');
        const objectStore = transaction.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const request = objectStore.getAll();

            request.onsuccess = () => {
                resolve(request.result);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    // 通过索引查询
    async getByIndex(storeName, indexName, value) {
        const transaction = this.db.transaction([storeName], 'readonly');
        const objectStore = transaction.objectStore(storeName);
        const index = objectStore.index(indexName);

        return new Promise((resolve, reject) => {
            const request = index.get(value);

            request.onsuccess = () => {
                resolve(request.result);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    // 范围查询
    async getByRange(storeName, indexName, lower, upper) {
        const transaction = this.db.transaction([storeName], 'readonly');
        const objectStore = transaction.objectStore(storeName);
        const index = objectStore.index(indexName);

        const range = IDBKeyRange.bound(lower, upper);

        return new Promise((resolve, reject) => {
            const request = index.getAll(range);

            request.onsuccess = () => {
                resolve(request.result);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    // 更新数据
    async update(storeName, data) {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const objectStore = transaction.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const request = objectStore.put(data);

            request.onsuccess = () => {
                resolve(request.result);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    // 删除数据
    async delete(storeName, key) {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const objectStore = transaction.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const request = objectStore.delete(key);

            request.onsuccess = () => {
                resolve();
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    // 清空对象仓库
    async clear(storeName) {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const objectStore = transaction.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const request = objectStore.clear();

            request.onsuccess = () => {
                resolve();
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    // 获取数量
    async count(storeName) {
        const transaction = this.db.transaction([storeName], 'readonly');
        const objectStore = transaction.objectStore(storeName);

        return new Promise((resolve, reject) => {
            const request = objectStore.count();

            request.onsuccess = () => {
                resolve(request.result);
            };

            request.onerror = () => {
                reject(request.error);
            };
        });
    }

    // 关闭数据库
    close() {
        if (this.db) {
            this.db.close();
        }
    }
}

// 使用示例
const db = new IndexedDBHelper('MyApp', 1);

await db.open([
    {
        name: 'users',
        keyPath: 'id',
        autoIncrement: true,
        indexes: [
            { name: 'email', unique: true },
            { name: 'age', unique: false }
        ]
    },
    {
        name: 'posts',
        keyPath: 'id',
        autoIncrement: true,
        indexes: [
            { name: 'userId', unique: false },
            { name: 'createdAt', unique: false }
        ]
    }
]);

// 添加用户
const userId = await db.add('users', {
    name: 'Alice',
    email: 'alice@example.com',
    age: 25
});

// 查询用户
const user = await db.get('users', userId);
console.log(user);

// 通过邮箱查询
const userByEmail = await db.getByIndex('users', 'email', 'alice@example.com');
console.log(userByEmail);

// 年龄范围查询
const usersInRange = await db.getByRange('users', 'age', 20, 30);
console.log(usersInRange);
```

---

## 性能对比与选型建议

"我做了详细的性能测试, " 你展示测试结果:

```javascript
// 性能对比测试
async function performanceComparison() {
    const testData = Array.from({ length: 1000 }, (_, i) => ({
        id: i,
        name: `User ${i}`,
        email: `user${i}@example.com`,
        age: 20 + (i % 30)
    }));

    // 测试 localStorage
    console.log('=== localStorage 测试 ===');
    console.time('localStorage: 写入 1000 条');
    for (const item of testData) {
        localStorage.setItem(`user_${item.id}`, JSON.stringify(item));
    }
    console.timeEnd('localStorage: 写入 1000 条');

    console.time('localStorage: 读取 1000 条');
    for (let i = 0; i < 1000; i++) {
        const data = JSON.parse(localStorage.getItem(`user_${i}`));
    }
    console.timeEnd('localStorage: 读取 1000 条');

    // 清理
    for (let i = 0; i < 1000; i++) {
        localStorage.removeItem(`user_${i}`);
    }

    // 测试 IndexedDB
    console.log('=== IndexedDB 测试 ===');
    const db = new IndexedDBHelper('PerformanceTest', 1);
    await db.open([{
        name: 'users',
        keyPath: 'id',
        indexes: [{ name: 'email', unique: true }]
    }]);

    console.time('IndexedDB: 写入 1000 条');
    await db.addAll('users', testData);
    console.timeEnd('IndexedDB: 写入 1000 条');

    console.time('IndexedDB: 读取 1000 条');
    const allUsers = await db.getAll('users');
    console.timeEnd('IndexedDB: 读取 1000 条');

    console.time('IndexedDB: 索引查询 100 次');
    for (let i = 0; i < 100; i++) {
        await db.getByIndex('users', 'email', `user${i}@example.com`);
    }
    console.timeEnd('IndexedDB: 索引查询 100 次');

    db.close();
}

// 测试结果 (Chrome):
// === localStorage 测试 ===
// localStorage: 写入 1000 条: 45ms
// localStorage: 读取 1000 条: 12ms
//
// === IndexedDB 测试 ===
// IndexedDB: 写入 1000 条: 8ms
// IndexedDB: 读取 1000 条: 2ms
// IndexedDB: 索引查询 100 次: 15ms
```

你总结了性能对比:

```
性能对比 (1000 条数据):

操作              | localStorage | IndexedDB
-----------------|--------------|----------
批量写入          | 45ms         | 8ms
批量读取          | 12ms         | 2ms
索引查询 (100 次) | -            | 15ms
主线程阻塞        | 是           | 否

结论:
- localStorage: 小数据量 (<100 条) 同步读写快速
- IndexedDB: 大数据量 (>1000 条) 异步操作高效
```

### 选型决策矩阵

你展示了最终的选型建议:

```
存储方案选型决策:

1. 使用 Cookie 的场景:
   ✅ 需要在 HTTP 请求中自动携带
   ✅ 数据量很小 (<1KB)
   ✅ 服务器需要读取的数据
   ❌ 不适合: 大量数据、频繁修改、敏感信息

2. 使用 localStorage 的场景:
   ✅ 需要持久化存储
   ✅ 数据量中等 (<5MB)
   ✅ 跨标签页共享
   ✅ 简单的键值对
   ❌ 不适合: 大量数据、高频读写、复杂查询

   典型用例:
   - 用户设置 (主题、语言)
   - 认证 token
   - 离线数据缓存
   - 跨标签页通信

3. 使用 sessionStorage 的场景:
   ✅ 会话级临时数据
   ✅ 表单草稿 (刷新不丢失)
   ✅ 多步骤表单
   ✅ 页面状态保存
   ❌ 不适合: 需要持久化、跨标签页

   典型用例:
   - 表单草稿自动保存
   - 多步骤向导数据
   - 页面滚动位置
   - 临时筛选条件

4. 使用 IndexedDB 的场景:
   ✅ 大量结构化数据 (>5MB)
   ✅ 需要索引和快速查询
   ✅ 复杂数据关系
   ✅ 异步操作 (不阻塞)
   ❌ 不适合: 简单数据、快速原型

   典型用例:
   - 离线应用数据
   - 大文件缓存
   - 聊天记录
   - 文档编辑器
```

### 实际项目的最终方案

老李问: "那我们的离线编辑功能, 应该用哪个?"

你展示了混合方案:

```javascript
// 混合存储方案: 根据数据类型选择存储
class AppStorage {
    constructor() {
        this.db = new IndexedDBHelper('OfflineApp', 1);
    }

    async init() {
        await this.db.open([
            {
                name: 'documents',
                keyPath: 'id',
                autoIncrement: true,
                indexes: [
                    { name: 'title', unique: false },
                    { name: 'createdAt', unique: false },
                    { name: 'updatedAt', unique: false }
                ]
            }
        ]);
    }

    // 用户设置: localStorage (持久化, 小数据)
    saveSetting(key, value) {
        localStorage.setItem(`setting_${key}`, JSON.stringify(value));
    }

    loadSetting(key) {
        const value = localStorage.getItem(`setting_${key}`);
        return value ? JSON.parse(value) : null;
    }

    // 编辑中的文档: sessionStorage (会话级, 自动保存)
    saveDraft(docId, content) {
        sessionStorage.setItem(`draft_${docId}`, JSON.stringify({
            content,
            savedAt: Date.now()
        }));
    }

    loadDraft(docId) {
        const draft = sessionStorage.getItem(`draft_${docId}`);
        return draft ? JSON.parse(draft) : null;
    }

    clearDraft(docId) {
        sessionStorage.removeItem(`draft_${docId}`);
    }

    // 完整文档: IndexedDB (大数据, 索引查询)
    async saveDocument(doc) {
        if (doc.id) {
            return await this.db.update('documents', doc);
        } else {
            return await this.db.add('documents', {
                ...doc,
                createdAt: Date.now(),
                updatedAt: Date.now()
            });
        }
    }

    async loadDocument(id) {
        return await this.db.get('documents', id);
    }

    async getAllDocuments() {
        return await this.db.getAll('documents');
    }

    async searchDocuments(keyword) {
        const allDocs = await this.getAllDocuments();
        return allDocs.filter(doc =>
            doc.title.includes(keyword) ||
            doc.content.includes(keyword)
        );
    }

    async deleteDocument(id) {
        await this.db.delete('documents', id);
    }
}

// 使用
const storage = new AppStorage();
await storage.init();

// 保存用户设置
storage.saveSetting('theme', 'dark');
storage.saveSetting('fontSize', 16);

// 编辑时自动保存草稿
setInterval(() => {
    const currentDocId = getCurrentDocId();
    const content = getEditorContent();
    storage.saveDraft(currentDocId, content);
}, 5000);  // 每 5 秒自动保存

// 正式保存文档
await storage.saveDocument({
    title: '我的文档',
    content: '...',
    tags: ['工作', '重要']
});

// 查询所有文档
const docs = await storage.getAllDocuments();
console.log(`共 ${docs.length} 篇文档`);
```

---

## 知识档案: 前端存储的八个核心机制

**规则 1: Cookie 是为 HTTP 通信设计的, 不是客户端存储方案**

Cookie 的主要用途是在客户端和服务器之间传递信息, 每次 HTTP 请求都会自动携带同源 Cookie。

```javascript
// Cookie 的特性
// 1. 容量限制: 单个 Cookie 4KB, 每个域名约 50 个
// 2. 自动携带: 每次请求自动发送, 增加网络开销
// 3. 字符串操作: 通过 document.cookie 读写字符串

// 设置 Cookie
document.cookie = "username=Alice; max-age=86400; path=/; secure; samesite=strict";

// 读取 Cookie (需要解析字符串)
const cookies = document.cookie.split('; ');
const cookieMap = {};
cookies.forEach(cookie => {
    const [key, value] = cookie.split('=');
    cookieMap[key] = value;
});

// Cookie 选项
// - max-age: 过期时间 (秒)
// - expires: 过期日期
// - path: 作用路径
// - domain: 作用域名
// - secure: 仅 HTTPS
// - samesite: 跨站策略 (strict/lax/none)
// - httpOnly: 无法通过 JS 访问 (服务器设置)
```

为什么 Cookie 不适合存储:
- **容量太小**: 4KB 无法存储复杂数据
- **性能影响**: 每次请求都携带, 浪费带宽
- **API 不友好**: 字符串操作, 不支持结构化数据
- **安全风险**: XSS 可窃取, CSRF 可利用

---

**规则 2: localStorage 提供同步的键值对持久化存储**

localStorage 在 HTML5 中引入, 提供简单的同步 API 存储字符串数据, 数据永久保存直到手动删除。

```javascript
// localStorage API
localStorage.setItem('key', 'value');           // 存储
const value = localStorage.getItem('key');      // 读取
localStorage.removeItem('key');                 // 删除
localStorage.clear();                           // 清空
const count = localStorage.length;              // 数量
const firstKey = localStorage.key(0);           // 第一个键

// 只能存储字符串, 对象需要序列化
const user = { name: 'Alice', age: 25 };

// ❌ 错误: 直接存储对象
localStorage.setItem('user', user);
localStorage.getItem('user');  // "[object Object]"

// ✅ 正确: 序列化后存储
localStorage.setItem('user', JSON.stringify(user));
const retrieved = JSON.parse(localStorage.getItem('user'));
```

localStorage 的限制:
- **容量限制**: Chrome/Safari 5MB, Firefox 10MB
- **同步 API**: 读写阻塞主线程, 大量数据会卡顿
- **字符串类型**: 只能存储字符串, 需要序列化
- **无过期机制**: 需要手动管理过期时间
- **安全问题**: 同源任何脚本都可访问, XSS 可窃取

---

**规则 3: sessionStorage 和 localStorage API 相同, 但生命周期是标签页会话**

sessionStorage 的唯一区别是生命周期, 关闭标签页数据就丢失, 但刷新页面数据仍在。

```javascript
// sessionStorage API 与 localStorage 完全相同
sessionStorage.setItem('tempData', 'value');
const data = sessionStorage.getItem('tempData');
sessionStorage.removeItem('tempData');
sessionStorage.clear();

// 生命周期对比
localStorage.setItem('persistent', 'value');    // 永久存在
sessionStorage.setItem('temporary', 'value');   // 关闭标签页丢失

// 刷新页面
location.reload();
localStorage.getItem('persistent');    // ✅ 仍然存在
sessionStorage.getItem('temporary');   // ✅ 仍然存在

// 关闭标签页后重新打开
// localStorage.getItem('persistent');    // ✅ 仍然存在
// sessionStorage.getItem('temporary');   // ❌ 已清空
```

sessionStorage 的作用域:
- **标签页级别**: 每个标签页独立, 不共享
- **同 URL 新标签页**: 数据独立, 不复制
- **刷新页面**: 数据保留
- **关闭标签页**: 数据清空

典型应用场景:
- **表单草稿**: 刷新不丢失, 提交后清空
- **多步骤表单**: 保存中间状态
- **页面状态**: 滚动位置, 筛选条件
- **临时数据**: 不需要持久化的状态

---

**规则 4: localStorage 的 storage 事件实现跨标签页通信**

localStorage 修改会触发 storage 事件, 但只在**其他**标签页触发, 当前标签页不会收到。

```javascript
// 标签页 A: 监听存储变化
window.addEventListener('storage', (event) => {
    console.log('存储变化:');
    console.log('- 键:', event.key);
    console.log('- 旧值:', event.oldValue);
    console.log('- 新值:', event.newValue);
    console.log('- URL:', event.url);
    console.log('- 存储对象:', event.storageArea);
});

// 标签页 B: 修改存储
localStorage.setItem('message', 'Hello from Tab B');
// 标签页 A 会收到 storage 事件

// 实现跨标签页通信
class TabMessenger {
    static send(type, data) {
        const message = {
            type,
            data,
            timestamp: Date.now()
        };
        localStorage.setItem('tab_message', JSON.stringify(message));
    }

    static listen(handler) {
        window.addEventListener('storage', (event) => {
            if (event.key === 'tab_message' && event.newValue) {
                const message = JSON.parse(event.newValue);
                handler(message);
            }
        });
    }
}

// 标签页 A
TabMessenger.listen((message) => {
    console.log('收到消息:', message);
});

// 标签页 B
TabMessenger.send('notification', { title: '新消息', count: 5 });
```

storage 事件特性:
- **触发范围**: 仅其他标签页, 当前标签页不触发
- **事件属性**: key, oldValue, newValue, url, storageArea
- **触发时机**: setItem/removeItem/clear 时触发
- **仅 localStorage**: sessionStorage 修改不触发跨标签页事件

---

**规则 5: localStorage 超出容量限制会抛出 QuotaExceededError**

localStorage 有固定的容量限制, 超出时 setItem 会抛出 QuotaExceededError 异常。

```javascript
// 容量限制因浏览器而异
// Chrome/Safari: 5MB
// Firefox: 10MB

// 处理容量超限
function safeSetItem(key, value) {
    try {
        localStorage.setItem(key, value);
        return { success: true };
    } catch (error) {
        if (error.name === 'QuotaExceededError') {
            console.error('localStorage 容量已满');

            // 策略 1: 清理旧数据
            const keys = Object.keys(localStorage);
            const oldestKey = keys.sort((a, b) => {
                const aTime = JSON.parse(localStorage.getItem(a)).timestamp || 0;
                const bTime = JSON.parse(localStorage.getItem(b)).timestamp || 0;
                return aTime - bTime;
            })[0];

            if (oldestKey) {
                localStorage.removeItem(oldestKey);
                return safeSetItem(key, value);  // 重试
            }

            return { success: false, error: 'capacity_exceeded' };
        }

        return { success: false, error: error.message };
    }
}

// 监控容量使用
function getStorageSize() {
    let total = 0;

    for (const key in localStorage) {
        if (localStorage.hasOwnProperty(key)) {
            total += key.length + localStorage.getItem(key).length;
        }
    }

    return {
        bytes: total,
        kilobytes: (total / 1024).toFixed(2),
        megabytes: (total / 1024 / 1024).toFixed(2),
        percentage: ((total / (5 * 1024 * 1024)) * 100).toFixed(2) + '%'  // 假设 5MB 限制
    };
}

console.log(getStorageSize());
// { bytes: 123456, kilobytes: "120.56", megabytes: "0.12", percentage: "2.35%" }
```

容量管理策略:
- **错误捕获**: 始终 try-catch localStorage.setItem
- **容量监控**: 定期检查使用量, 接近限制时清理
- **数据过期**: 实现 TTL 机制, 自动清理过期数据
- **降级策略**: 容量满时使用 sessionStorage 或内存缓存

---

**规则 6: IndexedDB 提供异步的事务型数据库存储**

IndexedDB 是浏览器内置的 NoSQL 数据库, 支持索引、事务、大容量存储和异步操作。

```javascript
// IndexedDB 核心概念
// - Database: 数据库
// - ObjectStore: 对象仓库 (类似表)
// - Index: 索引 (加速查询)
// - Transaction: 事务 (保证原子性)
// - KeyPath: 主键字段
// - Cursor: 游标 (遍历数据)

// 打开数据库
const request = indexedDB.open('MyDB', 1);

request.onupgradeneeded = (event) => {
    const db = event.target.result;

    // 创建对象仓库
    const objectStore = db.createObjectStore('users', {
        keyPath: 'id',          // 主键
        autoIncrement: true     // 自动递增
    });

    // 创建索引
    objectStore.createIndex('email', 'email', { unique: true });
    objectStore.createIndex('age', 'age', { unique: false });
};

request.onsuccess = (event) => {
    const db = event.target.result;

    // 添加数据 (需要事务)
    const transaction = db.transaction(['users'], 'readwrite');
    const objectStore = transaction.objectStore('users');

    objectStore.add({ name: 'Alice', email: 'alice@example.com', age: 25 });

    // 查询数据
    const getRequest = objectStore.get(1);  // 通过主键查询
    getRequest.onsuccess = () => {
        console.log(getRequest.result);
    };

    // 通过索引查询
    const index = objectStore.index('email');
    const indexRequest = index.get('alice@example.com');
    indexRequest.onsuccess = () => {
        console.log(indexRequest.result);
    };
};
```

IndexedDB 的特性:
- **大容量**: 无固定限制, 可用磁盘空间的 60%
- **异步 API**: 所有操作异步, 不阻塞主线程
- **事务保证**: 操作在事务中, 保证原子性
- **索引支持**: 快速查询和范围查找
- **复杂类型**: 支持对象、数组、Blob、File 等

---

**规则 7: IndexedDB 的所有操作必须在事务中进行**

IndexedDB 使用事务保证数据一致性, 所有读写操作必须在事务中执行。

```javascript
// 事务类型
// - readonly: 只读, 多个事务可并发
// - readwrite: 读写, 同一对象仓库只能有一个
// - versionchange: 版本升级 (onupgradeneeded 中)

const db = await openDatabase();

// 只读事务
const readTransaction = db.transaction(['users'], 'readonly');
const readStore = readTransaction.objectStore('users');
const user = await readStore.get(1);

// 读写事务
const writeTransaction = db.transaction(['users'], 'readwrite');
const writeStore = writeTransaction.objectStore('users');
await writeStore.add({ name: 'Bob', age: 30 });

// 事务自动提交
writeTransaction.oncomplete = () => {
    console.log('事务提交成功');
};

writeTransaction.onerror = () => {
    console.error('事务失败, 自动回滚');
};

// 手动中止事务
writeTransaction.abort();

// 多个操作在同一事务中
const transaction = db.transaction(['users', 'posts'], 'readwrite');
const userStore = transaction.objectStore('users');
const postStore = transaction.objectStore('posts');

// 添加用户和文章
userStore.add({ name: 'Charlie', age: 35 });
postStore.add({ userId: 1, title: 'My Post' });

// 所有操作成功才提交, 任一失败全部回滚
```

事务的生命周期:
- **创建**: db.transaction(['storeName'], 'mode')
- **活跃**: 执行操作, 可以继续添加操作
- **提交**: 所有操作完成, 自动提交
- **回滚**: 任一操作失败, 自动回滚
- **完成**: oncomplete 触发
- **失败**: onerror 触发

事务最佳实践:
- **最小范围**: 只包含必要的对象仓库
- **快速执行**: 不要在事务中执行耗时操作
- **错误处理**: 监听 onerror 事件
- **批量操作**: 多个操作放在同一事务中

---

**规则 8: 选择存储方案要根据数据特性和使用场景**

不同的存储方案有不同的特性和限制, 应根据数据大小、读写频率、持久化需求选择合适的方案。

```javascript
// 存储方案决策树
function chooseStorage(requirements) {
    const { size, persistent, structured, performance, crossTab } = requirements;

    // 1. 数据量很小 (<1KB) 且需要服务器读取
    if (size < 1024 && requirements.serverAccess) {
        return 'Cookie';
    }

    // 2. 会话级临时数据
    if (!persistent) {
        return 'sessionStorage';
    }

    // 3. 简单键值对, 中等数据量 (<5MB)
    if (size < 5 * 1024 * 1024 && !structured && !performance) {
        return 'localStorage';
    }

    // 4. 大量数据 (>5MB) 或需要复杂查询
    if (size >= 5 * 1024 * 1024 || structured || performance) {
        return 'IndexedDB';
    }

    return 'localStorage';  // 默认
}

// 示例 1: 用户设置
chooseStorage({
    size: 100,              // 100 bytes
    persistent: true,       // 持久化
    structured: false,      // 简单数据
    performance: false,     // 性能要求不高
    crossTab: true          // 跨标签页共享
});
// → localStorage

// 示例 2: 离线文档
chooseStorage({
    size: 10 * 1024 * 1024, // 10MB
    persistent: true,       // 持久化
    structured: true,       // 结构化数据
    performance: true,      // 需要索引查询
    crossTab: false
});
// → IndexedDB

// 示例 3: 表单草稿
chooseStorage({
    size: 1024,             // 1KB
    persistent: false,      // 会话级
    structured: false,
    performance: false,
    crossTab: false
});
// → sessionStorage
```

选型决策矩阵:

| 需求维度          | Cookie   | localStorage | sessionStorage | IndexedDB  |
|------------------|----------|--------------|----------------|------------|
| 容量             | 4KB      | 5-10MB       | 5-10MB         | 无限制     |
| 持久化           | 可配置   | ✅           | ❌             | ✅         |
| 同步/异步        | 同步     | 同步         | 同步           | 异步       |
| 数据类型         | 字符串   | 字符串       | 字符串         | 任意类型   |
| 索引查询         | ❌       | ❌           | ❌             | ✅         |
| 事务支持         | ❌       | ❌           | ❌             | ✅         |
| HTTP 自动携带    | ✅       | ❌           | ❌             | ❌         |
| 跨标签页         | ✅       | ✅           | ❌             | ✅         |
| 性能 (大数据)    | 差       | 中           | 中             | 优         |
| API 复杂度       | 中       | 低           | 低             | 高         |

实际项目推荐:
- **用户设置**: localStorage (简单、持久化)
- **认证 Token**: localStorage + httpOnly Cookie (安全)
- **表单草稿**: sessionStorage (会话级、自动清理)
- **离线数据**: IndexedDB (大容量、索引)
- **跨标签页通信**: localStorage + storage 事件
- **临时缓存**: sessionStorage (无需持久化)

---

**事故档案编号**: NETWORK-2024-1957
**影响范围**: Cookie, localStorage, sessionStorage, IndexedDB, 前端存储方案
**根本原因**: 不同存储方案有不同的容量、持久化、API 特性, 需要根据实际需求选择合适方案
**学习成本**: 中 (需理解 Cookie 机制、Web Storage API、IndexedDB 事务模型)

这是 JavaScript 世界第 157 次被记录的网络与数据事故。Cookie 是为 HTTP 通信设计的, 容量仅 4KB, 不适合客户端存储。localStorage 提供同步的持久化键值对存储, 容量 5-10MB, 适合简单数据。sessionStorage 与 localStorage API 相同, 但生命周期是标签页会话, 关闭标签页数据清空。localStorage 的 storage 事件只在其他标签页触发, 可实现跨标签页通信。localStorage 超出容量会抛出 QuotaExceededError, 需要错误捕获和容量管理。IndexedDB 提供异步的事务型数据库, 支持大容量、索引、复杂查询。IndexedDB 的所有操作必须在事务中进行, 保证数据一致性。选择存储方案要根据数据大小、持久化需求、查询复杂度、性能要求综合考虑。理解每种存储方案的特性、限制、适用场景是构建可靠前端应用的基础。

---
