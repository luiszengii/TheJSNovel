《第 97 次记录: 批量操作竞速 —— Promise.all 的陷阱》

---

## 性能优化的需求

周四上午十点,技术总监老陈把你叫到会议室。

"用户反馈系统太慢了,"他打开性能监控面板,指着一条红色的曲线,"首页加载要 8 秒,这不可接受。"

你看着监控数据,首页需要加载:用户信息、权限列表、通知消息、统计数据、最近订单。现在的代码是这样的:

```javascript
function loadDashboard(userId) {
    return fetchUserInfo(userId)
        .then(function(user) {
            return fetchPermissions(user.id);
        })
        .then(function(permissions) {
            return fetchNotifications(userId);
        })
        .then(function(notifications) {
            return fetchStatistics(userId);
        })
        .then(function(statistics) {
            return fetchRecentOrders(userId);
        })
        .then(function(orders) {
            console.log('所有数据加载完成');
        });
}
```

"这些请求是串行的,"老陈说,"每个请求 1.5 秒,五个请求就是 7.5 秒。但它们之间没有依赖关系,完全可以并行加载。"

"我知道 Promise.all 可以并行执行,"你说,"但之前没在生产环境用过..."

"今天就是机会,"老陈拍了拍你的肩膀,"把加载时间降到 2 秒以内。"

---

## Promise.all 的第一次尝试

上午十一点,你开始重构代码。

"Promise.all 接受一个 Promise 数组,等所有 Promise 完成后返回结果数组,"你回忆着文档里的描述。

你快速写下新代码:

```javascript
function loadDashboard(userId) {
    return Promise.all([
        fetchUserInfo(userId),
        fetchPermissions(userId),
        fetchNotifications(userId),
        fetchStatistics(userId),
        fetchRecentOrders(userId)
    ])
    .then(function(results) {
        const [user, permissions, notifications, statistics, orders] = results;
        console.log('所有数据加载完成:', {
            user,
            permissions,
            notifications,
            statistics,
            orders
        });
        return { user, permissions, notifications, statistics, orders };
    });
}
```

你在测试环境运行,盯着 Network 面板。

"1.6 秒!"你兴奋地说,"从 7.5 秒降到 1.6 秒,快了 5 倍!"

你立刻部署到生产环境,向老陈报告了好消息。

下午三点,测试工程师小李发来消息:"首页有时候会完全空白,刷新几次才能加载出来。"

"什么?"你困惑,"我测试了好几次都没问题啊..."

---

## Promise.all 的快速失败

下午三点半,你开始复现问题。

你故意让其中一个 API 返回错误:

```javascript
function fetchNotifications(userId) {
    return new Promise(function(resolve, reject) {
        setTimeout(function() {
            reject(new Error('通知服务暂时不可用'));
        }, 500);
    });
}

// 测试
loadDashboard('U123');
```

控制台输出:

```
Uncaught (in promise) Error: 通知服务暂时不可用
```

"等等..."你盯着页面,"其他数据也没有显示?"

你打开 Network 面板,发现所有请求都发出去了,用户信息、权限、统计、订单都成功返回了,但因为通知服务失败,整个 Promise.all 都 reject 了。

"天哪,"你意识到问题的严重性,"Promise.all 是'全有或全无'——只要有一个失败,整体就失败,所有成功的结果都被丢弃了!"

你画了一张图:

```
Promise.all([
    fetchUser     → 成功 ✓
    fetchPerms    → 成功 ✓
    fetchNotify   → 失败 ✗ ← 这个失败了
    fetchStats    → 成功 ✓
    fetchOrders   → 成功 ✓
])
→ 整体 reject,所有结果丢失!
```

"这太危险了,"你说,"如果通知服务不稳定,用户就会看到空白页面,即使其他数据都是正常的。"

---

## 降级策略:Promise.allSettled

下午四点,你开始搜索解决方案。

"有没有办法让 Promise.all 不因为单个失败而整体失败?"你在 MDN 上搜索。

你发现了一个方法:`Promise.allSettled`。

"和 Promise.all 不同,allSettled 等待所有 Promise 完成(无论成功还是失败),然后返回每个 Promise 的状态,"你读着文档。

你立刻尝试:

```javascript
function loadDashboard(userId) {
    return Promise.allSettled([
        fetchUserInfo(userId),
        fetchPermissions(userId),
        fetchNotifications(userId),
        fetchStatistics(userId),
        fetchRecentOrders(userId)
    ])
    .then(function(results) {
        console.log('所有请求完成:', results);
        // results 的格式:
        // [
        //   { status: 'fulfilled', value: {...} },
        //   { status: 'fulfilled', value: {...} },
        //   { status: 'rejected', reason: Error },
        //   { status: 'fulfilled', value: {...} },
        //   { status: 'fulfilled', value: {...} }
        // ]
    });
}
```

测试输出:

```javascript
[
    { status: 'fulfilled', value: { id: 'U123', name: '张三' } },
    { status: 'fulfilled', value: ['read', 'write'] },
    { status: 'rejected', reason: Error('通知服务不可用') },
    { status: 'fulfilled', value: { orders: 42, revenue: 12000 } },
    { status: 'fulfilled', value: [{...}, {...}] }
]
```

"完美!"你说,"即使通知服务失败,其他数据都还在。"

你继续处理结果:

```javascript
function loadDashboard(userId) {
    return Promise.allSettled([
        fetchUserInfo(userId),
        fetchPermissions(userId),
        fetchNotifications(userId),
        fetchStatistics(userId),
        fetchRecentOrders(userId)
    ])
    .then(function(results) {
        const data = {};

        // 提取成功的结果
        if (results[0].status === 'fulfilled') {
            data.user = results[0].value;
        }
        if (results[1].status === 'fulfilled') {
            data.permissions = results[1].value;
        }
        if (results[2].status === 'fulfilled') {
            data.notifications = results[2].value;
        } else {
            // 通知失败,使用空数组
            data.notifications = [];
            console.warn('通知加载失败:', results[2].reason);
        }
        if (results[3].status === 'fulfilled') {
            data.statistics = results[3].value;
        }
        if (results[4].status === 'fulfilled') {
            data.orders = results[4].value;
        }

        return data;
    });
}
```

"但这样写太冗长了,"你皱眉,"每个结果都要判断 status,太麻烦..."

---

## 优雅的降级处理

下午五点,你开始优化代码。

"可以写个辅助函数来处理 allSettled 的结果,"你想。

```javascript
function extractResults(results, defaults = []) {
    return results.map(function(result, index) {
        if (result.status === 'fulfilled') {
            return result.value;
        } else {
            console.warn(`请求 ${index} 失败:`, result.reason);
            return defaults[index] !== undefined ? defaults[index] : null;
        }
    });
}

function loadDashboard(userId) {
    return Promise.allSettled([
        fetchUserInfo(userId),
        fetchPermissions(userId),
        fetchNotifications(userId),
        fetchStatistics(userId),
        fetchRecentOrders(userId)
    ])
    .then(function(results) {
        // 提供默认值
        const defaults = [
            null,           // user 没有默认值
            [],             // permissions 默认空数组
            [],             // notifications 默认空数组
            { orders: 0 },  // statistics 默认值
            []              // orders 默认空数组
        ];

        const [user, permissions, notifications, statistics, orders] =
            extractResults(results, defaults);

        if (!user) {
            throw new Error('用户信息加载失败,无法继续');
        }

        return { user, permissions, notifications, statistics, orders };
    });
}
```

"这样就优雅多了,"你说,"非关键数据失败时使用默认值,关键数据(用户信息)失败时抛出错误。"

---

## Promise.race 的竞速游戏

下午六点,你想起文档里还提到过 `Promise.race`。

"race 是竞速,谁先完成就返回谁的结果,"你测试了一下:

```javascript
Promise.race([
    new Promise(resolve => setTimeout(() => resolve('慢'), 1000)),
    new Promise(resolve => setTimeout(() => resolve('快'), 100))
])
.then(function(result) {
    console.log('获胜者:', result); // '快'
});
```

"这有什么用呢?"你想了想,"对了,可以实现超时控制!"

你写了一个超时包装函数:

```javascript
function timeout(promise, ms) {
    const timeoutPromise = new Promise(function(resolve, reject) {
        setTimeout(function() {
            reject(new Error(`操作超时 (${ms}ms)`));
        }, ms);
    });

    return Promise.race([promise, timeoutPromise]);
}

// 使用
timeout(fetchUserInfo('U123'), 3000)
    .then(function(user) {
        console.log('用户信息:', user);
    })
    .catch(function(error) {
        console.error('加载失败或超时:', error.message);
    });
```

你测试了一下,确实有效——如果请求超过 3 秒,就会自动超时。

