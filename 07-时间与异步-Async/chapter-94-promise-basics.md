《第 94 次记录: Promise 契约 —— 未来的约定》

---

## 重构的决心

周一上午九点，你打开上周五那个回调地狱般的注册函数，深吸一口气。

"一定有更好的方法，"你说着，开始搜索 Promise 的教程。

第一个视频教程的标题吸引了你："Promise：告别回调地狱"。你点开播放，讲师的第一句话就让你眼前一亮：

"Promise 是对异步操作的抽象，它代表一个'未来会完成的操作'。"

"未来会完成的操作？"你停下视频，开始思考这句话的含义。

你在笔记上写下："回调函数 = 完成后要做的事。Promise = 未来会完成的事。"

"这有什么区别？"你疑惑。

你继续看教程，讲师画了一张对比图：

```
回调模式：
doAsync(function(result) {
    // 你告诉 doAsync："完成后调用这个函数"
});

Promise 模式：
const promise = doAsync();
// doAsync 返回一个 Promise，代表"未来的结果"

promise.then(function(result) {
    // 你告诉 Promise："等你完成后，我要做这个"
});
```

"等等..."你的手指停在笔记本上，"Promise 是一个对象？返回一个对象来代表未来的结果？"

你突然有了一个直觉：**如果异步操作返回一个对象，而不是接受一个回调，那代码的控制权就回到了我手里。**

---

## 第一个 Promise

上午十点，你决定亲手写一个简单的 Promise 来理解它。

"先不管复杂的，"你说，"我只想看看 Promise 到底是什么。"

你在控制台输入：

```javascript
const promise = new Promise(function(resolve, reject) {
    setTimeout(function() {
        resolve('成功了！');
    }, 1000);
});

console.log(promise); // Promise { <pending> }
```

"Promise 对象？"你看着输出，"状态是 pending（等待中）。"

你继续输入：

```javascript
promise.then(function(result) {
    console.log('结果:', result);
});

// 一秒后输出：结果: 成功了！
```

"then 方法？"你惊讶，"我可以在 Promise 对象上调用 then，传入一个函数？"

你再次查看 promise 对象：

```javascript
console.log(promise); // Promise { <fulfilled>: '成功了！' }
```

"状态变了！"你兴奋起来，"从 pending 变成了 fulfilled（已完成）。"

你在笔记上画了 Promise 的状态机：

```
        pending (等待中)
           /    \
  resolve()      reject()
        /          \
   fulfilled      rejected
  (已完成)      (已拒绝)
```

"原来如此，"你恍然大悟，"Promise 有三种状态。创建时是 pending，调用 resolve 变成 fulfilled，调用 reject 变成 rejected。"

---

## Promise 的第一次尝试

上午十一点，你尝试用 Promise 改写上周的注册函数。

"先从最简单的开始，"你说，"把 saveUser 改成返回 Promise。"

```javascript
function saveUser(userData) {
    return new Promise(function(resolve, reject) {
        // 模拟数据库操作
        setTimeout(function() {
            if (userData.username) {
                resolve({ id: 1, ...userData });
            } else {
                reject(new Error('用户名不能为空'));
            }
        }, 100);
    });
}
```

你测试了一下：

```javascript
saveUser({ username: 'alice', password: '123' })
    .then(function(user) {
        console.log('用户创建成功:', user);
    })
    .catch(function(error) {
        console.error('创建失败:', error.message);
    });
```

控制台输出：`用户创建成功: { id: 1, username: 'alice', password: '123' }`

"太棒了！"你激动地说，"then 处理成功，catch 处理错误。不需要在每一层都判断 `if (err)`！"

你继续改写 sendEmail：

```javascript
function sendEmail(email, template) {
    return new Promise(function(resolve, reject) {
        setTimeout(function() {
            if (email.includes('@')) {
                console.log(`邮件已发送到 ${email}`);
                resolve();
            } else {
                reject(new Error('邮箱格式不正确'));
            }
        }, 100);
    });
}
```

"现在，"你想，"如果我要先保存用户，再发送邮件，应该怎么写？"

你尝试：

```javascript
saveUser({ username: 'alice', password: '123' })
    .then(function(user) {
        return sendEmail(user.email, 'welcome');
    })
    .then(function() {
        console.log('所有操作完成');
    })
    .catch(function(error) {
        console.error('出错了:', error.message);
    });
```

"等等..."你盯着代码，"我在第一个 then 里 `return sendEmail()`，返回的是另一个 Promise..."

