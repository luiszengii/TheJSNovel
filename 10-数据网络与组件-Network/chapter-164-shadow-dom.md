《第 164 次记录: 周三的重构困境 —— Shadow DOM 封闭子树的样式隔离之谜》

---

## 遗留组件的改造计划

周三上午 9 点半, 你打开项目中的 `legacy-components/` 目录, 盯着这些运行了三年的老组件, 心情复杂。

上周的技术债务评审会上, 架构师老王提出了一个大胆的方案: "我们的组件库已经有 200 多个组件了, 但样式冲突问题越来越严重。我建议用 Shadow DOM 重构核心组件, 实现真正的样式隔离。"

前端组长小张当场反对: "Shadow DOM 太激进了, 我们的样式系统都是基于全局 CSS 的, 改动风险太大。" 但老王的数据很有说服力: 过去一年, 30% 的线上 bug 都与样式冲突有关, CSS 特异性战争已经让团队疲于奔命。

最终团队决定: 选 5 个基础组件做 PoC (Proof of Concept), 你负责第一个 —— 重构 `<app-modal>` 对话框组件。

你深吸一口气, 创建了新文件 `modal-v2.js`。这次重构的核心目标很明确: 用 Shadow DOM 实现完全的样式封闭, 让组件内部样式与页面样式彻底隔离。

"应该不会太难, " 你想, "只要把原来的 innerHTML 改成 shadowRoot.innerHTML 就行了。"

---

## 第一个障碍: 样式丢失

你快速写下了第一版代码:

```javascript
// modal-v2.js - 初版实现
class AppModal extends HTMLElement {
    constructor() {
        super();

        // 创建 Shadow DOM
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <div class="modal-overlay">
                <div class="modal-container">
                    <slot></slot>
                </div>
            </div>
        `;
    }
}

customElements.define('app-modal', AppModal);
```

你在测试页面中使用它:

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="global-styles.css">
</head>
<body>
    <app-modal>
        <h2>对话框标题</h2>
        <p>这是对话框的内容。</p>
    </app-modal>

    <script src="modal-v2.js"></script>
</body>
</html>
```

刷新页面, 你愣住了。

对话框出现了, 但完全没有样式 —— 既没有原本全局 CSS 中定义的 `.modal-overlay` 背景半透明黑色, 也没有 `.modal-container` 的白色卡片样式。整个组件看起来像是裸奔的 HTML。

"怎么回事?" 你打开 DevTools, 检查元素结构。你看到了一个奇怪的现象:

```html
<app-modal>
    #shadow-root (open)
        <div class="modal-overlay">
            <div class="modal-container">
                <slot>
                    ↳ <h2>对话框标题</h2>
                    ↳ <p>这是对话框的内容。</p>
                </slot>
            </div>
        </div>
</app-modal>
```

你注意到一个特殊的标记: `#shadow-root (open)`。

"难道 Shadow DOM 会阻止外部样式?" 你想起老王之前说的 "样式隔离", 但你以为隔离是单向的 —— 阻止组件内部样式泄漏到外部, 而不是阻止外部样式进入组件。

你打开 `global-styles.css`, 确认样式确实存在:

```css
/* global-styles.css */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-container {
    background: white;
    border-radius: 8px;
    padding: 24px;
    max-width: 600px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
```

但这些样式完全没有应用到 Shadow DOM 内部的元素上。

你突然意识到问题的严重性: "Shadow DOM 的样式隔离是**双向**的 —— 外部样式进不来, 内部样式也出不去。"

---

## 样式重建: 封闭世界的代价

你意识到必须把所有样式都写到 Shadow DOM 内部。你修改代码:

```javascript
class AppModal extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                /* ✅ Shadow DOM 内部样式 */
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .modal-container {
                    background: white;
                    border-radius: 8px;
                    padding: 24px;
                    max-width: 600px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                }
            </style>

            <div class="modal-overlay">
                <div class="modal-container">
                    <slot></slot>
                </div>
            </div>
        `;
    }
}
```

刷新页面, 对话框终于有样式了! 背景半透明, 容器白色卡片, 一切正常。

但你很快发现了第二个问题: **slot 投射的内容样式丢失了**。

你在页面中给对话框传入了一些内容:

```html
<app-modal>
    <h2 class="modal-title">对话框标题</h2>
    <p class="modal-text">这是对话框的内容。</p>
    <button class="btn-primary">确认</button>
</app-modal>
```

你的全局样式中定义了这些类:

```css
/* global-styles.css */
.modal-title {
    font-size: 24px;
    color: #333;
    margin-bottom: 16px;
}

.modal-text {
    font-size: 16px;
    color: #666;
    line-height: 1.6;
}

.btn-primary {
    background: #007bff;
    color: white;
    padding: 12px 24px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
```

但页面上的按钮没有蓝色背景, 标题也不是 24px。

"等等, " 你看着 DevTools 的 Elements 面板, 突然明白了: "slot 投射的内容属于 **Light DOM**, 不属于 Shadow DOM。Light DOM 的样式应该受全局 CSS 影响才对。"

但事实是 —— 这些全局样式确实生效了, 只是你写的样式太弱了。你意识到问题所在: 全局 CSS 中这些类的选择器权重不够, 被浏览器默认样式覆盖了。

你在全局样式中加了更高的权重:

```css
/* global-styles.css */
app-modal .modal-title {
    font-size: 24px;
    color: #333;
    margin-bottom: 16px;
}

app-modal .modal-text {
    font-size: 16px;
    color: #666;
    line-height: 1.6;
}

app-modal .btn-primary {
    background: #007bff;
    color: white;
    padding: 12px 24px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
```

刷新页面, 样式生效了。你松了一口气。

---

## 第二个障碍: 主题定制需求

正当你准备提交代码时, 产品经理发来消息: "对话框能不能支持深色模式? 我们要根据用户设置动态切换主题。"

你皱起眉头。如果是以前的全局 CSS, 只需要给 `<body>` 加一个 `.dark-theme` 类, 所有样式都会自动切换。但现在 Shadow DOM 隔离了外部样式, 你该怎么让组件响应外部的主题变化?

你想到了第一个方案: **属性传递**。

```javascript
class AppModal extends HTMLElement {
    static get observedAttributes() {
        return ['theme'];
    }

    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.render();
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'theme' && oldValue !== newValue) {
            this.render();
        }
    }

    render() {
        const theme = this.getAttribute('theme') || 'light';

        this.shadowRoot.innerHTML = `
            <style>
                .modal-overlay {
                    background: ${theme === 'dark' ? 'rgba(0, 0, 0, 0.8)' : 'rgba(0, 0, 0, 0.5)'};
                }

                .modal-container {
                    background: ${theme === 'dark' ? '#333' : 'white'};
                    color: ${theme === 'dark' ? 'white' : '#333'};
                }
            </style>

            <div class="modal-overlay">
                <div class="modal-container">
                    <slot></slot>
                </div>
            </div>
        `;
    }
}
```

使用时:

```html
<app-modal theme="dark">
    <h2>深色主题对话框</h2>
