《第 95 次记录: Promise 链断裂事故 —— 数据传递的迷失》

---

## Promise 链的第一次失败

周二上午九点,你满怀信心地打开编辑器。

昨天学会了 Promise,重构了注册函数,感觉整个世界都变得清晰了。今天你要用 Promise 链改写一个更复杂的功能——用户订单处理流程:验证库存、创建订单、扣减库存、发送通知、记录日志。

"这次一定能写得很优雅,"你自言自语,"Promise 链让一切都变简单了。"

你快速写下代码:

```javascript
function processOrder(userId, productId, quantity) {
    return checkStock(productId, quantity)
        .then(function(stock) {
            return createOrder(userId, productId, quantity);
        })
        .then(function(order) {
            return reduceStock(productId, quantity);
        })
        .then(function() {
            return sendNotification(userId, 'order_created');
        })
        .then(function() {
            return logOrderAction('order_created');
        })
        .then(function() {
            console.log('订单处理完成');
        });
}
```

"完美!"你点击运行,测试用例顺利通过。

但下午三点,测试工程师小李发来消息:"订单通知里为什么没有订单号?用户收到的邮件是空的。"

你打开通知模板,发现 `sendNotification` 需要传入订单信息。但你看着代码,困惑了:"订单信息在第二步 `createOrder` 就创建了,为什么第四步 `sendNotification` 拿不到?"

---

## 数据在链条中的消失

下午三点半,你开始调试。

你在每个 then 里添加 console.log,想看看数据是怎么流动的:

```javascript
function processOrder(userId, productId, quantity) {
    return checkStock(productId, quantity)
        .then(function(stock) {
            console.log('步骤 1: 库存', stock);
            return createOrder(userId, productId, quantity);
        })
        .then(function(order) {
            console.log('步骤 2: 订单', order);
            return reduceStock(productId, quantity);
        })
        .then(function(result) {
            console.log('步骤 3: 扣减结果', result);
            return sendNotification(userId, 'order_created');
        })
        .then(function(result) {
            console.log('步骤 4: 通知结果', result);
        });
}
```

运行后,控制台输出:

```
步骤 1: 库存 { available: 100, reserved: 0 }
步骤 2: 订单 { orderId: 'ORD-001', userId: 'U123', total: 299 }
步骤 3: 扣减结果 { success: true, remaining: 99 }
步骤 4: 通知结果 { sent: true }
```

"等等..."你盯着输出,"订单信息在步骤 2 就有了,但到了步骤 3、4 就看不到了。"

你突然意识到一个问题:**每个 then 只能接收到上一个 then 返回的值**。

"所以当我在步骤 2 返回 `reduceStock` 的 Promise 时,"你喃喃自语,"步骤 3 收到的就是 `reduceStock` 的结果,而不是 `createOrder` 的结果。订单信息在链条的某个环节丢失了。"

你的手指停在键盘上。这不就是回调地狱的另一种形式吗?虽然代码扁平了,但数据传递的问题依然存在。

---

## 尝试保存数据

下午四点,你开始尝试解决数据传递问题。

"如果每个 then 只能拿到上一个返回值,"你想,"那我需要一个地方保存中间数据。"

你的第一反应是用外层变量:

```javascript
function processOrder(userId, productId, quantity) {
    let orderInfo; // 保存订单信息

    return checkStock(productId, quantity)
        .then(function(stock) {
            return createOrder(userId, productId, quantity);
        })
        .then(function(order) {
            orderInfo = order; // 保存订单
            return reduceStock(productId, quantity);
        })
        .then(function() {
            // 现在可以使用 orderInfo 了
            return sendNotification(userId, orderInfo);
        })
        .then(function() {
            return logOrderAction(orderInfo.orderId);
        });
}
```

你测试了一下,确实可以工作。但你看着代码,总觉得不够优雅。

"这和闭包变量有什么区别?"你皱眉,"而且如果需要保存多个中间值呢?要定义一堆变量?"

你尝试保存更多数据:

```javascript
function processOrder(userId, productId, quantity) {
    let stockInfo;
    let orderInfo;
    let reduceResult;

    return checkStock(productId, quantity)
        .then(function(stock) {
            stockInfo = stock; // 保存库存
            return createOrder(userId, productId, quantity);
        })
        .then(function(order) {
            orderInfo = order; // 保存订单
            return reduceStock(productId, quantity);
        })
        .then(function(result) {
            reduceResult = result; // 保存扣减结果
            return sendNotification(userId, orderInfo);
        })
        .then(function() {
            // 现在可以使用所有数据了
            return logOrderAction({
                stock: stockInfo,
                order: orderInfo,
                reduce: reduceResult
            });
        });
}
```

"天哪,"你看着这一堆变量声明,"这比回调地狱好不了多少..."

---

## 传递数据的艺术

下午五点,你搜索了"Promise 链数据传递最佳实践"。

你看到的第一个方案是:让每个 then 都返回需要的数据。

"原来如此,"你恍然大悟,"我可以在 then 里返回一个包含所有需要数据的对象!"

你开始重写:

```javascript
function processOrder(userId, productId, quantity) {
    return checkStock(productId, quantity)
        .then(function(stock) {
            return createOrder(userId, productId, quantity)
                .then(function(order) {
                    // 返回包含两个结果的对象
                    return { stock, order };
                });
        })
        .then(function(data) {
            return reduceStock(productId, quantity)
                .then(function(reduceResult) {
                    // 继续传递,并添加新数据
                    return { ...data, reduceResult };
                });
        })
        .then(function(data) {
            // 现在可以访问 stock, order, reduceResult
            return sendNotification(userId, data.order);
        })
        .then(function() {
            console.log('订单处理完成');
        });
}
```

你测试了代码,确实可以工作。但你盯着这段代码,越看越不对劲。

"等等..."你的眉头紧锁,"这又嵌套了!我在 then 里又写了 then,这不就是'Promise 版的回调地狱'吗?"

你画了一张图:

```
.then(function(stock) {
    return createOrder()
        .then(function(order) {    // ← 嵌套了!
            return { stock, order };
        });
})
```

"虽然数据传递解决了,"你想,"但代码又变得复杂了。一定有更好的方法..."

---

## 发现 Promise 链的正确姿势

下午六点,你继续翻阅文档,看到了一个巧妙的模式。

"关键在于返回值的设计,"你读着一篇博客,"每个异步操作应该返回包含所需数据的对象,而不是在 then 里嵌套。"

你突然理解了:"不是在 then 里嵌套,而是让异步函数本身返回需要的数据!"

你重新设计了函数:

```javascript
function createOrderWithStock(userId, productId, quantity, stock) {
    return createOrder(userId, productId, quantity)
        .then(function(order) {
            // 返回包含 stock 和 order 的对象
            return { stock, order };
        });
}

function reduceStockWithOrder(productId, quantity, orderData) {
    return reduceStock(productId, quantity)
        .then(function(reduceResult) {
            // 继续传递之前的数据,并添加新数据
            return { ...orderData, reduceResult };
        });
}

function processOrder(userId, productId, quantity) {
    return checkStock(productId, quantity)
        .then(function(stock) {
            return createOrderWithStock(userId, productId, quantity, stock);
        })
        .then(function(orderData) {
            return reduceStockWithOrder(productId, quantity, orderData);
        })
        .then(function(data) {
            return sendNotification(userId, data.order);
        })
        .then(function() {
            console.log('订单处理完成');
        });
}
```

"这样就扁平了!"你说,"每个 then 都在同一层级,没有嵌套,数据通过函数参数和返回值传递。"

但你又想到一个问题:"可是这样的话,每个操作都要单独包装成函数,会不会太麻烦?"

---

## 更简洁的数据传递模式

下午七点,你发现了一个更简洁的模式。

"如果不需要保留所有中间数据呢?"你想,"大部分情况下,我只需要某几个关键数据。"

你重新审视需求:订单通知和日志记录只需要订单信息,不需要库存和扣减结果。