你测试了代码，发现它确实按顺序执行了：先保存用户，再发送邮件。

"天哪！"你拍了下桌子，"then 方法可以链式调用！如果我在 then 里返回一个 Promise，下一个 then 会等它完成！"

你的眼睛亮了起来。

---

## 链式调用的发现

中午十二点，你沉浸在 Promise 链式调用的探索中，甚至忘了吃午饭。

"如果可以链式调用，"你想，"那我可以把之前的九层嵌套变成扁平的链条..."

你开始重写注册函数：

```javascript
function register(username, password) {
    let user; // 保存用户信息供后续使用

    return saveUser({ username, password })
        .then(function(savedUser) {
            user = savedUser;
            return sendEmail(user.email, 'welcome');
        })
        .then(function() {
            return createUserSettings(user.id);
        })
        .then(function(settings) {
            return grantPoints(user.id, 100);
        })
        .then(function() {
            return logUserAction(user.id, 'register');
        })
        .then(function() {
            console.log('注册完成');
            return user;
        })
        .catch(function(error) {
            console.error('注册失败:', error.message);
            throw error; // 重新抛出错误
        });
}
```

你盯着这段代码，感到一阵惊喜：

"没有嵌套！"你说，"所有的异步操作都在同一个层级上，从上到下，清晰易读。"

"而且，"你继续分析，"只有一个 catch，统一处理所有错误。不用在每一步都判断 `if (err)`。"

但你注意到一个问题：

"我需要在外层定义 `let user`，"你皱眉，"因为后续的步骤需要用到 user 信息。这有点不优雅..."

你搜索了一下，发现可以把数据传递下去：

```javascript
function register(username, password) {
    return saveUser({ username, password })
        .then(function(user) {
            return sendEmail(user.email, 'welcome')
                .then(function() {
                    return user; // 传递 user 到下一步
                });
        })
        .then(function(user) {
            return createUserSettings(user.id)
                .then(function(settings) {
                    return { user, settings }; // 传递多个值
                });
        })
        .then(function(data) {
            return grantPoints(data.user.id, 100)
                .then(function() {
                    return data.user;
                });
        })
        .then(function(user) {
            console.log('注册完成:', user);
            return user;
        })
        .catch(function(error) {
            console.error('注册失败:', error.message);
        });
}
```

"嗯...这样又有点嵌套了，"你说，"但至少比九层嵌套好多了。"

---

## 并行执行的惊喜

下午两点，你想起了上周的并行执行需求。

"Promise 能让多个异步操作并行执行吗？"你搜索文档，发现了 `Promise.all`。

```javascript
Promise.all([promise1, promise2, promise3])
    .then(function(results) {
        // results 是一个数组，包含所有 Promise 的结果
    });
```

"Promise.all 接受一个 Promise 数组，"你读着文档，"等所有 Promise 都完成后，返回一个包含所有结果的数组。"

你立刻尝试：

```javascript
function register(username, password) {
    return saveUser({ username, password })
        .then(function(user) {
            // 邮件和配置可以并行执行
            return Promise.all([
                sendEmail(user.email, 'welcome'),
                createUserSettings(user.id)
            ]).then(function(results) {
                // results[0] 是 sendEmail 的结果
                // results[1] 是 createUserSettings 的结果
                return user;
            });
        })
        .then(function(user) {
            // 继续后续操作
            return grantPoints(user.id, 100);
        })
        .then(function() {
            console.log('注册完成');
        })
        .catch(function(error) {
            console.error('注册失败:', error);
        });
}
```

你测试了代码，发现邮件和配置确实是并行执行的——总耗时不是两者之和，而是最慢的那个。

"太完美了！"你兴奋地说，"我不需要手动跟踪状态，不需要 `countDone` 变量，Promise.all 自动帮我处理了！"

"而且，"你继续分析，"如果任何一个 Promise 失败，Promise.all 会立即 reject，错误会被 catch 捕获。"

你在笔记本上写下：

```
回调模式的并行：
let done = 0;
const results = {};
doA(function(err, resA) {
    if (err) { /* 错误处理 */ }
    results.a = resA;
    done++;
    if (done === 2) doNext(results);
});
doB(function(err, resB) {
    if (err) { /* 错误处理 */ }
    results.b = resB;
    done++;
    if (done === 2) doNext(results);
});

Promise 模式的并行：
Promise.all([doA(), doB()])
    .then(function(results) {
        doNext(results);
    })
    .catch(function(err) {
        // 统一错误处理
    });
```