</app-modal>
```

你测试了一下, 功能确实可以工作。但你很快意识到这个方案的问题:

1. **每个组件都要手动传 theme 属性** —— 如果页面有 50 个组件, 就要写 50 次 `theme="dark"`
2. **动态切换需要手动更新所有组件** —— 用户切换主题时, 要遍历所有组件修改属性
3. **代码重复** —— 每个组件都要写相似的主题切换逻辑

你在团队群里问了老王: "Shadow DOM 的样式隔离太强了, 怎么实现主题定制?"

老王回复: "用 CSS 自定义属性。Shadow DOM 不阻止 CSS 变量的继承。"

你眼前一亮。

---

## CSS 自定义属性: 穿透封闭的通道

你重写了组件, 使用 CSS 变量:

```javascript
class AppModal extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    /* ✅ 使用 CSS 变量, 允许外部定制 */
                    background: var(--modal-overlay-bg, rgba(0, 0, 0, 0.5));
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .modal-container {
                    /* ✅ 使用 CSS 变量 */
                    background: var(--modal-bg, white);
                    color: var(--modal-color, #333);
                    border-radius: var(--modal-radius, 8px);
                    padding: var(--modal-padding, 24px);
                    max-width: var(--modal-max-width, 600px);
                    box-shadow: var(--modal-shadow, 0 4px 12px rgba(0, 0, 0, 0.15));
                }
            </style>

            <div class="modal-overlay">
                <div class="modal-container">
                    <slot></slot>
                </div>
            </div>
        `;
    }
}

customElements.define('app-modal', AppModal);
```

然后在全局样式中定义主题:

```css
/* global-styles.css */

/* 浅色主题 (默认) */
:root {
    --modal-overlay-bg: rgba(0, 0, 0, 0.5);
    --modal-bg: white;
    --modal-color: #333;
    --modal-radius: 8px;
    --modal-padding: 24px;
    --modal-max-width: 600px;
    --modal-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 深色主题 */
body.dark-theme {
    --modal-overlay-bg: rgba(0, 0, 0, 0.8);
    --modal-bg: #333;
    --modal-color: white;
    --modal-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}
```

你测试了一下, 惊喜地发现:

```javascript
// 切换主题只需要一行代码
document.body.classList.toggle('dark-theme');
```

所有使用 Shadow DOM 的对话框组件都会自动响应主题变化! CSS 变量成功穿透了 Shadow DOM 的边界。

"原来如此, " 你明白了, "Shadow DOM 阻止的是**样式规则**的渗透, 但不阻止 **CSS 变量值**的继承。"

---

## 第三个障碍: slot 内容的样式控制

正当你以为问题解决了, 新的需求又来了。UI 设计师说: "对话框内部的段落间距太紧了, 能不能让 slot 投射的 `<p>` 标签自动有 16px 的下边距?"

你想: "简单, 在 Shadow DOM 样式里加个 `p { margin-bottom: 16px; }` 就行了。"

```javascript
shadow.innerHTML = `
    <style>
        /* 尝试 1: 直接选择器 */
        p {
            margin-bottom: 16px;
        }
    </style>

    <div class="modal-overlay">
        <div class="modal-container">
            <slot></slot>
        </div>
    </div>
`;
```

刷新页面 —— 没有效果。

"为什么?" 你困惑了。你打开 DevTools, 仔细查看 DOM 结构:

```html
<app-modal>
    #shadow-root (open)
        <style>p { margin-bottom: 16px; }</style>
        <div class="modal-overlay">
            <div class="modal-container">
                <slot>
                    ↳ <p>这是段落 1</p>
                    ↳ <p>这是段落 2</p>
                </slot>
            </div>
        </div>
</app-modal>
```

你注意到: **`<p>` 标签并不在 Shadow DOM 内部, 而是在 Light DOM 中, 只是被 slot 投射到了 Shadow DOM 的渲染位置。**

"Shadow DOM 的样式规则无法选中 Light DOM 的元素, " 你意识到, "即使它们被 slot 投射进来了。"

你查阅文档, 发现了 `::slotted()` 伪元素:

```javascript
shadow.innerHTML = `
    <style>
        /* ✅ 使用 ::slotted() 选择 slot 内容 */
        ::slotted(p) {
            margin-bottom: 16px;
        }
    </style>

    <div class="modal-overlay">
        <div class="modal-container">
            <slot></slot>
        </div>
    </div>
`;
```

刷新页面, 样式生效了! 所有投射到 slot 的 `<p>` 标签都有了 16px 的下边距。

但你又发现了新问题: `::slotted()` 只能选择**直接子元素**, 无法选择后代元素。

比如如果 slot 内容是这样:

```html
<app-modal>
    <div>
        <p>嵌套的段落</p>
    </div>
</app-modal>
```

`::slotted(p)` 就无法选中这个 `<p>`, 因为它不是 slot 的直接子元素。你必须写:

```css
::slotted(div) {
    /* 只能选中 div, 无法深入选中 div 内的 p */
}
```

"限制太多了, " 你叹气, "Shadow DOM 的样式隔离虽然强大, 但代价是灵活性的丧失。"

---

## 第四个障碍: 事件重定向之谜

对话框功能基本完成后, 你开始实现关闭按钮。你在组件内部添加了一个关闭按钮:

```javascript
shadow.innerHTML = `
    <style>
        .close-btn {
            position: absolute;
            top: 16px;
            right: 16px;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: var(--modal-color, #333);
        }
    </style>

    <div class="modal-overlay">
        <div class="modal-container">
            <button class="close-btn">×</button>
            <slot></slot>
        </div>
    </div>
`;

// 添加事件监听
shadow.querySelector('.close-btn').addEventListener('click', () => {
    this.dispatchEvent(new CustomEvent('modal-close', {
        bubbles: true,
        composed: true
    }));
});
```

使用时:

```html
<app-modal id="myModal">
    <h2>对话框</h2>
</app-modal>

<script>
document.getElementById('myModal').addEventListener('modal-close', (e) => {
    console.log('对话框关闭事件');
    console.log('事件目标:', e.target);
});
</script>
```

你测试了一下, 事件确实触发了, 但你注意到一个奇怪的现象:

```javascript
// 外部监听器中
console.log('事件目标:', e.target);  // 输出: <app-modal>

// 但实际点击的是 Shadow DOM 内部的 <button class="close-btn">
```

"事件的 `target` 被重定向了!" 你惊讶地发现。

你查阅文档后明白了: **当事件从 Shadow DOM 穿透到外部时, 浏览器会自动将 `e.target` 重定向为 Shadow Host (也就是 `<app-modal>` 元素), 而不是真实的触发源 (`<button>`)。**

这是 Shadow DOM 的**封装保护机制** —— 外部代码无法知道 Shadow DOM 内部的实现细节。

但如果你确实需要获取真实的事件路径呢? 你发现了 `composedPath()` 方法:

```javascript
document.getElementById('myModal').addEventListener('modal-close', (e) => {
    console.log('事件目标 (重定向后):', e.target);  // <app-modal>
    console.log('真实事件路径:', e.composedPath());
    // [<button.close-btn>, ShadowRoot, <div.modal-container>, <div.modal-overlay>,
    //  <app-modal>, <body>, <html>, document, Window]
});
```

`composedPath()` 返回事件传播的完整路径, 包括 Shadow DOM 内部的元素。但这个方法只有在事件设置了 `composed: true` 时才能穿透 Shadow DOM 边界。

---

## 真相浮现: Shadow DOM 的边界规则

你终于理解了 Shadow DOM 的完整机制。

**Shadow DOM 创建了一个封闭的子树**, 它有明确的边界规则:

**样式边界**:
- 外部样式规则无法进入 Shadow DOM (双向隔离)
- CSS 变量可以穿透边界 (继承机制)
- `::slotted()` 可以样式化 Light DOM 的直接子元素 (有限穿透)

**DOM 边界**:
- Shadow DOM 内部的元素对外部 `querySelector` 不可见
- Light DOM 的内容通过 `<slot>` 投射到 Shadow DOM 的渲染位置
- 但 Light DOM 元素仍然保持在原位 (只是渲染位置改变)

**事件边界**:
- 事件默认不穿透 Shadow DOM (`composed: false`)
- 设置 `composed: true` 的事件可以穿透
- 穿透时 `e.target` 会被重定向为 Shadow Host (封装保护)
- `e.composedPath()` 可以获取完整的事件路径

你在笔记中总结了一个关键洞察:

**Shadow DOM 的设计哲学: 强封装优先, 按需穿透。**

默认情况下, Shadow DOM 会尽可能封闭自己的实现细节 (样式、DOM 结构、事件目标), 但提供了有限的穿透机制 (CSS 变量、composed 事件、composedPath) 让组件可以与外部协作。

---

## 重构完成: 封闭与开放的平衡

你完成了最终版的 `<app-modal>` 组件:

```javascript
// modal-v2.js - 最终版本
class AppModal extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                /* 使用 CSS 变量实现主题定制 */
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: var(--modal-overlay-bg, rgba(0, 0, 0, 0.5));
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: var(--modal-z-index, 1000);
                }

                .modal-container {
                    position: relative;
                    background: var(--modal-bg, white);
                    color: var(--modal-color, #333);
                    border-radius: var(--modal-radius, 8px);
                    padding: var(--modal-padding, 24px);
                    max-width: var(--modal-max-width, 600px);
                    box-shadow: var(--modal-shadow, 0 4px 12px rgba(0, 0, 0, 0.15));
                }

                .close-btn {
                    position: absolute;
                    top: 16px;
                    right: 16px;
                    background: none;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    color: var(--modal-color, #333);
                    opacity: 0.6;
                    transition: opacity 0.2s;
                }

                .close-btn:hover {
                    opacity: 1;
                }

                /* 样式化 slot 内容 */
                ::slotted(h2) {
                    margin-top: 0;
                    margin-bottom: 16px;
                    font-size: 24px;
                }

                ::slotted(p) {
                    margin-bottom: 16px;
                    line-height: 1.6;
                }

                ::slotted(button) {
                    margin-top: 16px;
                }
            </style>

            <div class="modal-overlay">
                <div class="modal-container">
                    <button class="close-btn" aria-label="关闭对话框">×</button>
                    <slot></slot>
                </div>
            </div>
        `;

        // 内部事件处理
        this._closeBtn = shadow.querySelector('.close-btn');
        this._overlay = shadow.querySelector('.modal-overlay');

        this._handleClose = this._handleClose.bind(this);
        this._handleOverlayClick = this._handleOverlayClick.bind(this);
    }

    connectedCallback() {
        this._closeBtn.addEventListener('click', this._handleClose);
        this._overlay.addEventListener('click', this._handleOverlayClick);
    }

    disconnectedCallback() {
        this._closeBtn.removeEventListener('click', this._handleClose);
        this._overlay.removeEventListener('click', this._handleOverlayClick);
    }

    _handleClose() {
        // 触发自定义事件, composed: true 允许穿透 Shadow DOM
        this.dispatchEvent(new CustomEvent('modal-close', {
            bubbles: true,
            composed: true,
            detail: { source: 'close-button' }
        }));
    }

    _handleOverlayClick(e) {
        // 点击遮罩层关闭 (但不包括点击容器内部)
        if (e.target === this._overlay) {
            this.dispatchEvent(new CustomEvent('modal-close', {
                bubbles: true,
                composed: true,
                detail: { source: 'overlay' }
            }));
        }
    }

    // 公开 API
    open() {
        this.style.display = 'block';
        this.dispatchEvent(new CustomEvent('modal-open', {
            bubbles: true,
            composed: true
        }));
    }

    close() {
        this.style.display = 'none';
        this.dispatchEvent(new CustomEvent('modal-close', {
            bubbles: true,
            composed: true,
            detail: { source: 'api' }
        }));
    }
}

