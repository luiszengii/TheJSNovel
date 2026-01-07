《第 100 次记录: 同步假象 —— async/await 的时间让渡》

---

## Promise 链的冗长困扰

周五上午九点, 你盯着屏幕上那段 Promise 链, 感到一阵疲惫。

这是昨天写的用户注册流程代码——经过一周的学习, 你已经从回调地狱进化到了 Promise 链。代码确实比之前清晰了很多, 但看着这一长串 `.then()`, 你仍然觉得不够优雅:

```javascript
function register(username, password) {
    let user;
    let settings;

    return validateInput(username, password)
        .then(function(validData) {
            return createUser(validData);
        })
        .then(function(createdUser) {
            user = createdUser;
            return sendWelcomeEmail(user.email);
        })
        .then(function() {
            return createUserSettings(user.id);
        })
        .then(function(createdSettings) {
            settings = createdSettings;
            return grantInitialPoints(user.id, 100);
        })
        .then(function() {
            return logUserAction(user.id, 'register');
        })
        .then(function() {
            console.log('注册完成');
            return { user, settings };
        })
        .catch(function(error) {
            console.error('注册失败:', error);
            throw error;
        });
}
```

"还是太啰嗦了, " 你喃喃自语, "每一步都要包在 `then` 里面, 还要用外层变量保存中间结果..."

你的同事老李走过来, 瞥了一眼屏幕: "为什么不用 `async/await`? 代码会清晰很多。"

"`async/await`?" 你困惑, "那是什么?"

"ES2017 的新特性, " 老李说, "可以让异步代码看起来像同步代码。你试试看。"

他在你的编辑器旁边打开了一个新文件, 快速敲下几行代码:

```javascript
async function register(username, password) {
    const validData = await validateInput(username, password);
    const user = await createUser(validData);
    await sendWelcomeEmail(user.email);
    const settings = await createUserSettings(user.id);
    await grantInitialPoints(user.id, 100);
    await logUserAction(user.id, 'register');

    console.log('注册完成');
    return { user, settings };
}
```

你盯着这段代码, 愣住了。

"这... 这是异步代码?" 你难以置信, "看起来就像同步代码一样!"

"对, " 老李笑了, "这就是 `async/await` 的魔法——让异步代码以同步的方式书写。"

他离开后, 你开始仔细研究这段代码。没有 `.then()`, 没有回调函数, 没有外层变量保存中间结果... 一切都那么直观。

"但这真的是异步的吗?" 你心中充满疑惑, "它到底是怎么工作的?"

---

## 第一次尝试 async/await

上午十点, 你决定亲手尝试 async/await。

"先从最简单的开始, " 你想。

你写下第一个 async 函数:

```javascript
async function test() {
    console.log('函数开始');
    return 'hello';
}

const result = test();
console.log(result);
```

你猜测输出应该是:
```
函数开始
hello
```

但当你运行代码, 控制台的输出让你惊讶:

```
函数开始
Promise { <fulfilled>: 'hello' }
```

"什么?!" 你盯着输出, "`async` 函数返回的是 Promise?"

你立刻修改代码, 加上 `.then()`:

```javascript
async function test() {
    console.log('函数开始');
    return 'hello';
}

test().then(function(result) {
    console.log(result);
});
```

输出:
```
函数开始
hello
```

"所以 `async` 函数会自动把返回值包装成 Promise, " 你恍然大悟, "即使我直接 `return 'hello'`, 它也会变成 `Promise.resolve('hello')`。"

你继续测试 `await`:

```javascript
async function test() {
    console.log('开始');

    const result = await Promise.resolve('hello');
    console.log('result:', result);

    console.log('结束');
    return result;
}

test();
```

输出:
```
开始
result: hello
结束
```

"等等... " 你困惑了, "`await` 居然能'等待' Promise 完成? 这不是阻塞了主线程吗?"

你测试了一个关键场景:

