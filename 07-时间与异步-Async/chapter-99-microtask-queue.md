《第 99 次记录: 执行顺序谜案 —— 微任务的插队特权》

---

## 诡异的输出顺序

周四下午三点, 你盯着控制台的输出, 完全困惑了。

这是一个看起来非常简单的测试代码——你只想验证一下 Promise 和 setTimeout 的执行顺序。毕竟上周刚学完 Promise, 你觉得自己已经掌握了异步编程的精髓。

你在控制台输入了这段代码:

```javascript
console.log('开始');

setTimeout(function() {
    console.log('setTimeout');
}, 0);

Promise.resolve().then(function() {
    console.log('Promise then');
});

console.log('结束');
```

"很简单, " 你自信地说, "先打印'开始'和'结束', 然后是 setTimeout 和 Promise.then。"

但当你按下回车键, 控制台的输出让你愣住了:

```
开始
结束
Promise then
setTimeout
```

"什么?!" 你揉了揉眼睛, "Promise.then 怎么在 setTimeout 前面?"

你明明设置了 `setTimeout(..., 0)`, 延迟时间是 0 毫秒啊! 按理说应该立即执行才对。但 Promise.then 居然比它还快?

"难道是浏览器的 bug?" 你切换到 Firefox, 运行同样的代码——输出完全一样。

你的手指停在键盘上。这不是 bug, 这是某种你不知道的执行规则。

---

## 时间刻度的迷思

下午三点半, 你开始深入调查。

"也许是延迟时间的问题?" 你想, "0 毫秒可能不够快。"

你把延迟时间改成了更明确的值:

```javascript
console.log('测试 1: setTimeout 延迟 0ms');

setTimeout(function() {
    console.log('setTimeout 0ms');
}, 0);

Promise.resolve().then(function() {
    console.log('Promise.then');
});

console.log('---');

console.log('测试 2: setTimeout 延迟 10ms');

setTimeout(function() {
    console.log('setTimeout 10ms');
}, 10);

Promise.resolve().then(function() {
    console.log('Promise.then 2');
});
```

输出:

```
测试 1: setTimeout 延迟 0ms
---
测试 2: setTimeout 延迟 10ms
Promise.then
Promise.then 2
setTimeout 0ms
setTimeout 10ms
```

"等等..." 你皱眉, "即使是 0 毫秒的 setTimeout, Promise.then 仍然先执行?"

这违背了你的直觉。你一直以为"延迟 0 毫秒"意味着"下一刻立即执行", 但现在看来, Promise.then 有某种"插队特权"。

你又尝试了更复杂的测试:

```javascript
console.log('1');

setTimeout(function() {
    console.log('2');

    Promise.resolve().then(function() {
        console.log('3');
    });
}, 0);

Promise.resolve().then(function() {
    console.log('4');

    setTimeout(function() {
        console.log('5');
    }, 0);
});

console.log('6');
```

你猜测输出应该是: `1, 6, 2, 4, 3, 5`。

但实际输出是:

```
1
6
4
2
3
5
```

"4 在 2 前面?" 你的眉头皱得更紧了, "3 在 5 前面我能理解, 因为它们都在各自的 setTimeout 里面。但为什么外层的 Promise.then (输出 4) 会在外层的 setTimeout (输出 2) 前面?"

你感觉自己触碰到了某个关键规则的边缘, 但还没有完全理解。

---

## 事件循环的真相

下午四点, 你决定查阅 MDN 文档。

你搜索"JavaScript 执行顺序", 看到了一个词:**事件循环 (Event Loop)**。

"事件循环?" 你点开文档, 开始阅读。

文档告诉你, JavaScript 的异步任务分为两种队列:

1. **宏任务队列 (Macrotask Queue)**: setTimeout, setInterval, I/O 操作
2. **微任务队列 (Microtask Queue)**: Promise.then, MutationObserver

"两个队列?" 你喃喃自语, "那执行顺序是什么?"

你继续阅读, 看到了事件循环的执行规则:

```
事件循环的每一轮 (tick):
1. 执行所有同步代码
2. 检查微任务队列, 执行所有微任务
3. 从宏任务队列取出一个任务执行
4. 回到步骤 2
```

