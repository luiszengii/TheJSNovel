《第74次记录：定时器调度 —— 时间在JavaScript中的漂移》

---

## 计时偏差

周三下午三点，产品经理小刘走到你的工位前，脸色不太好看：

"上周上线的倒计时功能有问题，用户反馈说计时不准。有人录了视频对比，跑了10分钟的倒计时，实际只过了9分52秒，偏差了8秒。"

"8秒？"你有些吃惊，"倒计时功能我写得很简单啊，就是个`setInterval`每秒减一，应该不会出问题吧？"

"你自己看看吧。"小刘把平板递过来，播放了用户录制的对比视频。屏幕一分为二，左边是你的网页倒计时，右边是手机秒表，两个同时启动。

刚开始还挺同步，但随着时间推移，差距越来越明显。10分钟后，网页显示"9:52"，手机秒表显示"10:00"。

"确实偏差了8秒..."你皱起眉头，立刻打开代码：

```javascript
// countdown.js - 倒计时功能
class Countdown {
    constructor(duration) {
        this.duration = duration; // 总时长（秒）
        this.remaining = duration;
        this.intervalId = null;
    }

    start() {
        this.intervalId = setInterval(() => {
            this.remaining--;

            // 更新UI
            this.updateDisplay(this.remaining);

            if (this.remaining <= 0) {
                this.stop();
                this.onFinish();
            }
        }, 1000); // 每1000毫秒执行一次
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    updateDisplay(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        document.getElementById('countdown').textContent =
            `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    onFinish() {
        alert('倒计时结束！');
    }
}

// 使用
const countdown = new Countdown(600); // 10分钟倒计时
countdown.start();
```

"代码看起来没问题啊..."你自言自语，"每1000ms减一，理论上应该是准确的。"

后端同事老张走过来："`setInterval`不是精确的定时器，每次执行都可能有偏差，累积起来就很明显了。"

"偏差？为什么会有偏差？"你疑惑地问。

"因为JavaScript是单线程的，定时器只能保证'最早在指定时间后执行'，不能保证'精确在指定时间执行'。"老张解释道，"如果主线程在忙，定时器回调就会延迟。"

"那怎么解决？"你问。

"改用`setTimeout`递归调用，并且根据实际经过的时间来修正偏差。"老张说，"我给你演示一下。"

---

## 精度测试

下午三点半，老张在你的编辑器里新建了一个测试文件：

```javascript
// 测试1: setInterval的累积偏差
let count = 0;
const startTime = Date.now();

const intervalId = setInterval(() => {
    count++;
    const elapsed = Date.now() - startTime;
    const expected = count * 1000; // 期望经过的时间
    const drift = elapsed - expected; // 实际偏差

    console.log(`第${count}次 | 期望:${expected}ms | 实际:${elapsed}ms | 偏差:${drift}ms`);

    if (count >= 10) {
        clearInterval(intervalId);
        console.log(`总偏差: ${drift}ms`);
    }
}, 1000);
```

运行结果让你吃惊：

```
第1次 | 期望:1000ms | 实际:1002ms | 偏差:2ms
第2次 | 期望:2000ms | 实际:2005ms | 偏差:5ms
第3次 | 期望:3000ms | 实际:3008ms | 偏差:8ms
第4次 | 期望:4000ms | 实际:4013ms | 偏差:13ms
第5次 | 期望:5000ms | 实际:5017ms | 偏差:17ms
第6次 | 期望:6000ms | 实际:6023ms | 偏差:23ms
第7次 | 期望:7000ms | 实际:7028ms | 偏差:28ms
第8次 | 期望:8000ms | 实际:8034ms | 偏差:34ms
第9次 | 期望:9000ms | 实际:9041ms | 偏差:41ms
第10次 | 期望:10000ms | 实际:10047ms | 偏差:47ms
总偏差: 47ms
```

"看，只跑了10秒，就已经偏差了47毫秒。"老张指着控制台，"偏差是累积的，时间越长越明显。你的倒计时跑10分钟，偏差8秒完全正常。"

"为什么会累积？"你不解。

"因为`setInterval`不会考虑上一次回调的执行时间，"老张画了个图：

```
理想情况:
|--1000ms--|--1000ms--|--1000ms--|
0          1000       2000       3000