```javascript
console.log('1');

async function test() {
    console.log('2');
    await Promise.resolve();
    console.log('3');
}

test();

console.log('4');
```

你猜测如果 `await` 真的阻塞, 输出应该是: `1, 2, 3, 4`

但实际输出是:

```
1
2
4
3
```

"什么?!" 你的眼睛瞪大了, "`await` 之后的代码 (输出 3) 居然在后面?"

你的手指停在键盘上。这太诡异了——`await` 看起来像是在"等待", 但它并没有阻塞主线程...

---

## await 的真实面目

上午十一点, 你开始深入研究 `await` 的机制。

"如果 `await` 不阻塞主线程, 那它到底做了什么?" 你自问。

你画了一张执行时间线:

```javascript
console.log('1');  // 同步代码

async function test() {
    console.log('2');              // 同步代码
    await Promise.resolve();       // ← 这里发生了什么?
    console.log('3');              // await 之后的代码
}

test();

console.log('4');  // 同步代码
```

你分析执行过程:

1. 输出 `1` (同步代码)
2. 调用 `test()`, 输出 `2` (同步代码)
3. 遇到 `await Promise.resolve()`
4. 跳出 `test()` 函数, 继续执行外层代码
5. 输出 `4` (同步代码)
6. Promise 完成后, 恢复 `test()` 函数执行
7. 输出 `3` (await 之后的代码)

"所以 `await` 的作用是**暂停当前函数**, " 你恍然大悟, "但不阻塞主线程!"

你立刻想到一个类比: "`await` 就像是把函数'让渡'出去——我先让别人执行, 等 Promise 完成后再回来继续。"

你又测试了一个更复杂的例子:

```javascript
async function async1() {
    console.log('async1 开始');
    await async2();
    console.log('async1 结束');
}

async function async2() {
    console.log('async2 开始');
    await Promise.resolve();
    console.log('async2 结束');
}

console.log('脚本开始');
async1();
console.log('脚本结束');
```

你猜测输出, 然后运行:

```
脚本开始
async1 开始
async2 开始
脚本结束
async2 结束
async1 结束
```

"太神奇了!" 你说, "每个 `await` 都会暂停当前函数, 但不影响外层代码的执行。"

你画了详细的执行流程图:

```
脚本开始 → async1 开始 → async2 开始 → (await 暂停 async2)
    ↓
脚本结束
    ↓
(async2 恢复) → async2 结束 → (await 暂停 async1)
    ↓
(async1 恢复) → async1 结束
```

"原来 `await` 的本质是**时间让渡**, " 你总结, "它把执行权交出去, 等条件满足后再恢复执行。"

---

## async/await 与 Promise 的等价性

中午十二点, 你开始研究 async/await 和 Promise 的关系。

"老李说 async/await 是语法糖, " 你想, "那它应该可以转换成 Promise 链..."

你尝试把一个 async 函数转换成等价的 Promise 代码:

```javascript
// async/await 版本
async function fetchUser(userId) {
    const user = await fetchUserData(userId);
    const orders = await fetchUserOrders(user.id);
    return { user, orders };
}

// 等价的 Promise 版本
function fetchUser(userId) {
    return fetchUserData(userId)
        .then(function(user) {
            return fetchUserOrders(user.id)
                .then(function(orders) {
                    return { user, orders };
                });
        });
}
```

"等等... " 你皱眉, "Promise 版本需要嵌套, 因为要保留 `user` 变量。"

你修改成扁平的 Promise 链:

```javascript
function fetchUser(userId) {
    let user;
    return fetchUserData(userId)
        .then(function(fetchedUser) {
            user = fetchedUser;
            return fetchUserOrders(user.id);
        })
        .then(function(orders) {
            return { user, orders };
        });
}
```

"这样就对了, " 你说, "async/await 本质上就是 Promise 链的语法糖, 但它消除了嵌套和外层变量。"

你总结了转换规则:

