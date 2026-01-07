《第 166 次记录: 周四下午的分享会争论 —— Slot 插槽的内容投射之谜》

---

## 技术分享会现场

周四下午 3 点, 你站在会议室的投影仪前, 准备展示这周完成的新组件库。

"这是我用 Web Components 重构的卡片组件, " 你点开 Demo 页面, "完全封装, 样式隔离, 可以在任何项目中复用。"

屏幕上显示着一个精美的卡片: 圆角边框、阴影效果、标题和内容整齐排列。前端组的同事们点头表示认可。

"但有个问题, " 坐在第一排的小李举手, "如果我想自定义卡片的内容怎么办? 你这个组件把 HTML 都写死在 Shadow DOM 里了。"

你愣了一下。确实, 你的实现是这样的: 所有内容都在组件内部定义, 使用者只能通过属性传递纯文本。但小李说得对 —— 如果用户想放一个按钮、一张图片、或者复杂的表单进去呢?

"我可以加更多属性啊, " 你试图辩解, "比如 `image-url`、`button-text`..."

"那如果我想放一个视频播放器呢?" 架构师老王在后排发话, "你打算为每种可能的内容都加一个属性?"

会议室陷入短暂的沉默。你意识到这是个根本性的问题: **如何让一个封闭的组件接受外部的任意内容?**

"Shadow DOM 不是把内部和外部隔离了吗?" 你困惑地想, "那用户传进来的 HTML 要怎么显示?"

---

## 同事的点拨

"你听说过 `<slot>` 吗?" 老王走到白板前, 画了一个简单的示意图。

"Slot? " 你摇头, "是 Web Components 的 API 吗?"

"对, " 老王解释, "它就像是 Shadow DOM 上开的一个'窗口', 可以让外部内容投射进来。你的组件定义插槽位置, 用户填充插槽内容。"

你还是有点懵: "投射? 内容不是应该在 Light DOM 里吗? Shadow DOM 怎么访问?"

老王在白板上写下一段代码:

```javascript
// 你的组件定义
class MyCard extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    border: 1px solid #ddd;
                    padding: 16px;
                    border-radius: 8px;
                }
            </style>
            <div class="card">
                <slot></slot>  <!-- 这是插槽 -->
            </div>
        `;
    }
}
```

"然后用户这样使用:"

```html
<my-card>
    <h2>这是标题</h2>
    <p>这是内容</p>
    <button>点击按钮</button>
</my-card>
```

"等等, " 你盯着代码, "用户写在 `<my-card>` 里面的 HTML, 会**自动显示在** Shadow DOM 的 `<slot>` 位置?"

"对, " 小李补充, "这就是 slot 的魔法。用户的内容看起来在你的组件里, 但实际上还是在 Light DOM 中, 只是**渲染位置**被投射到了 Shadow DOM 里。"

你皱起眉头: "这不是违背了 Shadow DOM 的封装原则吗? 外部内容怎么能进入封闭的 Shadow DOM?"

"不是进入, " 老王强调, "是**投射**。想象 Shadow DOM 是一个房间, slot 是房间墙上的一个窗口。外部内容还在外面, 但通过窗口, 你能在房间里看到它。"

"而且, " 小李补充, "用户的内容仍然受外部 CSS 影响, 而不是 Shadow DOM 内部的样式。"

你决定回到座位上亲自试一试。

---

## 动手验证

分享会结束后, 你回到工位, 打开刚才的组件代码。你想验证老王说的"投射"到底是怎么回事。

你修改了组件定义:

```javascript
class SlotDemo extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .container {
                    border: 2px solid blue;
                    padding: 20px;
                }
                /* Shadow DOM 的样式 */
                p {
                    color: red;
                    font-size: 24px;
                }
            </style>
            <div class="container">
                <h3>Shadow DOM 内容</h3>
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('slot-demo', SlotDemo);
```

然后在 HTML 中测试:

```html
<style>
    /* 外部样式 */
    p {
        color: green;
        font-size: 16px;
    }
</style>

<slot-demo>
    <p>这个段落会是什么颜色? 什么字号?</p>
</slot-demo>
```

你刷新页面, 结果让你吃惊: 段落显示的是**绿色 16px**, 而不是 Shadow DOM 里定义的红色 24px!

"所以用户的内容确实还在 Light DOM 里, " 你明白了, "只是渲染位置被投射到了 Shadow DOM 的 slot 位置。样式也还是外部的样式。"

你打开 DevTools 的 Elements 面板, 仔细观察 DOM 结构:

```html
<slot-demo>
    #shadow-root (open)
        <style>...</style>
        <div class="container">
            <h3>Shadow DOM 内容</h3>
            <slot>
                ↳ <p>这个段落会是什么颜色? 什么字号?</p>
            </slot>
        </div>
    <p>这个段落会是什么颜色? 什么字号?</p>
</slot-demo>
```

"原来如此, " 你恍然大悟, "`<p>` 标签实际上还在 `<slot-demo>` 的 Light DOM 中, 但通过 `<slot>`, 它的**渲染内容**出现在了 Shadow DOM 的 `.container` 里面。这就是'投射'的含义。"

但这又引发了新问题: "如果我想在不同位置放不同的内容呢? 比如卡片的头部、主体、底部?"

---

## 具名插槽的发现

你想起老王提到过"具名插槽"。你查阅 MDN 文档, 发现 `<slot>` 可以有 `name` 属性。

你重新设计组件:

```javascript
class FlexibleCard extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    overflow: hidden;
                }
                .header {
                    background: #007bff;
                    color: white;
                    padding: 16px;
                    font-weight: bold;
                }
                .body {
                    padding: 16px;
                }
                .footer {
                    background: #f5f5f5;
                    padding: 12px;
                    text-align: right;
                    font-size: 12px;
                }
            </style>
            <div class="card">
                <div class="header">
                    <slot name="header">默认标题</slot>
                </div>
                <div class="body">
                    <slot>默认内容</slot>
                </div>
                <div class="footer">
                    <slot name="footer">默认页脚</slot>
                </div>
            </div>
        `;
    }
}

customElements.define('flexible-card', FlexibleCard);
```

"我定义了三个插槽, " 你分析着代码:
- `<slot name="header">`: 具名插槽, 用于头部
- `<slot>`: 默认插槽 (没有 name 属性), 用于主体
- `<slot name="footer">`: 具名插槽, 用于页脚