实际情况:
|--1002ms--|--1003ms--|--1005ms--|
0          1002       2005       3010
            ↑          ↑          ↑
          偏差2ms    偏差5ms    偏差10ms (累积)
```

"每次偏差几毫秒，累积起来就很可观了。"老张说，"而且如果主线程被阻塞，偏差会更大。"

你写了个测试验证主线程阻塞的影响：

```javascript
// 测试2: 主线程阻塞导致的偏差
let count = 0;
const startTime = Date.now();

const intervalId = setInterval(() => {
    count++;
    const elapsed = Date.now() - startTime;

    console.log(`第${count}次 | 实际:${elapsed}ms`);

    // 模拟主线程被阻塞100ms
    const blockStart = Date.now();
    while (Date.now() - blockStart < 100) {
        // 空循环，阻塞主线程
    }

    if (count >= 5) {
        clearInterval(intervalId);
    }
}, 1000);
```

结果更糟：

```
第1次 | 实际:1002ms
第2次 | 实际:2104ms  ← 偏差104ms
第3次 | 实际:3207ms  ← 偏差207ms
第4次 | 实际:4311ms  ← 偏差311ms
第5次 | 实际:5414ms  ← 偏差414ms
```

"因为阻塞，每次延迟了100ms，累积起来偏差超过400ms。"老张解释道。

---

## 定时器原理

下午四点，老张给你讲解了JavaScript定时器的工作原理：

**原理1: 事件循环和任务队列**

```javascript
// JavaScript是单线程的，定时器通过事件循环调度

// 1. 注册定时器
setTimeout(() => {
    console.log('定时器回调');
}, 1000);

// 2. 浏览器在1000ms后把回调放入任务队列
// 3. 事件循环从任务队列取出回调执行

console.log('同步代码'); // 先执行同步代码

// 输出顺序:
// '同步代码'
// '定时器回调' (1000ms后)
```

**原理2: 最小延迟限制**

```javascript
// 浏览器对setTimeout/setInterval有最小延迟限制

// HTML5标准: 嵌套5层以上，最小延迟4ms
setTimeout(() => {
    setTimeout(() => {
        setTimeout(() => {
            setTimeout(() => {
                setTimeout(() => {
                    setTimeout(() => {
                        console.log('第6次嵌套，强制延迟4ms');
                    }, 0); // 即使设置0ms，也会延迟4ms
                }, 0);
            }, 0);
        }, 0);
    }, 0);
}, 0);

// 未激活标签页: 最小延迟1000ms
// 浏览器为了省电，会限制后台标签的定时器
```

**原理3: setTimeout vs setInterval**

```javascript
// setTimeout - 回调执行完后才调度下一次
function recursiveTimeout() {
    console.log('执行');

    setTimeout(recursiveTimeout, 1000);
}

recursiveTimeout();

// 时间线:
// 执行 → 等1000ms → 执行 → 等1000ms → ...


// setInterval - 不管回调是否执行完，都会调度
let count = 0;
setInterval(() => {
    console.log('开始执行', count++);

    // 模拟耗时操作500ms
    const start = Date.now();
    while (Date.now() - start < 500) {}

    console.log('执行完成');
}, 1000);

// 时间线:
// 0ms:    调度第1次
// 500ms:  第1次执行完成
// 1000ms: 调度第2次（立即执行，因为上一次已完成）
// 1500ms: 第2次执行完成
// 2000ms: 调度第3次
// ...

// 如果回调耗时超过间隔，会立即执行下一次
```

"明白了，"你说，"所以`setInterval`不会等回调执行完，而`setTimeout`递归可以保证间隔。"

"对，"老张点头，"而且`setTimeout`递归可以根据实际执行时间动态调整下一次的延迟，修正累积偏差。"

---

## 精确实现

下午五点，你开始重构倒计时功能，实现精确计时：

**方案1: setTimeout递归 + 误差修正**

```javascript
class AccurateCountdown {
    constructor(duration) {
        this.duration = duration * 1000; // 转为毫秒
        this.startTime = null;
        this.timeoutId = null;
        this.paused = false;
        this.pausedTime = 0;
    }