"但 race 有个问题,"你仔细思考,"即使超时了,原来的 Promise 还在运行,请求还在继续..."

---

## Promise.any 的发现

晚上七点,你继续探索 Promise API,发现了 `Promise.any`。

"any 和 race 有什么区别?"你查阅文档。

你写了测试代码:

```javascript
// 测试 Promise.race
Promise.race([
    Promise.reject(new Error('错误 1')),
    Promise.reject(new Error('错误 2')),
    new Promise(resolve => setTimeout(() => resolve('成功'), 100))
])
.then(function(result) {
    console.log('race 结果:', result); // 不会执行
})
.catch(function(error) {
    console.log('race 错误:', error.message); // '错误 1'
});

// 测试 Promise.any
Promise.any([
    Promise.reject(new Error('错误 1')),
    Promise.reject(new Error('错误 2')),
    new Promise(resolve => setTimeout(() => resolve('成功'), 100))
])
.then(function(result) {
    console.log('any 结果:', result); // '成功'
})
.catch(function(error) {
    console.log('any 错误:', error);
});
```

"原来 race 返回第一个完成的(无论成功失败),而 any 返回第一个成功的,"你总结。

"any 适合多个备选方案的场景,"你想到一个应用:

```javascript
function loadUserAvatar(userId) {
    return Promise.any([
        fetchFromCDN(userId),
        fetchFromBackupCDN(userId),
        fetchFromMainServer(userId)
    ])
    .then(function(avatar) {
        console.log('头像加载成功');
        return avatar;
    })
    .catch(function(error) {
        // 所有方案都失败了
        console.error('所有头像加载方案都失败');
        return getDefaultAvatar();
    });
}
```

"any 会尝试所有方案,只要有一个成功就返回,"你说,"如果全部失败,才 reject。"

---

## 四种 Promise 批量方法的对比

晚上八点,你开始系统整理这些批量方法。

你在笔记本上画了一张对比表:

```
┌─────────────┬──────────────┬──────────────┬─────────────┐
│   方法      │ 完成条件     │ 失败条件     │ 返回值      │
├─────────────┼──────────────┼──────────────┼─────────────┤
│ Promise.all │ 全部成功     │ 任一失败     │ 结果数组    │
├─────────────┼──────────────┼──────────────┼─────────────┤
│ allSettled  │ 全部完成     │ 不会失败     │ 状态数组    │
├─────────────┼──────────────┼──────────────┼─────────────┤
│ Promise.race│ 任一完成     │ 第一个失败   │ 第一个结果  │
├─────────────┼──────────────┼──────────────┼─────────────┤
│ Promise.any │ 任一成功     │ 全部失败     │ 第一个成功  │
└─────────────┴──────────────┴──────────────┴─────────────┘
```

你写下了每个方法的典型用例:

**Promise.all - 全有或全无**
```javascript
// 用例:关键步骤,必须全部成功
Promise.all([
    createUser(data),
    sendEmail(data.email),
    initializeAccount(data.userId)
])
.then(function([user, emailResult, account]) {
    console.log('账户创建完成');
})
.catch(function(error) {
    console.error('任一步骤失败,回滚操作');
    rollbackAccount();
});
```

**Promise.allSettled - 降级处理**
```javascript
// 用例:非关键步骤,部分失败可接受
Promise.allSettled([
    fetchMainContent(),
    fetchSidebar(),     // 失败了也不影响主内容
    fetchAds(),         // 广告加载失败不影响页面
    fetchComments()     // 评论加载失败不影响阅读
])
.then(function(results) {
    const content = results[0].status === 'fulfilled' ? results[0].value : null;
    const sidebar = results[1].status === 'fulfilled' ? results[1].value : getDefaultSidebar();
    // ... 使用降级数据渲染页面
});
```

**Promise.race - 超时控制**
```javascript
// 用例:超时控制、缓存竞速
Promise.race([
    fetchFromAPI(),
    timeout(5000) // 5 秒超时
])
.then(function(data) {
    console.log('在超时前获取到数据');
})
.catch(function(error) {
    console.error('请求失败或超时');
});
```

**Promise.any - 备选方案**
```javascript
// 用例:多个备选数据源
Promise.any([
    fetchFromCache(),
    fetchFromCDN(),
    fetchFromMainServer()
])
.then(function(data) {
    console.log('从最快的源获取到数据');
})
.catch(function(error) {
    console.error('所有数据源都失败');
});
```