"简直是天壤之别，"你感叹。

---

## 错误处理的优雅

下午三点，你开始深入研究 Promise 的错误处理。

"之前每一层都要 `if (err)`，"你回忆，"Promise 是怎么统一处理的？"

你做了个实验：

```javascript
saveUser({ username: 'alice' })
    .then(function(user) {
        console.log('步骤 1: 用户保存成功');
        return sendEmail(user.email, 'welcome');
    })
    .then(function() {
        console.log('步骤 2: 邮件发送成功');
        return createUserSettings(999); // 这一步会失败
    })
    .then(function() {
        console.log('步骤 3: 配置创建成功');
        // 这一步不会执行
    })
    .catch(function(error) {
        console.error('捕获到错误:', error.message);
    });
```

输出：

```
步骤 1: 用户保存成功
步骤 2: 邮件发送成功
捕获到错误: 配置创建失败
```

"等等..."你的眼睛亮了，"第三个 then 没有执行！错误直接跳到了 catch！"

你画了一张图：

```
.then()  ─┐
         ├─> 成功
.then()  ─┤
         ├─> 成功
.then()  ─┤
         ├─X 失败 ──┐
.then()  ─┤         │ (跳过所有中间的 then)
         │         │
.then()  ─┘         ▼
.catch() ◄───────────┘ 捕获错误
```

"原来如此！"你恍然大悟，"Promise 链中的任何一步失败，都会跳过后续的 then，直接进入 catch。"

"这就是错误传播，"你总结，"我不需要在每一步都检查错误，只需要在最后 catch 统一处理。"

你继续实验，发现还可以从错误中恢复：

```javascript
saveUser({ username: 'alice' })
    .then(function(user) {
        return sendEmail(user.email, 'welcome');
    })
    .catch(function(error) {
        console.warn('邮件发送失败，但继续注册:', error.message);
        return null; // 恢复，返回一个值
    })
    .then(function(result) {
        console.log('继续执行后续操作'); // 这一步会执行
    });
```

"太灵活了！"你说，"catch 可以捕获错误，也可以让 Promise 链恢复执行。"

---

## Promise 的状态不可变

下午四点，你发现了 Promise 的一个重要特性。

"Promise 一旦从 pending 变成 fulfilled 或 rejected，状态就不能再改变了，"你读着文档。

你测试了一下：

```javascript
const promise = new Promise(function(resolve, reject) {
    resolve('第一次');
    resolve('第二次'); // 无效
    reject(new Error('错误')); // 无效
});

promise.then(function(result) {
    console.log(result); // 只输出 '第一次'
});
```

"所以 resolve 和 reject 只会生效一次，"你总结，"第一次调用决定了 Promise 的最终状态。"

你又发现了一个有趣的特性：

```javascript
const promise = new Promise(function(resolve) {
    setTimeout(function() {
        resolve('完成');
    }, 1000);
});

// 一秒后
promise.then(function(result) {
    console.log('第一次调用 then:', result);
});

// 再过一秒
promise.then(function(result) {
    console.log('第二次调用 then:', result); // 仍然输出 '完成'
});
```

"Promise 会缓存结果，"你惊讶，"即使异步操作已经完成，后续的 then 仍然可以获取结果。"

你在笔记上写下：

"Promise 的状态特性：
1. **不可变性**：状态一旦改变（pending → fulfilled/rejected），就不能再变
2. **单次决议**：resolve/reject 只有第一次调用生效
3. **结果缓存**：状态确定后，结果会被缓存，后续的 then 直接使用缓存结果"

---

## then 的返回值魔法

下午五点，你深入研究 then 方法的返回值规则。

"then 方法总是返回一个新的 Promise，"你读着文档，"但这个 Promise 的值取决于回调函数的返回值。"

你做了一系列实验：

```javascript
// 实验 1: 返回普通值
Promise.resolve(1)
    .then(function(value) {
        return value + 1; // 返回普通值
    })
    .then(function(value) {
        console.log(value); // 2 - 普通值被包装成 Promise
    });

// 实验 2: 返回 Promise
Promise.resolve(1)
    .then(function(value) {
        return Promise.resolve(value + 1); // 返回 Promise
    })
    .then(function(value) {
        console.log(value); // 2 - Promise 被展开
    });

// 实验 3: 抛出错误
Promise.resolve(1)
    .then(function(value) {
        throw new Error('出错了'); // 抛出错误
    })
    .then(function(value) {
        console.log('不会执行');
    })
    .catch(function(error) {
        console.log('捕获到:', error.message); // '捕获到: 出错了'
    });

// 实验 4: 不返回任何值
Promise.resolve(1)
    .then(function(value) {
        console.log(value); // 1
        // 没有 return
    })
    .then(function(value) {
        console.log(value); // undefined
    });
```