"而且每个插槽都有默认内容, 如果用户不提供, 就显示默认值。"

你测试使用方式:

```html
<flexible-card>
    <!-- slot="header" 指定内容去 header 插槽 -->
    <span slot="header">自定义标题</span>

    <!-- 没有 slot 属性的内容去默认插槽 -->
    <p>这是卡片的主要内容...</p>
    <p>可以有多个段落</p>

    <!-- slot="footer" 指定内容去 footer 插槽 -->
    <small slot="footer">2024-01-15</small>
</flexible-card>
```

刷新页面, 效果完美! 三个区域的内容都正确显示在了对应位置。

"所以具名插槽的工作原理是, " 你总结道:
1. 组件定义 `<slot name="xxx">`
2. 用户在元素上添加 `slot="xxx"` 属性
3. 浏览器自动将带 `slot` 属性的元素投射到对应的具名插槽
4. 没有 `slot` 属性的元素投射到默认插槽 (没有 `name` 的 `<slot>`)
5. 如果某个插槽没有对应内容, 显示插槽的默认内容

你又测试了一个边界情况:

```html
<flexible-card>
    <!-- 只提供 header 和 body, 不提供 footer -->
    <span slot="header">只有标题</span>
    <p>只有内容</p>
</flexible-card>
```

结果显示: header 和 body 正常, footer 显示了默认的"默认页脚"。

"很合理, " 你点头, "这样用户可以按需提供内容, 不需要的部分就用默认值。"

---

## Slot 的 JavaScript 访问

第二天上午, 你想知道能否用 JavaScript 检测和操作 slot 的内容。

你查阅文档后发现, `<slot>` 元素有一些特殊的 API:

```javascript
class SlotAwareCard extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card { border: 1px solid #ddd; padding: 16px; }
            </style>
            <div class="card">
                <slot></slot>
            </div>
        `;

        // 获取 slot 元素
        const slot = shadow.querySelector('slot');

        // 监听 slot 内容变化
        slot.addEventListener('slotchange', (e) => {
            console.log('Slot 内容变化了!');

            // 获取分配到 slot 的节点
            const assignedNodes = slot.assignedNodes();
            console.log('分配的节点:', assignedNodes);

            // 只获取元素节点 (排除文本节点)
            const assignedElements = slot.assignedElements();
            console.log('分配的元素:', assignedElements);

            // 统计内容
            console.log(`Slot 中有 ${assignedElements.length} 个元素`);
        });
    }
}

customElements.define('slot-aware-card', SlotAwareCard);
```

你测试这个组件:

```html
<slot-aware-card id="card1">
    <p>段落 1</p>
    <p>段落 2</p>
    <span>一些文本</span>
</slot-aware-card>

<script>
setTimeout(() => {
    const card = document.getElementById('card1');

    // 动态添加内容
    const newP = document.createElement('p');
    newP.textContent = '动态添加的段落';
    card.appendChild(newP);

    // slotchange 事件会触发
}, 2000);
</script>
```

控制台输出:

```
Slot 内容变化了!
分配的节点: NodeList(5) [text, p, text, p, text, span, text]
分配的元素: (3) [p, p, span]
Slot 中有 3 个元素

(2 秒后)
Slot 内容变化了!
分配的节点: NodeList(7) [text, p, text, p, text, span, text, p]
分配的元素: (4) [p, p, span, p]
Slot 中有 4 个元素
```

"原来如此, " 你理解了:
- `assignedNodes()` 返回所有节点, 包括文本节点
- `assignedElements()` 只返回元素节点, 更常用
- `slotchange` 事件在 slot 内容变化时触发
- 可以用这些 API 实现动态响应

你又尝试了具名插槽的访问:

```javascript
class MultiSlotCard extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .header { background: #007bff; color: white; padding: 12px; }
                .body { padding: 16px; }
            </style>
            <div class="card">
                <div class="header">
                    <slot name="header"></slot>
                </div>
                <div class="body">
                    <slot></slot>
                </div>
            </div>
        `;

        // 访问具名插槽
        const headerSlot = shadow.querySelector('slot[name="header"]');
        const defaultSlot = shadow.querySelector('slot:not([name])');

        headerSlot.addEventListener('slotchange', () => {
            const elements = headerSlot.assignedElements();
            console.log('Header slot 内容:', elements);

            // 如果 header 为空, 可以隐藏整个 header 区域
            const headerDiv = shadow.querySelector('.header');
            headerDiv.style.display = elements.length > 0 ? 'block' : 'none';
        });

        defaultSlot.addEventListener('slotchange', () => {
            const elements = defaultSlot.assignedElements();
            console.log('Default slot 内容:', elements);
        });
    }
}

customElements.define('multi-slot-card', MultiSlotCard);
```

测试:

```html
<!-- 情况 1: 提供 header -->
<multi-slot-card>
    <span slot="header">有标题</span>
    <p>有内容</p>
</multi-slot-card>

<!-- 情况 2: 不提供 header -->
<multi-slot-card>
    <p>只有内容, 没有标题</p>
</multi-slot-card>
```

第二个卡片的 header 区域被自动隐藏了!

"这样就能根据用户是否提供内容来动态调整组件结构, " 你满意地想, "很灵活。"

---

## Slot 的样式控制

下午, 你想知道如何在 Shadow DOM 内部样式化 slot 的内容。

你尝试直接选择:

```javascript
shadow.innerHTML = `
    <style>
        .card { padding: 16px; }

        /* 尝试 1: 直接选择器 */
        p {
            color: red;  /* 能选中 slot 里的 p 吗? */
        }
    </style>
    <div class="card">
        <slot></slot>
    </div>
`;
```

测试后发现: **完全不起作用**。Slot 里的 `<p>` 还是外部的样式。

"对了, " 你想起来, "slot 的内容实际上还在 Light DOM 里, Shadow DOM 的样式选择器当然选不中它们。"

你查阅文档, 发现了 `::slotted()` 伪元素:

```javascript
shadow.innerHTML = `
    <style>
        .card {
            padding: 16px;
            border: 1px solid #ddd;
        }

        /* ::slotted() 可以选择 slot 中的内容 */
        ::slotted(p) {
            margin-bottom: 12px;
            line-height: 1.6;
        }