customElements.define('app-modal', AppModal);
```

使用示例:

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        /* 全局主题定义 */
        :root {
            --modal-overlay-bg: rgba(0, 0, 0, 0.5);
            --modal-bg: white;
            --modal-color: #333;
        }

        body.dark-theme {
            --modal-overlay-bg: rgba(0, 0, 0, 0.8);
            --modal-bg: #2c2c2c;
            --modal-color: #f0f0f0;
        }

        /* Light DOM 的样式 (仍然使用全局 CSS) */
        .modal-title {
            color: #007bff;
        }

        .btn-primary {
            background: #007bff;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <button id="openModal">打开对话框</button>
    <button id="toggleTheme">切换深色模式</button>

    <app-modal id="myModal" style="display: none;">
        <h2 class="modal-title">对话框标题</h2>
        <p>这是对话框的内容, 展示了 Shadow DOM 的样式隔离和穿透机制。</p>
        <button class="btn-primary">确认</button>
    </app-modal>

    <script src="modal-v2.js"></script>
    <script>
        const modal = document.getElementById('myModal');

        // 打开对话框
        document.getElementById('openModal').addEventListener('click', () => {
            modal.open();
        });

        // 监听关闭事件
        modal.addEventListener('modal-close', (e) => {
            console.log('对话框关闭, 来源:', e.detail.source);
            modal.close();
        });

        // 切换主题
        document.getElementById('toggleTheme').addEventListener('click', () => {
            document.body.classList.toggle('dark-theme');
        });
    </script>
</body>
</html>
```