---

## 批量方法的性能陷阱

晚上九点,你突然想到一个问题。

"Promise.all 会立即启动所有 Promise,如果有 1000 个请求,会不会把服务器压垮?"

你写了测试代码:

```javascript
// 危险:同时发起 1000 个请求
const promises = [];
for (let i = 0; i < 1000; i++) {
    promises.push(fetch(`/api/item/${i}`));
}

Promise.all(promises)
    .then(function(results) {
        console.log('1000 个请求全部完成');
    });
```

"这确实会同时发起 1000 个请求,"你说,"浏览器和服务器都可能扛不住。"

你开始研究并发控制。你写了一个限制并发数的函数:

```javascript
function promiseLimit(tasks, limit) {
    let index = 0;
    const results = [];
    const executing = [];

    function enqueue() {
        // 所有任务完成
        if (index === tasks.length) {
            return Promise.resolve();
        }

        const task = tasks[index++];
        const promise = Promise.resolve().then(() => task());
        results.push(promise);

        let clean = promise.then(() => {
            executing.splice(executing.indexOf(clean), 1);
        });
        executing.push(clean);

        // 控制并发数
        let result = Promise.resolve();
        if (executing.length >= limit) {
            result = Promise.race(executing);
        }

        return result.then(() => enqueue());
    }

    return enqueue().then(() => Promise.all(results));
}

// 使用
const tasks = [];
for (let i = 0; i < 1000; i++) {
    tasks.push(() => fetch(`/api/item/${i}`));
}

promiseLimit(tasks, 10) // 限制同时只有 10 个请求
    .then(function(results) {
        console.log('1000 个请求完成,但最多同时 10 个');
    });
```

"这样就安全多了,"你说,"同时最多 10 个请求,不会压垮服务器。"

---

## 你的 Promise API 笔记本

晚上十点,你整理了今天的收获。

你在笔记本上写下标题:"Promise 批量操作 —— 协调并行的艺术"

### 核心洞察 #1: Promise.all 的全有或全无

你写道:

"Promise.all 等待所有 Promise 完成,但任一失败则整体失败:

```javascript
Promise.all([p1, p2, p3])
    .then(function([r1, r2, r3]) {
        // 全部成功,按顺序返回结果
    })
    .catch(function(error) {
        // 任一失败,整体 reject
        // 其他成功的结果被丢弃!
    });
```

适用场景:
- 关键步骤,必须全部成功
- 事务性操作,部分失败需要回滚
- 严格依赖,缺一不可

危险:单点失败导致整体崩溃,成功的结果也会丢失。"

### 核心洞察 #2: Promise.allSettled 的降级处理

"allSettled 等待所有 Promise 完成,永远不会 reject:

```javascript
Promise.allSettled([p1, p2, p3])
    .then(function(results) {
        // results 是状态数组
        results.forEach(function(result) {
            if (result.status === 'fulfilled') {
                console.log('成功:', result.value);
            } else {
                console.log('失败:', result.reason);
            }
        });
    });
```

适用场景:
- 非关键数据加载
- 部分失败可接受
- 需要降级处理

优势:获取所有结果,无论成功失败,可以优雅降级。"

### 核心洞察 #3: Promise.race 的竞速机制

"race 返回第一个完成的 Promise(无论成功失败):

```javascript
Promise.race([p1, p2, p3])
    .then(function(result) {
        // 第一个成功的结果
    })
    .catch(function(error) {
        // 第一个失败的错误
    });
```

适用场景:
- 超时控制
- 缓存与网络竞速
- 快速响应(取最快的结果)

注意:race 之后,其他 Promise 仍在运行,无法取消。"

### 核心洞察 #4: Promise.any 的备选方案

"any 返回第一个成功的 Promise,全部失败才 reject:

```javascript
Promise.any([p1, p2, p3])
    .then(function(result) {
        // 第一个成功的结果
    })
    .catch(function(error) {
        // 全部失败才会到这里
        // error 是 AggregateError
    });
```

适用场景:
- 多个备选数据源
- 容错机制
- 至少一个成功即可

区别:any 忽略失败,等待第一个成功;race 返回第一个完成(无论成败)。"

你合上笔记本,满意地伸了个懒腰。

"明天要学习如何把旧的回调函数改造成 Promise,"你想,"今天终于掌握了批量操作的四大方法——all 的严格、allSettled 的包容、race 的速度、any 的容错。选对方法,才能写出健壮的并行代码。"

