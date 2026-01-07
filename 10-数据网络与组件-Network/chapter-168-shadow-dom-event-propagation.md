《第 168 次记录: 消失的点击事件 —— Shadow DOM 事件传播的封闭边界》

---

## 诡异的间歇性 Bug

周三上午 10 点 15 分, 你盯着测试报告发呆。

QA 团队提交的 bug 描述让你困惑不解: "自定义按钮组件的点击事件间歇性失效, 有时能触发, 有时完全没反应。复现概率约 30%。"

你在本地尝试了十几次, 每次点击都正常触发。你甚至怀疑是不是 QA 的测试环境有问题, 但小王发来的录屏视频证明问题确实存在: 他连续点击按钮 5 次, 其中 2 次完全没有响应。

"这不科学..." 你喃喃自语。这个 `<custom-button>` 组件是你上周刚用 Shadow DOM 重构的, 本地测试时运行完美, 代码审查也通过了。怎么到了测试环境就出现这种诡异的问题?

你打开组件的源代码:

```javascript
class CustomButton extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                button {
                    padding: 12px 24px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
            </style>
            <button>
                <slot></slot>
            </button>
        `;
    }
}

customElements.define('custom-button', CustomButton);
```

代码很简单, 就是一个封装了样式的按钮。用户这样使用:

```html
<custom-button id="submitBtn">
    提交订单
</custom-button>

<script>
document.getElementById('submitBtn').addEventListener('click', (e) => {
    console.log('按钮被点击了!');
    // 提交订单逻辑...
});
</script>
```

你在本地再次测试, 点击按钮, 控制台正常输出 "按钮被点击了!"。一切正常。

但小王又发来消息: "我刚才又测试了 20 次, 有 7 次失效。而且我发现一个规律: 如果我点击按钮的文字区域, 一定能触发; 但如果点击按钮的边缘区域 (padding 部分), 就可能失效。"

"点击位置影响事件触发?" 你眉头一皱, 这个线索很关键。

---

## 线索追踪

你打开 Chrome DevTools, 仔细检查了组件的 DOM 结构:

```html
<custom-button id="submitBtn">
    #shadow-root (open)
        <style>...</style>
        <button>
            <slot>
                ↳ 提交订单
            </slot>
        </button>
    提交订单