于是你简化了代码:

```javascript
function processOrder(userId, productId, quantity) {
    let order; // 只保存需要的数据

    return checkStock(productId, quantity)
        .then(function(stock) {
            // 库存检查通过,创建订单
            return createOrder(userId, productId, quantity);
        })
        .then(function(createdOrder) {
            order = createdOrder; // 保存订单信息
            // 扣减库存
            return reduceStock(productId, quantity);
        })
        .then(function() {
            // 发送通知,使用保存的订单信息
            return sendNotification(userId, order);
        })
        .then(function() {
            // 记录日志
            return logOrderAction(order.orderId);
        })
        .then(function() {
            console.log('订单处理完成:', order.orderId);
            return order; // 返回订单信息供外部使用
        });
}
```

"这样就平衡了,"你说,"既避免了嵌套,又只保存了必需的数据。"

但你马上又遇到了一个新问题。

---

## then 里忘记 return 的灾难

晚上八点,你准备收工时,测试工程师又发来消息:"有些订单的通知发送了,但日志没有记录。"

"怎么可能?"你困惑,"我明明写了日志记录的代码..."

你打开控制台调试,发现了一个诡异的现象:

```javascript
.then(function() {
    sendNotification(userId, order); // 忘记 return 了!
})
.then(function() {
    console.log('这里会立即执行,不等通知发送完成');
    return logOrderAction(order.orderId);
})
```

"等等..."你盯着代码,"我在 then 里调用了 `sendNotification`,但忘记 `return` 了!"

你立刻意识到问题的严重性:

```javascript
// ❌ 错误:没有 return,Promise 链断了
.then(function() {
    sendNotification(userId, order); // 异步操作启动,但 Promise 链不等它
    // 这个 then 返回 undefined
})
.then(function() {
    // 立即执行,不等上一步完成
    return logOrderAction(order.orderId);
})

// ✅ 正确:return Promise,链条继续
.then(function() {
    return sendNotification(userId, order); // 返回 Promise,链条等待
})
.then(function() {
    // 等通知发送完成后才执行
    return logOrderAction(order.orderId);
})
```

"所以如果 then 里启动了异步操作,必须 return 那个 Promise,"你总结,"否则链条不会等待,后续的 then 会立即执行。"

你画了一张对比图:

```
没有 return:
[checkStock] → [createOrder] → [sendNotification 启动但不等待]
                                        ↓
                                [logOrderAction 立即执行] ← 错误!

有 return:
[checkStock] → [createOrder] → [sendNotification 完成]
                                        ↓
                                [logOrderAction 等待后执行] ← 正确!
```

---

## then 链的其他陷阱

晚上九点,你开始系统整理 Promise 链的陷阱。

"还有哪些容易犯的错误?"你自问。

你写下了一系列测试代码:

```javascript
// 陷阱 1: 创建了 Promise 但没有返回
function badChain1() {
    return doA()
        .then(function() {
            doB(); // ❌ 创建了 Promise 但没有 return
        })
        .then(function() {
            doC(); // 会立即执行,不等 doB
        });
}

// 陷阱 2: 返回了嵌套的 then
function badChain2() {
    return doA()
        .then(function() {
            return doB()
                .then(function() {
                    return doC(); // ❌ 嵌套了,又回到回调地狱
                });
        });
}

// 陷阱 3: 在 then 里创建新的 Promise 链
function badChain3() {
    return doA()
        .then(function(result) {
            // ❌ 创建了独立的 Promise 链,不会被等待
            doB(result)
                .then(function() {
                    return doC();
                });
        });
}

// 正确做法:扁平的链条
function goodChain() {
    return doA()
        .then(function(result) {
            return doB(result); // ✅ 返回 Promise
        })
        .then(function() {
            return doC(); // ✅ 扁平,没有嵌套
        });
}
```

你测试了这些代码,验证了每个陷阱的后果。

"Promise 链最重要的规则,"你总结,"就是保持扁平,每个 then 都返回 Promise,不要嵌套,不要忘记 return。"

---