---

## 知识总结

**规则 1: Promise.all 的全有或全无机制**

Promise.all 等待所有 Promise 完成,任一失败则整体失败:

```javascript
Promise.all([
    fetchUser(),
    fetchOrders(),
    fetchSettings()
])
.then(function([user, orders, settings]) {
    // 全部成功,按顺序返回结果数组
    console.log('所有数据加载完成');
})
.catch(function(error) {
    // 任一失败,整体 reject
    console.error('某个请求失败:', error);
    // 其他成功的结果被丢弃!
});
```

行为:
- **并行执行**:所有 Promise 同时启动
- **全部成功**:返回结果数组,顺序与输入一致
- **任一失败**:立即 reject,其他成功结果丢失
- **快速失败**:第一个失败后立即 reject,但其他 Promise 仍在运行

---

**规则 2: Promise.allSettled 的降级处理**

allSettled 等待所有 Promise 完成,永远不会 reject:

```javascript
Promise.allSettled([
    fetchUser(),
    fetchOrders(),
    fetchSettings()
])
.then(function(results) {
    // results 是状态数组
    results.forEach(function(result, index) {
        if (result.status === 'fulfilled') {
            console.log(`请求 ${index} 成功:`, result.value);
        } else {
            console.log(`请求 ${index} 失败:`, result.reason);
        }
    });
});
```

结果格式:
```javascript
[
    { status: 'fulfilled', value: {...} },
    { status: 'rejected', reason: Error(...) },
    { status: 'fulfilled', value: {...} }
]
```

适用场景:
- 非关键数据加载(部分失败可接受)
- 需要降级处理(失败时使用默认值)
- 需要所有结果(无论成败)

---

**规则 3: Promise.race 的竞速机制**

race 返回第一个完成的 Promise,无论成功还是失败:

```javascript
Promise.race([
    fetchFromCache(),
    fetchFromAPI()
])
.then(function(data) {
    console.log('第一个完成的结果:', data);
})
.catch(function(error) {
    console.error('第一个失败:', error);
});
```

行为:
- **返回第一个**:谁先完成(fulfilled 或 rejected)就返回谁
- **其他继续**:race 之后,其他 Promise 仍在运行
- **无法取消**:无法停止其他 Promise 的执行

典型用例:
```javascript
// 用例 1: 超时控制
function timeout(promise, ms) {
    const timeoutPromise = new Promise((resolve, reject) => {
        setTimeout(() => reject(new Error('超时')), ms);
    });
    return Promise.race([promise, timeoutPromise]);
}

// 用例 2: 缓存与网络竞速
Promise.race([
    loadFromCache(),
    loadFromNetwork()
])
.then(displayData);
```

---

**规则 4: Promise.any 的备选方案机制**

any 返回第一个成功的 Promise,全部失败才 reject:

```javascript
Promise.any([
    fetchFromCDN(),
    fetchFromBackup(),
    fetchFromMain()
])
.then(function(data) {
    console.log('第一个成功的结果:', data);
})
.catch(function(error) {
    console.error('所有方案都失败:', error);
    // error 是 AggregateError,包含所有错误
});
```

行为:
- **返回第一个成功**:忽略失败,等待第一个 fulfilled
- **全部失败才 reject**:返回 AggregateError
- **容错机制**:只要有一个成功就满足

与 race 的区别:
```javascript
// Promise.race: 返回第一个完成(成功或失败)
Promise.race([
    Promise.reject('错误 1'),
    Promise.resolve('成功 2')
])
.then(r => console.log('race:', r))
.catch(e => console.log('race 错误:', e)); // 输出: race 错误: 错误 1

// Promise.any: 返回第一个成功
Promise.any([
    Promise.reject('错误 1'),
    Promise.resolve('成功 2')
])
.then(r => console.log('any:', r)) // 输出: any: 成功 2
.catch(e => console.log('any 错误:', e));
```

---

**规则 5: 四种方法的选择策略**

| 方法 | 完成条件 | 失败条件 | 返回值 | 适用场景 |
|------|---------|---------|--------|---------|
| **all** | 全部成功 | 任一失败 | 结果数组 | 关键步骤,全有或全无 |
| **allSettled** | 全部完成 | 不会失败 | 状态数组 | 非关键数据,降级处理 |
| **race** | 任一完成 | 第一个失败 | 第一个结果 | 超时控制,竞速 |
| **any** | 任一成功 | 全部失败 | 第一个成功 | 备选方案,容错 |