```javascript
// 规则 1: async 函数返回 Promise
async function foo() {
    return 'hello';
}
// 等价于:
function foo() {
    return Promise.resolve('hello');
}

// 规则 2: await 等价于 .then()
async function bar() {
    const result = await asyncOperation();
    return result;
}
// 等价于:
function bar() {
    return asyncOperation()
        .then(function(result) {
            return result;
        });
}

// 规则 3: await 之后的代码等价于 .then() 里的代码
async function baz() {
    await step1();
    console.log('step1 完成');
    await step2();
    console.log('step2 完成');
}
// 等价于:
function baz() {
    return step1()
        .then(function() {
            console.log('step1 完成');
            return step2();
        })
        .then(function() {
            console.log('step2 完成');
        });
}
```

"所以 async/await 并没有改变异步的本质, " 你总结, "它只是让异步代码的书写方式更接近同步代码。"

---

## 错误处理的优雅回归

下午两点, 你开始研究 async/await 的错误处理。

"Promise 链用 `.catch()` 处理错误, " 你想, "那 async/await 怎么处理?"

你测试了第一个例子:

```javascript
async function test() {
    const result = await Promise.reject(new Error('失败了'));
    console.log(result);  // 这行会执行吗?
}

test();
```

控制台输出:

```
Uncaught (in promise) Error: 失败了
```

"错误没有被捕获, " 你说, "和 Promise 链缺少 `.catch()` 一样。"

你立刻想到: "可以用 `try...catch`!"

```javascript
async function test() {
    try {
        const result = await Promise.reject(new Error('失败了'));
        console.log(result);
    } catch (error) {
        console.error('捕获到错误:', error.message);
    }
}

test();
```

输出:

```
捕获到错误: 失败了
```

"完美!" 你兴奋地说, "async/await 让我们重新用回同步代码的错误处理方式——`try...catch`!"

这意味着什么? 你立刻对比了 Promise 链和 async/await 的错误处理:

```javascript
// Promise 链: 分散的错误处理
function register(username, password) {
    return validateInput(username, password)
        .then(function(validData) {
            return createUser(validData);
        })
        .catch(function(error) {
            console.error('验证或创建失败:', error);
            throw error;
        })
        .then(function(user) {
            return sendWelcomeEmail(user.email);
        })
        .catch(function(error) {
            console.error('邮件发送失败:', error);
            // 邮件失败不影响注册, 不抛出错误
        })
        .then(function() {
            console.log('注册完成');
        });
}

// async/await: 集中的错误处理
async function register(username, password) {
    try {
        const validData = await validateInput(username, password);
        const user = await createUser(validData);

        try {
            await sendWelcomeEmail(user.email);
        } catch (emailError) {
            console.error('邮件发送失败:', emailError);
            // 邮件失败不影响注册
        }

        console.log('注册完成');
        return user;
    } catch (error) {
        console.error('注册失败:', error);
        throw error;
    }
}
```

"async/await 的错误处理更灵活, " 你总结, "可以用嵌套的 `try...catch` 实现分层错误处理, 也可以用一个 `try...catch` 统一处理。"

你又发现了一个细节:

```javascript
async function test() {
    try {
        await step1();
        await step2();
        await step3();
    } catch (error) {
        console.error('某个步骤失败:', error);
        // 但我不知道是哪一步失败的!
    }
}
```

"统一的 `try...catch` 有个问题, " 你说, "无法区分是哪一步失败。"

你改进了代码:

```javascript
async function test() {
    try {
        await step1();
    } catch (error) {
        console.error('step1 失败:', error);
        throw error;
    }

    try {
        await step2();
    } catch (error) {
        console.error('step2 失败:', error);
        throw error;
    }

    try {
        await step3();
    } catch (error) {
        console.error('step3 失败:', error);
        throw error;
    }
}
```

"这样就清晰了, " 你说, "每个步骤的错误都能精确定位。"

---