</custom-button>
```

你突然注意到一个细节: **文本 "提交订单" 实际上在 Light DOM 中, 只是通过 `<slot>` 投射到了 Shadow DOM 的 `<button>` 内部。**

"难道问题和 slot 有关?" 你决定做一个实验。

你在 Shadow DOM 内部的 `<button>` 上也添加了一个监听器:

```javascript
class CustomButton extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                button {
                    padding: 12px 24px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
            </style>
            <button>
                <slot></slot>
            </button>
        `;

        // 在 Shadow DOM 内部监听
        const button = shadow.querySelector('button');
        button.addEventListener('click', (e) => {
            console.log('Shadow DOM 内部捕获到点击!');
            console.log('事件目标:', e.target);
        });
    }
}
```

刷新页面, 点击按钮。控制台输出:

```
Shadow DOM 内部捕获到点击!
事件目标: <button>
按钮被点击了!
```

看起来正常。但你注意到一个奇怪的现象: **外部监听器中的 `e.target` 不是 `<button>`, 而是 `<custom-button>` 元素本身。**

你在外部监听器中打印 `e.target`:

```javascript
document.getElementById('submitBtn').addEventListener('click', (e) => {
    console.log('外部监听器中的 target:', e.target);
    // 输出: <custom-button id="submitBtn">...</custom-button>
});
```

"事件目标被重定向了!" 你意识到, 当事件从 Shadow DOM 穿透到外部时, `e.target` 被自动改成了 Shadow Host (`<custom-button>`)。

但这还不能解释为什么会间歇性失效。你继续调查。

---

## 突破发现

你想起小王说的 "点击文字区域一定能触发, 点击边缘可能失效"。你决定精确测试每个点击位置。

你修改了外部监听器, 记录更多信息:

```javascript
document.getElementById('submitBtn').addEventListener('click', (e) => {
    console.log('外部监听器触发');
    console.log('target:', e.target);
    console.log('currentTarget:', e.currentTarget);
    console.log('点击坐标:', e.clientX, e.clientY);
    console.log('事件路径:', e.composedPath());
});
```

你点击按钮的文字 "提交订单", 控制台输出:

```
Shadow DOM 内部捕获到点击!
事件目标: 提交订单 (文本节点)
外部监听器触发
target: <custom-button>
currentTarget: <custom-button>
点击坐标: 523 187
事件路径: [text, slot, button, #shadow-root, custom-button, body, html, document, Window]
```

你又点击按钮的边缘 (padding 区域), 控制台输出:

```
Shadow DOM 内部捕获到点击!
事件目标: <button>
```

**外部监听器没有触发!**

"找到了!" 你兴奋地喊出来。问题出在这里: **当点击 Shadow DOM 内部的 `<button>` 元素本身 (而非 slot 内容) 时, 事件没有穿透到外部!**

你查阅了 MDN 关于 Shadow DOM 事件传播的文档, 找到了关键信息:

> **事件的 `composed` 属性决定了事件是否能穿透 Shadow DOM 边界。**
>
> - `composed: true` 的事件可以穿透 Shadow DOM
> - `composed: false` 的事件被困在 Shadow DOM 内部
>
> 大多数原生 UI 事件 (如 `click`, `input`, `keydown`) 都是 `composed: true`。但如果事件在 Shadow DOM 内部被 `stopPropagation()` 阻止, 或者某些自定义事件默认 `composed: false`, 就无法穿透到外部。

你突然意识到问题所在。你检查了组件代码, 发现之前为了防止事件冒泡到父容器, 你在内部监听器中调用了 `e.stopPropagation()`:

```javascript
button.addEventListener('click', (e) => {
    console.log('Shadow DOM 内部捕获到点击!');
    e.stopPropagation(); // ❌ 这行代码阻止了事件继续传播!
});
```

"原来如此..." 你恍然大悟。虽然 `click` 事件本身是 `composed: true`, 但你在 Shadow DOM 内部调用了 `stopPropagation()`, 阻止了事件继续冒泡。

但这还不能完全解释 "点击文字能触发, 点击边缘不能触发" 的现象。你仔细分析事件路径:

- **点击文字 (slot 内容)**: 事件起源于 Light DOM 的文本节点 → 冒泡到 `<custom-button>` → 触发外部监听器 ✅
- **点击按钮边缘**: 事件起源于 Shadow DOM 的 `<button>` → 被 `stopPropagation()` 阻止 → 无法到达 `<custom-button>` → 外部监听器不触发 ❌

"所以问题的根源是: slot 内容在 Light DOM 中, 它的事件可以直接冒泡到外部; 但 Shadow DOM 内部元素的事件被我的 `stopPropagation()` 阻止了。" 你总结道。

---

## 真相浮现

你决定完整测试 Shadow DOM 的事件传播机制。你创建了一个实验组件:

```javascript
class EventTestComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .wrapper {
                    border: 2px solid blue;
                    padding: 20px;
                }
                button {
                    padding: 10px;
                    background: green;
                }
            </style>
            <div class="wrapper">
                <button id="innerBtn">Shadow DOM 按钮</button>
                <div>
                    <slot></slot>
                </div>
            </div>
        `;

        // Shadow DOM 内部监听
        shadow.addEventListener('click', (e) => {
            console.log('=== Shadow DOM 监听器 ===');
            console.log('target:', e.target);
            console.log('currentTarget:', e.currentTarget);
            console.log('composed:', e.composed);
            console.log('composedPath:', e.composedPath());
        });
    }

    connectedCallback() {
        // Shadow Host 监听
        this.addEventListener('click', (e) => {
            console.log('=== Host 监听器 ===');
            console.log('target:', e.target);
            console.log('currentTarget:', e.currentTarget);
        });
    }
}

customElements.define('event-test-component', EventTestComponent);
```

使用:

```html
<event-test-component id="test">
    <button>Light DOM 按钮</button>
</event-test-component>