    start() {
        if (this.paused) {
            // 从暂停恢复
            this.startTime += Date.now() - this.pausedTime;
            this.paused = false;
        } else {
            // 首次启动
            this.startTime = Date.now();
        }

        this.tick();
    }

    tick() {
        if (this.paused) return;

        // 计算实际经过的时间
        const elapsed = Date.now() - this.startTime;
        const remaining = this.duration - elapsed;

        if (remaining <= 0) {
            // 倒计时结束
            this.updateDisplay(0);
            this.onFinish();
            return;
        }

        // 更新显示
        this.updateDisplay(Math.ceil(remaining / 1000));

        // 计算下一次调用的延迟
        // 目标是在下一秒的整数秒处执行
        const nextTick = Math.ceil(remaining / 1000) * 1000;
        const delay = nextTick - remaining;

        // 递归调用setTimeout
        this.timeoutId = setTimeout(() => this.tick(), delay);
    }

    pause() {
        if (!this.paused) {
            this.paused = true;
            this.pausedTime = Date.now();
            if (this.timeoutId) {
                clearTimeout(this.timeoutId);
                this.timeoutId = null;
            }
        }
    }

    stop() {
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }
        this.paused = false;
    }

    updateDisplay(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        document.getElementById('countdown').textContent =
            `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    onFinish() {
        alert('倒计时结束！');
    }
}

// 使用
const countdown = new AccurateCountdown(600); // 10分钟
countdown.start();
```

**方案2: requestAnimationFrame (用于高频更新)**

```javascript
// 对于需要平滑动画的场景，使用requestAnimationFrame
class AnimatedCountdown {
    constructor(duration) {
        this.duration = duration * 1000;
        this.startTime = null;
        this.rafId = null;
    }

    start() {
        this.startTime = performance.now();
        this.animate();
    }

    animate() {
        const now = performance.now();
        const elapsed = now - this.startTime;
        const remaining = this.duration - elapsed;

        if (remaining <= 0) {
            this.updateDisplay(0);
            this.onFinish();
            return;
        }

        // 更新显示（可以精确到毫秒）
        this.updateDisplay(remaining / 1000);

        // 请求下一帧
        this.rafId = requestAnimationFrame(() => this.animate());
    }

    stop() {
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
    }

    updateDisplay(seconds) {
        // 可以显示小数
        document.getElementById('countdown').textContent =
            seconds.toFixed(2) + 's';
    }

    onFinish() {
        console.log('倒计时结束');
    }
}
```

**方案3: Web Worker (避免主线程阻塞)**

```javascript
// worker.js
let startTime = null;
let duration = null;
let intervalId = null;

self.onmessage = function(e) {
    if (e.data.type === 'start') {
        duration = e.data.duration * 1000;
        startTime = Date.now();

        intervalId = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const remaining = duration - elapsed;

            if (remaining <= 0) {
                clearInterval(intervalId);
                self.postMessage({ type: 'finish' });
            } else {
                self.postMessage({
                    type: 'tick',
                    remaining: Math.ceil(remaining / 1000)
                });
            }
        }, 100); // 每100ms检查一次，主线程不会被阻塞
    } else if (e.data.type === 'stop') {
        if (intervalId) {
            clearInterval(intervalId);
            intervalId = null;
        }
    }
};

// main.js
class WorkerCountdown {
    constructor(duration) {
        this.duration = duration;
        this.worker = new Worker('worker.js');

        this.worker.onmessage = (e) => {
            if (e.data.type === 'tick') {
                this.updateDisplay(e.data.remaining);
            } else if (e.data.type === 'finish') {
                this.onFinish();
            }
        };
    }

    start() {
        this.worker.postMessage({
            type: 'start',
            duration: this.duration
        });
    }

    stop() {
        this.worker.postMessage({ type: 'stop' });
    }

    updateDisplay(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        document.getElementById('countdown').textContent =
            `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    onFinish() {
        alert('倒计时结束！');
    }
}
```

下午六点，你部署了新的倒计时实现，并做了24小时测试：

```javascript
// 精度测试
const testCountdown = new AccurateCountdown(3600); // 1小时
testCountdown.start();