## 并行执行的陷阱

下午三点, 你遇到了一个性能问题。

你把原来的注册流程改成了 async/await:

```javascript
async function register(username, password) {
    const validData = await validateInput(username, password);
    const user = await createUser(validData);
    await sendWelcomeEmail(user.email);
    await createUserSettings(user.id);
    await grantInitialPoints(user.id, 100);
    await logUserAction(user.id, 'register');

    return user;
}
```

"代码很清晰, " 你满意地说, "但... 好像变慢了?"

你打开 DevTools, 测量了执行时间——从原来的 1.5 秒变成了 3 秒!

"为什么会变慢?" 你困惑, "难道 async/await 比 Promise 慢?"

你仔细分析代码, 突然意识到问题所在:

"邮件发送、创建配置、发放积分、记录日志——这四个操作是**串行执行**的!"

你画了执行时间线:

```
Promise 链 (并行):
createUser ───────┐
                  ├→ (1.5s 后全部完成)
sendEmail    ─────┤
createSettings ───┤
grantPoints  ─────┘

async/await (串行):
createUser ───→ sendEmail ───→ createSettings ───→ grantPoints
(0.5s)         (0.5s)          (0.5s)              (0.5s)
总计: 2 秒
```

"因为 `await` 会等待前一个操作完成, " 你恍然大悟, "所以默认是串行执行!"

你立刻查阅文档, 发现了解决方案——使用 `Promise.all`:

```javascript
async function register(username, password) {
    const validData = await validateInput(username, password);
    const user = await createUser(validData);

    // 并行执行多个独立操作
    await Promise.all([
        sendWelcomeEmail(user.email),
        createUserSettings(user.id),
        grantInitialPoints(user.id, 100),
        logUserAction(user.id, 'register')
    ]);

    return user;
}
```

"这样就对了!" 你测试后发现, 执行时间恢复到了 1.5 秒。

你总结了并行执行的规则:

```javascript
// ❌ 错误: 不必要的串行
async function loadDashboard() {
    const user = await fetchUser();
    const posts = await fetchPosts();    // 等待 user 完成
    const comments = await fetchComments(); // 等待 posts 完成
    return { user, posts, comments };
}

// ✅ 正确: 并行加载
async function loadDashboard() {
    const [user, posts, comments] = await Promise.all([
        fetchUser(),
        fetchPosts(),
        fetchComments()
    ]);
    return { user, posts, comments };
}

// 或者更灵活:
async function loadDashboard() {
    // 先并行启动所有请求
    const userPromise = fetchUser();
    const postsPromise = fetchPosts();
    const commentsPromise = fetchComments();

    // 再等待结果
    const user = await userPromise;
    const posts = await postsPromise;
    const comments = await commentsPromise;

    return { user, posts, comments };
}
```

---

## 循环中的 await 陷阱

下午四点, 你遇到了另一个性能问题。

你需要批量上传文件, 很自然地写下了这段代码:

```javascript
async function uploadFiles(files) {
    const results = [];

    for (const file of files) {
        const result = await uploadFile(file);  // 等待每个文件上传完成
        results.push(result);
    }

    return results;
}
```

你测试上传 10 个文件——每个文件 1 秒, 总共花了 10 秒。

"这也太慢了!" 你说, "10 个文件应该可以并行上传才对。"

但你仔细看了看代码, 发现问题所在: "`await` 在循环里, 每次都要等上一个文件上传完成!"

```
文件 1 ───→ 文件 2 ───→ 文件 3 ───→ ... ───→ 文件 10
(1s)       (1s)       (1s)              (1s)
总计: 10 秒
```

你修改成并行上传:

```javascript
async function uploadFiles(files) {
    // 方案 1: 使用 Promise.all
    const uploadPromises = files.map(file => uploadFile(file));
    const results = await Promise.all(uploadPromises);
    return results;
}

// 或者更简洁:
async function uploadFiles(files) {
    return await Promise.all(files.map(uploadFile));
}
```