## Promise 链的最佳实践

晚上十点,你整理了一天的收获。

你在笔记本上写下标题:"Promise 链 —— 顺序的延续"

### 核心洞察 #1: then 只接收上一个返回值

你写道:

"Promise 链中,每个 then 只能接收到上一个 then 返回的值:

```javascript
doA()
    .then(function(resultA) {
        return doB(resultA);
    })
    .then(function(resultB) {
        // 这里只能访问 resultB,访问不到 resultA
    });
```

数据传递方式:
1. **外层变量**:保存需要的中间数据(简单场景)
2. **对象传递**:每个 then 返回包含所需数据的对象
3. **函数封装**:将需要组合的操作封装成独立函数"

### 核心洞察 #2: 必须 return Promise

"then 里的异步操作必须 return,否则链条断裂:

```javascript
// ❌ 错误:Promise 链不会等待
.then(function() {
    asyncOperation(); // 启动但不等待
})

// ✅ 正确:返回 Promise,链条等待
.then(function() {
    return asyncOperation();
})
```

后果:忘记 return 会导致后续 then 立即执行,异步操作的顺序失控。"

### 核心洞察 #3: 避免 then 嵌套

"Promise 的目标是扁平化,嵌套是反模式:

```javascript
// ❌ 反模式:嵌套 then
.then(function() {
    return doA()
        .then(function() {
            return doB();
        });
})

// ✅ 最佳实践:扁平链条
.then(function() {
    return doA();
})
.then(function() {
    return doB();
})
```

扁平化让代码可读性更高,错误处理更简单。"

### 核心洞察 #4: 数据传递的权衡

"传递数据的三种策略及适用场景:

1. **外层变量**(适用:只需保存1-2个关键数据)
```javascript
let order;
return createOrder()
    .then(o => { order = o; return process(); })
    .then(() => notify(order));
```

2. **对象传递**(适用:需要保留多个中间结果)
```javascript
return createOrder()
    .then(order => process().then(result => ({ order, result })))
    .then(data => notify(data.order, data.result));
```

3. **函数封装**(适用:复杂的组合逻辑)
```javascript
function processWithOrder(order) {
    return process().then(result => ({ order, result }));
}
```

选择标准:简单场景用变量,复杂场景用对象,可复用逻辑封装函数。"

你合上笔记本,关掉电脑。

"明天要学习 Promise 的错误处理,"你想,"今天终于理解了 Promise 链的精髓——保持扁平,善用 return,合理传递数据。"

---

## 知识总结

**规则 1: then 方法的数据流动规则**

Promise 链中,每个 then 接收上一个 then 的返回值:

```javascript
Promise.resolve(1)
    .then(function(value) {
        console.log(value); // 1
        return value + 1;
    })
    .then(function(value) {
        console.log(value); // 2
        return value + 1;
    })
    .then(function(value) {
        console.log(value); // 3
    });
```

数据流向:每个 then 的返回值成为下一个 then 的参数。如果不 return,下一个 then 收到 `undefined`。

---

**规则 2: 必须返回 Promise 以保持链条**

then 里的异步操作必须 return,否则链条不会等待:

```javascript
// ❌ 错误:链条断裂
doAsync()
    .then(function() {
        asyncOperation(); // 启动但不等待
    })
    .then(function() {
        // 立即执行,不等上一步
    });

// ✅ 正确:返回 Promise
doAsync()
    .then(function() {
        return asyncOperation(); // 返回 Promise,链条等待
    })
    .then(function() {
        // 等待上一步完成后才执行
    });
```

忘记 return 是 Promise 链最常见的错误,导致异步操作顺序失控。

---

**规则 3: 避免 then 嵌套(Promise 反模式)**

Promise 的目标是扁平化代码,嵌套是反模式:

```javascript
// ❌ 反模式:嵌套 then
doA()
    .then(function() {
        return doB()
            .then(function() {
                return doC(); // 嵌套了
            });
    });

// ✅ 最佳实践:扁平链条
doA()
    .then(function() {
        return doB();
    })
    .then(function() {
        return doC();
    });
```

