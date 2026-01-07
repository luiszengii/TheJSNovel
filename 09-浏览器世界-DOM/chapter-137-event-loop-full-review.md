《第 137 次记录：时间的齿轮 —— 事件循环全景复盘》

## 异步执行顺序的终极挑战

周五下午 4 点 30 分，技术总监老李在团队会议上提出了一个挑战："我给你们写了一段代码，谁能准确说出它的输出顺序？"

他在白板上写下这段代码：

```javascript
console.log('1');

setTimeout(() => {
  console.log('2');
  Promise.resolve().then(() => {
    console.log('3');
  });
}, 0);

Promise.resolve().then(() => {
  console.log('4');
  setTimeout(() => {
    console.log('5');
  }, 0);
});

new Promise((resolve) => {
  console.log('6');
  resolve();
}).then(() => {
  console.log('7');
});

setTimeout(() => {
  console.log('8');
  Promise.resolve().then(() => {
    console.log('9');
  });
}, 0);

console.log('10');
```

会议室陷入了沉默。小陈试探性地说："1、6、10... 然后是 Promise 的 4、7... 再然后是 setTimeout 的 2、8..."

老李摇摇头："不对。运行一下看看。"

你打开控制台，粘贴代码，按下回车。输出结果是：

```
1
6
10
4
7
2
3
8
9
5
```

"为什么 5 是最后输出的？" 小陈困惑地问，"它不是在 4 里面的 setTimeout 吗？应该比 8 和 9 早才对啊。"

老李说："这就是事件循环的精髓。今天我们系统地复盘一遍浏览器的事件循环机制，把所有的异步执行规则串联起来。"

## 事件循环的完整架构

老李在白板上画出了事件循环的完整架构图：

```
┌─────────────────────────────────────────────────┐
│            JavaScript 执行栈（Call Stack）        │
│  ┌──────────────────────────────────────────┐  │
│  │        当前正在执行的同步代码              │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│                执行栈清空检查                      │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│            微任务队列（Microtask Queue）          │
│  • Promise.then/catch/finally                   │
│  • MutationObserver                             │
│  • queueMicrotask                               │
│                                                  │
│  执行规则：清空所有微任务（直到队列为空）          │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│          宏任务队列（Macrotask Queue）            │
│  • setTimeout/setInterval                       │
│  • setImmediate (Node.js)                       │
│  • I/O 操作                                      │
│  • UI 渲染                                       │
│                                                  │
│  执行规则：每次取一个宏任务执行                    │
└─────────────────────────────────────────────────┘
                      ↓
                  重复循环
```

老李解释道："事件循环的核心规则是：
1. 执行同步代码，直到调用栈清空
2. 执行所有微任务（一次性清空微任务队列）
3. 执行一个宏任务
4. 重复步骤 2-3"

## 逐步拆解执行流程

老李带着大家逐步分析刚才的代码：