"等等..." 你的眼睛亮了, "微任务队列在每轮循环中都会被完全清空, 而宏任务队列每次只执行一个?"

你画了一张图:

```
执行流程:

[同步代码]
    ↓
[微任务队列 - 全部执行]
    ↓
[宏任务队列 - 执行一个]
    ↓
[微任务队列 - 全部执行]  ← 检查是否有新的微任务
    ↓
[宏任务队列 - 执行一个]
    ↓
[循环...]
```

"所以 Promise.then 总是在 setTimeout 前面, " 你恍然大悟, "因为微任务队列的优先级更高!"

你立刻重新分析之前的代码:

```javascript
console.log('1');  // 同步代码, 立即执行

setTimeout(function() {
    console.log('2');  // 宏任务, 进入宏任务队列
}, 0);

Promise.resolve().then(function() {
    console.log('4');  // 微任务, 进入微任务队列
});

console.log('6');  // 同步代码, 立即执行
```

执行顺序:

1. **同步代码**: 输出 `1`, `6`
2. **微任务队列**: 执行所有微任务, 输出 `4`
3. **宏任务队列**: 执行第一个宏任务, 输出 `2`

"所以输出是 `1, 6, 4, 2`!" 你兴奋地说。

---

## 微任务的插队行为

下午五点, 你开始测试微任务的"插队"能力。

"如果微任务里又创建了新的微任务呢?" 你好奇。

```javascript
console.log('开始');

Promise.resolve().then(function() {
    console.log('微任务 1');

    Promise.resolve().then(function() {
        console.log('微任务 1 的子微任务');
    });
});

Promise.resolve().then(function() {
    console.log('微任务 2');
});

setTimeout(function() {
    console.log('宏任务 1');
}, 0);

console.log('结束');
```

你猜测输出顺序, 然后运行代码:

```
开始
结束
微任务 1
微任务 2
微任务 1 的子微任务
宏任务 1
```

"等等..." 你盯着输出, "'微任务 1 的子微任务'在'微任务 2'后面, 但在'宏任务 1'前面?"

你画了执行时间线:

```
同步代码: 开始 → 结束

微任务队列 (第一轮):
  - 微任务 1 → 输出'微任务 1', 并创建新的微任务
  - 微任务 2 → 输出'微任务 2'

微任务队列 (继续清空):
  - 微任务 1 的子微任务 → 输出'微任务 1 的子微任务'

宏任务队列:
  - 宏任务 1 → 输出'宏任务 1'
```

"原来如此!" 你恍然大悟, "微任务队列在同一轮循环中会被完全清空, 即使执行过程中又添加了新的微任务!"

这意味着:

- **微任务可以无限插队**, 只要还有微任务, 宏任务就永远不会执行
- **同一轮循环内的所有微任务**, 优先级都高于下一个宏任务

你又测试了一个极端情况:

```javascript
console.log('开始');

setTimeout(function() {
    console.log('我是宏任务, 但我永远不会执行');
}, 0);

function createEndlessMicrotasks() {
    Promise.resolve().then(function() {
        console.log('微任务');
        createEndlessMicrotasks(); // 不断创建新的微任务
    });
}

createEndlessMicrotasks();
```

"这段代码会怎样?" 你运行后, 浏览器标签页直接卡死了。

"天哪, " 你赶紧关闭标签页, "微任务的优先级太高了, 如果一直创建微任务, 宏任务队列永远得不到执行机会, 页面就会被阻塞!"

---

## 生产环境的隐蔽 Bug

下午六点, 你想起了上个月遇到的一个诡异 bug。

当时你在做一个图片轮播功能。用户点击"下一张"按钮时, 需要先显示 loading 状态, 然后加载图片, 最后隐藏 loading。

你写的代码是这样的:

```javascript
function loadNextImage() {
    showLoading(); // 显示 loading

    fetchImage(nextImageUrl)
        .then(function(image) {
            displayImage(image);
        })
        .then(function() {
            hideLoading(); // 隐藏 loading
        });
}
```

"这段代码看起来很合理, " 你当时想, "先显示 loading, 再加载图片, 最后隐藏 loading。"

但用户反馈说:"点击按钮后, loading 根本没有出现, 图片直接就显示了。"

你当时百思不得其解, 最后不得不加了一个 `setTimeout` 来强制显示 loading:

```javascript
function loadNextImage() {
    showLoading();

    setTimeout(function() {
        fetchImage(nextImageUrl)
            .then(function(image) {
                displayImage(image);
            })
            .then(function() {
                hideLoading();
            });
    }, 100); // 强制延迟 100ms
}
```

"现在我终于明白了, " 你恍然大悟, "问题出在微任务的执行时机上!"

你重新分析原来的代码:

```javascript
function loadNextImage() {
    showLoading();  // 修改 DOM, 但浏览器还没渲染

    fetchImage(nextImageUrl)  // 返回 Promise (微任务)
        .then(function(image) {
            displayImage(image);  // 微任务中修改 DOM
        })
        .then(function() {
            hideLoading();  // 微任务中修改 DOM
        });
}
```

执行流程:

1. **同步代码**: `showLoading()` 修改 DOM (loading 元素 display = 'block')
2. **微任务队列**: Promise.then 执行, `displayImage()` 和 `hideLoading()` 都在微任务中
3. **渲染**: 浏览器在所有微任务执行完后才渲染

"所以 loading 的显示和隐藏几乎同时发生, " 你总结, "浏览器看到的是最终状态 (loading 隐藏), 中间状态 (loading 显示) 根本没有渲染出来!"

你画了时间线:

```
同步代码:
  showLoading() → DOM 状态: loading = true

微任务队列:
  displayImage() → DOM 状态: image 显示
  hideLoading() → DOM 状态: loading = false

浏览器渲染:
  渲染最终状态 (loading = false, image 显示)
```

"用户看不到 loading, 因为浏览器跳过了中间状态!"

---

## 正确的异步时机控制

晚上七点, 你开始研究如何正确控制异步时机。

"如果要让浏览器渲染 loading, 就必须让渲染发生在微任务之前, " 你想。

你查阅文档, 发现了 `requestAnimationFrame`:

```javascript
function loadNextImage() {
    showLoading();

    // 等待浏览器下一帧渲染
    requestAnimationFrame(function() {
        fetchImage(nextImageUrl)
            .then(function(image) {
                displayImage(image);
            })
            .then(function() {
                hideLoading();
            });
    });
}
```

"但这样还是不够, " 你测试后发现, "requestAnimationFrame 在微任务之后, 渲染之前执行。"

你又找到了另一个方案——使用 `setTimeout` 模拟宏任务:

```javascript
function loadNextImage() {
    showLoading();

    setTimeout(function() {
        fetchImage(nextImageUrl)
            .then(function(image) {
                displayImage(image);
            })
            .then(function() {
                hideLoading();
            });
    }, 0);
}
```

执行流程:

1. **同步代码**: `showLoading()` 修改 DOM
2. **微任务队列**: 空
3. **浏览器渲染**: 渲染 loading 状态
4. **宏任务队列**: 执行 `setTimeout` 回调, 加载图片并隐藏 loading

"这样就对了!" 你说, "把图片加载放到宏任务里, 浏览器就有机会在加载之前渲染 loading 状态。"

你又测试了更优雅的方案——使用 `Promise` 和 `await`:

```javascript
async function loadNextImage() {
    showLoading();

    // 等待下一个宏任务
    await new Promise(resolve => setTimeout(resolve, 0));

    const image = await fetchImage(nextImageUrl);
    displayImage(image);
    hideLoading();
}
```

"完美!" 你说, "用 `await` 等待一个宏任务, 让浏览器有机会渲染, 然后再继续加载图片。"

---

## 微任务的实际应用

晚上八点, 你开始思考微任务的实际用途。

"既然微任务优先级这么高, 什么时候应该用它?" 你自问。

你总结了几个场景:

**场景 1: 批量 DOM 更新**

```javascript
function batchUpdate() {
    updateDOM1();
    updateDOM2();
    updateDOM3();

    // 在微任务中执行后续操作, 确保 DOM 更新完成
    Promise.resolve().then(function() {
        console.log('所有 DOM 更新已应用 (但还未渲染)');
        performCalculation(); // 基于更新后的 DOM 进行计算
    });
}
```

**场景 2: 错误处理的延迟**