测试后, 10 个文件并行上传, 只花了 1 秒!

"但如果文件太多呢?" 你想, "100 个文件同时上传, 浏览器和服务器都扛不住..."

你实现了一个并发控制的版本:

```javascript
async function uploadFilesWithLimit(files, limit = 5) {
    const results = [];
    const executing = [];

    for (const file of files) {
        const promise = uploadFile(file).then(result => {
            executing.splice(executing.indexOf(promise), 1);
            return result;
        });

        results.push(promise);
        executing.push(promise);

        if (executing.length >= limit) {
            await Promise.race(executing);  // 等待任意一个完成
        }
    }

    return await Promise.all(results);
}
```

"这样就完美了, " 你说, "同时最多 5 个文件上传, 既不会太慢, 也不会压垮服务器。"

你总结了循环中使用 await 的规则:

```javascript
// ❌ 串行执行 (慢)
for (const item of items) {
    await processItem(item);
}

// ✅ 并行执行 (快, 但可能压垮服务器)
await Promise.all(items.map(processItem));

// ✅ 限制并发 (快且安全)
// 使用并发控制库或自己实现
```

---

## 顶层 await 的发现

下午五点, 你在测试一个模块时, 遇到了一个奇怪的问题。

你想在模块顶层直接使用 `await`:

```javascript
// config.js
const config = await fetchConfig();  // 报错!

export default config;
```

浏览器报错: `SyntaxError: await is only valid in async function`

"为什么?" 你困惑, "`await` 必须在 async 函数里?"

你查阅文档, 发现了一个新特性: **Top-level await** (顶层 await)。

"ES2022 引入了顶层 await, " 你读着文档, "但只在模块中有效。"

你修改了模块设置, 确保使用 ES 模块:

```html
<script type="module" src="config.js"></script>
```

然后重新测试:

```javascript
// config.js
console.log('开始加载配置');

const config = await fetchConfig();  // 现在可以了!

console.log('配置加载完成');

export default config;
```

"太方便了!" 你说, "模块会在配置加载完成后才完成初始化。"

但你马上意识到一个问题:

```javascript
// main.js
import config from './config.js';  // 会等待 config 模块加载完成

console.log('主模块开始');  // 在 config 加载完成后才执行
```

"顶层 await 会阻塞模块的加载, " 你说, "如果配置加载很慢, 整个应用都会被阻塞..."

你测试了模块依赖的场景:

```javascript
// db.js
console.log('db 模块开始加载');
const connection = await connectDatabase();  // 耗时 2 秒
console.log('db 模块加载完成');
export default connection;

// api.js
console.log('api 模块开始加载');
import db from './db.js';  // 等待 db 模块
console.log('api 模块加载完成');
export { db };

// main.js
console.log('main 模块开始加载');
import api from './api.js';  // 等待 api 模块 (间接等待 db 模块)
console.log('main 模块加载完成');
```

输出:

```
db 模块开始加载
(等待 2 秒)
db 模块加载完成
api 模块开始加载
api 模块加载完成
main 模块开始加载
main 模块加载完成
```

"模块加载是串行的, " 你总结, "顶层 await 会阻塞依赖它的所有模块。使用时要谨慎!"

---

## async/await 的最佳实践

晚上七点, 你整理了一天的收获。

你在笔记本上写下标题: "async/await —— 异步代码的同步写法"

### 核心洞察 #1: async/await 的本质

你写道:

"`async/await` 是 Promise 的语法糖, 本质是时间让渡:

```javascript
// async 函数返回 Promise
async function foo() {
    return 'hello';
}
// 等价于:
function foo() {
    return Promise.resolve('hello');
}

// await 暂停函数, 等待 Promise 完成
async function bar() {
    const result = await asyncOperation();
    console.log(result);
}
// 等价于:
function bar() {
    return asyncOperation().then(function(result) {
        console.log(result);
    });
}
```