```javascript
// 初始状态：
// 执行栈: [全局代码]
// 微任务队列: []
// 宏任务队列: []

console.log('1'); // 输出: 1
// 执行栈: [全局代码]
// 微任务队列: []
// 宏任务队列: []

setTimeout(() => {
  console.log('2');
  Promise.resolve().then(() => {
    console.log('3');
  });
}, 0);
// 将 setTimeout 回调加入宏任务队列
// 执行栈: [全局代码]
// 微任务队列: []
// 宏任务队列: [setTimeout1]

Promise.resolve().then(() => {
  console.log('4');
  setTimeout(() => {
    console.log('5');
  }, 0);
});
// 将 then 回调加入微任务队列
// 执行栈: [全局代码]
// 微任务队列: [Promise1]
// 宏任务队列: [setTimeout1]

new Promise((resolve) => {
  console.log('6'); // 输出: 6（executor 同步执行）
  resolve();
}).then(() => {
  console.log('7');
});
// 将 then 回调加入微任务队列
// 执行栈: [全局代码]
// 微任务队列: [Promise1, Promise2]
// 宏任务队列: [setTimeout1]

setTimeout(() => {
  console.log('8');
  Promise.resolve().then(() => {
    console.log('9');
  });
}, 0);
// 将 setTimeout 回调加入宏任务队列
// 执行栈: [全局代码]
// 微任务队列: [Promise1, Promise2]
// 宏任务队列: [setTimeout1, setTimeout2]

console.log('10'); // 输出: 10
// 执行栈: [全局代码]
// 微任务队列: [Promise1, Promise2]
// 宏任务队列: [setTimeout1, setTimeout2]

// ===== 同步代码执行完毕，执行栈清空 =====

// 第 1 轮微任务：执行 Promise1
console.log('4'); // 输出: 4
setTimeout(() => {
  console.log('5');
}, 0);
// 执行栈: []
// 微任务队列: [Promise2]
// 宏任务队列: [setTimeout1, setTimeout2, setTimeout3]

// 第 2 轮微任务：执行 Promise2
console.log('7'); // 输出: 7
// 执行栈: []
// 微任务队列: []
// 宏任务队列: [setTimeout1, setTimeout2, setTimeout3]

// ===== 微任务队列清空 =====

// 第 1 个宏任务：setTimeout1
console.log('2'); // 输出: 2
Promise.resolve().then(() => {
  console.log('3');
});
// 执行栈: []
// 微任务队列: [Promise3]
// 宏任务队列: [setTimeout2, setTimeout3]

// 微任务：执行 Promise3
console.log('3'); // 输出: 3
// 执行栈: []
// 微任务队列: []
// 宏任务队列: [setTimeout2, setTimeout3]

// 第 2 个宏任务：setTimeout2
console.log('8'); // 输出: 8
Promise.resolve().then(() => {
  console.log('9');
});
// 执行栈: []
// 微任务队列: [Promise4]
// 宏任务队列: [setTimeout3]

// 微任务：执行 Promise4
console.log('9'); // 输出: 9
// 执行栈: []
// 微任务队列: []
// 宏任务队列: [setTimeout3]

// 第 3 个宏任务：setTimeout3
console.log('5'); // 输出: 5
// 执行栈: []
// 微任务队列: []
// 宏任务队列: []

// 最终输出顺序：1, 6, 10, 4, 7, 2, 3, 8, 9, 5
```

"看明白了吗？" 老李问，"关键点有三个：
1. Promise 的 executor 是同步执行的，所以 6 先输出
2. 微任务在每个宏任务之间全部执行，所以 4 和 7 在 2 之前
3. 在微任务中创建的宏任务会排在已有宏任务之后，所以 5 最后输出"

## 微任务与宏任务的区别

老李展示了更清晰的对比：

```javascript
// 示例 1: 微任务的批量执行
console.log('开始');

Promise.resolve().then(() => {
  console.log('微任务 1');
  Promise.resolve().then(() => {
    console.log('微任务 1.1');
  });
});

Promise.resolve().then(() => {
  console.log('微任务 2');
  Promise.resolve().then(() => {
    console.log('微任务 2.1');
  });
});

setTimeout(() => {
  console.log('宏任务 1');
}, 0);

console.log('结束');

// 输出顺序：
// 开始
// 结束
// 微任务 1
// 微任务 2
// 微任务 1.1
// 微任务 2.1
// 宏任务 1

// 分析：
// 1. 同步代码：开始、结束
// 2. 微任务队列：[微任务1, 微任务2]
// 3. 执行微任务1，产生微任务1.1
// 4. 执行微任务2，产生微任务2.1
// 5. 执行微任务1.1
// 6. 执行微任务2.1
// 7. 微任务队列清空，执行宏任务1
```

```javascript
// 示例 2: 宏任务的单个执行
console.log('开始');

setTimeout(() => {
  console.log('宏任务 1');
  setTimeout(() => {
    console.log('宏任务 1.1');
  }, 0);
}, 0);

setTimeout(() => {
  console.log('宏任务 2');
  setTimeout(() => {
    console.log('宏任务 2.1');
  }, 0);
}, 0);

Promise.resolve().then(() => {
  console.log('微任务 1');
});

console.log('结束');

// 输出顺序：
// 开始
// 结束
// 微任务 1
// 宏任务 1
// 宏任务 2
// 宏任务 1.1
// 宏任务 2.1

// 分析：
// 1. 同步代码：开始、结束
// 2. 微任务队列：[微任务1]
// 3. 执行微任务1，队列清空
// 4. 执行宏任务1，产生宏任务1.1（加入队列末尾）
// 5. 执行宏任务2，产生宏任务2.1（加入队列末尾）
// 6. 执行宏任务1.1
// 7. 执行宏任务2.1
```

## async/await 的事件循环行为

老李展示了 async/await 在事件循环中的表现：