```javascript
function processData(data) {
    try {
        validateData(data);
    } catch (error) {
        // 使用微任务延迟错误处理, 让当前函数完成
        Promise.resolve().then(function() {
            handleError(error);
        });
    }

    // 继续执行其他逻辑
    doOtherWork();
}
```

**场景 3: 状态一致性保证**

```javascript
class StateMachine {
    constructor() {
        this.state = 'idle';
        this.listeners = [];
    }

    setState(newState) {
        this.state = newState;

        // 在微任务中通知监听器, 确保状态已完全更新
        Promise.resolve().then(() => {
            this.listeners.forEach(listener => listener(newState));
        });
    }
}
```

"微任务的核心优势, " 你总结, "是在当前代码执行完成后、浏览器渲染之前执行。适合用于:

1. 需要在 DOM 更新后、渲染前执行的操作
2. 需要保证执行顺序, 但不想阻塞当前代码
3. 需要批量处理, 避免多次触发渲染"

---

## 你的事件循环笔记本

晚上九点, 你整理了今天的收获。

你在笔记本上写下标题:"微任务队列 —— 时间的插队特权"

### 核心洞察 #1: 事件循环的执行顺序

你写道:

"事件循环的每一轮 (tick) 执行顺序:

```
1. 执行所有同步代码
2. 清空微任务队列 (执行所有微任务)
3. 浏览器渲染 (可选)
4. 从宏任务队列取出一个任务执行
5. 回到步骤 2
```

关键规则:
- 微任务队列在每轮循环中被完全清空
- 宏任务队列每次只执行一个任务
- 微任务的优先级永远高于下一个宏任务"

### 核心洞察 #2: 微任务的插队能力

"微任务可以无限插队:

```javascript
Promise.resolve().then(function() {
    console.log('微任务 1');

    Promise.resolve().then(function() {
        console.log('微任务 1 的子任务'); // 仍然在同一轮循环中执行
    });
});

setTimeout(function() {
    console.log('宏任务'); // 必须等所有微任务执行完
}, 0);
```

危险:
- 如果不断创建微任务, 宏任务永远得不到执行
- 页面会被阻塞, 无法响应用户操作"

### 核心洞察 #3: 渲染时机

"浏览器渲染发生在微任务之后、下一个宏任务之前:

```javascript
showLoading();  // 修改 DOM

Promise.resolve().then(function() {
    hideLoading();  // 微任务中修改 DOM
});

// 浏览器渲染: 只看到最终状态 (loading 隐藏)
```

解决方案:
- 使用 setTimeout 将操作延迟到下一个宏任务
- 让浏览器有机会渲染中间状态"

### 核心洞察 #4: 任务队列分类

"JavaScript 的任务分为两类:

**宏任务 (Macrotask)**:
- setTimeout / setInterval
- I/O 操作
- UI 渲染
- setImmediate (Node.js)

**微任务 (Microtask)**:
- Promise.then / catch / finally
- MutationObserver
- queueMicrotask
- process.nextTick (Node.js)

选择标准:
- 需要立即执行, 但不阻塞当前代码 → 微任务
- 需要延迟执行, 让浏览器有机会渲染 → 宏任务"

你合上笔记本, 关掉电脑。

"明天要学习 async/await 了, " 你想, "今天终于理解了事件循环的秘密——微任务的插队特权。Promise.then 之所以总是比 setTimeout 快, 不是因为它速度快, 而是因为它的优先级更高。理解这个机制, 才能真正掌握 JavaScript 的异步世界。"

---

## 知识总结

**规则 1: 事件循环的执行顺序**

事件循环的每一轮 (tick) 按以下顺序执行:

```javascript
// 1. 执行所有同步代码
console.log('同步 1');
console.log('同步 2');

// 2. 清空微任务队列
Promise.resolve().then(() => console.log('微任务 1'));
Promise.resolve().then(() => console.log('微任务 2'));

// 3. 浏览器渲染 (可选)
// ...

// 4. 从宏任务队列取出一个任务执行
setTimeout(() => console.log('宏任务 1'), 0);
setTimeout(() => console.log('宏任务 2'), 0);

// 输出顺序:
// 同步 1
// 同步 2
// 微任务 1
// 微任务 2
// 宏任务 1
// 宏任务 2
```

执行流程:
- 同步代码优先级最高, 立即执行
- 微任务队列在每轮循环中被完全清空
- 宏任务队列每次只执行一个任务
- 微任务的优先级永远高于下一个宏任务