选择原则:
- **严格要求** → all(缺一不可)
- **允许部分失败** → allSettled(降级处理)
- **需要快速响应** → race(取最快)
- **需要容错** → any(至少一个成功)

---

**规则 6: 并发控制避免服务器压力**

Promise.all 会立即启动所有 Promise,大量并发可能压垮服务器:

```javascript
// ❌ 危险:同时 1000 个请求
const promises = items.map(item => fetch(`/api/${item.id}`));
Promise.all(promises); // 同时发起 1000 个请求!

// ✅ 正确:限制并发数
function promiseLimit(tasks, limit) {
    let index = 0;
    const results = [];
    const executing = [];

    function enqueue() {
        if (index === tasks.length) {
            return Promise.resolve();
        }

        const task = tasks[index++];
        const promise = Promise.resolve().then(() => task());
        results.push(promise);

        const clean = promise.then(() => {
            executing.splice(executing.indexOf(clean), 1);
        });
        executing.push(clean);

        let result = Promise.resolve();
        if (executing.length >= limit) {
            result = Promise.race(executing);
        }

        return result.then(() => enqueue());
    }

    return enqueue().then(() => Promise.all(results));
}

// 使用:限制同时最多 10 个请求
const tasks = items.map(item => () => fetch(`/api/${item.id}`));
promiseLimit(tasks, 10);
```

并发控制原则:
- 浏览器限制:单域名最多 6 个并发
- 服务器负载:根据服务器能力设置限制
- 推荐并发数:10-20 个(取决于场景)

---

**规则 7: allSettled 的优雅处理模式**

提取 allSettled 结果的辅助函数:

```javascript
// 模式 1: 提取所有成功结果
function getSuccessful(results) {
    return results
        .filter(r => r.status === 'fulfilled')
        .map(r => r.value);
}

// 模式 2: 提供默认值
function extractWithDefaults(results, defaults) {
    return results.map((result, index) => {
        if (result.status === 'fulfilled') {
            return result.value;
        }
        const defaultValue = defaults[index];
        console.warn(`请求 ${index} 失败,使用默认值:`, result.reason);
        return defaultValue !== undefined ? defaultValue : null;
    });
}

// 使用
Promise.allSettled([fetchA(), fetchB(), fetchC()])
    .then(results => {
        const [a, b, c] = extractWithDefaults(results, [null, [], {}]);
        // a, b, c 都有值(成功结果或默认值)
    });
```

---

**规则 8: race 的超时控制模式**

实现通用超时包装:

```javascript
// 基础版本
function timeout(promise, ms) {
    return Promise.race([
        promise,
        new Promise((resolve, reject) => {
            setTimeout(() => reject(new Error(`超时 (${ms}ms)`)), ms);
        })
    ]);
}

// 高级版本:可取消
function timeoutWithCancel(promise, ms) {
    let timeoutId;
    const timeoutPromise = new Promise((resolve, reject) => {
        timeoutId = setTimeout(() => {
            reject(new Error(`超时 (${ms}ms)`));
        }, ms);
    });

    return Promise.race([
        promise.finally(() => clearTimeout(timeoutId)),
        timeoutPromise
    ]);
}

// 使用
timeout(fetchData(), 3000)
    .then(data => console.log('成功:', data))
    .catch(error => console.error('失败或超时:', error));
```

---

**事故档案编号**: ASYNC-2024-1897
**影响范围**: Promise.all, Promise.allSettled, Promise.race, Promise.any
**根本原因**: 使用 Promise.all 的全有或全无机制导致部分失败时整体崩溃,应使用 allSettled 降级处理
**修复成本**: 低(替换方法)

这是 JavaScript 世界第 97 次被记录的 Promise 批量操作事故。Promise.all 等待所有 Promise 完成,任一失败则整体失败,成功结果也会丢失,适合关键步骤。Promise.allSettled 等待所有完成,永不 reject,返回状态数组,适合降级处理。Promise.race 返回第一个完成的(无论成败),适合超时控制和竞速。Promise.any 返回第一个成功的,全部失败才 reject,适合备选方案。选择策略:严格要求用 all,允许部分失败用 allSettled,需要快速响应用 race,需要容错用 any。Promise.all 会立即启动所有 Promise,大量并发需要并发控制。理解四种方法的差异是编写健壮并行代码的关键。

---