关键特性:
- `async` 函数总是返回 Promise
- `await` 只能在 async 函数内使用 (或模块顶层)
- `await` 暂停当前函数, 但不阻塞主线程
- `await` 之后的代码相当于 `.then()` 里的代码"

### 核心洞察 #2: 错误处理的优雅回归

"async/await 让我们重新用同步代码的错误处理方式:

```javascript
async function register(username, password) {
    try {
        const validData = await validateInput(username, password);
        const user = await createUser(validData);

        // 邮件失败不影响注册
        try {
            await sendWelcomeEmail(user.email);
        } catch (emailError) {
            console.warn('邮件发送失败:', emailError);
        }

        return user;
    } catch (error) {
        console.error('注册失败:', error);
        throw error;
    }
}
```

优势:
- 使用熟悉的 `try...catch`
- 可以嵌套实现分层错误处理
- 错误堆栈更清晰"

### 核心洞察 #3: 并行执行

"默认情况下, `await` 是串行的:

```javascript
// ❌ 串行执行 (慢)
const user = await fetchUser();
const posts = await fetchPosts();
const comments = await fetchComments();

// ✅ 并行执行 (快)
const [user, posts, comments] = await Promise.all([
    fetchUser(),
    fetchPosts(),
    fetchComments()
]);

// ✅ 灵活并行
const userPromise = fetchUser();
const postsPromise = fetchPosts();
const user = await userPromise;
const posts = await postsPromise;
```

规则:
- 独立操作应该并行执行
- 有依赖关系的操作才串行执行"

### 核心洞察 #4: 循环中的 await

"循环中使用 `await` 要小心:

```javascript
// ❌ 串行处理 (慢)
for (const item of items) {
    await processItem(item);
}

// ✅ 并行处理 (快)
await Promise.all(items.map(processItem));

// ✅ 限制并发 (快且安全)
async function processWithLimit(items, limit) {
    const executing = [];
    for (const item of items) {
        const promise = processItem(item);
        executing.push(promise);

        if (executing.length >= limit) {
            await Promise.race(executing);
            executing.splice(0, 1);
        }
    }
    await Promise.all(executing);
}
```

选择策略:
- 数据量小 → 并行处理
- 数据量大 → 限制并发
- 有顺序要求 → 串行处理"

你合上笔记本, 关掉电脑。

"下周要学习 Generator 了, " 你想, "今天终于掌握了 async/await——它不是魔法, 只是让异步代码看起来像同步代码的语法糖。关键是要理解它的本质: 时间让渡。`await` 不是阻塞, 而是暂停当前函数, 让出执行权, 等 Promise 完成后再恢复。这种机制让异步代码的书写和阅读都变得更自然。"

---

## 知识总结

**规则 1: async 函数的返回值**

async 函数总是返回 Promise, 无论返回什么值:

```javascript
// 返回普通值
async function test1() {
    return 'hello';
}
test1(); // Promise { <fulfilled>: 'hello' }

// 返回 Promise
async function test2() {
    return Promise.resolve('hello');
}
test2(); // Promise { <fulfilled>: 'hello' }

// 抛出错误
async function test3() {
    throw new Error('错误');
}
test3(); // Promise { <rejected>: Error }

// 不返回
async function test4() {
    console.log('无返回');
}
test4(); // Promise { <fulfilled>: undefined }
```

转换规则:
- `return value` → `Promise.resolve(value)`
- `throw error` → `Promise.reject(error)`
- 不返回 → `Promise.resolve(undefined)`

---

**规则 2: await 的执行机制**

await 暂停当前函数, 但不阻塞主线程:

```javascript
console.log('1');

async function test() {
    console.log('2');
    await Promise.resolve();  // 暂停 test 函数
    console.log('3');         // await 之后的代码
}

test();

console.log('4');

// 输出:
// 1  ← 同步代码
// 2  ← async 函数开始 (同步执行)
// 4  ← 外层代码继续 (test 函数已暂停)
// 3  ← test 函数恢复执行
```

