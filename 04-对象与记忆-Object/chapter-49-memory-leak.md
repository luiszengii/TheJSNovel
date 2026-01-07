《第49次记录: 内存泄漏事故 —— 浏览器的缓慢死亡》

---

## 性能告警

周六上午九点半, 你还在被窝里, 手机突然响了。是运维值班电话。

"喂, 老王, 出大事了!"运维小刘的声音很急促,"监控系统报警, 好几个用户反馈实时数据看板打开半小时后浏览器就卡死了, 必须强制关闭标签页才行!"

你瞬间清醒, 翻身坐起来:"卡死? 服务端有压力吗?"

"服务端完全正常, CPU和内存都在20%以下。"小刘说,"我看了一下, 好像是前端的问题。用户说页面刚打开时很流畅, 但过一会儿就开始卡顿, 鼠标都移不动。"

"我马上看。"你挂断电话, 打开笔记本。

这个实时数据看板是你们的核心产品, 企业客户用它监控业务数据。页面会每5秒刷新一次图表, 显示最新的销售、库存、订单数据。昨天上线的新版本增加了几个图表组件, 当时测试都正常。

你打开Chrome, 访问数据看板。页面加载很快, 图表渲染也很流畅。你看了看任务管理器, 浏览器内存占用200MB, 正常。

五分钟后, 内存占用400MB。十分钟后, 800MB。十五分钟后, 1. 2GB。

"不对劲..."你盯着内存数字, 它像失控的火车头, 持续上涨。

二十分钟后, 内存占用1. 8GB, 页面开始卡顿。图表刷新明显延迟, 鼠标点击反应变慢。

二十五分钟后, 内存占用2. 1GB。你的电脑风扇开始狂转, 浏览器标签页显示"页面无响应"。

三十分钟后, Chrome标签页崩溃, 弹出"啊哦, 出错了"的页面。

你盯着崩溃页面, 手心开始出汗。这是典型的内存泄漏! 而且泄漏速度极快, 30分钟就能吃掉2GB内存。如果不能在今天修复, 周一一开盘, 所有客户都会遇到这个问题。

你快速拨通了前端负责人老张的电话:"老张, 醒醒, 出大事了!"

---

## 内存分析

上午十点, 你打开Chrome DevTools的Performance面板, 录制了一分钟的内存快照。看到内存使用曲线时, 你倒吸一口凉气——一条陡峭的斜线, 没有任何下降的迹象。

正常情况下, JavaScript的垃圾回收机制会自动清理不再使用的对象, 内存曲线应该是锯齿状的: 上升→垃圾回收→下降→上升。但现在的曲线是单向上升, 说明大量对象无法被回收!

你切换到Memory面板, 拍了两个堆快照, 对比前后的内存增长:

```javascript
// 快照1 (5分钟): 200MB
// 快照2 (10分钟): 400MB
// 增量: 200MB

// 增量对象分析:
// - (closure): 50MB
// - HTMLDivElement: 80MB
// - Array: 40MB
// - EventListener: 30MB
```

"闭包、DOM元素、事件监听器... 这些都在泄漏。"你喃喃自语。

你打开数据看板的核心代码, 这是图表渲染组件:

```javascript
class ChartWidget {
    constructor(container) {
        this. container = container;
        this. data = [];
        this. startAutoRefresh();
    }

    startAutoRefresh() {
        setInterval(() => {
            this. fetchData();
        }, 5000); // 每5秒刷新
    }

    fetchData() {
        fetch('/api/data')
            . then(res => res. json())
            . then(data => {
                this. data = data; // 保存数据
                this. render();
            });
    }

    render() {
        // 清空容器
        this. container. innerHTML = '';

        // 创建新的图表元素
        this. data. forEach(item => {
            const div = document. createElement('div');
            div. className = 'chart-item';
            div. innerHTML = `<span>${item. name}: ${item. value}</span>`;

            // 添加点击事件
            div. addEventListener('click', () => {
                this. showDetail(item); // 闭包引用了item和this
            });

            this. container. appendChild(div);
        });
    }

    showDetail(item) {
        console. log('Detail:', item);
    }
}
```