---

**规则 2: 微任务队列的完全清空机制**

微任务队列会在同一轮循环中被完全清空, 即使执行过程中添加了新的微任务:

```javascript
console.log('开始');

Promise.resolve().then(function() {
    console.log('微任务 1');

    // 在微任务中创建新的微任务
    Promise.resolve().then(function() {
        console.log('微任务 1-1');
    });
});

Promise.resolve().then(function() {
    console.log('微任务 2');
});

setTimeout(function() {
    console.log('宏任务');
}, 0);

console.log('结束');

// 输出:
// 开始
// 结束
// 微任务 1
// 微任务 2
// 微任务 1-1  ← 虽然是后创建的, 但仍在同一轮循环中执行
// 宏任务
```

关键特性:
- 微任务可以在执行过程中添加新的微任务
- 新添加的微任务仍在当前轮循环中执行
- 只有当微任务队列完全为空时, 才会执行下一个宏任务

---

**规则 3: 微任务的无限插队与阻塞风险**

微任务可以无限插队, 导致宏任务永远得不到执行:

```javascript
console.log('开始');

setTimeout(function() {
    console.log('我是宏任务, 但永远不会执行');
}, 0);

function createEndlessMicrotasks() {
    Promise.resolve().then(function() {
        console.log('微任务');
        createEndlessMicrotasks(); // 递归创建微任务
    });
}

createEndlessMicrotasks();

// 结果: 页面卡死, 宏任务永远不会执行
```

阻塞原因:
- 微任务不断创建新的微任务
- 微任务队列永远无法清空
- 宏任务队列永远得不到执行机会
- 页面无法渲染, 用户操作无响应

---

**规则 4: 宏任务与微任务的分类**

JavaScript 的异步任务分为两类:

**宏任务 (Macrotask)**:
- `setTimeout` / `setInterval`
- I/O 操作 (如文件读写)
- UI 渲染事件
- `requestAnimationFrame` (在微任务之后, 渲染之前)
- `setImmediate` (Node.js 特有)

**微任务 (Microtask)**:
- `Promise.then` / `catch` / `finally`
- `MutationObserver` (DOM 变化监听)
- `queueMicrotask` (直接创建微任务)
- `process.nextTick` (Node.js 特有, 优先级高于 Promise)

区别:
```javascript
// 宏任务: 延迟到下一个事件循环
setTimeout(() => console.log('宏任务'), 0);

// 微任务: 在当前循环结束前执行
Promise.resolve().then(() => console.log('微任务'));

queueMicrotask(() => console.log('直接创建微任务'));

// 输出:
// 微任务
// 直接创建微任务
// 宏任务
```

---

**规则 5: 浏览器渲染时机与 DOM 更新**

浏览器渲染发生在微任务之后、下一个宏任务之前:

```javascript
function showLoading() {
    document.querySelector('.loading').style.display = 'block';
}

function hideLoading() {
    document.querySelector('.loading').style.display = 'none';
}

// ❌ 问题: loading 不会显示
function loadDataBad() {
    showLoading();  // 修改 DOM

    fetchData().then(function(data) {
        processData(data);  // 微任务中修改 DOM
        hideLoading();      // 微任务中修改 DOM
    });

    // 执行顺序:
    // 1. showLoading() - DOM 状态: loading = true
    // 2. 微任务: processData(), hideLoading() - DOM 状态: loading = false
    // 3. 浏览器渲染: 只渲染最终状态 (loading = false)
}

// ✅ 正确: 让浏览器有机会渲染
function loadDataGood() {
    showLoading();

    // 延迟到下一个宏任务
    setTimeout(function() {
        fetchData().then(function(data) {
            processData(data);
            hideLoading();
        });
    }, 0);

    // 执行顺序:
    // 1. showLoading() - DOM 状态: loading = true
    // 2. 微任务队列: 空
    // 3. 浏览器渲染: 渲染 loading 状态
    // 4. 宏任务: fetchData() 和后续操作
}
```

渲染时机规律:
- DOM 修改后不会立即渲染
- 浏览器在所有微任务执行完后才渲染
- 如果微任务中多次修改 DOM, 只渲染最终状态

---