你测试了所有功能:

✅ 样式完全隔离, 不与页面全局样式冲突
✅ 通过 CSS 变量实现主题定制, 一行代码切换深色模式
✅ slot 内容正确渲染并应用 `::slotted()` 样式
✅ 关闭按钮和遮罩点击事件正常工作
✅ 自定义事件正确穿透 Shadow DOM 边界
✅ 事件 target 被正确重定向, 封装了内部实现细节

---

## Code Review: 架构师的点评

周五下午的代码审查会上, 你演示了重构后的 `<app-modal>` 组件。

老王看完后点头: "不错, 你理解了 Shadow DOM 的核心机制。但我有几个建议。"

他打开你的代码, 指出第一个问题:

**问题 1: mode 选择**

"你用的是 `mode: 'open'`, 这意味着外部可以通过 `element.shadowRoot` 访问 Shadow DOM 内部。如果你想要**完全封闭**, 应该用 `mode: 'closed'`。"

```javascript
// mode: 'open' - 外部可访问
const shadow = this.attachShadow({ mode: 'open' });
console.log(element.shadowRoot);  // ShadowRoot 对象

// mode: 'closed' - 外部无法访问
const shadow = this.attachShadow({ mode: 'closed' });
console.log(element.shadowRoot);  // null
```

"但 `closed` 模式会增加调试难度, " 老王补充, "所以通常用 `open`, 除非你有特殊的安全需求。"

**问题 2: :host 选择器**

"你没有用 `:host` 选择器, " 老王说, "`:host` 可以选择 Shadow Host 本身, 也就是 `<app-modal>` 元素。"

```javascript
shadow.innerHTML = `
    <style>
        /* ✅ 使用 :host 选择器 */
        :host {
            /* 选择 <app-modal> 元素本身 */
            display: block;
        }

        :host([hidden]) {
            /* 当 <app-modal hidden> 时 */
            display: none;
        }

        :host(.modal-large) {
            /* 当 <app-modal class="modal-large"> 时 */
            --modal-max-width: 900px;
        }
    </style>
`;
```

**问题 3: :host-context() 上下文感知**

"如果你想根据祖先元素的状态改变组件样式, 可以用 `:host-context()`。"

```javascript
shadow.innerHTML = `
    <style>
        /* 当祖先元素有 .dark-theme 类时 */
        :host-context(.dark-theme) .modal-container {
            /* 这里可以不用 CSS 变量, 直接写固定样式 */
            background: #2c2c2c;
            color: #f0f0f0;
        }

        /* 当在 <article> 内部时 */
        :host-context(article) {
            --modal-max-width: 800px;
        }
    </style>
`;
```

**问题 4: CSS Shadow Parts**

"如果你想让外部样式**有限地**定制 Shadow DOM 内部的某些元素, 可以用 `::part()` 伪元素。"

```javascript
shadow.innerHTML = `
    <style>
        .modal-container {
            background: var(--modal-bg, white);
        }
    </style>

    <div class="modal-overlay">
        <!-- ✅ 暴露 part -->
        <div class="modal-container" part="container">
            <button class="close-btn" part="close-button">×</button>
            <slot></slot>
        </div>
    </div>
`;
```

外部可以这样样式化:

```css
/* 外部样式表 */
app-modal::part(container) {
    border: 2px solid blue;
    border-radius: 16px;
}

app-modal::part(close-button) {
    color: red;
    font-size: 32px;
}
```

"这样你既保持了封装, 又提供了有限的定制能力, " 老王解释, "外部只能样式化你明确暴露的 `part`, 而不能访问其他内部元素。"