你总结了规则：

```
then 回调的返回值：
1. 返回普通值 → 包装成 Promise.resolve(value)
2. 返回 Promise → 直接传递给下一个 then
3. 抛出错误 → 变成 Promise.reject(error)
4. 不返回 → 相当于 return undefined
```

"这就是为什么 Promise 链能扁平化，"你恍然大悟，"每个 then 返回一个新 Promise，自动处理值传递和错误传播。"

---

## 你的 Promise 顿悟时刻

晚上六点，你重新审视重构后的注册函数。

之前的九层嵌套、200 多行代码，现在变成了：

```javascript
function register(username, password, inviteCode, promoCode) {
    let user;

    return saveUser({ username, password })
        .then(function(savedUser) {
            user = savedUser;

            // 并行执行邮件和配置
            return Promise.all([
                sendEmail(user.email, 'welcome'),
                createUserSettings(user.id)
            ]);
        })
        .then(function() {
            return grantPoints(user.id, 100);
        })
        .then(function() {
            return logUserAction(user.id, 'register');
        })
        .then(function() {
            // 处理邀请码（可选）
            if (inviteCode) {
                return checkInviteCode(inviteCode)
                    .then(function(inviter) {
                        return grantPoints(inviter.id, 50);
                    });
            }
        })
        .then(function() {
            // 处理推荐码（可选）
            if (promoCode) {
                return validatePromoCode(promoCode)
                    .then(function(promo) {
                        return addCoupon(user.id, promo.couponId);
                    });
            }
        })
        .then(function() {
            console.log('注册完成');
            return user;
        })
        .catch(function(error) {
            console.error('注册失败:', error.message);
            throw error;
        });
}
```

你靠在椅背上，长舒一口气。

"Promise 解决了回调地狱的所有问题，"你总结：

1. **扁平化**：链式调用代替深层嵌套
2. **统一错误处理**：一个 catch 捕获所有错误
3. **并行控制**：Promise.all 简化并行操作
4. **控制权回归**：异步操作返回对象，而不是接受回调
5. **状态可预测**：Promise 状态不可变，结果被缓存

"但还有一个问题，"你想，"虽然比回调好很多，但仍然有点啰嗦。这么多 then，这么多 function 关键字..."

你搜索了一下，看到了一个叫 async/await 的语法。

"这个看起来更简洁，"你点开教程，"但我得先彻底掌握 Promise，才能理解 async/await..."

---

## 你的 Promise 笔记本

晚上八点，你整理了今天的收获。

你在笔记本上写下标题："Promise —— 异步的救赎"

### 核心洞察 #1: Promise 是一个容器

你写道：

"Promise 是一个容器对象，代表一个'未来会完成的值'：

```javascript
const promise = new Promise(function(resolve, reject) {
    // 异步操作
    setTimeout(function() {
        resolve('结果'); // 决议
    }, 1000);
});
```

Promise 有三种状态：
- `pending`：等待中（初始状态）
- `fulfilled`：已完成（调用 resolve）
- `rejected`：已拒绝（调用 reject）

状态一旦改变，就不能再变。"

### 核心洞察 #2: then 链实现扁平化

"then 方法返回新的 Promise，实现链式调用：

```javascript
doA()
    .then(function(resultA) {
        return doB(resultA); // 返回 Promise
    })
    .then(function(resultB) {
        return doC(resultB);
    });
```

链式调用的规则：
- then 总是返回新 Promise
- 回调返回值决定新 Promise 的值
- 返回 Promise 会被自动展开
- 抛出错误变成 reject"

### 核心洞察 #3: 错误会自动传播

"Promise 链中的错误会自动向下传播，直到被 catch 捕获：

```javascript
doA()
    .then(doB) // 成功
    .then(doC) // 失败 ──┐
    .then(doD) // 跳过   │
    .then(doE) // 跳过   │
    .catch(handleError); // ◄─┘ 捕获
```

不需要在每一步都判断错误，一个 catch 统一处理。"

### 核心洞察 #4: Promise.all 简化并行

"Promise.all 让并行操作变得简单：