        ::slotted(h2) {
            color: #007bff;
            margin-top: 0;
        }

        ::slotted(.highlight) {
            background: yellow;
            padding: 4px;
        }

        /* 选择所有 slot 内容 */
        ::slotted(*) {
            box-sizing: border-box;
        }
    </style>
    <div class="card">
        <slot></slot>
    </div>
`;
```

测试:

```html
<style>
    /* 外部样式 */
    p { font-size: 14px; }
</style>

<slot-styled-card>
    <h2>标题会是蓝色</h2>
    <p>段落会有 margin-bottom 和 line-height</p>
    <p class="highlight">高亮段落会有黄色背景</p>
</slot-styled-card>
```

效果完美! 但你又发现了一个限制:

```javascript
// ❌ 这些选择器不会生效
::slotted(div p) {
    /* 无法选择 div 内部的 p */
}

::slotted(p span) {
    /* 无法选择 p 内部的 span */
}
```

你测试证实了: **`::slotted()` 只能选择 slot 的直接子元素, 无法深入后代。**

```html
<slot-styled-card>
    <!-- ✅ 可以被 ::slotted(p) 选中 -->
    <p>直接子元素</p>

    <!-- ❌ 不能被 ::slotted(p) 选中 -->
    <div>
        <p>嵌套在 div 里的 p</p>
    </div>
</slot-styled-card>
```

"这是个限制, " 你记下来, "如果需要深度样式化 slot 内容, 只能通过外部 CSS, 或者让用户自己添加样式。"

你又尝试了具名插槽的样式:

```javascript
shadow.innerHTML = `
    <style>
        /* 默认 slot 的样式 */
        ::slotted(*) {
            margin: 8px 0;
        }

        /* 具名 slot 的样式 */
        slot[name="header"]::slotted(*) {
            font-size: 24px;
            font-weight: bold;
            color: white;
        }

        slot[name="footer"]::slotted(*) {
            font-size: 12px;
            color: #666;
        }
    </style>
    <div class="card">
        <div class="header">
            <slot name="header"></slot>
        </div>
        <div class="body">
            <slot></slot>
        </div>
        <div class="footer">
            <slot name="footer"></slot>
        </div>
    </div>
`;
```

"可以针对不同的 slot 设置不同的样式, " 你满意地点头, "这样组件的样式控制就很灵活了。"

---

## 高级应用场景

周五下午, 你决定用 slot 重构之前的卡片组件库。

### 场景 1: 可折叠卡片

```javascript
class CollapsibleCard extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    overflow: hidden;
                }
                .header {
                    background: #f5f5f5;
                    padding: 12px 16px;
                    cursor: pointer;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .header:hover {
                    background: #e8e8e8;
                }
                .toggle {
                    transition: transform 0.3s;
                }
                .toggle.collapsed {
                    transform: rotate(-90deg);
                }
                .body {
                    padding: 16px;
                    max-height: 500px;
                    overflow: hidden;
                    transition: max-height 0.3s, padding 0.3s;
                }
                .body.collapsed {
                    max-height: 0;
                    padding: 0 16px;
                }

                ::slotted([slot="title"]) {
                    font-weight: bold;
                    font-size: 16px;
                }
            </style>
            <div class="card">
                <div class="header">
                    <slot name="title">Collapsible Card</slot>
                    <span class="toggle">▼</span>
                </div>
                <div class="body">
                    <slot></slot>
                </div>
            </div>
        `;

        this._header = shadow.querySelector('.header');
        this._body = shadow.querySelector('.body');
        this._toggle = shadow.querySelector('.toggle');
        this._collapsed = false;

        this._header.addEventListener('click', () => {
            this._collapsed = !this._collapsed;
            this._body.classList.toggle('collapsed');
            this._toggle.classList.toggle('collapsed');

            this.dispatchEvent(new CustomEvent('toggle', {
                detail: { collapsed: this._collapsed }
            }));
        });
    }

    // 公开 API
    get collapsed() {
        return this._collapsed;
    }

    collapse() {
        if (!this._collapsed) {
            this._header.click();
        }
    }

    expand() {
        if (this._collapsed) {
            this._header.click();
        }
    }
}

customElements.define('collapsible-card', CollapsibleCard);
```

使用:

```html
<collapsible-card>
    <span slot="title">可折叠的卡片</span>

    <p>这是卡片的内容...</p>
    <p>可以放任何 HTML 元素</p>
    <button>甚至可以放按钮</button>
    <img src="image.jpg" alt="图片">
</collapsible-card>

<script>
const card = document.querySelector('collapsible-card');

card.addEventListener('toggle', (e) => {
    console.log('卡片状态:', e.detail.collapsed ? '折叠' : '展开');
});

// 通过 API 控制
setTimeout(() => {
    card.collapse();  // 3 秒后自动折叠
}, 3000);
</script>
```

### 场景 2: 标签页组件

```javascript
class TabPanel extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .tabs {
                    display: flex;
                    border-bottom: 2px solid #ddd;
                }
                .panel {
                    padding: 16px;
                }

                ::slotted([slot^="tab-"]) {
                    display: none;
                }
                ::slotted([slot^="tab-"].active) {
                    display: block;
                }
            </style>
            <div class="tabs">
                <slot name="tabs"></slot>
            </div>
            <div class="panel">
                <slot name="tab-1" class="active"></slot>
                <slot name="tab-2"></slot>
                <slot name="tab-3"></slot>
            </div>
        `;
    }
}

customElements.define('tab-panel', TabPanel);
```

使用:

```html
<tab-panel>
    <button slot="tabs" data-tab="1">标签 1</button>
    <button slot="tabs" data-tab="2">标签 2</button>
    <button slot="tabs" data-tab="3">标签 3</button>

    <div slot="tab-1">
        <h3>标签 1 的内容</h3>
        <p>这里是第一个标签的内容...</p>
    </div>

    <div slot="tab-2">
        <h3>标签 2 的内容</h3>
        <p>这里是第二个标签的内容...</p>
    </div>

    <div slot="tab-3">
        <h3>标签 3 的内容</h3>
        <p>这里是第三个标签的内容...</p>
    </div>
</tab-panel>
```

### 场景 3: 带操作栏的卡片