代码看起来没什么问题, 但老张在电话里提醒你:"注意看`render`方法, 每次渲染都会创建新的DOM元素和事件监听器, 但旧的监听器被清理了吗?"

你突然意识到问题:"没有! 我用`innerHTML = ''`清空容器, DOM元素确实被移除了, 但**事件监听器还在内存里**!"

你快速写了个测试:

```javascript
// 测试: 事件监听器泄漏
const container = document. querySelector('#test');

for (let i = 0; i < 1000; i++) {
    const div = document. createElement('div');
    div. addEventListener('click', () => {
        console. log(i); // 闭包捕获了i
    });
    container. appendChild(div);
}

// 清空容器
container. innerHTML = ''; // DOM元素删除了

// 但1000个事件监听器还在内存里!
// 每个监听器都闭包引用了外层变量
```

"原来如此!"你恍然大悟。每次`render`创建100个图表项, 每5秒刷新一次, 30分钟刷新360次, 创建了36000个事件监听器! 每个监听器都通过闭包引用了`item`和`this`, 这些对象永远无法被垃圾回收!

你还发现了第二个泄漏点:

```javascript
startAutoRefresh() {
    setInterval(() => {
        this. fetchData();
    }, 5000);
}
```

"这个`setInterval`也有问题!"你自言自语,"如果组件被销毁, 但`setInterval`还在运行, 它会一直持有对`this`的引用, 导致整个组件无法被回收!"

上午十一点, 老张赶到公司, 两人一起分析代码, 列出了所有泄漏点:
1. 事件监听器未清理
2. `setInterval`未清除
3. 闭包引用导致大对象无法释放

"先修最严重的, 把事件监听器清理掉。"老张说。

---

## 修复方案

你们快速修复了代码, 整理出内存泄漏的常见模式和修复方案:

**泄漏场景1: 事件监听器未移除**

```javascript
/* ❌ 错误: 事件监听器泄漏 */
class Widget {
    render() {
        this. container. innerHTML = ''; // 删除DOM

        this. data. forEach(item => {
            const div = document. createElement('div');
            div. addEventListener('click', () => {
                this. handleClick(item); // 闭包引用item和this
            });
            this. container. appendChild(div);
        });
        // DOM删除了, 但事件监听器还在内存里!
    }
}

/* ✅ 修复1: 使用事件委托 */
class Widget {
    constructor(container) {
        this. container = container;

        // 在容器上监听, 而不是每个子元素
        this. container. addEventListener('click', (e) => {
            if (e. target. classList. contains('chart-item')) {
                const index = e. target. dataset. index;
                this. handleClick(this. data[index]);
            }
        });
    }

    render() {
        this. container. innerHTML = '';
        this. data. forEach((item, index) => {
            const div = document. createElement('div');
            div. className = 'chart-item';
            div. dataset. index = index; // 存储索引
            div. textContent = item. name;
            this. container. appendChild(div);
        });
        // 只有一个监听器, 在容器上
    }
}

/* ✅ 修复2: 手动移除监听器 */
class Widget {
    constructor() {
        this. elements = []; // 保存元素引用
    }

    render() {
        // 先移除旧监听器
        this. elements. forEach(el => {
            el. removeEventListener('click', el._handler);
        });
        this. elements = [];

        // 创建新元素
        this. data. forEach(item => {
            const div = document. createElement('div');
            const handler = () => this. handleClick(item);
            div._handler = handler; // 保存handler引用
            div. addEventListener('click', handler);
            this. elements. push(div);
            this. container. appendChild(div);
        });
    }
}
```

**泄漏场景2: 定时器未清除**