// 1小时后检查
setTimeout(() => {
    const actualTime = Date.now() - testCountdown.startTime;
    const error = Math.abs(actualTime - 3600000);
    console.log(`偏差: ${error}ms`); // 偏差: < 50ms
}, 3600000);
```

"偏差控制在50毫秒以内，完美！"你满意地看着测试结果。

---

## 定时器知识

晚上八点，你整理了关于JavaScript定时器的核心知识：

**规则 1: setTimeout基础**

`setTimeout`在指定延迟后执行回调一次：

```javascript
// 基本用法
const timeoutId = setTimeout(() => {
    console.log('1秒后执行');
}, 1000);

// 取消定时器
clearTimeout(timeoutId);

// 传递参数
setTimeout((name, age) => {
    console.log(`Hello, ${name}! You are ${age}.`);
}, 1000, 'Alice', 25);

// this绑定
const obj = {
    name: 'Alice',
    greet() {
        console.log(`Hello, ${this.name}`);
    }
};

// ✗ 错误：this丢失
setTimeout(obj.greet, 1000); // Hello, undefined

// ✓ 正确：绑定this
setTimeout(() => obj.greet(), 1000); // Hello, Alice
setTimeout(obj.greet.bind(obj), 1000); // Hello, Alice
```

**延迟为0的setTimeout**:

```javascript
console.log('1');

setTimeout(() => {
    console.log('3');
}, 0);

console.log('2');

// 输出: 1 2 3
// 即使延迟0ms，回调也会在所有同步代码执行完后才执行
```

---

**规则 2: setInterval基础**

`setInterval`以固定间隔重复执行回调：

```javascript
// 基本用法
let count = 0;
const intervalId = setInterval(() => {
    console.log(++count);
    if (count >= 5) {
        clearInterval(intervalId); // 停止
    }
}, 1000);

// 问题：不考虑回调执行时间
setInterval(() => {
    // 如果这个函数执行超过1000ms，下一次会立即执行
    heavyComputation();
}, 1000);
```

**setInterval的陷阱**:

```javascript
// 陷阱1: 回调执行时间过长
let count = 0;
setInterval(() => {
    console.log('开始', Date.now());

    // 模拟耗时2秒
    const start = Date.now();
    while (Date.now() - start < 2000) {}

    console.log('结束', Date.now());
}, 1000);

// 输出:
// 开始 0ms
// 结束 2000ms
// 开始 2000ms (立即执行，没有等待1000ms)
// 结束 4000ms
// ...


// 陷阱2: 队列堆积
let processing = false;

setInterval(() => {
    if (processing) {
        console.warn('上一次还未完成，跳过本次执行');
        return;
    }

    processing = true;
    heavyTask().then(() => {
        processing = false;
    });
}, 1000);
```

---

**规则 3: setTimeout递归 vs setInterval**

```javascript
// setInterval: 固定间隔调度（不推荐）
setInterval(() => {
    console.log('执行');
}, 1000);

// setTimeout递归: 灵活调度（推荐）
function recursiveTimeout() {
    console.log('执行');

    setTimeout(recursiveTimeout, 1000);
}

recursiveTimeout();


// 精确计时：修正累积误差
function accurateInterval(callback, interval) {
    let expected = Date.now() + interval;

    function step() {
        const drift = Date.now() - expected;

        callback();

        expected += interval;
        setTimeout(step, Math.max(0, interval - drift));
    }

    setTimeout(step, interval);
}

accurateInterval(() => {
    console.log('精确执行');
}, 1000);
```

---

**规则 4: requestAnimationFrame**

`requestAnimationFrame`用于平滑动画，浏览器优化的帧率控制：

```javascript
// 基本用法
function animate() {
    // 更新动画
    updatePosition();

    // 请求下一帧
    requestAnimationFrame(animate);
}

animate();

// 带停止条件
let rafId;