```javascript
class ActionCard extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    overflow: hidden;
                }
                .header {
                    padding: 16px;
                    background: #f5f5f5;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .body {
                    padding: 16px;
                }
                .footer {
                    padding: 12px 16px;
                    background: #f5f5f5;
                    display: flex;
                    justify-content: flex-end;
                    gap: 8px;
                }

                ::slotted([slot="title"]) {
                    font-size: 18px;
                    font-weight: bold;
                }

                ::slotted([slot="actions"]) {
                    display: inline-flex;
                    gap: 8px;
                }

                ::slotted([slot="footer-actions"]) {
                    /* 按钮样式 */
                }
            </style>
            <div class="card">
                <div class="header">
                    <slot name="title"></slot>
                    <slot name="actions"></slot>
                </div>
                <div class="body">
                    <slot></slot>
                </div>
                <div class="footer">
                    <slot name="footer-actions"></slot>
                </div>
            </div>
        `;
    }
}

customElements.define('action-card', ActionCard);
```

使用:

```html
<action-card>
    <span slot="title">用户信息</span>

    <div slot="actions">
        <button onclick="edit()">编辑</button>
        <button onclick="remove()">删除</button>
    </div>

    <div>
        <p>姓名: 张三</p>
        <p>邮箱: zhangsan@example.com</p>
        <p>电话: 138****1234</p>
    </div>

    <div slot="footer-actions">
        <button onclick="cancel()">取消</button>
        <button onclick="save()">保存</button>
    </div>
</action-card>
```

---

## Slot 的边界与限制

周五傍晚, 你整理这周的收获时, 也记录了 slot 的一些限制和边界情况:

### 限制 1: 默认 slot 只能有一个

```javascript
shadow.innerHTML = `
    <div>
        <slot></slot>  <!-- 第一个默认 slot -->
        <slot></slot>  <!-- 第二个默认 slot -->
    </div>
`;
```

如果有多个没有 `name` 的 `<slot>`, 所有默认内容会被分配到**第一个** slot。

### 限制 2: slot 内容仍在 Light DOM

```javascript
// ❌ 无法通过 Shadow DOM 查询 slot 内容
shadow.querySelector('.user-content');  // null

// ✅ 必须通过 Light DOM 查询
this.querySelector('.user-content');  // 找到了
```

Slot 只是渲染位置的投射, 内容的 DOM 位置没有改变。

### 限制 3: ::slotted() 不能深入后代

```css
/* ✅ 可以 */
::slotted(p) { }
::slotted(.class) { }
::slotted([attr]) { }

/* ❌ 不可以 */
::slotted(div p) { }
::slotted(p span) { }
::slotted(p)::before { }
```

只能选择 slot 的直接子元素。

### 限制 4: Slot 内容的事件

```javascript
class EventSlotCard extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <div class="card">
                <slot></slot>
            </div>
        `;

        // ❌ 这样绑定无效
        const slot = shadow.querySelector('slot');
        slot.addEventListener('click', (e) => {
            console.log('这个事件不会触发');
        });

        // ✅ 应该在 host 上监听
        this.addEventListener('click', (e) => {
            console.log('Click on:', e.target);
            // e.target 是 Light DOM 的元素
        });
    }
}
```

Slot 内容的事件会冒泡到 host 元素, 而不是 slot 元素本身。

### 限制 5: Slot 的循环引用

```javascript
// ❌ 不能把组件本身放进 slot
<my-card>
    <my-card>
        <my-card>...</my-card>
    </my-card>
</my-card>
```

虽然语法上可行, 但要注意避免无限嵌套导致性能问题。

---

## 知识档案: Slot 插槽机制的八个核心特性

**规则 1: Slot 是 Shadow DOM 与 Light DOM 的内容投射通道**

Slot 机制允许 Shadow DOM 接受外部内容而不破坏封装性。组件定义 `<slot>` 元素作为"窗口", 用户的内容通过这个窗口投射到 Shadow DOM 的渲染位置。

```javascript
// 组件定义 slot
class MyComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .wrapper { border: 1px solid #ddd; padding: 16px; }
            </style>
            <div class="wrapper">
                <slot></slot>  <!-- 投射点 -->
            </div>
        `;
    }
}

customElements.define('my-component', MyComponent);
```

使用时:

```html
<my-component>
    <p>这个段落会被投射到 slot 位置</p>
</my-component>
```

**DOM 结构**:
```html
<my-component>
    #shadow-root (open)
        <div class="wrapper">
            <slot>
                ↳ <p>这个段落会被投射到 slot 位置</p>
            </slot>
        </div>
    <p>这个段落会被投射到 slot 位置</p>  <!-- 实际位置仍在 Light DOM -->
</my-component>
```

**关键洞察**: Slot 内容的 DOM 位置没有改变 (仍在 Light DOM), 但**渲染位置**被投射到了 Shadow DOM 内部。

---

**规则 2: Slot 内容保持在 Light DOM, 受外部样式影响**

通过 slot 投射的内容实际上还在组件的 Light DOM 中, 因此它们受外部 CSS 影响, 而不是 Shadow DOM 的内部样式。

```javascript
class StyledComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                /* Shadow DOM 样式 */
                p {
                    color: red;
                    font-size: 24px;
                }
            </style>
            <div>
                <p>Shadow DOM 的段落 (红色 24px)</p>
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('styled-component', StyledComponent);
```

使用:

```html
<style>
    /* 外部样式 */
    p {
        color: blue;
        font-size: 16px;
    }
</style>

<styled-component>
    <p>Slot 的段落 (蓝色 16px)</p>