```javascript
console.log('1');

async function async1() {
  console.log('2');
  await async2();
  console.log('3'); // await 后面的代码相当于 .then 回调
}

async function async2() {
  console.log('4');
}

async1();

new Promise((resolve) => {
  console.log('5');
  resolve();
}).then(() => {
  console.log('6');
});

console.log('7');

// 输出顺序：1, 2, 4, 5, 7, 3, 6

// 分析：
// 1. 输出 1（同步）
// 2. 调用 async1，输出 2（同步）
// 3. 调用 async2，输出 4（同步）
// 4. await async2() 相当于 Promise.resolve(async2()).then(...)
//    所以 console.log('3') 被加入微任务队列
// 5. Promise executor 同步执行，输出 5
// 6. then 回调加入微任务队列
// 7. 输出 7（同步）
// 8. 执行栈清空，执行微任务
// 9. 输出 3（第一个微任务）
// 10. 输出 6（第二个微任务）
```

老李强调："await 后面的代码会被转换成微任务。理解这一点是掌握 async/await 执行顺序的关键。"

```javascript
// 等价转换示例

// 写法 1: async/await
async function foo() {
  console.log('A');
  await bar();
  console.log('B');
}

// 等价写法 2: Promise
function foo() {
  console.log('A');
  return Promise.resolve(bar()).then(() => {
    console.log('B');
  });
}

// 两者完全等价，输出顺序相同
```

## requestAnimationFrame 的时机

老李展示了 requestAnimationFrame 在事件循环中的位置：

```javascript
console.log('1');

setTimeout(() => {
  console.log('2');
}, 0);

requestAnimationFrame(() => {
  console.log('3');
});

Promise.resolve().then(() => {
  console.log('4');
});

console.log('5');

// 输出顺序：1, 5, 4, 3, 2

// 浏览器的完整事件循环顺序：
// 1. 执行同步代码
// 2. 执行所有微任务
// 3. 浏览器渲染（包括 requestAnimationFrame）
// 4. 执行一个宏任务
// 5. 重复 2-4

// 所以 requestAnimationFrame 在微任务之后、宏任务之前执行
```

老李画出了完整的浏览器事件循环流程：

```
┌─────────────────────────────────────────┐
│         1. 执行同步代码                    │
│         （执行栈清空）                     │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│         2. 执行所有微任务                  │
│         • Promise.then/catch/finally    │
│         • MutationObserver              │
│         • queueMicrotask                │
│         （清空微任务队列）                 │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│         3. 浏览器渲染（如果需要）           │
│         • 计算样式                        │
│         • 布局                           │
│         • 绘制                           │
│         • requestAnimationFrame         │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│         4. 执行一个宏任务                  │
│         • setTimeout/setInterval        │
│         • I/O 回调                       │
│         • UI 事件回调                     │
└─────────────────────────────────────────┘
                ↓
            返回步骤 2
```

## 实战：防抖与节流的事件循环优化

老李展示了如何利用事件循环优化防抖和节流：

```javascript
// 方案 1: 使用 setTimeout 的防抖（宏任务）
function debounce(fn, delay) {
  let timer = null;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => {
      fn.apply(this, args);
    }, delay);
  };
}

// 方案 2: 使用 Promise 的防抖（微任务）
function microtaskDebounce(fn) {
  let pending = false;
  return function (...args) {
    if (pending) return;
    pending = true;

    Promise.resolve().then(() => {
      pending = false;
      fn.apply(this, args);
    });
  };
}

// 对比测试
const input = document.querySelector('input');

// setTimeout 防抖：延迟到宏任务
const handleInputDebounced = debounce((e) => {
  console.log('处理输入:', e.target.value);
}, 300);

input.addEventListener('input', handleInputDebounced);

// 微任务防抖：在当前宏任务后立即执行
const handleInputMicrotask = microtaskDebounce((e) => {
  console.log('微任务处理:', e.target.value);
});

input.addEventListener('input', handleInputMicrotask);

// 区别：
// - setTimeout 防抖：延迟 300ms，在下一个宏任务执行
// - 微任务防抖：在当前事件循环的微任务阶段执行，几乎立即响应
```

## 任务优先级的实际应用

老李展示了如何利用任务优先级优化性能：