---

## 总结: Shadow DOM 的权衡

会议结束后, 你在笔记本上总结了这次重构的经验:

**Shadow DOM 的优势**:
- ✅ 真正的样式隔离, 不再有 CSS 特异性战争
- ✅ 组件实现细节完全封装, 外部无法意外破坏
- ✅ 可复用性强, 可以在任何页面中使用而不担心样式冲突
- ✅ 浏览器原生支持, 不需要构建工具

**Shadow DOM 的代价**:
- ❌ 外部样式无法进入, 必须重写所有内部样式
- ❌ 全局样式重置 (如 normalize.css) 不会影响 Shadow DOM
- ❌ `::slotted()` 只能选择直接子元素, 无法深入
- ❌ 调试复杂度增加, DevTools 需要展开 Shadow Root
- ❌ 第三方样式库 (如 Bootstrap) 无法直接作用于 Shadow DOM

**最佳实践**:
1. 用 **CSS 变量** 实现主题定制和外部配置
2. 用 **`::part()`** 暴露需要外部定制的关键元素
3. 用 **`:host`** 和 **`:host-context()`** 实现上下文感知样式
4. 用 **`composed: true`** 让关键事件穿透 Shadow DOM
5. 用 **`::slotted()`** 样式化投射内容 (记住只能选直接子元素)
6. 默认用 **`mode: 'open'`** 以便调试, 除非有特殊安全需求

你回想起老王在会议开始时说的话: "Shadow DOM 不是银弹, 它是一个**权衡**。你用强封装换取了可维护性, 但也牺牲了灵活性。关键是理解这个权衡, 在合适的场景使用它。"

对于你们团队的组件库, Shadow DOM 确实解决了样式冲突的核心问题。虽然重构成本不低, 但长期来看, 样式隔离带来的可维护性提升是值得的。

---

## 知识档案: Shadow DOM 封闭子树的八个核心机制

**规则 1: Shadow DOM 创建封闭的子树, 有 open 和 closed 两种模式**

Shadow DOM 通过 `attachShadow()` 创建, 形成一个独立的 DOM 子树, 与 Light DOM 隔离。

```javascript
// attachShadow() 创建 Shadow Root
class MyElement extends HTMLElement {
    constructor() {
        super();

        // mode: 'open' - 外部可通过 element.shadowRoot 访问
        const shadow = this.attachShadow({ mode: 'open' });
        console.log(this.shadowRoot);  // ShadowRoot 对象 ✅

        // mode: 'closed' - 外部无法访问, shadowRoot 为 null
        // const shadow = this.attachShadow({ mode: 'closed' });
        // console.log(this.shadowRoot);  // null

        shadow.innerHTML = `
            <style>
                p { color: red; }
            </style>
            <p>Shadow DOM content</p>
        `;
    }
}

customElements.define('my-element', MyElement);
```

mode 选择建议:
- **open**: 大多数场景, 便于调试和测试, 外部可以访问但不应依赖内部实现
- **closed**: 特殊安全需求, 完全隐藏内部实现, 但增加调试难度

**重要**: 一个元素只能调用一次 `attachShadow()`, 重复调用会抛出异常。

```javascript
// ❌ 错误: 重复创建 Shadow Root
const shadow1 = element.attachShadow({ mode: 'open' });
const shadow2 = element.attachShadow({ mode: 'open' });
// DOMException: Failed to execute 'attachShadow' on 'Element': Shadow root cannot be created on a host which already hosts a shadow tree.
```

---

**规则 2: Shadow DOM 实现双向样式隔离, 外部样式进不来, 内部样式出不去**

这是 Shadow DOM 最核心的特性: 完全的样式封装。

```javascript
class StyleIsolation extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                /* Shadow DOM 内部样式 */
                p {
                    color: red;      /* 只影响 Shadow DOM 内的 p */
                    font-size: 24px;
                }

                .highlight {
                    background: yellow;  /* 只影响 Shadow DOM 内的 .highlight */
                }
            </style>

            <p>Shadow DOM 段落 (红色 24px)</p>
            <div class="highlight">高亮文本</div>
        `;
    }
}

customElements.define('style-isolation', StyleIsolation);
```

```html
<style>
    /* 全局样式 */
    p {
        color: blue;       /* 不影响 Shadow DOM 内的 p */
        font-size: 16px;
    }

    .highlight {
        background: pink;  /* 不影响 Shadow DOM 内的 .highlight */
    }
</style>

<p>全局段落 (蓝色 16px)</p>
<div class="highlight">全局高亮 (粉色背景)</div>