```javascript
/* ❌ 错误: 定时器泄漏 */
class DataFetcher {
    startPolling() {
        setInterval(() => {
            this. fetch(); // 持有this引用
        }, 5000);
    }
    // 组件销毁后, 定时器还在运行!
}

/* ✅ 修复: 清除定时器 */
class DataFetcher {
    startPolling() {
        this. timer = setInterval(() => {
            this. fetch();
        }, 5000);
    }

    destroy() {
        if (this. timer) {
            clearInterval(this. timer);
            this. timer = null;
        }
    }
}
```

**泄漏场景3: 闭包引用大对象**

```javascript
/* ❌ 错误: 闭包引用导致泄漏 */
function createClosure() {
    const largeData = new Array(1000000). fill('data'); // 大对象

    return function() {
        console. log(largeData[0]); // 闭包引用整个数组
    };
}

const fn = createClosure(); // largeData永远不会被回收!

/* ✅ 修复: 只引用需要的数据 */
function createClosure() {
    const largeData = new Array(1000000). fill('data');
    const firstItem = largeData[0]; // 只保存需要的

    return function() {
        console. log(firstItem); // 只引用firstItem
    };
    // largeData可以被回收
}
```

中午十二点, 你们完成了修复, 重新部署。打开数据看板, 内存占用稳定在200MB, 运行30分钟后依然流畅。

"搞定!"老张长舒一口气。

---

## 内存管理

**规则 1: JavaScript垃圾回收机制**

```javascript
/* 标记-清除算法(主流) */
// 1. GC从根对象(window, global)开始遍历
// 2. 标记所有可达对象
// 3. 清除未标记对象
// 4. 压缩内存(可选)

/* 对象可达性 */
let obj = { data: 'hello' }; // 可达: 被obj引用
obj = null; // 不可达: 无引用, 可被回收

/* 循环引用不影响GC */
function test() {
    let a = {};
    let b = {};
    a. ref = b;
    b. ref = a; // 循环引用
}
test();
// 函数执行完, a和b都不可达, 会被回收
```

**触发垃圾回收**:
- 自动触发: 内存达到阈值
- 无法手动触发(Chrome有`gc()`但仅调试用)

---

**规则 2: 常见内存泄漏场景**

```javascript
/* 场景1: 意外的全局变量 */
function leak() {
    name = 'global'; // 忘记var/let/const, 变成全局变量!
}
leak();
// window. name = 'global' - 永远不会被回收

/* 场景2: 被遗忘的定时器 */
const timer = setInterval(() => {
    console. log('running');
}, 1000);
// 忘记clearInterval(timer), 定时器永远运行

/* 场景3: 脱离DOM的引用 */
const elements = [];
for (let i = 0; i < 1000; i++) {
    const div = document. createElement('div');
    elements. push(div); // 保存引用
    document. body. appendChild(div);
}
document. body. innerHTML = ''; // DOM删除了
// 但elements数组还引用着1000个div!

/* 场景4: 闭包引用 */
function outer() {
    const largeData = new Array(1000000);
    return function inner() {
        return largeData. length; // 引用整个数组
    };
}
const fn = outer();
// largeData无法被回收
```

---

**规则 3: 事件监听器内存管理**

```javascript
/* ❌ 问题: 每次创建新监听器 */
function render() {
    container. innerHTML = '';
    data. forEach(item => {
        const btn = document. createElement('button');
        btn. addEventListener('click', () => {
            handleClick(item); // 新监听器
        });
        container. appendChild(btn);
    });
}
setInterval(render, 5000); // 每5秒创建新监听器!

/* ✅ 方案1: 事件委托 */
container. addEventListener('click', (e) => {
    if (e. target. tagName === 'BUTTON') {
        const item = data[e. target. dataset. index];
        handleClick(item);
    }
});

/* ✅ 方案2: 移除旧监听器 */
let currentHandler = null;
function render() {
    if (currentHandler) {
        button. removeEventListener('click', currentHandler);
    }
    currentHandler = () => handleClick();
    button. addEventListener('click', currentHandler);
}

/* ✅ 方案3: AbortController (现代API) */
const controller = new AbortController();
button. addEventListener('click', handler, {
    signal: controller. signal
});
// 销毁时:
controller. abort(); // 自动移除所有监听器
```