<script>
document.addEventListener('click', (e) => {
    console.log('=== 文档监听器 ===');
    console.log('target:', e.target);
});
</script>
```

你点击 "Shadow DOM 按钮", 输出:

```
=== Shadow DOM 监听器 ===
target: <button id="innerBtn">
currentTarget: #shadow-root
composed: true
composedPath: [button, div.wrapper, #shadow-root, event-test-component, body, html, document, Window]

=== Host 监听器 ===
target: <event-test-component>  ← 被重定向了!
currentTarget: <event-test-component>

=== 文档监听器 ===
target: <event-test-component>  ← 仍然是重定向后的
```

你点击 "Light DOM 按钮", 输出:

```
=== Shadow DOM 监听器 ===
target: <button>
currentTarget: #shadow-root
composed: true
composedPath: [button, slot, div, #shadow-root, event-test-component, body, html, document, Window]

=== Host 监听器 ===
target: <button>  ← 没有被重定向!
currentTarget: <event-test-component>

=== 文档监听器 ===
target: <button>  ← 仍然是原始 target
```

"完全明白了!" 你兴奋地总结:

**Shadow DOM 事件传播的三个关键机制**:

**① 事件重定向 (Event Retargeting)**:
- 当事件从 Shadow DOM **内部元素**穿透到外部时, `e.target` 被重定向为 Shadow Host
- 这是封装保护机制, 外部代码无法知道 Shadow DOM 的内部实现
- 但 **slot 内容的事件不会被重定向**, 因为 slot 内容本身就在 Light DOM

**② composed 属性控制穿透**:
- `composed: true` 的事件可以穿透 Shadow DOM 边界
- `composed: false` 的事件被困在 Shadow DOM 内部
- 大多数原生事件都是 `composed: true`

**③ composedPath() 获取真实路径**:
- `e.composedPath()` 返回完整的事件传播路径, 包括 Shadow DOM 内部元素
- 这是获取真实事件目标的唯一方法

---

## 修复方案

你修改了 `<custom-button>` 组件, 移除了 `stopPropagation()` 调用:

```javascript
class CustomButton extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                button {
                    padding: 12px 24px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
            </style>
            <button>
                <slot></slot>
            </button>
        `;

        // ✅ 不再阻止事件传播
        const button = shadow.querySelector('button');
        button.addEventListener('click', (e) => {
            console.log('Shadow DOM 内部处理');
            // 不调用 e.stopPropagation()
        });
    }
}
```

你测试了 50 次点击, 包括点击文字和点击边缘, 全部正常触发外部监听器。

小王也确认测试通过: "现在完全正常了, 点击任何位置都能触发!"

但你意识到还有一个问题: 如果你**确实需要触发自定义事件**传递到外部, 该怎么做?

你创建了一个更完善的版本:

```javascript
class CustomButton extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                button {
                    padding: 12px 24px;
                    background: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
            </style>
            <button>
                <slot></slot>
            </button>
        `;

        const button = shadow.querySelector('button');
        button.addEventListener('click', (e) => {
            // ✅ 触发自定义事件, 设置 composed: true
            this.dispatchEvent(new CustomEvent('custom-click', {
                bubbles: true,
                composed: true,  // 允许穿透 Shadow DOM
                detail: {
                    originalEvent: e,
                    timestamp: Date.now()
                }
            }));
        });
    }
}
```

使用:

```html
<custom-button id="submitBtn">
    提交订单
</custom-button>

<script>
document.getElementById('submitBtn').addEventListener('custom-click', (e) => {
    console.log('自定义事件触发!');
    console.log('详情:', e.detail);
    console.log('target:', e.target);  // <custom-button>
});
</script>
```

测试通过! 你还测试了如果设置 `composed: false` 会怎样:

```javascript
this.dispatchEvent(new CustomEvent('internal-event', {
    bubbles: true,
    composed: false  // ❌ 不穿透 Shadow DOM
}));
```

外部监听器无法捕获这个事件, 符合预期。

---

## 复盘总结

晚上, 你整理了这次 bug 调查的收获。你画了一张 Shadow DOM 事件传播的完整图:

```
点击事件传播路径:

[情况 1: 点击 Shadow DOM 内部元素]
<button> (Shadow DOM 内部)
    ↓ (事件冒泡, composed: true)
#shadow-root
    ↓ (穿透边界, target 重定向)
<custom-button> (Shadow Host)
    ↓ (继续冒泡, target 仍是 <custom-button>)
<body>
    ↓
document

[情况 2: 点击 slot 内容 (Light DOM)]
文本节点 (Light DOM)
    ↓ (通过 slot 投射渲染)
<button> (Shadow DOM 内部)
    ↓ (事件冒泡, 但 target 仍是原始 Light DOM 元素)
<custom-button> (Shadow Host)
    ↓ (继续冒泡, target 没有被重定向)
<body>
    ↓
document
```

你总结出几个关键洞察:

**洞察 #1: 事件重定向的触发条件**
- 只有当事件**起源于 Shadow DOM 内部元素**时, 才会发生 target 重定向
- Slot 内容的事件不会被重定向, 因为它们本身就在 Light DOM

**洞察 #2: stopPropagation 的影响范围**
- 在 Shadow DOM 内部调用 `stopPropagation()` 会阻止事件冒泡
- 但这只影响**起源于 Shadow DOM 内部的事件**
- Slot 内容的事件不受影响, 因为它们在 Light DOM 中就已经开始冒泡

**洞察 #3: composed 属性的关键作用**
- 原生事件 (click, input, keydown) 默认 `composed: true`
- 自定义事件默认 `composed: false`, 必须显式设置 `composed: true`
- 即使 `composed: true`, 如果被 `stopPropagation()` 阻止, 仍然无法穿透

你还记录了几个实战建议:

```javascript
// ✅ 最佳实践 1: 不要在 Shadow DOM 内部随意 stopPropagation
class MyComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.addEventListener('click', (e) => {
            // ❌ 避免这样做, 会阻止外部监听器接收事件
            // e.stopPropagation();

            // ✅ 如果需要阻止特定行为, 使用 preventDefault
            if (needsToPrevent) {
                e.preventDefault();
            }
        });
    }
}