function animate() {
    updatePosition();

    if (shouldContinue) {
        rafId = requestAnimationFrame(animate);
    }
}

animate();

// 取消动画
cancelAnimationFrame(rafId);


// 时间戳参数
function animate(timestamp) {
    console.log('当前时间:', timestamp); // 高精度时间戳(DOMHighResTimeStamp)

    requestAnimationFrame(animate);
}

animate();


// 实际应用：平滑动画
let start = null;

function animate(timestamp) {
    if (!start) start = timestamp;

    const progress = timestamp - start;
    const element = document.getElementById('box');

    // 在1秒内从0移动到300px
    element.style.left = Math.min(progress / 3, 300) + 'px';

    if (progress < 1000) {
        requestAnimationFrame(animate);
    }
}

requestAnimationFrame(animate);
```

**rAF vs setTimeout**:

```javascript
// setTimeout: 可能掉帧或浪费性能
setInterval(() => {
    updateAnimation(); // 可能在非重绘时执行
}, 16); // 60fps ≈ 16.67ms

// requestAnimationFrame: 浏览器优化的帧率
function animate() {
    updateAnimation(); // 保证在重绘前执行
    requestAnimationFrame(animate);
}

animate();
```

---

**规则 5: 定时器精度和限制**

**浏览器限制**:

```javascript
// 1. 最小延迟
// 现代浏览器: 4ms (嵌套5层以上)
// 历史浏览器: 10ms

// 2. 未激活标签页
// Chrome/Firefox: 最小1000ms
// 用于省电和减少资源消耗

// 测试未激活标签页的限制
let count = 0;
setInterval(() => {
    console.log(`第${++count}次执行`, Date.now());
    // 切换到其他标签页后，间隔会变成1000ms
}, 100);


// 3. 最大延迟
// 32位系统: 最大约24.8天 (2^31 - 1 毫秒)
// 超过会立即执行

setTimeout(() => {
    console.log('永远不会执行');
}, 2147483648); // 超过最大值，立即执行
```

**高精度计时**:

```javascript
// performance.now() - 高精度时间
const start = performance.now();

// 执行操作
doSomething();

const end = performance.now();
console.log(`执行时间: ${(end - start).toFixed(3)}ms`);

// 精度: 微秒级 (0.001ms)
// Date.now()精度: 毫秒级


// 计算准确的时间间隔
class PreciseTimer {
    constructor(interval, callback) {
        this.interval = interval;
        this.callback = callback;
        this.expected = null;
        this.timeout = null;
    }

    start() {
        this.expected = Date.now() + this.interval;
        this.timeout = setTimeout(() => this.step(), this.interval);
    }

    step() {
        const drift = Date.now() - this.expected;

        if (drift > this.interval) {
            // 漂移超过一个周期，跳过回调避免堆积
            console.warn(`定时器漂移 ${drift}ms，跳过本次执行`);
        } else {
            this.callback();
        }

        this.expected += this.interval;
        this.timeout = setTimeout(
            () => this.step(),
            Math.max(0, this.interval - drift)
        );
    }

    stop() {
        clearTimeout(this.timeout);
    }
}

// 使用
const timer = new PreciseTimer(1000, () => {
    console.log('精确执行');
});

timer.start();
```

---

**规则 6: 定时器最佳实践**

**实践1: 清理定时器避免内存泄漏**

```javascript
// ✗ 不好：忘记清理
function startPolling() {
    setInterval(() => {
        fetchData();
    }, 5000);
} // intervalId丢失，无法清理


// ✓ 好：保存ID，及时清理
class DataPoller {
    constructor(interval) {
        this.interval = interval;
        this.intervalId = null;
    }

    start() {
        if (this.intervalId) return; // 防止重复启动

        this.intervalId = setInterval(() => {
            this.fetchData();
        }, this.interval);
    }

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    fetchData() {
        // 数据获取逻辑
    }
}