嵌套 then 违背了 Promise 扁平化的初衷,降低可读性,增加错误处理难度。

---

**规则 4: 数据传递的三种策略**

当后续 then 需要访问前面的数据时,有三种传递方式:

**策略 1:外层变量**(简单场景,1-2 个关键数据)
```javascript
let userData;

return fetchUser()
    .then(function(user) {
        userData = user; // 保存数据
        return fetchOrders(user.id);
    })
    .then(function(orders) {
        // 使用保存的 userData
        return processOrders(userData, orders);
    });
```

**策略 2:对象传递**(复杂场景,多个中间结果)
```javascript
return fetchUser()
    .then(function(user) {
        return fetchOrders(user.id)
            .then(function(orders) {
                return { user, orders }; // 包装成对象
            });
    })
    .then(function(data) {
        return processOrders(data.user, data.orders);
    });
```

**策略 3:函数封装**(可复用逻辑)
```javascript
function fetchUserWithOrders(userId) {
    return fetchUser(userId)
        .then(function(user) {
            return fetchOrders(user.id)
                .then(function(orders) {
                    return { user, orders };
                });
        });
}

// 使用
return fetchUserWithOrders(123)
    .then(function(data) {
        return processOrders(data.user, data.orders);
    });
```

---

**规则 5: then 链的常见陷阱**

**陷阱 1:创建 Promise 但不返回**
```javascript
// ❌ 错误
.then(function() {
    doAsync(); // 创建了 Promise 但没有 return
})
```

**陷阱 2:返回嵌套的 then**
```javascript
// ❌ 错误
.then(function() {
    return doA()
        .then(function() {
            return doB(); // 嵌套了
        });
})
```

**陷阱 3:创建独立的 Promise 链**
```javascript
// ❌ 错误
.then(function() {
    doA().then(doB).then(doC); // 独立链,不会被等待
})
```

**陷阱 4:混淆 return 的位置**
```javascript
// ❌ 错误
.then(function() {
    if (condition) {
        return doA(); // 只在 if 分支 return
    }
    doB(); // else 分支没有 return
})
```

---

**规则 6: Promise 链的扁平化模式**

扁平化 Promise 链的最佳实践:

**模式 1:每个 then 都 return**
```javascript
return step1()
    .then(function(r1) { return step2(r1); })
    .then(function(r2) { return step3(r2); })
    .then(function(r3) { return step4(r3); });
```

**模式 2:箭头函数简化**
```javascript
return step1()
    .then(r1 => step2(r1))
    .then(r2 => step3(r2))
    .then(r3 => step4(r3));
```

**模式 3:链式传递函数引用**
```javascript
return step1()
    .then(step2) // 如果参数匹配,直接传递函数引用
    .then(step3)
    .then(step4);
```

扁平化原则:
- 每个 then 返回新的 Promise
- 避免嵌套,所有 then 在同一层级
- 数据通过返回值或外层变量传递
- 错误通过 catch 统一处理

---

**事故档案编号**: ASYNC-2024-1895
**影响范围**: Promise 链, then 方法, 数据传递, 链式调用
**根本原因**: 不理解 then 的数据流动规则,忘记 return Promise,导致链条断裂或嵌套
**修复成本**: 低(理解规则后容易修复)

这是 JavaScript 世界第 95 次被记录的 Promise 链式调用事故。Promise 链中,每个 then 只接收上一个 then 的返回值。then 里的异步操作必须 return,否则链条不会等待,后续 then 立即执行。Promise 的目标是扁平化代码,嵌套 then 是反模式,违背了扁平化初衷。数据传递有三种策略:外层变量(简单场景)、对象传递(复杂场景)、函数封装(可复用逻辑)。常见陷阱包括:创建 Promise 不返回、返回嵌套 then、创建独立链、混淆 return 位置。扁平化模式:每个 then 都 return、使用箭头函数简化、链式传递函数引用。理解 then 的数据流动和返回规则是掌握 Promise 链的关键。

---