---

**规则 4: 定时器内存管理**

```javascript
/* ❌ 问题: 定时器未清除 */
class Component {
    constructor() {
        this. data = new Array(10000);
        setInterval(() => {
            this. update(); // 引用this
        }, 1000);
    }
}
const comp = new Component();
comp = null; // comp无法被回收! 定时器还在引用

/* ✅ 修复: 清除定时器 */
class Component {
    constructor() {
        this. data = new Array(10000);
        this. timer = setInterval(() => {
            this. update();
        }, 1000);
    }

    destroy() {
        clearInterval(this. timer);
        this. timer = null;
        this. data = null; // 清除大对象引用
    }
}

/* setTimeout也要清除 */
this. timeout = setTimeout(() => {}, 5000);
clearTimeout(this. timeout);
```

---

**规则 5: WeakMap和WeakSet防止泄漏**

```javascript
/* Map vs WeakMap */

/* ❌ Map: 强引用, 可能泄漏 */
const map = new Map();
let obj = { data: 'test' };
map. set(obj, 'value');
obj = null; // obj被回收了吗?
// 不会! Map还引用着它

/* ✅ WeakMap: 弱引用, 不阻止GC */
const weakMap = new WeakMap();
let obj2 = { data: 'test' };
weakMap. set(obj2, 'value');
obj2 = null;
// obj2会被回收, weakMap的条目自动删除

/* 使用场景: DOM元素元数据 */
const metadata = new WeakMap();
document. querySelectorAll('div'). forEach(el => {
    metadata. set(el, { clicks: 0 });
});
// DOM元素删除后, metadata自动清理

/* WeakSet同理 */
const weakSet = new WeakSet();
weakSet. add(obj);
obj = null; // 自动从weakSet删除
```

---

**规则 6: 内存泄漏检测与分析**

```javascript
/* Chrome DevTools检测 */

// 1. Performance面板 - 录制内存分配
// 看内存曲线: 应该是锯齿状(上升→GC→下降)
// 如果持续上升无下降, 说明泄漏

// 2. Memory面板 - 堆快照对比
// 拍快照1 → 操作页面 → 拍快照2 → 对比
// 查看增量对象, 找泄漏源

// 3. Memory面板 - Allocation instrumentation
// 实时记录内存分配, 找泄漏点

/* 代码中检测内存 */
if (performance. memory) {
    console. log('Used:', performance. memory. usedJSHeapSize);
    console. log('Total:', performance. memory. totalJSHeapSize);
    console. log('Limit:', performance. memory. jsHeapSizeLimit);
}

/* 泄漏判断 */
// 1. 内存持续增长, 不回落
// 2. 操作后内存不恢复到初始值
// 3. 内存增长速度与操作频率成正比
```

**最佳实践**:
- 组件销毁时清理定时器、事件监听器
- 使用事件委托代替大量独立监听器
- 避免闭包引用大对象
- 使用WeakMap/WeakSet存储临时关联数据
- 定期进行内存分析, 及早发现泄漏

---

**事故档案编号**: OBJ-2024-1749
**影响范围**: 实时数据看板, 所有长时间运行的页面
**根本原因**: 事件监听器和定时器未清理, 导致闭包引用无法释放
**修复成本**: 中等(需要重构组件生命周期管理)

这是JavaScript世界第49次被记录的内存泄漏事故。JavaScript有自动垃圾回收, 但不代表不会内存泄漏。常见泄漏源包括: 未清除的定时器、未移除的事件监听器、意外的全局变量、闭包引用大对象。理解可达性、理解垃圾回收机制、养成清理资源的习惯, 是防止浏览器"缓慢死亡"的关键。

---