// ✅ 最佳实践 2: 自定义事件必须设置 composed: true
class MyComponent extends HTMLElement {
    emitCustomEvent() {
        this.dispatchEvent(new CustomEvent('my-event', {
            bubbles: true,
            composed: true,  // 必须设置, 否则无法穿透
            detail: { data: 'value' }
        }));
    }
}

// ✅ 最佳实践 3: 使用 composedPath() 获取真实事件路径
class MyComponent extends HTMLElement {
    connectedCallback() {
        this.addEventListener('click', (e) => {
            // e.target 可能被重定向, 不可靠
            console.log('重定向后的 target:', e.target);

            // 使用 composedPath() 获取真实路径
            const path = e.composedPath();
            const realTarget = path[0];
            console.log('真实的触发元素:', realTarget);

            // 检查是否点击了特定内部元素
            const clickedButton = path.find(el =>
                el.tagName === 'BUTTON' && el.classList.contains('submit')
            );
            if (clickedButton) {
                console.log('点击了提交按钮');
            }
        });
    }
}

// ✅ 最佳实践 4: 区分内部事件和外部事件
class MyComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `<button id="btn">Click</button>`;

        // 内部事件处理 (不需要穿透)
        shadow.getElementById('btn').addEventListener('click', (e) => {
            // 内部处理逻辑
            this.handleInternalClick(e);

            // 触发外部可见的自定义事件
            this.dispatchEvent(new CustomEvent('button-clicked', {
                bubbles: true,
                composed: true,  // 允许外部监听
                detail: { source: 'internal-button' }
            }));
        });
    }
}
```

你还发现了一个容易踩的坑:

**坑: 多层嵌套 Shadow DOM 的事件重定向**

```javascript
// 父组件
class ParentComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });
        shadow.innerHTML = `
            <child-component></child-component>
        `;
    }
}

// 子组件
class ChildComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });
        shadow.innerHTML = `
            <button>Click</button>
        `;
    }
}
```

如果点击子组件的按钮, 事件传播路径:

```
<button> (ChildComponent Shadow DOM)
    ↓ (target: <button>)
#shadow-root (ChildComponent)
    ↓ (target 重定向为 <child-component>)
<child-component>
    ↓ (在 ParentComponent 的 Shadow DOM 内部)
#shadow-root (ParentComponent)
    ↓ (target 重定向为 <parent-component>)
<parent-component>
    ↓ (target: <parent-component>)
document
```

**每穿过一层 Shadow DOM 边界, target 就会被重定向一次。** 外部文档监听器永远只能看到最外层的 Shadow Host。

你保存了笔记, 关上电脑。虽然这个 bug 花了整整一天时间调查, 但你庆幸自己彻底理解了 Shadow DOM 的事件传播机制。

更重要的是, 你现在知道如何设计组件, 让内部事件既能被正确封装, 又能在需要时穿透到外部。

---

## 知识档案: Shadow DOM 事件传播的八个核心规则

**规则 1: 原生 UI 事件默认可以穿透 Shadow DOM, 但 target 会被重定向**

大多数原生 UI 事件的 `composed` 属性为 `true`, 可以穿透 Shadow DOM 边界。但当事件从 Shadow DOM 内部穿透到外部时, `e.target` 会被自动重定向为 Shadow Host, 隐藏内部实现细节。

```javascript
class EventComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <button id="innerBtn">内部按钮</button>
        `;

        // Shadow DOM 内部监听
        shadow.getElementById('innerBtn').addEventListener('click', (e) => {
            console.log('内部监听器 - target:', e.target);
            // 输出: <button id="innerBtn">
        });
    }

    connectedCallback() {
        // Shadow Host 监听
        this.addEventListener('click', (e) => {
            console.log('Host 监听器 - target:', e.target);
            // 输出: <event-component> (被重定向了!)
        });
    }
}

customElements.define('event-component', EventComponent);
```

使用:

```html
<event-component id="test"></event-component>

<script>
document.getElementById('test').addEventListener('click', (e) => {
    console.log('外部监听器 - target:', e.target);
    // 输出: <event-component> (仍然是重定向后的)
});
</script>
```

**原生事件的 composed 属性**:

```javascript
// ✅ composed: true (可穿透 Shadow DOM)
- click, dblclick
- mousedown, mouseup, mousemove
- wheel
- keydown, keyup, keypress
- input, change
- touchstart, touchmove, touchend
- pointerdown, pointerup, pointermove

// ❌ composed: false (不穿透 Shadow DOM)
- focus, blur (但 focusin/focusout 是 composed: true)
- mouseenter, mouseleave (不冒泡也不 composed)
- load, error, scroll (不冒泡)
```