执行流程:
1. 同步执行 async 函数, 直到遇到第一个 `await`
2. `await` 暂停函数, 返回外层代码
3. Promise 完成后, 恢复函数执行
4. `await` 之后的代码相当于 `.then()` 里的代码

---

**规则 3: async/await 与 Promise 链的等价性**

async/await 是 Promise 的语法糖:

```javascript
// async/await 版本
async function fetchUserData(userId) {
    const user = await fetchUser(userId);
    const orders = await fetchOrders(user.id);
    return { user, orders };
}

// 等价的 Promise 版本
function fetchUserData(userId) {
    let user;
    return fetchUser(userId)
        .then(function(fetchedUser) {
            user = fetchedUser;
            return fetchOrders(user.id);
        })
        .then(function(orders) {
            return { user, orders };
        });
}
```

转换规则:
- `async function` → 返回 Promise 的函数
- `await expression` → `.then(function(result) { ... })`
- `await` 之后的代码 → `.then()` 里的代码

---

**规则 4: try...catch 错误处理**

async/await 使用 try...catch 处理错误:

```javascript
// async/await 版本
async function register(username, password) {
    try {
        const user = await createUser(username, password);
        await sendEmail(user.email);
        return user;
    } catch (error) {
        console.error('注册失败:', error);
        throw error;
    }
}

// 等价的 Promise 版本
function register(username, password) {
    return createUser(username, password)
        .then(function(user) {
            return sendEmail(user.email)
                .then(function() {
                    return user;
                });
        })
        .catch(function(error) {
            console.error('注册失败:', error);
            throw error;
        });
}
```

错误处理优势:
- 使用熟悉的 try...catch 语法
- 可以嵌套实现分层错误处理
- 错误堆栈更清晰易读

分层错误处理示例:
```javascript
async function process() {
    try {
        const data = await fetchData();

        // 邮件发送失败不影响整体流程
        try {
            await sendNotification(data);
        } catch (emailError) {
            console.warn('通知发送失败:', emailError);
        }

        return data;
    } catch (error) {
        console.error('处理失败:', error);
        throw error;
    }
}
```

---

**规则 5: 并行执行的性能优化**

await 默认是串行的, 独立操作应该并行执行:

```javascript
// ❌ 串行执行 (慢 - 3 秒)
async function loadDashboard() {
    const user = await fetchUser();        // 1 秒
    const posts = await fetchPosts();      // 1 秒
    const comments = await fetchComments(); // 1 秒
    return { user, posts, comments };
}

// ✅ 并行执行 (快 - 1 秒)
async function loadDashboard() {
    const [user, posts, comments] = await Promise.all([
        fetchUser(),
        fetchPosts(),
        fetchComments()
    ]);
    return { user, posts, comments };
}

// ✅ 灵活并行 (部分依赖)
async function loadDashboard() {
    const user = await fetchUser();  // 必须先获取用户

    // 并行获取用户的帖子和评论
    const [posts, comments] = await Promise.all([
        fetchUserPosts(user.id),
        fetchUserComments(user.id)
    ]);

    return { user, posts, comments };
}
```

并行执行规则:
- 独立操作 → `Promise.all` 并行
- 有依赖关系 → 串行执行
- 部分依赖 → 混合使用

---

**规则 6: 循环中的 await 陷阱**

循环中使用 await 会导致串行执行:

```javascript
// ❌ 串行处理 (10 个文件 = 10 秒)
async function uploadFiles(files) {
    const results = [];
    for (const file of files) {
        const result = await uploadFile(file);  // 等待每个文件
        results.push(result);
    }
    return results;
}

// ✅ 并行处理 (10 个文件 = 1 秒, 但可能压垮服务器)
async function uploadFiles(files) {
    return await Promise.all(files.map(uploadFile));
}

// ✅ 限制并发 (快且安全)
async function uploadFilesWithLimit(files, limit = 5) {
    const results = [];
    const executing = [];

    for (const file of files) {
        const promise = uploadFile(file).then(result => {
            executing.splice(executing.indexOf(promise), 1);
            return result;
        });

        results.push(promise);
        executing.push(promise);

        // 达到并发限制, 等待任意一个完成
        if (executing.length >= limit) {
            await Promise.race(executing);
        }
    }

    return await Promise.all(results);
}
```

选择策略:
- 数据量小 (< 10) → 并行处理
- 数据量大 (> 50) → 限制并发 (5-10)
- 有顺序要求 → 串行处理

---

**规则 7: 顶层 await (Top-level await)**

ES2022 允许在模块顶层使用 await:

```javascript
// config.js (ES 模块)
console.log('开始加载配置');

// 顶层 await
const config = await fetchConfig();

console.log('配置加载完成');

export default config;
```

使用条件:
- 必须是 ES 模块 (`<script type="module">`)
- 会阻塞模块的加载
- 依赖此模块的其他模块也会被阻塞

模块依赖链:
```javascript
// db.js
const connection = await connectDatabase();  // 耗时 2 秒
export default connection;

// api.js
import db from './db.js';  // 等待 db 模块加载 (2 秒)
export { db };

// main.js
import api from './api.js';  // 等待 api 模块加载 (间接等待 db)
console.log('启动完成');  // 总共等待 2 秒
```

注意事项:
- 顶层 await 会阻塞模块加载
- 影响应用启动时间
- 应该只用于必须的初始化操作

---

**规则 8: async/await 的常见陷阱**

**陷阱 1: 忘记 await**
```javascript
// ❌ 忘记 await
async function test() {
    const result = asyncOperation();  // 返回 Promise, 不是结果
    console.log(result);  // Promise { <pending> }
}

// ✅ 正确
async function test() {
    const result = await asyncOperation();
    console.log(result);  // 实际结果
}
```

**陷阱 2: 在非 async 函数中使用 await**
```javascript
// ❌ 错误
function test() {
    const result = await asyncOperation();  // SyntaxError
}

// ✅ 正确
async function test() {
    const result = await asyncOperation();
}
```

**陷阱 3: 串行化独立操作**
```javascript
// ❌ 不必要的串行
async function loadData() {
    const user = await fetchUser();
    const posts = await fetchPosts();  // 不依赖 user, 但等待了
}

// ✅ 并行执行
async function loadData() {
    const [user, posts] = await Promise.all([
        fetchUser(),
        fetchPosts()
    ]);
}
```

**陷阱 4: 在循环中不必要地使用 await**
```javascript
// ❌ 串行处理
for (const item of items) {
    await processItem(item);
}

// ✅ 并行处理
await Promise.all(items.map(processItem));
```

---

**事故档案编号**: ASYNC-2024-1900
**影响范围**: async/await, 异步函数, 错误处理, 性能优化
**根本原因**: 不理解 async/await 的本质和执行机制, 导致不必要的串行执行和性能问题
**修复成本**: 低 (理解机制后容易优化)

这是 JavaScript 世界第 100 次被记录的异步编程事故。async/await 是 Promise 的语法糖, 让异步代码以同步的方式书写。async 函数总是返回 Promise, 无论返回什么值。await 暂停当前函数但不阻塞主线程, 本质是时间让渡——让出执行权, 等 Promise 完成后再恢复。await 之后的代码相当于 `.then()` 里的代码。async/await 使用 try...catch 处理错误, 可以嵌套实现分层错误处理。await 默认是串行的, 独立操作应该并行执行以提升性能。循环中使用 await 要小心, 避免不必要的串行化。ES2022 引入顶层 await, 但会阻塞模块加载。理解 async/await 的本质和执行机制是避免性能问题和正确使用的关键。

---