<style-isolation></style-isolation>
```

结果:
- 全局 `<p>` 是蓝色 16px (全局样式生效)
- Shadow DOM 内的 `<p>` 是红色 24px (Shadow DOM 样式生效)
- 全局 `.highlight` 是粉色背景 (全局样式生效)
- Shadow DOM 内的 `.highlight` 是黄色背景 (Shadow DOM 样式生效)

**关键洞察**: Shadow DOM 的样式隔离是**双向的**, 不仅阻止内部样式泄漏, 也阻止外部样式侵入。

**实际影响**:
- ✅ 优势: 组件样式完全独立, 不会与页面全局样式冲突
- ❌ 代价: 必须在 Shadow DOM 内部重写所有样式, 无法复用全局 CSS
- ❌ 代价: 全局样式重置 (如 normalize.css) 不会影响 Shadow DOM
- ❌ 代价: 第三方样式库 (如 Bootstrap) 无法直接作用于 Shadow DOM

---

**规则 3: CSS 自定义属性 (CSS 变量) 可以穿透 Shadow DOM 边界, 实现主题定制**

虽然样式规则无法穿透, 但 CSS 变量值可以通过继承穿透 Shadow DOM。

```javascript
class ThemeableComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    /* ✅ 使用 CSS 变量, 外部可定制 */
                    background: var(--card-bg, white);
                    color: var(--card-color, #333);
                    border-radius: var(--card-radius, 8px);
                    padding: var(--card-padding, 16px);
                    box-shadow: var(--card-shadow, 0 2px 8px rgba(0,0,0,0.1));
                }
            </style>

            <div class="card">
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('themeable-component', ThemeableComponent);
```

外部主题定制:

```css
/* 全局样式 - 定义主题变量 */
:root {
    --card-bg: white;
    --card-color: #333;
    --card-radius: 8px;
    --card-padding: 16px;
    --card-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* 深色主题 */
body.dark-theme {
    --card-bg: #2c2c2c;
    --card-color: #f0f0f0;
    --card-shadow: 0 2px 8px rgba(0,0,0,0.5);
}

/* 针对特定组件定制 */
themeable-component.large {
    --card-padding: 32px;
    --card-radius: 16px;
}
```

使用:

```html
<themeable-component>
    <h3>默认主题</h3>
</themeable-component>

<themeable-component class="large">
    <h3>大尺寸变体</h3>
</themeable-component>

<script>
// 一键切换深色主题
document.body.classList.toggle('dark-theme');
</script>
```

**关键洞察**: CSS 变量是 Shadow DOM 样式隔离的"合法通道", 组件内部定义变量名和默认值, 外部提供具体值。

**最佳实践**:
- 为所有可定制的样式属性提供 CSS 变量接口
- 总是提供默认值 (如 `var(--card-bg, white)`)
- 使用语义化的变量名 (如 `--modal-bg` 而非 `--bg1`)
- 在组件文档中列出所有可用的 CSS 变量

---

**规则 4: :host 选择器选择 Shadow Host, :host-context() 实现上下文感知**

`:host` 选择器用于样式化 Shadow Host (承载 Shadow DOM 的元素本身)。

```javascript
class HostStyling extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                /* :host 选择 <host-styling> 元素本身 */
                :host {
                    display: block;
                    border: 2px solid #ddd;
                    padding: 16px;
                }

                /* :host() 函数 - 根据 Host 的属性/类选择 */
                :host([disabled]) {
                    opacity: 0.5;
                    pointer-events: none;
                }

                :host(.large) {
                    padding: 32px;
                    font-size: 1.2em;
                }

                :host(:hover) {
                    border-color: #007bff;
                }

                /* :host-context() - 根据祖先元素选择 */
                :host-context(.dark-theme) {
                    background: #2c2c2c;
                    border-color: #555;
                }

                :host-context(article) {
                    max-width: 800px;
                }

                :host-context(.compact) :host {
                    padding: 8px;
                }
            </style>

            <div class="content">
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('host-styling', HostStyling);
```

使用:

```html
<!-- 默认样式 -->
<host-styling>
    <p>默认内容</p>
</host-styling>

<!-- disabled 状态 -->
<host-styling disabled>
    <p>禁用状态 (半透明, 无法交互)</p>
</host-styling>

<!-- large 变体 -->
<host-styling class="large">
    <p>大尺寸变体</p>
</host-styling>

<!-- 在深色主题容器内 -->
<div class="dark-theme">
    <host-styling>
        <p>深色主题样式</p>
    </host-styling>
</div>

<!-- 在 article 内 -->
<article>
    <host-styling>
        <p>最大宽度 800px</p>
    </host-styling>
</article>
```

**:host vs :host() vs :host-context() 对比**:

```javascript
:host { }                      // 选择 Shadow Host 本身
:host(.class) { }              // 当 Host 有 .class 类时
:host([attr]) { }              // 当 Host 有 attr 属性时
:host(:hover) { }              // 当 Host 被 hover 时
:host-context(.parent) { }     // 当祖先元素有 .parent 类时
```

**优先级规则**: 外部样式 > :host-context() > :host() > :host

```css
/* 优先级从低到高 */
:host { color: red; }                    /* 优先级 (0,0,1) */
:host(.active) { color: blue; }          /* 优先级 (0,1,1) */
:host-context(.theme) { color: green; }  /* 优先级 (0,1,1) */
host-styling { color: purple; }          /* 优先级 (0,0,1), 但外部样式优先 */
```

---

**规则 5: ::slotted() 可以样式化 slot 投射的 Light DOM 内容, 但仅限直接子元素**

`::slotted()` 伪元素允许 Shadow DOM 内部样式选择通过 `<slot>` 投射的 Light DOM 内容。

```javascript
class SlotStyling extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                /* ✅ 正确: ::slotted() 选择 slot 的直接子元素 */
                ::slotted(p) {
                    margin-bottom: 16px;
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

                ::slotted([data-priority="high"]) {
                    color: red;
                    font-weight: bold;
                }

                /* ❌ 限制: 无法选择后代元素 */
                ::slotted(div p) {
                    /* 无效! ::slotted() 不能深入后代 */
                }

                ::slotted(*) {
                    /* 选择所有 slot 直接子元素 */
                    margin: 8px 0;
                }
            </style>

            <div class="container">
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('slot-styling', SlotStyling);
```

使用示例:

```html
<slot-styling>
    <!-- ✅ 这些是 slot 的直接子元素, ::slotted() 可以选中 -->
    <h2>标题 (蓝色)</h2>
    <p>段落 (16px 下边距)</p>
    <p class="highlight">高亮段落 (黄色背景)</p>
    <p data-priority="high">高优先级 (红色粗体)</p>

    <!-- ❌ 嵌套元素无法被 ::slotted(p) 选中 -->
    <div>
        <p>嵌套段落 (不受 ::slotted(p) 影响)</p>
    </div>
</slot-styling>
```

**::slotted() 的限制**:

1. **只能选择直接子元素**, 无法深入后代:

```css
/* ❌ 这些都不会生效 */
::slotted(div p) { }           /* 无法选择 div 的 p 子元素 */
::slotted(p span) { }          /* 无法选择 p 的 span 子元素 */
::slotted(.parent .child) { }  /* 无法选择后代 */
```

2. **只能选择元素节点**, 不能选择文本节点:

```html
<slot-styling>
    文本节点 (无法被 ::slotted(*) 选中)
    <p>元素节点 (可以被选中)</p>
</slot-styling>
```

3. **选择器复杂度有限**:

```css
/* ✅ 支持 */
::slotted(*) { }               /* 通配符 */
::slotted(p) { }               /* 类型选择器 */
::slotted(.class) { }          /* 类选择器 */
::slotted([attr]) { }          /* 属性选择器 */
::slotted(p.class[attr]) { }   /* 组合 */

/* ❌ 不支持 */
::slotted(p)::before { }       /* 无法使用伪元素 */
::slotted(p:hover) { }         /* 部分浏览器不支持伪类 */
```

**解决方案**: 如果需要深入样式化 slot 内容, 只能通过外部全局 CSS 或让用户自己添加样式。

---

**规则 6: ::part() 允许外部有限地样式化 Shadow DOM 内部暴露的元素**

CSS Shadow Parts 提供了一种受控的方式, 让组件明确暴露哪些内部元素可以被外部样式化。

```javascript
class PartExposure extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .container {
                    padding: 16px;
                    border: 1px solid #ddd;
                }

                .title {
                    font-size: 18px;
                    color: #333;
                }

                .content {
                    color: #666;
                }
            </style>

            <div class="container" part="container">
                <!-- ✅ 暴露 part="title", 外部可样式化 -->
                <div class="title" part="title">
                    <slot name="title">默认标题</slot>
                </div>

                <!-- ✅ 暴露 part="content", 外部可样式化 -->
                <div class="content" part="content">
                    <slot>默认内容</slot>
                </div>

                <!-- ❌ 没有 part 属性, 外部无法样式化 -->
                <div class="footer">
                    内部实现细节 (不暴露)
                </div>
            </div>
        `;
    }
}

customElements.define('part-exposure', PartExposure);
```

外部样式化:

```css
/* 外部样式表 */

/* ✅ 可以样式化暴露的 part */
part-exposure::part(container) {
    border-color: blue;
    border-width: 2px;
    border-radius: 8px;
    background: #f0f0f0;
}

part-exposure::part(title) {
    color: #007bff;
    font-size: 24px;
    font-weight: bold;
}

part-exposure::part(content) {
    line-height: 1.8;
    color: #333;
}

/* ❌ 无法样式化没有 part 的元素 */
part-exposure::part(footer) {
    /* 无效! footer 没有暴露为 part */
}

/* ❌ 无法使用伪类/伪元素 */
part-exposure::part(title):hover {
    /* 大多数浏览器不支持 */
}

part-exposure::part(title)::before {
    /* 无法使用 */
}
```

**多个 part 名称**:

```javascript
shadow.innerHTML = `
    <!-- 一个元素可以有多个 part 名称 -->
    <button class="submit-btn" part="button submit-button">
        提交
    </button>
`;
```

```css
/* 外部可以用任何一个 part 名称选择 */
part-exposure::part(button) { }
part-exposure::part(submit-button) { }
```

**part 的转发** (导出):

```javascript
// 父组件
class ParentComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <!-- ✅ 使用 exportparts 转发子组件的 part -->
            <child-component exportparts="title, content"></child-component>
        `;
    }
}