**为什么要重定向 target**:

- **封装保护**: 外部代码无法知道 Shadow DOM 的内部实现细节
- **抽象隔离**: 组件内部的 DOM 结构变化不会影响外部代码
- **一致性**: 外部看到的 target 始终是组件本身, 而不是内部元素

---

**规则 2: Slot 内容的事件不会被重定向, 因为它们在 Light DOM 中**

通过 `<slot>` 投射的内容实际上仍在 Light DOM 中, 只是渲染位置被投射到 Shadow DOM 内部。因此, slot 内容触发的事件不会被重定向。

```javascript
class SlotEventComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .wrapper {
                    border: 2px solid blue;
                    padding: 20px;
                }
                button {
                    margin: 10px;
                }
            </style>
            <div class="wrapper">
                <button id="shadowBtn">Shadow DOM 按钮</button>
                <slot></slot>
            </div>
        `;

        // Shadow DOM 监听器
        shadow.addEventListener('click', (e) => {
            console.log('Shadow DOM 监听 - target:', e.target);
        });
    }

    connectedCallback() {
        this.addEventListener('click', (e) => {
            console.log('Host 监听 - target:', e.target);
        });
    }
}

customElements.define('slot-event-component', SlotEventComponent);
```

使用:

```html
<slot-event-component>
    <button id="lightBtn">Light DOM 按钮</button>
</slot-event-component>

<script>
document.addEventListener('click', (e) => {
    console.log('文档监听 - target:', e.target);
});
</script>
```

**点击 "Shadow DOM 按钮" 的输出**:

```
Shadow DOM 监听 - target: <button id="shadowBtn">
Host 监听 - target: <slot-event-component>  ← 被重定向
文档监听 - target: <slot-event-component>  ← 仍是重定向后的
```

**点击 "Light DOM 按钮" 的输出**:

```
Shadow DOM 监听 - target: <button id="lightBtn">
Host 监听 - target: <button id="lightBtn">  ← 没有被重定向!
文档监听 - target: <button id="lightBtn">  ← 仍是原始 target
```

**关键洞察**:

- Slot 内容的事件起源于 Light DOM, 事件冒泡过程中不会穿越 Shadow DOM 边界
- 虽然 slot 内容**渲染**在 Shadow DOM 内部, 但它们的 **DOM 位置**仍在 Light DOM
- 因此, slot 内容的 `e.target` 不会被重定向, 保持为原始的 Light DOM 元素

---

**规则 3: composedPath() 可以获取包含 Shadow DOM 内部的完整事件路径**

`e.composedPath()` 返回事件传播的完整路径, 包括 Shadow DOM 内部的元素, 是获取真实事件目标的唯一方法。

```javascript
class PathComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <div class="outer">
                <div class="inner">
                    <button id="btn">Click Me</button>
                </div>
            </div>
        `;

        shadow.getElementById('btn').addEventListener('click', (e) => {
            console.log('=== 在 Shadow DOM 内部 ===');
            console.log('target:', e.target);
            // <button id="btn">

            console.log('composedPath:', e.composedPath());
            // [button, div.inner, div.outer, #shadow-root,
            //  path-component, body, html, document, Window]
        });
    }

    connectedCallback() {
        this.addEventListener('click', (e) => {
            console.log('=== 在 Shadow Host ===');
            console.log('target:', e.target);
            // <path-component> (被重定向)

            // ✅ 使用 composedPath() 获取真实路径
            const path = e.composedPath();
            const realTarget = path[0];
            console.log('真实触发元素:', realTarget);
            // <button id="btn">

            // 检查是否点击了特定内部元素
            const clickedButton = path.find(el =>
                el.id === 'btn'
            );
            if (clickedButton) {
                console.log('点击了内部按钮');
            }
        });
    }
}

customElements.define('path-component', PathComponent);
```

**composedPath() 的应用场景**:

```javascript
// 场景 1: 判断点击来源
this.addEventListener('click', (e) => {
    const path = e.composedPath();

    // 判断是否点击了关闭按钮
    const isCloseButton = path.some(el =>
        el.classList && el.classList.contains('close-btn')
    );

    // 判断是否点击了遮罩层
    const isOverlay = path.some(el =>
        el.classList && el.classList.contains('modal-overlay')
    );

    if (isCloseButton || isOverlay) {
        this.close();
    }
});

// 场景 2: 事件委托
this.addEventListener('click', (e) => {
    const path = e.composedPath();

    // 查找最近的 data-action 属性
    const actionElement = path.find(el =>
        el.dataset && el.dataset.action
    );

    if (actionElement) {
        const action = actionElement.dataset.action;
        this.handleAction(action);
    }
});

// 场景 3: 阻止特定内部元素的事件
this.addEventListener('click', (e) => {
    const path = e.composedPath();

    // 如果点击了内部的禁用元素, 阻止默认行为
    const isDisabled = path.some(el =>
        el.hasAttribute && el.hasAttribute('disabled')
    );

    if (isDisabled) {
        e.preventDefault();
        e.stopPropagation();
    }
});
```