```javascript
Promise.all([promiseA, promiseB, promiseC])
    .then(function(results) {
        // results = [resultA, resultB, resultC]
    });
```

特性：
- 等待所有 Promise 完成
- 返回结果数组
- 任一失败则整体失败"

你合上笔记本，关掉电脑。

"明天继续学习 Promise 的其他特性，"你说，"then 链还有很多细节要掌握..."

---

## 知识总结

**规则 1: Promise 的三种状态**

Promise 是一个状态机，有三种状态：

```javascript
const promise = new Promise(function(resolve, reject) {
    // pending 状态

    if (success) {
        resolve(value); // → fulfilled 状态
    } else {
        reject(error); // → rejected 状态
    }
});
```

状态转换：
- `pending` → `fulfilled`（通过 resolve）
- `pending` → `rejected`（通过 reject）
- 状态一旦改变，不能再变（不可逆）

---

**规则 2: then 方法的链式调用**

`then` 方法返回新的 Promise，实现链式调用：

```javascript
promise
    .then(onFulfilled, onRejected) // 返回新 Promise
    .then(onFulfilled, onRejected) // 返回新 Promise
    .catch(onRejected); // 等价于 then(null, onRejected)
```

回调函数的返回值决定新 Promise 的状态：
- 返回普通值 → `Promise.resolve(value)`
- 返回 Promise → 直接传递（展开）
- 抛出错误 → `Promise.reject(error)`
- 不返回 → `Promise.resolve(undefined)`

---

**规则 3: 错误传播与 catch**

Promise 链中的错误会自动向下传播：

```javascript
doA()
    .then(doB) // 如果失败，跳过后续 then
    .then(doC) // 跳过
    .then(doD) // 跳过
    .catch(handleError); // 捕获任何一步的错误
```

`catch` 等价于 `then(null, onRejected)`，可以恢复 Promise 链：

```javascript
promise
    .then(onSuccess)
    .catch(function(err) {
        console.warn('错误:', err);
        return fallbackValue; // 恢复
    })
    .then(continueWork); // 继续执行
```

---

**规则 4: Promise.all 并行执行**

`Promise.all` 并行执行多个 Promise，等待全部完成：

```javascript
Promise.all([promise1, promise2, promise3])
    .then(function(results) {
        // results = [result1, result2, result3]
        // 顺序与输入顺序一致
    })
    .catch(function(error) {
        // 任何一个失败，立即 reject
    });
```

特性：
- 等待所有 Promise 完成
- 返回结果数组（顺序与输入一致）
- 任一失败则整体失败（快速失败）

---

**规则 5: Promise.resolve 和 Promise.reject**

快速创建已决议的 Promise：

```javascript
// Promise.resolve(value)
Promise.resolve(42).then(function(value) {
    console.log(value); // 42
});

// 如果参数是 Promise，直接返回
const p = Promise.resolve(42);
Promise.resolve(p) === p; // true

// Promise.reject(reason)
Promise.reject(new Error('失败')).catch(function(err) {
    console.error(err); // Error: 失败
});
```

---

**规则 6: Promise 的状态不可变性**

Promise 状态确定后，结果被缓存：

```javascript
const promise = new Promise(function(resolve) {
    resolve(42);
    resolve(100); // 无效
});

promise.then(function(value) {
    console.log(value); // 42 - 第一次 resolve 生效
});

// 多次调用 then，每次都能获取缓存的结果
promise.then(function(value) {
    console.log(value); // 42 - 使用缓存
});
```

特性：
- resolve/reject 只有第一次调用生效
- 状态确定后，结果被缓存
- 后续的 then 直接使用缓存结果

---

**事故档案编号**: ASYNC-2024-1894
**影响范围**: Promise, then 链, 错误处理, 并行控制
**根本原因**: 从回调地狱迁移到 Promise，需理解状态机、链式调用和错误传播
**修复成本**: 中（需重写异步代码为 Promise）

这是 JavaScript 世界第 94 次被记录的 Promise 使用事故。Promise 是一个容器对象，代表未来会完成的值，有三种状态：pending、fulfilled、rejected。状态一旦改变不可逆，结果被缓存。then 方法返回新 Promise，实现链式调用和扁平化。回调返回值决定新 Promise 的值：普通值被包装，Promise 被展开，错误变成 reject。错误自动向下传播，catch 统一处理。Promise.all 并行执行多个 Promise，等待全部完成或任一失败。Promise 解决了回调地狱的嵌套、错误处理和控制流问题，让异步代码更清晰、可维护。

---