</styled-component>
```

结果:
- Shadow DOM 内部的 `<p>`: 红色 24px (Shadow DOM 样式)
- Slot 投射的 `<p>`: 蓝色 16px (外部样式)

**样式隔离边界**:
- Shadow DOM → Light DOM: ❌ 内部样式不影响外部
- Light DOM → Shadow DOM: ❌ 外部样式不影响内部
- Light DOM → Slot 内容: ✅ 外部样式影响 slot 内容 (因为 slot 内容在 Light DOM)

---

**规则 3: 具名插槽允许多个内容投射点, 默认插槽接收未指定内容**

通过 `name` 属性, 可以定义多个具名插槽, 实现复杂的内容布局。没有 `name` 的 `<slot>` 是默认插槽。

```javascript
class MultiSlotCard extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card { border: 1px solid #ddd; }
                .header { background: #f5f5f5; padding: 12px; }
                .body { padding: 16px; }
                .footer { background: #f5f5f5; padding: 8px; font-size: 12px; }
            </style>
            <div class="card">
                <div class="header">
                    <slot name="header">Default Header</slot>
                </div>
                <div class="body">
                    <slot></slot>  <!-- 默认插槽 -->
                </div>
                <div class="footer">
                    <slot name="footer">Default Footer</slot>
                </div>
            </div>
        `;
    }
}

customElements.define('multi-slot-card', MultiSlotCard);
```

使用:

```html
<multi-slot-card>
    <!-- slot="header" 指定去 header 插槽 -->
    <span slot="header">Custom Header</span>

    <!-- 没有 slot 属性, 去默认插槽 -->
    <p>Main content paragraph 1</p>
    <p>Main content paragraph 2</p>

    <!-- slot="footer" 指定去 footer 插槽 -->
    <small slot="footer">Custom Footer</small>
</multi-slot-card>
```

**分配规则**:
1. 带 `slot="xxx"` 的元素 → 分配到 `<slot name="xxx">`
2. 不带 `slot` 属性的元素 → 分配到默认 `<slot>` (没有 `name`)
3. 如果某个具名插槽没有对应内容 → 显示插槽的默认内容
4. 如果多个元素指定同一个 `slot` 名 → 都会投射到该插槽 (按顺序)

**默认内容机制**:
```html
<slot name="header">Default Header</slot>
```
- 如果用户提供了 `slot="header"` 的内容 → 显示用户内容
- 如果用户没有提供 → 显示 "Default Header"

---

**规则 4: slotchange 事件和 assignedNodes/Elements API 用于监听和访问 slot 内容**

`<slot>` 元素提供了 JavaScript API 来监听内容变化和访问分配的节点。

```javascript
class SlotAwareComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .container { padding: 16px; }
            </style>
            <div class="container">
                <slot></slot>
            </div>
        `;

        const slot = shadow.querySelector('slot');

        // 监听 slot 内容变化
        slot.addEventListener('slotchange', (e) => {
            console.log('Slot content changed');

            // 获取所有分配的节点 (包括文本节点)
            const allNodes = slot.assignedNodes();
            console.log('All nodes:', allNodes);
            // NodeList [text, p, text, span, text]

            // 获取元素节点 (排除文本节点)
            const elements = slot.assignedElements();
            console.log('Elements only:', elements);
            // [p, span]

            // 带 flatten 选项 (展开嵌套的 slot)
            const flattenedElements = slot.assignedElements({ flatten: true });
            console.log('Flattened:', flattenedElements);
        });
    }

    connectedCallback() {
        // 初始访问 slot 内容
        const slot = this.shadowRoot.querySelector('slot');
        const initialElements = slot.assignedElements();
        console.log('Initial slot content:', initialElements);
    }
}

customElements.define('slot-aware-component', SlotAwareComponent);
```

**API 详解**:

```javascript
const slot = shadow.querySelector('slot');

// assignedNodes(): 返回所有分配的节点 (包括文本节点)
const allNodes = slot.assignedNodes();
// 返回: NodeList [文本节点, 元素, 文本节点, ...]

// assignedElements(): 只返回元素节点
const elements = slot.assignedElements();
// 返回: [元素1, 元素2, ...]

// assignedElements({ flatten: true }): 展开嵌套 slot
// 如果 slot 内容包含其他使用 slot 的组件, flatten 会递归展开
const flattenedElements = slot.assignedElements({ flatten: true });
```

**slotchange 事件触发时机**:
- 组件首次连接到 DOM 时
- 用户动态添加/删除/修改 slot 内容时
- 属性 `slot` 被修改时 (改变内容的插槽分配)

**实际应用**:

```javascript
// 示例 1: 统计 slot 内容
slot.addEventListener('slotchange', () => {
    const count = slot.assignedElements().length;
    console.log(`Slot has ${count} elements`);
});

// 示例 2: 动态隐藏空 slot 区域
headerSlot.addEventListener('slotchange', () => {
    const hasContent = headerSlot.assignedElements().length > 0;
    headerDiv.style.display = hasContent ? 'block' : 'none';
});

// 示例 3: 验证 slot 内容类型
slot.addEventListener('slotchange', () => {
    const elements = slot.assignedElements();
    const hasInvalidElement = elements.some(el => !el.matches('.valid-item'));
    if (hasInvalidElement) {
        console.warn('Slot contains invalid elements');
    }
});
```

---

**规则 5: ::slotted() 伪元素允许 Shadow DOM 样式化 slot 内容, 但只能选择直接子元素**

Shadow DOM 可以使用 `::slotted()` 伪元素来样式化分配到 slot 的内容, 但有严格限制。

```javascript
class StylableSlot extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .container {
                    padding: 16px;
                    border: 1px solid #ddd;
                }

                /* ✅ 可以: 选择 slot 的直接子元素 */
                ::slotted(p) {
                    margin-bottom: 12px;
                    line-height: 1.6;
                }

                ::slotted(h2) {
                    color: #007bff;
                    margin-top: 0;
                }

                ::slotted(.highlight) {
                    background: yellow;
                    padding: 4px;
                }

                ::slotted([data-important]) {
                    border-left: 3px solid red;
                    padding-left: 8px;
                }

                /* 通配符: 选择所有 slot 子元素 */
                ::slotted(*) {
                    box-sizing: border-box;
                }

                /* ❌ 不可以: 无法深入后代 */
                ::slotted(div p) {
                    /* 不生效 */
                }

                ::slotted(p span) {
                    /* 不生效 */
                }

                /* ❌ 不可以: 无法使用伪元素 */
                ::slotted(p)::before {
                    /* 不生效 */
                }

                /* ❌ 不可以: 大多数伪类不支持 */
                ::slotted(p:hover) {
                    /* 可能不生效 */
                }

                /* 具名 slot 的样式 */
                slot[name="header"]::slotted(*) {
                    font-size: 24px;
                    font-weight: bold;
                }