---

**规则 4: 自定义事件默认 composed: false, 必须显式设置 composed: true 才能穿透**

自定义事件 (通过 `new CustomEvent()` 创建) 默认 `composed: false`, 无法穿透 Shadow DOM 边界。必须显式设置 `composed: true`。

```javascript
class CustomEventComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <button id="btn1">触发 composed: false 事件</button>
            <button id="btn2">触发 composed: true 事件</button>
        `;

        // ❌ composed: false (默认), 无法穿透
        shadow.getElementById('btn1').addEventListener('click', () => {
            this.dispatchEvent(new CustomEvent('non-composed-event', {
                bubbles: true,
                composed: false  // 默认值, 显式写出
            }));
        });

        // ✅ composed: true, 可以穿透
        shadow.getElementById('btn2').addEventListener('click', () => {
            this.dispatchEvent(new CustomEvent('composed-event', {
                bubbles: true,
                composed: true  // 必须显式设置
            }));
        });
    }
}

customElements.define('custom-event-component', CustomEventComponent);
```

使用:

```html
<custom-event-component id="test"></custom-event-component>

<script>
const component = document.getElementById('test');

// ❌ 无法捕获 composed: false 的事件
document.addEventListener('non-composed-event', (e) => {
    console.log('永远不会执行');
});

// ✅ 可以捕获 composed: true 的事件
document.addEventListener('composed-event', (e) => {
    console.log('成功捕获!');
});
</script>
```

**最佳实践: 组件对外暴露的自定义事件**

```javascript
class MyComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `<button id="btn">Submit</button>`;

        shadow.getElementById('btn').addEventListener('click', (e) => {
            // 内部处理逻辑
            this.processSubmit();

            // ✅ 触发对外可见的自定义事件
            this.dispatchEvent(new CustomEvent('submit', {
                bubbles: true,
                composed: true,  // 允许外部监听
                detail: {
                    timestamp: Date.now(),
                    source: 'internal-button'
                }
            }));
        });
    }

    processSubmit() {
        // 内部处理逻辑
    }
}
```

---

**规则 5: stopPropagation() 在 Shadow DOM 内部会阻止事件穿透到外部**

在 Shadow DOM 内部调用 `e.stopPropagation()` 会阻止事件继续冒泡, 即使事件的 `composed` 属性为 `true`, 也无法穿透到外部。

```javascript
class StopPropagationComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <button id="btn1">不阻止传播</button>
            <button id="btn2">阻止传播</button>
        `;

        // ✅ 不阻止传播, 外部可以监听
        shadow.getElementById('btn1').addEventListener('click', (e) => {
            console.log('内部处理, 但不阻止传播');
        });

        // ❌ 阻止传播, 外部无法监听
        shadow.getElementById('btn2').addEventListener('click', (e) => {
            console.log('内部处理, 并阻止传播');
            e.stopPropagation();  // 阻止事件继续冒泡
        });
    }

    connectedCallback() {
        this.addEventListener('click', (e) => {
            console.log('Host 监听器');
        });
    }
}

customElements.define('stop-propagation-component', StopPropagationComponent);
```

**点击 btn1 的输出**:

```
内部处理, 但不阻止传播
Host 监听器  ← 外部监听器正常触发
```

**点击 btn2 的输出**:

```
内部处理, 并阻止传播
(Host 监听器不会触发)  ← 被阻止了
```

**关键洞察**:

- `stopPropagation()` 会阻止事件继续冒泡, 无论是否设置了 `composed: true`
- 在 Shadow DOM 内部调用 `stopPropagation()` 会阻止事件穿透到外部
- 如果需要阻止默认行为但不阻止传播, 使用 `preventDefault()` 而非 `stopPropagation()`

**最佳实践: 避免在 Shadow DOM 内部随意 stopPropagation**