```javascript
// 场景：大量 DOM 更新操作
class BatchDOMUpdater {
  constructor() {
    this.updates = [];
    this.scheduled = false;
  }

  // 方法 1: 使用微任务批处理（最快响应）
  scheduleMicrotask(update) {
    this.updates.push(update);

    if (!this.scheduled) {
      this.scheduled = true;
      queueMicrotask(() => {
        this.flush();
      });
    }
  }

  // 方法 2: 使用 requestAnimationFrame（最流畅）
  scheduleFrame(update) {
    this.updates.push(update);

    if (!this.scheduled) {
      this.scheduled = true;
      requestAnimationFrame(() => {
        this.flush();
      });
    }
  }

  // 方法 3: 使用 setTimeout（降低优先级）
  scheduleDeferred(update) {
    this.updates.push(update);

    if (!this.scheduled) {
      this.scheduled = true;
      setTimeout(() => {
        this.flush();
      }, 0);
    }
  }

  flush() {
    console.log('批量执行', this.updates.length, '个更新');
    this.updates.forEach(update => update());
    this.updates = [];
    this.scheduled = false;
  }
}

// 使用示例
const updater = new BatchDOMUpdater();

// 场景 1: 紧急更新（用户交互反馈）
button.addEventListener('click', () => {
  updater.scheduleMicrotask(() => {
    button.classList.add('active');
  });
});

// 场景 2: 动画更新（流畅度优先）
updater.scheduleFrame(() => {
  element.style.transform = `translateX(${x}px)`;
});

// 场景 3: 低优先级更新（后台统计）
updater.scheduleDeferred(() => {
  trackEvent('page_view');
});
```

## 常见陷阱与解决方案

老李总结了几个常见陷阱：

```javascript
// 陷阱 1: 在微任务中产生无限微任务
function badMicrotask() {
  Promise.resolve().then(() => {
    console.log('执行微任务');
    badMicrotask(); // ❌ 创建新的微任务
  });
}

// badMicrotask(); // 会阻塞事件循环，页面卡死

// 解决方案：使用宏任务分散压力
function goodMicrotask() {
  setTimeout(() => { // ✅ 使用 setTimeout 让出控制权
    console.log('执行宏任务');
    goodMicrotask();
  }, 0);
}

// 陷阱 2: 混淆 setTimeout 的执行顺序
setTimeout(() => {
  console.log('A');
}, 0);

setTimeout(() => {
  console.log('B');
}, 0);

// ✅ 输出: A, B（按添加顺序执行）
// 宏任务队列: [A, B]

// 陷阱 3: Promise 的 executor 同步执行
console.log('1');

new Promise((resolve) => {
  console.log('2'); // ✅ 同步执行
  resolve();
}).then(() => {
  console.log('3'); // ❌ 异步执行（微任务）
});

console.log('4');

// 输出: 1, 2, 4, 3

// 陷阱 4: await 的多次使用
async function test() {
  console.log('A');
  await Promise.resolve();
  console.log('B');
  await Promise.resolve();
  console.log('C');
}

test();
console.log('D');

// 输出: A, D, B, C
// 分析：
// - A 同步执行
// - 第一个 await 后，B 进入微任务队列
// - D 同步执行
// - 执行微任务 B
// - 第二个 await 后，C 进入微任务队列
// - 执行微任务 C
```

## 完整的执行顺序练习

老李给出了一道综合练习题：

```javascript
console.log('script start');

async function async1() {
  await async2();
  console.log('async1 end');
}

async function async2() {
  console.log('async2 end');
}

async1();

setTimeout(() => {
  console.log('setTimeout');
}, 0);

new Promise((resolve) => {
  console.log('Promise');
  resolve();
})
  .then(() => {
    console.log('promise1');
  })
  .then(() => {
    console.log('promise2');
  });

console.log('script end');

// 正确答案：
// script start
// async2 end
// Promise
// script end
// async1 end
// promise1
// promise2
// setTimeout

// 详细分析：
// 1. 同步代码：
//    - script start
//    - 调用 async1() → 调用 async2() → async2 end
//    - Promise executor 同步执行 → Promise
//    - script end

// 2. 微任务队列：[async1 end, promise1]
//    - 执行 async1 end
//    - 执行 promise1，产生 promise2 微任务
//    - 执行 promise2

// 3. 宏任务队列：[setTimeout]
//    - 执行 setTimeout
```

下午 6 点，老李的讲解结束了。你终于对事件循环有了系统的理解。这不仅仅是一个异步执行的机制，而是浏览器调度所有任务的核心引擎。你在笔记本上记下了核心要点，准备在下周的技术分享会上讲给团队其他成员听。

---

## 知识档案：事件循环完整机制

**规则 1: 事件循环的执行顺序**

浏览器事件循环按照"同步代码 → 微任务 → 宏任务"的顺序循环执行，每个宏任务执行完后会清空所有微任务。