// 外部可以直接样式化子组件的 part
parent-component::part(title) {
    color: red;
}
```

**part vs 外部样式 vs CSS 变量 对比**:

| 机制 | 灵活性 | 封装性 | 适用场景 |
|------|--------|--------|----------|
| CSS 变量 | 低 (只能改值) | 高 | 主题定制, 配置参数 |
| ::part() | 中 (可改多个属性) | 中 | 关键元素定制 |
| 外部样式 | 高 (完全控制) | 低 | Light DOM 内容 |

---

**规则 7: 事件默认不穿透 Shadow DOM, 需设置 composed: true 才能跨越边界**

Shadow DOM 对事件传播也有封装机制, 阻止内部事件泄漏到外部。

```javascript
class EventBoundary extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <button id="btn1">不穿透按钮</button>
            <button id="btn2">穿透按钮</button>
        `;

        // ❌ 默认事件不穿透
        shadow.getElementById('btn1').addEventListener('click', (e) => {
            this.dispatchEvent(new CustomEvent('non-composed-click', {
                bubbles: true,
                composed: false  // 默认值, 不穿透 Shadow DOM
            }));
        });

        // ✅ 设置 composed: true 才穿透
        shadow.getElementById('btn2').addEventListener('click', (e) => {
            this.dispatchEvent(new CustomEvent('composed-click', {
                bubbles: true,
                composed: true  // 穿透 Shadow DOM
            }));
        });
    }
}

customElements.define('event-boundary', EventBoundary);
```

测试:

```html
<event-boundary id="component"></event-boundary>

<script>
const component = document.getElementById('component');

// ❌ 无法捕获 composed: false 的事件
document.addEventListener('non-composed-click', (e) => {
    console.log('永远不会执行');  // 事件被 Shadow DOM 边界阻止
});

// ✅ 可以捕获 composed: true 的事件
document.addEventListener('composed-click', (e) => {
    console.log('成功捕获!');  // 事件穿透了 Shadow DOM
});
</script>
```

**原生事件的 composed 属性**:

大多数原生事件都是 `composed: true`, 可以穿透 Shadow DOM:

```javascript
// ✅ 这些原生事件可以穿透 Shadow DOM
- click, dblclick
- mousedown, mouseup, mousemove, mouseenter, mouseleave
- wheel
- keydown, keyup, keypress
- focus, blur (但不冒泡, 需要用 focusin/focusout)
- input, change
- touchstart, touchmove, touchend

// ❌ 这些原生事件不穿透 Shadow DOM
- load, error, scroll (不冒泡)
- focus, blur (composed: false)
- mouseenter, mouseleave (不冒泡)
```

测试原生事件:

```javascript
shadow.innerHTML = `<button id="testBtn">测试</button>`;

const button = shadow.getElementById('testBtn');

// 外部可以捕获 click (composed: true)
document.addEventListener('click', (e) => {
    console.log('捕获到 click 事件');
    console.log('目标:', e.target);  // 注意: target 会被重定向!
});
```

---