```javascript
class BestPracticeComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <button id="btn">Submit</button>
        `;

        shadow.getElementById('btn').addEventListener('click', (e) => {
            // ✅ 阻止默认行为 (如表单提交)
            if (needsToPrevent) {
                e.preventDefault();
            }

            // ❌ 避免这样做, 会阻止外部监听器
            // e.stopPropagation();

            // ✅ 触发自定义事件, 让外部知道内部发生了什么
            this.dispatchEvent(new CustomEvent('submit', {
                bubbles: true,
                composed: true
            }));
        });
    }
}
```

---

**规则 6: 多层嵌套 Shadow DOM 会导致 target 多次重定向**

当有多层嵌套的 Shadow DOM 时, 事件每穿过一层 Shadow DOM 边界, `e.target` 就会被重定向一次。外部文档监听器只能看到最外层的 Shadow Host。

```javascript
// 外层组件
class OuterComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <div class="outer-wrapper">
                <inner-component></inner-component>
            </div>
        `;

        shadow.addEventListener('click', (e) => {
            console.log('OuterComponent Shadow DOM - target:', e.target);
        });
    }

    connectedCallback() {
        this.addEventListener('click', (e) => {
            console.log('OuterComponent Host - target:', e.target);
        });
    }
}

// 内层组件
class InnerComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <div class="inner-wrapper">
                <button id="btn">Click Me</button>
            </div>
        `;

        shadow.addEventListener('click', (e) => {
            console.log('InnerComponent Shadow DOM - target:', e.target);
        });
    }

    connectedCallback() {
        this.addEventListener('click', (e) => {
            console.log('InnerComponent Host - target:', e.target);
        });
    }
}

customElements.define('outer-component', OuterComponent);
customElements.define('inner-component', InnerComponent);
```

使用:

```html
<outer-component id="test"></outer-component>

<script>
document.addEventListener('click', (e) => {
    console.log('Document - target:', e.target);
});
</script>
```

**点击内层按钮的输出**:

```
InnerComponent Shadow DOM - target: <button id="btn">
InnerComponent Host - target: <inner-component>  ← 第一次重定向
OuterComponent Shadow DOM - target: <inner-component>
OuterComponent Host - target: <outer-component>  ← 第二次重定向
Document - target: <outer-component>
```

**事件传播路径图**:

```
<button> (InnerComponent Shadow DOM)
    ↓ target: <button>
#shadow-root (InnerComponent)
    ↓ target: <button>
<inner-component>
    ↓ 穿越第一层边界, target 重定向为 <inner-component>
#shadow-root (OuterComponent)
    ↓ target: <inner-component>
<outer-component>
    ↓ 穿越第二层边界, target 重定向为 <outer-component>
document
    ↓ target: <outer-component>
```

**使用 composedPath() 获取完整路径**:

```javascript
document.addEventListener('click', (e) => {
    console.log('target (重定向后):', e.target);
    // <outer-component>

    const path = e.composedPath();
    console.log('完整路径:', path);
    // [button, div.inner-wrapper, #shadow-root (InnerComponent),
    //  inner-component, div.outer-wrapper, #shadow-root (OuterComponent),
    //  outer-component, body, html, document, Window]

    const realTarget = path[0];
    console.log('真实触发元素:', realTarget);
    // <button id="btn">
});
```

---

**规则 7: 事件重定向不影响 currentTarget, currentTarget 始终是监听器绑定的元素**

虽然 `e.target` 会被重定向, 但 `e.currentTarget` 始终是当前监听器绑定的元素, 不会被重定向。

```javascript
class CurrentTargetComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <div class="wrapper">
                <button id="btn">Click Me</button>
            </div>
        `;

        // 在 wrapper 上监听
        shadow.querySelector('.wrapper').addEventListener('click', (e) => {
            console.log('wrapper 监听器:');
            console.log('  target:', e.target);  // <button>
            console.log('  currentTarget:', e.currentTarget);  // <div.wrapper>
        });

        // 在 shadow root 上监听
        shadow.addEventListener('click', (e) => {
            console.log('shadow root 监听器:');
            console.log('  target:', e.target);  // <button>
            console.log('  currentTarget:', e.currentTarget);  // #shadow-root
        });
    }

    connectedCallback() {
        // 在 host 上监听
        this.addEventListener('click', (e) => {
            console.log('host 监听器:');
            console.log('  target:', e.target);  // <current-target-component> (重定向)
            console.log('  currentTarget:', e.currentTarget);  // <current-target-component>
        });
    }
}

customElements.define('current-target-component', CurrentTargetComponent);
```

**输出**:

```
wrapper 监听器:
  target: <button id="btn">
  currentTarget: <div class="wrapper">

shadow root 监听器:
  target: <button id="btn">
  currentTarget: #shadow-root

host 监听器:
  target: <current-target-component>  ← 被重定向
  currentTarget: <current-target-component>  ← 仍是 host 本身
```

**关键洞察**:

- `target` 表示事件的真实触发元素 (可能被重定向)
- `currentTarget` 表示当前监听器绑定的元素 (永远不会被重定向)
- 在事件处理函数中, `this` 等于 `currentTarget`

---

**规则 8: 事件委托在 Shadow DOM 中需要使用 composedPath() 而非 target**

在 Shadow DOM 组件中使用事件委托时, 不能依赖 `e.target`, 必须使用 `e.composedPath()` 来查找真实的事件触发元素。