**规则 6: Promise.then 与 setTimeout(0) 的执行顺序**

Promise.then 总是在 setTimeout(0) 之前执行:

```javascript
console.log('1');

setTimeout(function() {
    console.log('2');
}, 0);

Promise.resolve().then(function() {
    console.log('3');
});

console.log('4');

// 输出:
// 1  ← 同步代码
// 4  ← 同步代码
// 3  ← 微任务 (Promise.then)
// 2  ← 宏任务 (setTimeout)
```

原因:
- `setTimeout(fn, 0)` 创建宏任务
- `Promise.then` 创建微任务
- 微任务的优先级高于宏任务
- 即使延迟时间是 0, setTimeout 仍然是宏任务

---

**规则 7: 嵌套异步任务的执行顺序**

嵌套的微任务和宏任务有特定的执行顺序:

```javascript
console.log('1');

setTimeout(function() {
    console.log('2');

    Promise.resolve().then(function() {
        console.log('3');
    });
}, 0);

Promise.resolve().then(function() {
    console.log('4');

    setTimeout(function() {
        console.log('5');
    }, 0);
});

console.log('6');

// 输出:
// 1  ← 同步代码
// 6  ← 同步代码
// 4  ← 外层微任务
// 2  ← 外层宏任务
// 3  ← 宏任务中的微任务
// 5  ← 微任务中的宏任务
```

执行分析:
1. 同步代码: 输出 `1`, `6`
2. 清空微任务队列: 执行外层 Promise.then, 输出 `4`, 创建新的 setTimeout
3. 执行第一个宏任务: setTimeout 回调, 输出 `2`, 创建新的 Promise.then
4. 清空微任务队列: 执行宏任务中的 Promise.then, 输出 `3`
5. 执行下一个宏任务: 微任务中创建的 setTimeout, 输出 `5`

---

**规则 8: 微任务的实际应用场景**

微任务适合以下场景:

**场景 1: 批量 DOM 更新后的计算**
```javascript
function batchUpdate() {
    updateDOM1();
    updateDOM2();
    updateDOM3();

    // 在微任务中执行计算, 确保所有 DOM 更新已应用
    Promise.resolve().then(function() {
        const height = element.offsetHeight;  // 读取更新后的 DOM
        performCalculation(height);
    });
}
```

**场景 2: 状态一致性保证**
```javascript
class StateMachine {
    constructor() {
        this.state = 'idle';
        this.listeners = [];
    }

    setState(newState) {
        this.state = newState;

        // 在微任务中通知监听器, 确保状态已完全更新
        Promise.resolve().then(() => {
            this.listeners.forEach(listener => listener(newState));
        });
    }
}
```

**场景 3: 延迟错误处理**
```javascript
function processData(data) {
    try {
        validateData(data);
    } catch (error) {
        // 使用微任务延迟错误处理, 让当前函数完成
        Promise.resolve().then(() => handleError(error));
    }

    doOtherWork();  // 继续执行
}
```

使用原则:
- 需要在当前代码执行完成后立即执行 → 微任务
- 需要在 DOM 更新后、浏览器渲染前执行 → 微任务
- 需要让浏览器有机会渲染 → 宏任务

---

**事故档案编号**: ASYNC-2024-1899
**影响范围**: 事件循环, 微任务队列, 宏任务队列, 浏览器渲染时机
**根本原因**: 不理解微任务的插队特权和浏览器渲染时机, 导致 UI 更新不符合预期
**修复成本**: 低 (理解执行顺序后容易修复)

这是 JavaScript 世界第 99 次被记录的异步执行顺序事故。事件循环的每一轮按照"同步代码 → 微任务队列 → 渲染 → 宏任务"的顺序执行。微任务队列在每轮循环中被完全清空, 即使执行过程中添加了新的微任务。宏任务队列每次只执行一个任务。Promise.then 总是在 setTimeout(0) 之前执行, 因为微任务的优先级高于宏任务。浏览器渲染发生在微任务之后、下一个宏任务之前, 如果微任务中多次修改 DOM, 浏览器只渲染最终状态。微任务可以无限插队, 如果不断创建微任务, 宏任务永远得不到执行, 页面会被阻塞。理解事件循环和任务队列的执行顺序是掌握 JavaScript 异步编程的关键。

---