                slot[name="footer"]::slotted(*) {
                    font-size: 12px;
                    color: #666;
                }
            </style>
            <div class="container">
                <div class="header">
                    <slot name="header"></slot>
                </div>
                <div class="body">
                    <slot></slot>
                </div>
                <div class="footer">
                    <slot name="footer"></slot>
                </div>
            </div>
        `;
    }
}

customElements.define('stylable-slot', StylableSlot);
```

使用:

```html
<stylable-slot>
    <span slot="header">Header Content</span>

    <!-- ✅ 这些是 slot 的直接子元素, 可以被 ::slotted() 选中 -->
    <h2>Title (蓝色)</h2>
    <p>Paragraph (margin-bottom, line-height)</p>
    <p class="highlight">Highlighted (黄色背景)</p>
    <p data-important>Important (红色边框)</p>

    <!-- ❌ 嵌套元素不能被 ::slotted(p) 选中 -->
    <div>
        <p>Nested paragraph (不受 ::slotted(p) 影响)</p>
    </div>

    <small slot="footer">Footer Content</small>
</stylable-slot>
```

**::slotted() 限制总结**:

```css
/* ✅ 支持 */
::slotted(*)               /* 通配符 */
::slotted(p)               /* 类型选择器 */
::slotted(.class)          /* 类选择器 */
::slotted([attr])          /* 属性选择器 */
::slotted(p.class[attr])   /* 组合选择器 */

/* ❌ 不支持 */
::slotted(div p)           /* 后代选择器 */
::slotted(p > span)        /* 子选择器 */
::slotted(p + p)           /* 相邻兄弟选择器 */
::slotted(p)::before       /* 伪元素 */
::slotted(p:hover)         /* 大多数伪类 */
```

**为什么有这些限制**:
- Slot 内容在 Light DOM, Shadow DOM 只能"看到"顶层元素
- 深入后代会破坏 Light DOM 的样式封装
- 伪元素和伪类涉及更复杂的渲染流程, 技术上难以实现

**解决方案**:
如果需要深度样式化 slot 内容:
1. 使用外部 CSS 样式化
2. 让用户自己添加样式类
3. 通过 CSS 自定义属性 (CSS 变量) 传递样式值

---

**规则 6: Slot 支持默认内容, 可用于降级体验和占位符**

每个 `<slot>` 元素内部可以定义默认内容, 当用户未提供对应内容时显示。

```javascript
class DefaultSlotCard extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 16px;
                }
                .header {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 12px;
                }
                .body {
                    margin-bottom: 12px;
                }
                .footer {
                    font-size: 12px;
                    color: #666;
                }
            </style>
            <div class="card">
                <div class="header">
                    <slot name="title">
                        <!-- 默认标题 -->
                        <span>Untitled Card</span>
                    </slot>
                </div>
                <div class="body">
                    <slot>
                        <!-- 默认内容 -->
                        <p>No content provided. This is the default message.</p>
                    </slot>
                </div>
                <div class="footer">
                    <slot name="footer">
                        <!-- 默认页脚 -->
                        <small>Created by default</small>
                    </slot>
                </div>
            </div>
        `;
    }
}

customElements.define('default-slot-card', DefaultSlotCard);
```

使用场景:

```html
<!-- 场景 1: 提供所有内容 -->
<default-slot-card>
    <span slot="title">Custom Title</span>
    <p>Custom content here</p>
    <small slot="footer">Custom footer</small>
</default-slot-card>
<!-- 结果: 全部显示用户内容 -->

<!-- 场景 2: 只提供部分内容 -->
<default-slot-card>
    <span slot="title">Only Title</span>
</default-slot-card>
<!-- 结果: -->
<!-- Header: "Only Title" (用户) -->
<!-- Body: "No content provided..." (默认) -->
<!-- Footer: "Created by default" (默认) -->

<!-- 场景 3: 完全不提供内容 -->
<default-slot-card></default-slot-card>
<!-- 结果: 全部显示默认内容 -->
```

**默认内容的显示逻辑**:
```
IF (用户提供了对应 slot 的内容) {
    显示用户内容
} ELSE {
    显示 slot 的默认内容
}
```

**实际应用场景**:

```javascript
// 1. 加载占位符
shadow.innerHTML = `
    <slot name="content">
        <div class="loading">
            <spinner></spinner>
            <p>Loading...</p>
        </div>
    </slot>
`;

// 2. 空状态提示
shadow.innerHTML = `
    <slot name="items">
        <div class="empty-state">
            <p>No items to display</p>
            <button>Add Item</button>
        </div>
    </slot>
`;

// 3. 可选功能区域
shadow.innerHTML = `
    <div class="toolbar">
        <slot name="actions">
            <!-- 如果用户不提供操作按钮, 显示默认的 -->
            <button>Default Action</button>
        </slot>
    </div>
`;

// 4. 降级体验
shadow.innerHTML = `
    <slot name="advanced-feature">
        <!-- 如果用户浏览器不支持高级功能, 显示降级内容 -->
        <div class="fallback">
            Basic version (upgrade your browser)
        </div>
    </slot>
`;
```

**高级用法: 动态检测是否有内容**:

```javascript
constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });

    shadow.innerHTML = `
        <style>
            .section { padding: 16px; }
            .section.empty { display: none; }
        </style>
        <div class="section">
            <h3>Optional Section</h3>
            <slot name="optional"></slot>
        </div>
    `;

    const slot = shadow.querySelector('slot[name="optional"]');
    const section = shadow.querySelector('.section');

    slot.addEventListener('slotchange', () => {
        const hasContent = slot.assignedElements().length > 0;
        section.classList.toggle('empty', !hasContent);
    });
}
```

---

**规则 7: Slot 内容可以是任何 HTML, 包括其他自定义元素和嵌套组件**

Slot 可以接受任意 HTML 内容, 包括文本、元素、SVG、甚至其他 Web Components, 实现复杂的组合模式。

```javascript
class FlexibleContainer extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .container {
                    border: 2px solid #007bff;
                    padding: 20px;
                    border-radius: 8px;
                }
            </style>
            <div class="container">
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('flexible-container', FlexibleContainer);

class NestedCard extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    border: 1px solid #ddd;
                    padding: 12px;
                    margin: 8px 0;
                }
            </style>
            <div class="card">
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('nested-card', NestedCard);
```

使用示例:

```html
<!-- 1. 普通 HTML 元素 -->
<flexible-container>
    <h2>Title</h2>
    <p>Paragraph</p>
    <button>Button</button>
</flexible-container>