```javascript
// 事件循环的执行流程：
// 1. 执行当前宏任务（第一次是全局脚本）
// 2. 执行栈清空后，执行所有微任务（清空微任务队列）
// 3. 浏览器渲染（如果需要）
// 4. 取下一个宏任务执行
// 5. 重复步骤 2-4

console.log('1'); // 同步代码

setTimeout(() => {
  console.log('2'); // 宏任务
}, 0);

Promise.resolve().then(() => {
  console.log('3'); // 微任务
});

console.log('4'); // 同步代码

// 输出顺序：1, 4, 3, 2

// 队列状态演变：
// 初始：执行栈[全局代码], 微任务[], 宏任务[]
// 同步代码执行完：执行栈[], 微任务[Promise], 宏任务[setTimeout]
// 微任务阶段：输出 3, 执行栈[], 微任务[], 宏任务[setTimeout]
// 宏任务阶段：输出 2, 执行栈[], 微任务[], 宏任务[]
```

**规则 2: 微任务会清空整个队列**

微任务阶段会清空所有微任务，包括执行过程中新产生的微任务。宏任务每次只执行一个。

```javascript
// 微任务的批量执行特性

Promise.resolve().then(() => {
  console.log('微任务 1');
  Promise.resolve().then(() => {
    console.log('微任务 1.1'); // 在当前微任务阶段执行
  });
});

Promise.resolve().then(() => {
  console.log('微任务 2');
});

setTimeout(() => {
  console.log('宏任务 1');
}, 0);

// 输出顺序：微任务 1, 微任务 2, 微任务 1.1, 宏任务 1

// 关键：微任务 1.1 在本轮微任务阶段执行，不会等到下一轮

// 对比：宏任务的单个执行特性

setTimeout(() => {
  console.log('宏任务 1');
  setTimeout(() => {
    console.log('宏任务 1.1'); // 排在宏任务 2 之后
  }, 0);
}, 0);

setTimeout(() => {
  console.log('宏任务 2');
}, 0);

// 输出顺序：宏任务 1, 宏任务 2, 宏任务 1.1

// 关键：宏任务 1.1 被加入队列末尾，等待宏任务 2 执行完
```

**规则 3: Promise executor 同步执行**

Promise 的 executor 函数（传给 `new Promise` 的函数）是同步执行的，只有 then/catch/finally 回调是异步的（微任务）。

```javascript
console.log('1');

new Promise((resolve) => {
  console.log('2'); // ✅ 同步执行
  resolve();
}).then(() => {
  console.log('3'); // ❌ 异步执行（微任务）
});

console.log('4');

// 输出顺序：1, 2, 4, 3

// 常见错误理解：
// ❌ 认为整个 Promise 都是异步的
// ✅ 只有 then/catch/finally 回调是异步的

// 实际应用：
function fetchDataSync() {
  return new Promise((resolve) => {
    console.log('开始获取数据'); // 立即执行
    const data = getDataFromCache(); // 同步操作
    resolve(data);
  });
}

fetchDataSync().then(data => {
  console.log('处理数据'); // 微任务
});

console.log('后续代码'); // 先于 "处理数据" 输出
```

**规则 4: await 后面的代码相当于 then 回调**

`await` 关键字会将后续代码转换为微任务，相当于在 `.then()` 回调中执行。

```javascript
// 写法 1: async/await
async function foo() {
  console.log('A');
  await bar();
  console.log('B'); // 相当于 then 回调
}

// 写法 2: Promise（等价）
function foo() {
  console.log('A');
  return Promise.resolve(bar()).then(() => {
    console.log('B');
  });
}

// 两者完全等价

// 实际执行顺序：
async function test() {
  console.log('1');
  await Promise.resolve();
  console.log('2');
}

test();
console.log('3');

// 输出：1, 3, 2

// 分析：
// - console.log('1') 同步执行
// - await 将 console.log('2') 转为微任务
// - console.log('3') 同步执行
// - 执行微任务 console.log('2')

// 多个 await 的情况：
async function multi() {
  console.log('A');
  await Promise.resolve();
  console.log('B');
  await Promise.resolve();
  console.log('C');
}

multi();
console.log('D');

// 输出：A, D, B, C

// 分析：
// - A 同步
// - D 同步
// - B 第一个微任务
// - C 第二个微任务
```

**规则 5: requestAnimationFrame 在渲染阶段执行**