```javascript
class DelegationComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .list { padding: 16px; }
                .item { padding: 8px; margin: 4px; border: 1px solid #ddd; }
                button { margin-left: 8px; }
            </style>
            <div class="list">
                <div class="item" data-id="1">
                    Item 1
                    <button data-action="edit">编辑</button>
                    <button data-action="delete">删除</button>
                </div>
                <div class="item" data-id="2">
                    Item 2
                    <button data-action="edit">编辑</button>
                    <button data-action="delete">删除</button>
                </div>
            </div>
        `;
    }

    connectedCallback() {
        // ❌ 错误的事件委托方式
        this.addEventListener('click', (e) => {
            // e.target 被重定向为 <delegation-component>, 无法判断真实点击目标
            console.log('target:', e.target);  // <delegation-component>

            // 这样无法工作
            if (e.target.dataset.action === 'edit') {
                // 永远不会执行
            }
        });

        // ✅ 正确的事件委托方式
        this.addEventListener('click', (e) => {
            // 使用 composedPath() 获取完整路径
            const path = e.composedPath();

            // 查找最近的带 data-action 的元素
            const actionElement = path.find(el =>
                el.dataset && el.dataset.action
            );

            if (actionElement) {
                const action = actionElement.dataset.action;

                // 查找最近的 .item 元素获取 item ID
                const itemElement = path.find(el =>
                    el.classList && el.classList.contains('item')
                );
                const itemId = itemElement?.dataset.id;

                console.log('执行操作:', action, 'on item:', itemId);

                // 触发自定义事件通知外部
                this.dispatchEvent(new CustomEvent('item-action', {
                    bubbles: true,
                    composed: true,
                    detail: { action, itemId }
                }));
            }
        });
    }
}

customElements.define('delegation-component', DelegationComponent);
```

使用:

```html
<delegation-component id="list"></delegation-component>

<script>
document.getElementById('list').addEventListener('item-action', (e) => {
    console.log('外部监听到操作:');
    console.log('  action:', e.detail.action);
    console.log('  itemId:', e.detail.itemId);

    if (e.detail.action === 'delete') {
        if (confirm(`确定删除 item ${e.detail.itemId}?`)) {
            // 执行删除逻辑
        }
    }
});
</script>
```

**事件委托的最佳实践**:

```javascript
class BestDelegationComponent extends HTMLElement {
    connectedCallback() {
        this.addEventListener('click', (e) => {
            const path = e.composedPath();

            // 策略 1: 查找特定类名的元素
            const button = path.find(el =>
                el.classList && el.classList.contains('action-btn')
            );

            // 策略 2: 查找特定标签的元素
            const link = path.find(el => el.tagName === 'A');

            // 策略 3: 查找带特定属性的元素
            const actionElement = path.find(el =>
                el.dataset && el.dataset.action
            );

            // 策略 4: 查找特定 ID 的元素
            const closeBtn = path.find(el => el.id === 'close-btn');

            // 根据不同元素执行不同操作
            if (closeBtn) {
                this.close();
            } else if (actionElement) {
                this.handleAction(actionElement.dataset.action);
            } else if (link) {
                this.handleLinkClick(link);
            }
        });
    }
}
```

---

**事故档案编号**: NETWORK-2024-1968
**影响范围**: Shadow DOM 事件系统, 事件传播, 事件重定向, composedPath, 事件委托
**根本原因**: 在 Shadow DOM 内部调用 stopPropagation() 阻止了事件穿透, 且对 Slot 内容事件传播机制理解不足
**学习成本**: 中高 (需理解事件传播路径、target 重定向规则、composed 属性、composedPath 用法)

这是 JavaScript 世界第 168 次被记录的网络与数据事故。Shadow DOM 事件传播遵循 composed 属性控制穿透边界, 大多数原生 UI 事件默认 composed: true 可以穿透但 target 会被重定向为 Shadow Host。Slot 内容的事件不会被重定向因为它们起源于 Light DOM, 事件冒泡过程中不穿越 Shadow DOM 边界。composedPath() 方法返回包含 Shadow DOM 内部元素的完整事件路径, 是获取真实事件目标的唯一方法, 在事件委托中必须使用而非依赖 target。自定义事件默认 composed: false 无法穿透 Shadow DOM, 必须显式设置 composed: true。在 Shadow DOM 内部调用 stopPropagation() 会阻止事件继续冒泡无法穿透到外部, 即使 composed: true 也无效。多层嵌套 Shadow DOM 会导致 target 每穿过一层边界就重定向一次, 外部只能看到最外层 Shadow Host。currentTarget 始终是监听器绑定的元素不会被重定向, 与 target 的重定向无关。理解 Shadow DOM 事件传播的边界规则和重定向机制是构建健壮 Web Components 的关键。

---