<!-- 2. 富文本内容 -->
<flexible-container>
    <article>
        <h1>Article Title</h1>
        <p>Paragraph with <strong>bold</strong> and <em>italic</em>.</p>
        <ul>
            <li>List item 1</li>
            <li>List item 2</li>
        </ul>
    </article>
</flexible-container>

<!-- 3. 表单元素 -->
<flexible-container>
    <form>
        <input type="text" placeholder="Name">
        <input type="email" placeholder="Email">
        <button type="submit">Submit</button>
    </form>
</flexible-container>

<!-- 4. SVG 图形 -->
<flexible-container>
    <svg width="100" height="100">
        <circle cx="50" cy="50" r="40" fill="blue"/>
    </svg>
</flexible-container>

<!-- 5. 嵌套的 Web Components -->
<flexible-container>
    <nested-card>
        <h3>Card 1</h3>
        <p>Content 1</p>
    </nested-card>

    <nested-card>
        <h3>Card 2</h3>
        <p>Content 2</p>
    </nested-card>

    <nested-card>
        <h3>Card 3</h3>
        <flexible-container>
            <p>Even deeper nesting!</p>
        </flexible-container>
    </nested-card>
</flexible-container>

<!-- 6. 混合内容 -->
<flexible-container>
    <!-- 文本 -->
    Plain text

    <!-- 元素 -->
    <p>Paragraph</p>

    <!-- 自定义组件 -->
    <nested-card>Card</nested-card>

    <!-- 更多文本 -->
    More text

    <!-- 图片 -->
    <img src="image.jpg" alt="Image">
</flexible-container>
```

**组合模式示例**:

```javascript
// 布局组件
class GridLayout extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 16px;
                }
            </style>
            <div class="grid">
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('grid-layout', GridLayout);

// 卡片组件
class ProductCard extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 16px;
                }
            </style>
            <div class="card">
                <slot name="image"></slot>
                <slot name="title"></slot>
                <slot name="description"></slot>
                <slot name="price"></slot>
                <slot name="actions"></slot>
            </div>
        `;
    }
}

customElements.define('product-card', ProductCard);
```

使用组合:

```html
<grid-layout>
    <product-card>
        <img slot="image" src="product1.jpg" alt="Product 1">
        <h3 slot="title">Product 1</h3>
        <p slot="description">Description of product 1</p>
        <span slot="price">$99.99</span>
        <button slot="actions">Add to Cart</button>
    </product-card>

    <product-card>
        <img slot="image" src="product2.jpg" alt="Product 2">
        <h3 slot="title">Product 2</h3>
        <p slot="description">Description of product 2</p>
        <span slot="price">$149.99</span>
        <button slot="actions">Add to Cart</button>
    </product-card>

    <product-card>
        <img slot="image" src="product3.jpg" alt="Product 3">
        <h3 slot="title">Product 3</h3>
        <p slot="description">Description of product 3</p>
        <span slot="price">$199.99</span>
        <button slot="actions">Add to Cart</button>
    </product-card>
</grid-layout>
```

**嵌套 Slot 的行为**:

```javascript
// 外层组件
class OuterComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <div class="outer">
                <h2>Outer Component</h2>
                <slot></slot>
            </div>
        `;
    }
}

// 内层组件
class InnerComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <div class="inner">
                <h3>Inner Component</h3>
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('outer-component', OuterComponent);
customElements.define('inner-component', InnerComponent);
```

使用嵌套:

```html
<outer-component>
    <inner-component>
        <p>This content goes through both slots</p>
    </inner-component>
</outer-component>
```

渲染结果:
```html
<outer-component>
    #shadow-root
        <div class="outer">
            <h2>Outer Component</h2>
            <inner-component>
                #shadow-root
                    <div class="inner">
                        <h3>Inner Component</h3>
                        <p>This content goes through both slots</p>
                    </div>
            </inner-component>
        </div>
</outer-component>
```

**关键洞察**: Slot 的灵活性使得 Web Components 可以像乐高积木一样组合, 创建复杂的 UI 结构, 同时保持每个组件的封装性。

---

**规则 8: Slot 的事件冒泡会穿过 Shadow DOM 边界, 但 target 会重定向**

Slot 内容触发的事件会冒泡到 host 元素, 但 `event.target` 会在穿过 Shadow DOM 边界时被重定向。

```javascript
class EventSlotComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .wrapper {
                    border: 2px solid blue;
                    padding: 20px;
                }
            </style>
            <div class="wrapper">
                <h3>Component Header (Shadow DOM)</h3>
                <slot></slot>
            </div>
        `;

        // 在 Shadow DOM 内部监听
        shadow.addEventListener('click', (e) => {
            console.log('Shadow DOM listener:');
            console.log('  target:', e.target);
            console.log('  currentTarget:', e.currentTarget);
            console.log('  composedPath:', e.composedPath());
        });
    }

    connectedCallback() {
        // 在 host 上监听
        this.addEventListener('click', (e) => {
            console.log('Host listener:');
            console.log('  target:', e.target);
            console.log('  currentTarget:', e.currentTarget);
        });
    }
}

customElements.define('event-slot-component', EventSlotComponent);
```

使用和测试:

```html
<event-slot-component id="component">
    <button id="btn">Click Me (Light DOM Button)</button>
</event-slot-component>

<script>
const component = document.getElementById('component');
const button = document.getElementById('btn');

// 外部监听
document.addEventListener('click', (e) => {
    console.log('Document listener:');
    console.log('  target:', e.target);
    console.log('  currentTarget:', e.currentTarget);
});

// 点击 button 时的输出:
</script>
```

**点击 Slot 中的 button 时的事件传播**:

```
1. Shadow DOM listener:
   target: <button id="btn">
   currentTarget: #shadow-root
   composedPath: [button, slot, div.wrapper, #shadow-root, event-slot-component, body, html, document, Window]

2. Host listener:
   target: <event-slot-component>  ← 重定向了!
   currentTarget: <event-slot-component>

3. Document listener:
   target: <event-slot-component>  ← 仍然是重定向后的
   currentTarget: #document
```

**事件重定向规则**:
- **在 Shadow DOM 内部**: `e.target` 是真实的触发元素 (Light DOM 的 `<button>`)
- **跨越 Shadow DOM 边界后**: `e.target` 被重定向为 host 元素 (`<event-slot-component>`)
- **在外部文档**: `e.target` 仍然是 host 元素