**规则 8: 事件穿透 Shadow DOM 时, target 被重定向为 Shadow Host, composedPath() 可获取真实路径**

当事件从 Shadow DOM 穿透到外部时, 浏览器会**重定向** `e.target`, 隐藏内部实现细节。

```javascript
class EventRetargeting extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                button { margin: 8px; }
            </style>

            <div class="container">
                <button class="inner-button">点击我</button>
            </div>
        `;

        const button = shadow.querySelector('.inner-button');

        // Shadow DOM 内部监听器
        button.addEventListener('click', (e) => {
            console.log('=== 内部监听器 ===');
            console.log('target:', e.target);
            // <button class="inner-button">

            console.log('currentTarget:', e.currentTarget);
            // <button class="inner-button">

            console.log('composed:', e.composed);
            // true (click 是原生事件)
        });
    }

    connectedCallback() {
        // Shadow Host 上的监听器
        this.addEventListener('click', (e) => {
            console.log('=== Host 监听器 ===');
            console.log('target:', e.target);
            // <event-retargeting> (被重定向!)

            console.log('currentTarget:', e.currentTarget);
            // <event-retargeting>

            // ✅ 使用 composedPath() 获取真实路径
            console.log('composedPath:', e.composedPath());
            // [<button>, <div.container>, ShadowRoot,
            //  <event-retargeting>, <body>, <html>, document, Window]
        });
    }
}

customElements.define('event-retargeting', EventRetargeting);
```

使用:

```html
<event-retargeting id="component"></event-retargeting>

<script>
const component = document.getElementById('component');

// 外部文档监听器
document.addEventListener('click', (e) => {
    console.log('=== 文档监听器 ===');
    console.log('target:', e.target);
    // <event-retargeting> (仍然是重定向后的)

    console.log('composedPath:', e.composedPath());
    // 完整路径包含 Shadow DOM 内部元素
});
</script>
```

点击按钮时的输出:

```
=== 内部监听器 ===
target: <button class="inner-button">
currentTarget: <button class="inner-button">
composed: true

=== Host 监听器 ===
target: <event-retargeting>               ← 重定向!
currentTarget: <event-retargeting>
composedPath: [<button>, <div.container>, ShadowRoot, <event-retargeting>, <body>, <html>, document, Window]

=== 文档监听器 ===
target: <event-retargeting>               ← 仍然是重定向后的
composedPath: [<button>, <div.container>, ShadowRoot, <event-retargeting>, <body>, <html>, document, Window]
```

**事件重定向的规则**:

1. **在 Shadow DOM 内部**: `e.target` 是真实的触发元素
2. **跨越 Shadow 边界后**: `e.target` 被重定向为 Shadow Host
3. **多层嵌套**: 如果有多层 Shadow DOM, 每层边界都会重定向 `e.target`

```javascript
// 多层 Shadow DOM 的事件重定向
<parent-component>
    #shadow-root
        <child-component>
            #shadow-root
                <button>Click</button>  ← 真实触发源
```

事件传播过程中 `e.target` 的变化:
- 在 `<button>` 的监听器中: `e.target` 是 `<button>`
- 在 `<child-component>` 的监听器中: `e.target` 是 `<child-component>`
- 在 `<parent-component>` 的监听器中: `e.target` 是 `<parent-component>`
- 在文档的监听器中: `e.target` 是 `<parent-component>`

**composedPath() 的用途**:

```javascript
// 判断事件是否源自特定内部元素
this.addEventListener('click', (e) => {
    const path = e.composedPath();

    // 检查是否点击了特定按钮
    const isCloseButton = path.some(el =>
        el.classList && el.classList.contains('close-btn')
    );

    // 检查是否点击了遮罩层
    const isOverlay = path.some(el =>
        el.classList && el.classList.contains('modal-overlay')
    );

    if (isCloseButton) {
        this.close();
    } else if (isOverlay) {
        this.close();
    }
});
```

**stopPropagation() 在 Shadow DOM 中的行为**:

```javascript
button.addEventListener('click', (e) => {
    e.stopPropagation();
    // 阻止事件继续在 Shadow DOM 内部冒泡
    // 但如果是 composed: true, 仍会穿透到外部
});

// 要完全阻止事件, 需要在 Shadow Host 上调用
this.addEventListener('click', (e) => {
    e.stopPropagation();
    // 这样可以阻止事件继续冒泡到文档
});
```

---

**事故档案编号**: NETWORK-2024-1964
**影响范围**: Shadow DOM, 样式封装, Light DOM, 事件系统, CSS 自定义属性
**根本原因**: Shadow DOM 的双向样式隔离超出预期, 未理解 CSS 变量穿透机制和事件重定向规则
**学习成本**: 中高 (需理解封闭子树概念、样式边界、DOM 边界、事件边界、穿透机制)

这是 JavaScript 世界第 164 次被记录的网络与数据事故。Shadow DOM 通过 attachShadow() 创建封闭子树, 有 open 和 closed 两种模式, open 允许外部通过 shadowRoot 访问但 closed 完全封闭。Shadow DOM 实现双向样式隔离, 外部样式无法进入内部样式也无法泄漏, 必须在 Shadow DOM 内部重写所有样式。CSS 自定义属性 (CSS 变量) 是唯一可以穿透 Shadow DOM 边界的样式机制, 实现主题定制和外部配置。:host 选择器样式化 Shadow Host 本身, :host-context() 实现上下文感知, :host() 根据 Host 属性选择。::slotted() 可以样式化 slot 投射的 Light DOM 内容但仅限直接子元素, 无法深入后代。::part() 允许组件明确暴露哪些内部元素可被外部样式化, 实现受控的样式定制。事件默认不穿透 Shadow DOM, 需设置 composed: true 才能跨越边界, 大多数原生事件都是 composed: true。事件穿透时 target 被重定向为 Shadow Host 以隐藏内部实现, composedPath() 可获取包含 Shadow DOM 内部元素的完整事件路径。理解 Shadow DOM 的封闭机制和有限穿透通道是实现健壮 Web Components 的关键。

---