`requestAnimationFrame` 在微任务之后、宏任务之前的渲染阶段执行，适合动画更新。

```javascript
console.log('1');

setTimeout(() => {
  console.log('2'); // 宏任务
}, 0);

requestAnimationFrame(() => {
  console.log('3'); // 渲染阶段
});

Promise.resolve().then(() => {
  console.log('4'); // 微任务
});

console.log('5');

// 输出顺序：1, 5, 4, 3, 2

// 完整的事件循环顺序：
// 1. 执行同步代码（输出 1, 5）
// 2. 执行所有微任务（输出 4）
// 3. 浏览器渲染（输出 3，requestAnimationFrame）
// 4. 执行一个宏任务（输出 2）

// requestAnimationFrame 的特点：
// - 在浏览器重绘之前执行
// - 帧率匹配显示器刷新率（通常 60fps）
// - 适合流畅的动画更新

// 对比：setTimeout 的动画（性能差）
function animateWithSetTimeout() {
  element.style.left = position + 'px';
  position += 1;
  setTimeout(animateWithSetTimeout, 16); // 约 60fps
}

// ✅ requestAnimationFrame 的动画（性能好）
function animateWithRAF() {
  element.style.left = position + 'px';
  position += 1;
  requestAnimationFrame(animateWithRAF);
}
```

**规则 6: 利用任务优先级优化性能**

根据任务的优先级选择合适的调度方式：紧急反馈用微任务，流畅动画用 requestAnimationFrame，低优先级用 setTimeout。

```javascript
// 优先级层级：
// 1. 同步代码（最高优先级）
// 2. 微任务（高优先级，快速响应）
// 3. requestAnimationFrame（中高优先级，流畅动画）
// 4. 宏任务（普通优先级，避免阻塞）

class TaskScheduler {
  // 高优先级：用户交互反馈（微任务）
  scheduleHighPriority(task) {
    queueMicrotask(() => {
      task();
    });
  }

  // 中优先级：动画更新（requestAnimationFrame）
  scheduleAnimation(task) {
    requestAnimationFrame(() => {
      task();
    });
  }

  // 低优先级：后台任务（宏任务）
  scheduleLowPriority(task) {
    setTimeout(() => {
      task();
    }, 0);
  }

  // 闲时任务：requestIdleCallback（最低优先级）
  scheduleIdle(task) {
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => {
        task();
      });
    } else {
      setTimeout(() => {
        task();
      }, 1000);
    }
  }
}

// 实际应用示例
const scheduler = new TaskScheduler();

// 场景 1: 按钮点击反馈（紧急）
button.addEventListener('click', () => {
  scheduler.scheduleHighPriority(() => {
    button.classList.add('active');
    showToast('操作成功');
  });
});

// 场景 2: 动画更新（流畅）
function animate() {
  scheduler.scheduleAnimation(() => {
    element.style.transform = `translateX(${x}px)`;
    x += 1;
    if (x < 100) animate();
  });
}

// 场景 3: 数据统计（不紧急）
scheduler.scheduleLowPriority(() => {
  sendAnalytics({
    event: 'page_view',
    timestamp: Date.now()
  });
});

// 场景 4: 预加载资源（最低优先级）
scheduler.scheduleIdle(() => {
  preloadImages(['/img1.jpg', '/img2.jpg']);
});
```

---

**记录者注**:

事件循环是 JavaScript 运行时的核心机制，负责调度同步代码、微任务和宏任务的执行。理解事件循环是掌握异步编程的基础，也是排查异步执行顺序问题的关键。

核心规则是：同步代码在调用栈中立即执行，执行栈清空后执行所有微任务（清空微任务队列），然后执行一个宏任务，再次清空微任务队列，如此循环。Promise 的 executor 同步执行，then 回调是微任务；await 后面的代码相当于 then 回调；requestAnimationFrame 在渲染阶段执行，介于微任务和宏任务之间。

实际应用中，可以利用任务优先级优化性能：紧急的用户反馈用微任务（queueMicrotask），流畅的动画用 requestAnimationFrame，低优先级的后台任务用 setTimeout。避免在微任务中创建无限微任务导致页面卡死，必要时用 setTimeout 让出控制权。

记住：**同步代码 → 微任务（清空） → 渲染 → 宏任务（单个） → 重复；Promise executor 同步，then 异步；await 后相当于 then；requestAnimationFrame 在渲染阶段；根据优先级选择调度方式**。深入理解事件循环是成为高级前端开发者的必经之路。