**获取真实事件路径**:

```javascript
this.addEventListener('click', (e) => {
    // e.target 已被重定向
    console.log('Redirected target:', e.target);  // <event-slot-component>

    // 使用 composedPath() 获取完整路径
    const path = e.composedPath();
    console.log('Full path:', path);
    // [<button>, <slot>, <div.wrapper>, #shadow-root,
    //  <event-slot-component>, <body>, <html>, document, Window]

    // 找到真实的触发元素
    const realTarget = path[0];
    console.log('Real target:', realTarget);  // <button>

    // 检查是否点击了特定元素
    const isButton = path.some(el => el.tagName === 'BUTTON');
    console.log('Clicked a button:', isButton);
});
```

**stopPropagation 的行为**:

```javascript
class StopPropagationDemo extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <div class="wrapper">
                <slot></slot>
            </div>
        `;

        // 在 Shadow DOM 内部阻止冒泡
        shadow.addEventListener('click', (e) => {
            console.log('Shadow DOM: 捕获到事件');
            // e.stopPropagation();
            // ← 这里调用 stopPropagation 只会阻止在 Shadow DOM 内部的冒泡
            //    事件仍会冒泡到 host 和外部文档
        });
    }

    connectedCallback() {
        // 在 host 上阻止冒泡
        this.addEventListener('click', (e) => {
            console.log('Host: 捕获到事件');
            e.stopPropagation();
            // ← 这里调用才能阻止事件继续冒泡到外部文档
        });
    }
}
```

**composed 属性的影响**:

```javascript
class ComposedEventDemo extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `<slot></slot>`;

        // 监听按钮点击, 触发自定义事件
        shadow.querySelector('slot').addEventListener('slotchange', () => {
            const button = this.querySelector('button');

            button?.addEventListener('click', () => {
                // ❌ composed: false (默认) - 事件不穿透 Shadow DOM
                this.dispatchEvent(new CustomEvent('non-composed-event', {
                    bubbles: true,
                    composed: false,
                    detail: { message: 'This will not reach document' }
                }));

                // ✅ composed: true - 事件穿透 Shadow DOM
                this.dispatchEvent(new CustomEvent('composed-event', {
                    bubbles: true,
                    composed: true,
                    detail: { message: 'This will reach document' }
                }));
            });
        });
    }
}

customElements.define('composed-event-demo', ComposedEventDemo);
```

测试:

```html
<composed-event-demo>
    <button>Trigger Events</button>
</composed-event-demo>

<script>
document.addEventListener('non-composed-event', (e) => {
    console.log('Never fires');  // ❌ 不会触发
});

document.addEventListener('composed-event', (e) => {
    console.log('Fires:', e.detail.message);  // ✅ 会触发
});
</script>
```

**原生事件的 composed 属性**:

大多数原生 UI 事件都是 `composed: true`, 可以穿透 Shadow DOM:

```javascript
// ✅ 这些事件可以穿透 Shadow DOM
- click, dblclick
- mousedown, mouseup, mousemove
- keydown, keyup
- focus, blur (注意: 不冒泡, 使用 focusin/focusout)
- input, change
- submit

// ❌ 这些事件不穿透 Shadow DOM
- load, error, scroll (不冒泡)
- focus, blur (composed: false)
```

**实际应用: 事件委托**:

```javascript
class ListComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .list { padding: 16px; }
            </style>
            <div class="list">
                <slot></slot>
            </div>
        `;
    }

    connectedCallback() {
        // 在 host 上使用事件委托
        this.addEventListener('click', (e) => {
            // 使用 composedPath() 找到真实的点击目标
            const path = e.composedPath();
            const button = path.find(el => el.tagName === 'BUTTON');

            if (button) {
                console.log('Button clicked:', button.textContent);

                // 触发自定义事件, 让外部监听
                this.dispatchEvent(new CustomEvent('item-action', {
                    bubbles: true,
                    composed: true,
                    detail: {
                        action: button.dataset.action,
                        itemId: button.closest('[data-id]')?.dataset.id
                    }
                }));
            }
        });
    }
}

customElements.define('list-component', ListComponent);
```

使用:

```html
<list-component id="list">
    <div data-id="1">
        Item 1
        <button data-action="edit">Edit</button>
        <button data-action="delete">Delete</button>
    </div>
    <div data-id="2">
        Item 2
        <button data-action="edit">Edit</button>
        <button data-action="delete">Delete</button>
    </div>
</list-component>

<script>
document.getElementById('list').addEventListener('item-action', (e) => {
    console.log('Action:', e.detail.action);
    console.log('Item ID:', e.detail.itemId);
});
</script>
```

---

**事故档案编号**: NETWORK-2024-1966
**影响范围**: Slot 插槽机制, Shadow DOM 内容投射, Light DOM 与 Shadow DOM 交互, Web Components 组合模式
**根本原因**: 对 Slot 投射机制理解不足, 误以为 Shadow DOM 完全封闭无法接受外部内容, 忽视了 Slot 的桥接作用
**学习成本**: 中 (需理解 Shadow DOM 边界、Light DOM 与 Shadow DOM 的关系、投射渲染机制、事件重定向规则)

这是 JavaScript 世界第 166 次被记录的网络与数据事故。Slot 是 Shadow DOM 与 Light DOM 之间的内容投射通道, 允许封闭的 Shadow DOM 接受外部内容而不破坏封装性。Slot 内容的 DOM 位置保持在 Light DOM (受外部样式影响), 但渲染位置被投射到 Shadow DOM 的 slot 元素位置。具名插槽通过 name 属性支持多个投射点, 默认插槽接收未指定 slot 属性的内容, 每个插槽可定义默认内容作为降级体验。slotchange 事件和 assignedNodes/Elements API 用于监听和访问分配到 slot 的内容。::slotted() 伪元素允许 Shadow DOM 样式化 slot 内容但只能选择直接子元素无法深入后代。Slot 可以接受任意 HTML 内容包括嵌套的 Web Components 实现复杂组合模式。Slot 内容触发的事件会冒泡穿过 Shadow DOM 边界但 event.target 会被重定向为 host 元素, 使用 composedPath() 可获取包含真实触发元素的完整事件路径。理解 Slot 的投射机制和边界规则是构建灵活可组合 Web Components 的关键。

---