// React组件中
useEffect(() => {
    const poller = new DataPoller(5000);
    poller.start();

    return () => poller.stop(); // 组件卸载时清理
}, []);
```

**实践2: 防抖和节流**

```javascript
// 防抖(debounce): 延迟执行，重复触发会重置计时
function debounce(func, delay) {
    let timeoutId;

    return function(...args) {
        clearTimeout(timeoutId); // 清除上一次的定时器
        timeoutId = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
}

// 使用：搜索输入
const searchInput = document.getElementById('search');
searchInput.addEventListener('input', debounce((e) => {
    performSearch(e.target.value);
}, 500)); // 停止输入500ms后才执行


// 节流(throttle): 限制执行频率
function throttle(func, limit) {
    let lastRun = 0;

    return function(...args) {
        const now = Date.now();
        if (now - lastRun >= limit) {
            func.apply(this, args);
            lastRun = now;
        }
    };
}

// 使用：滚动事件
window.addEventListener('scroll', throttle(() => {
    updateScrollPosition();
}, 200)); // 每200ms最多执行一次
```

**实践3: 选择合适的定时器**

```javascript
// 场景1: 一次性延迟执行
setTimeout(() => {
    showNotification();
}, 3000);

// 场景2: 周期性任务(需要精确间隔)
function accurateInterval(callback, interval) {
    let expected = Date.now() + interval;

    function step() {
        const drift = Date.now() - expected;
        callback();
        expected += interval;
        setTimeout(step, Math.max(0, interval - drift));
    }

    setTimeout(step, interval);
}

accurateInterval(() => {
    syncData();
}, 60000); // 每分钟同步一次

// 场景3: 动画(需要平滑和性能优化)
function animate() {
    updateAnimation();
    requestAnimationFrame(animate);
}

animate();

// 场景4: 长时间运行(避免主线程阻塞)
// 使用Web Worker
const worker = new Worker('timer-worker.js');
worker.postMessage({ type: 'start', interval: 1000 });
worker.onmessage = (e) => {
    if (e.data.type === 'tick') {
        updateUI();
    }
};
```

**实践4: 错误处理**

```javascript
// 定时器回调中的错误不会被外部try-catch捕获
try {
    setTimeout(() => {
        throw new Error('错误'); // 不会被捕获
    }, 1000);
} catch (e) {
    console.log('不会执行');
}


// 正确处理错误
function safeTimeout(callback, delay) {
    return setTimeout(() => {
        try {
            callback();
        } catch (error) {
            console.error('定时器错误:', error);
            // 上报错误
            reportError(error);
        }
    }, delay);
}
```

---

周四上午，产品经理小刘测试了新的倒计时功能。运行了1小时后，只偏差了23毫秒。

"这次真的准了！"小刘竖起大拇指，"用户应该不会再投诉了。"

"定时器的精度问题很容易被忽视，"你总结道，"简单的`setInterval`在短时间内看不出问题，但长时间运行就会暴露累积偏差。使用`setTimeout`递归加上误差修正，才能实现真正精确的计时。"

技术负责人也认可了你的方案："很好的优化。以后涉及计时功能，都要考虑精度和漂移问题，选择合适的实现方式。"

---

**事故档案编号**: FUNC-2024-1874
**影响范围**: 定时器精度,累积偏差,setInterval vs setTimeout,计时准确性
**根本原因**: 使用setInterval不考虑回调执行时间和累积误差,未理解JavaScript定时器的工作原理
**修复成本**: 低(重构为setTimeout递归),中等(如需Web Worker隔离)

这是JavaScript世界第74次被记录的定时器精度事故。JavaScript定时器(`setTimeout`/`setInterval`)并非精确计时器,只能保证"最早在指定时间后执行",不能保证"精确在指定时间执行"。`setInterval`的主要问题:不考虑回调执行时间、累积误差随时间增长、可能导致队列堆积。精确计时的解决方案:`setTimeout`递归调用并根据实际时间修正误差、使用`performance.now()`获取高精度时间戳、关键场景使用`requestAnimationFrame`(动画)或Web Worker(避免主线程阻塞)。理解定时器的异步本质和浏览器限制(最小延迟4ms、未激活标签1000ms、最大延迟约24.8天),选择合适的实现方式,才能构建可靠的计时功能。

---
