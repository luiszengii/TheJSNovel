《第 162 次记录: 周六深夜的紧急召回 —— Web Components 自定义组件系统》

---

## 紧急召回

周六晚上 11 点 14 分, 你刚洗完澡, 准备睡觉。

手机突然连续震动了三次。你拿起来一看, Slack 上 @channel 的红色标记刺眼地闪烁着。运维组长发的消息让你心里一沉:

"生产环境首页白屏, 用户无法访问。影响范围: 所有用户。@前端组 紧急排查。"

你立刻打开笔记本, 访问生产环境的 URL。页面确实是白屏, 控制台里一片红色错误。

```
Uncaught DOMException: Failed to execute 'define' on 'CustomElementRegistry':
the name "product-card" has already been defined
    at app.bundle.js:1247
```

"CustomElementRegistry?" 你皱起眉头, "这是什么?"

你快速回忆今天下午的部署: 前端新人小陈提交了一个 PR, 重构了产品卡片组件。你当时看了一眼代码, 觉得挺简洁的, 就批准合并了。代码里用了一些你不太熟悉的 API, 但测试环境运行正常, 你也就没多想。

现在看来, 问题出在这里。

你打开 Chrome DevTools 的 Network 面板, 发现页面加载了两个 JavaScript 文件: `app.bundle.js` 和 `vendor.bundle.js`。你怀疑是重复加载导致的, 但为什么测试环境没问题?

Slack 里消息不断刷新:

"客服部门电话快被打爆了"
"用户在社交媒体上开始吐槽"
"这个问题多久能修复?"

你深吸一口气, 开始追踪代码。

---

## 故障排查

你打开 Git 仓库, 找到小陈下午提交的 PR。

代码看起来很现代, 使用了一种你不太熟悉的写法:

```javascript
// product-card.js - 小陈的实现
class ProductCard extends HTMLElement {
    constructor() {
        super();

        // 创建 Shadow DOM
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 16px;
                }
                .title {
                    font-size: 18px;
                    font-weight: bold;
                }
                .price {
                    color: #f00;
                    font-size: 24px;
                }
            </style>
            <div class="card">
                <div class="title"></div>
                <div class="price"></div>
            </div>
        `;
    }

    connectedCallback() {
        this.render();
    }

    render() {
        const shadow = this.shadowRoot;
        shadow.querySelector('.title').textContent = this.getAttribute('title') || '';
        shadow.querySelector('.price').textContent = this.getAttribute('price') || '';
    }
}

// 注册自定义元素
customElements.define('product-card', ProductCard);
```

"这是什么写法?" 你盯着 `extends HTMLElement` 和 `customElements.define`, 感觉进入了一个陌生的世界。

你在 HTML 中看到这样的使用:

```html
<product-card
    title="机械键盘"
    price="¥399">
</product-card>
```

"原来可以自定义 HTML 标签?" 你惊讶地想。这个 `<product-card>` 不是 HTML 原生标签, 但浏览器居然能识别?

你继续追踪错误信息。控制台显示 "the name 'product-card' has already been defined", 说明这个组件被注册了两次。

你检查打包配置, 发现 Webpack 的代码分割策略有问题: `product-card.js` 既被打包进了 `app.bundle.js`, 又被打包进了 `vendor.bundle.js`。两个文件都在页面中加载, 所以 `customElements.define('product-card', ProductCard)` 被执行了两次。

"为什么测试环境没问题?" 你想起来, 测试环境的打包配置不同, 只生成了一个文件。

但现在的紧急情况是: 如何快速修复?

你想到三个方案:

**方案 1**: 修改打包配置, 避免重复打包。但这需要重新构建和部署, 至少要 15 分钟。

**方案 2**: 回滚到上一个版本。但回滚会丢失今天下午部署的其他功能。

**方案 3**: 快速修复组件注册逻辑, 避免重复注册。

你决定先尝试方案 3, 如果不行再回滚。

你修改了注册逻辑:

```javascript
// 修复: 检查是否已注册
if (!customElements.get('product-card')) {
    customElements.define('product-card', ProductCard);
}
```

你在本地测试, 模拟重复加载的场景:

```html
<script src="app.bundle.js"></script>
<script src="vendor.bundle.js"></script>
```

控制台不再报错, 页面正常显示。你快速构建并部署到生产环境。

3 分钟后, 监控显示错误率降为零。你刷新生产环境的页面, 首页恢复正常。

Slack 里的消息变成了 "页面恢复了" 和 "干得好"。

你松了一口气, 但心里充满疑问: 这个 `customElements` 到底是什么? 为什么可以自定义 HTML 标签? 这和 React 组件有什么区别?

---

## Web Components 的真相

周日上午 10 点, 你带着咖啡打开电脑, 决定好好研究一下昨晚遇到的 Web Components。

你找到 MDN 文档, 标题是 "Web Components - 构建可重用的自定义元素"。

"原来这是浏览器原生支持的组件系统, " 你读着文档, "不需要 React 或 Vue, 直接用原生 JavaScript 就能创建组件。"

### Web Components 的三大核心技术

文档说, Web Components 由三个主要技术组成:

**① Custom Elements (自定义元素)**

允许开发者定义自己的 HTML 元素。

```javascript
// 定义一个简单的自定义元素
class MyGreeting extends HTMLElement {
    constructor() {
        super();
        this.innerHTML = `<p>Hello, World!</p>`;
    }
}

// 注册自定义元素
customElements.define('my-greeting', MyGreeting);
```

使用时就像普通 HTML 标签:

```html
<my-greeting></my-greeting>
```

"这就是为什么可以写 `<product-card>`!" 你恍然大悟。

**② Shadow DOM (影子 DOM)**

提供封装机制, 让组件的样式和 DOM 结构与页面其他部分隔离。

```javascript
class IsolatedComponent extends HTMLElement {
    constructor() {
        super();

        // 创建 Shadow Root
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                /* 这些样式只作用于 Shadow DOM 内部 */
                p {
                    color: red;
                }
            </style>
            <p>This text is red</p>
        `;
    }
}

customElements.define('isolated-component', IsolatedComponent);
```

你测试了一下:

```html
<style>
    p {
        color: blue;
    }
</style>

<p>Outside: blue</p>
<isolated-component></isolated-component>
```

结果显示: 外部的 `<p>` 是蓝色, 但 `<isolated-component>` 内部的 `<p>` 是红色。样式完全隔离!

"这就是昨晚代码里的 `this.attachShadow()`!" 你明白了, "Shadow DOM 让组件的样式不会污染页面, 页面的样式也不会影响组件。"

**③ HTML Templates (模板)**

定义可重用的 HTML 片段。

```html
<template id="card-template">
    <style>
        .card {
            border: 1px solid #ddd;
            padding: 16px;
        }
    </style>
    <div class="card">
        <slot name="title"></slot>
        <slot name="content"></slot>
    </div>
</template>
```

```javascript
class TemplateCard extends HTMLElement {
    constructor() {
        super();

        const shadow = this.attachShadow({ mode: 'open' });

        // 克隆模板内容
        const template = document.getElementById('card-template');
        shadow.appendChild(template.content.cloneNode(true));
    }
}

customElements.define('template-card', TemplateCard);
```

"三大技术结合, 就能创建完全封装的可重用组件, " 你总结道。

### 生命周期回调

你继续研究, 发现自定义元素有四个生命周期回调:

```javascript
class LifecycleDemo extends HTMLElement {
    constructor() {
        super();
        console.log('1. constructor: 元素被创建');
    }

    connectedCallback() {
        console.log('2. connectedCallback: 元素被插入 DOM');
        // 适合在这里获取数据、添加事件监听器
    }

    disconnectedCallback() {
        console.log('3. disconnectedCallback: 元素从 DOM 移除');
        // 清理工作: 移除事件监听器、取消定时器
    }

    attributeChangedCallback(name, oldValue, newValue) {
        console.log(`4. attributeChangedCallback: ${name} 从 ${oldValue} 变为 ${newValue}`);
        // 响应属性变化
    }

    // 声明要监听哪些属性
    static get observedAttributes() {
        return ['title', 'count'];
    }
}

customElements.define('lifecycle-demo', LifecycleDemo);
```

你测试了一下:

```javascript
// 创建元素
const demo = document.createElement('lifecycle-demo');
// 输出: 1. constructor: 元素被创建

// 插入 DOM
document.body.appendChild(demo);
// 输出: 2. connectedCallback: 元素被插入 DOM

// 修改属性
demo.setAttribute('title', 'Hello');
// 输出: 4. attributeChangedCallback: title 从 null 变为 Hello

// 移除元素
demo.remove();
// 输出: 3. disconnectedCallback: 元素从 DOM 移除
```

"这和 React 的生命周期很像, " 你想, "但这是浏览器原生支持的。"

### 属性与属性同步

你注意到昨晚的代码中, 组件通过 `getAttribute()` 读取属性:

```javascript
render() {
    const title = this.getAttribute('title') || '';
    const price = this.getAttribute('price') || '';
    // ...
}
```

"但如果属性变化了呢?" 你好奇地想。

你实现了一个更完善的版本:

```javascript
class ReactiveCard extends HTMLElement {
    constructor() {
        super();

        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 16px;
                    transition: all 0.3s;
                }
                .card:hover {
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }
                .title {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 8px;
                }
                .price {
                    color: #f00;
                    font-size: 24px;
                }
            </style>
            <div class="card">
                <div class="title"></div>
                <div class="price"></div>
            </div>
        `;
    }

    // 声明要监听的属性
    static get observedAttributes() {
        return ['title', 'price'];
    }

    // 属性变化时重新渲染
    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue !== newValue) {
            this.render();
        }
    }

    connectedCallback() {
        this.render();
    }

    render() {
        const shadow = this.shadowRoot;
        shadow.querySelector('.title').textContent = this.getAttribute('title') || '';
        shadow.querySelector('.price').textContent = this.getAttribute('price') || '';
    }
}

customElements.define('reactive-card', ReactiveCard);
```

测试:

```javascript
const card = document.createElement('reactive-card');
card.setAttribute('title', '机械键盘');
card.setAttribute('price', '¥399');
document.body.appendChild(card);

// 3 秒后修改价格
setTimeout(() => {
    card.setAttribute('price', '¥299');  // 页面自动更新!
}, 3000);
```

"只要声明 `observedAttributes`, 浏览器就会自动监听属性变化, " 你总结, "这比手动监听 DOM 变化方便多了。"

### Slot 插槽机制

你继续探索, 发现了 `<slot>` 元素。

"这和 Vue 的插槽一样!" 你兴奋地想。

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
                    padding: 16px;
                }
                .header {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 12px;
                }
                .content {
                    margin-bottom: 12px;
                }
                .footer {
                    text-align: right;
                    font-size: 12px;
                    color: #666;
                }
            </style>
            <div class="card">
                <div class="header">
                    <slot name="header">默认标题</slot>
                </div>
                <div class="content">
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

使用时:

```html
<flexible-card>
    <span slot="header">自定义标题</span>
    <p>这是卡片的主要内容...</p>
    <small slot="footer">2024-01-01</small>
</flexible-card>
```

"组件提供了三个插槽: header, 默认, footer, " 你理解了, "使用者可以插入任何内容。"

你测试了不提供某些插槽的情况:

```html
<flexible-card>
    <p>只提供主要内容</p>
</flexible-card>
```

结果显示: header 和 footer 显示了默认文本。

"和 Vue 的具名插槽几乎一样, " 你感慨, "但这是浏览器原生支持的。"

### 事件处理

你想知道如何在自定义元素中处理事件。

```javascript
class InteractiveButton extends HTMLElement {
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
                    font-size: 16px;
                }
                button:hover {
                    background: #0056b3;
                }
                button:active {
                    transform: scale(0.98);
                }
            </style>
            <button>
                <slot>点击我</slot>
            </button>
        `;

        // 内部事件监听
        this._button = shadow.querySelector('button');
        this._button.addEventListener('click', this._handleClick.bind(this));
    }

    _handleClick(e) {
        // 触发自定义事件
        this.dispatchEvent(new CustomEvent('button-click', {
            bubbles: true,
            composed: true,  // 允许事件穿透 Shadow DOM
            detail: {
                timestamp: Date.now()
            }
        }));
    }

    disconnectedCallback() {
        // 清理事件监听器
        this._button.removeEventListener('click', this._handleClick);
    }
}

customElements.define('interactive-button', InteractiveButton);
```

使用时:

```html
<interactive-button id="myBtn">提交</interactive-button>

<script>
document.getElementById('myBtn').addEventListener('button-click', (e) => {
    console.log('按钮被点击:', e.detail.timestamp);
});
</script>
```

"关键是 `composed: true`, " 你注意到, "否则事件无法穿透 Shadow DOM。"

---

## 深度理解与最佳实践

下午, 你决定重构昨晚的 `product-card` 组件, 应用今天学到的知识。

### 完善的组件实现

```javascript
// product-card-v2.js - 重构后的版本
class ProductCard extends HTMLElement {
    constructor() {
        super();

        // 创建 Shadow DOM
        const shadow = this.attachShadow({ mode: 'open' });

        // 使用 template 而非 innerHTML
        const template = document.createElement('template');
        template.innerHTML = `
            <style>
                :host {
                    display: block;
                    width: 100%;
                }
                :host([disabled]) {
                    opacity: 0.5;
                    pointer-events: none;
                }
                .card {
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 16px;
                    transition: all 0.3s;
                    cursor: pointer;
                }
                .card:hover {
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    transform: translateY(-2px);
                }
                .image {
                    width: 100%;
                    height: 200px;
                    object-fit: cover;
                    border-radius: 4px;
                    margin-bottom: 12px;
                }
                .title {
                    font-size: 18px;
                    font-weight: bold;
                    margin-bottom: 8px;
                    color: #333;
                }
                .description {
                    font-size: 14px;
                    color: #666;
                    margin-bottom: 12px;
                    line-height: 1.5;
                }
                .price {
                    color: #f00;
                    font-size: 24px;
                    font-weight: bold;
                }
                .old-price {
                    color: #999;
                    font-size: 16px;
                    text-decoration: line-through;
                    margin-left: 8px;
                }
            </style>
            <div class="card">
                <img class="image" alt="">
                <div class="title"></div>
                <div class="description"></div>
                <div>
                    <span class="price"></span>
                    <span class="old-price"></span>
                </div>
            </div>
        `;

        shadow.appendChild(template.content.cloneNode(true));

        // 缓存 DOM 引用
        this._card = shadow.querySelector('.card');
        this._image = shadow.querySelector('.image');
        this._title = shadow.querySelector('.title');
        this._description = shadow.querySelector('.description');
        this._price = shadow.querySelector('.price');
        this._oldPrice = shadow.querySelector('.old-price');

        // 绑定事件
        this._card.addEventListener('click', this._handleClick.bind(this));
    }

    // 声明监听的属性
    static get observedAttributes() {
        return ['title', 'price', 'old-price', 'description', 'image', 'disabled'];
    }

    // 属性变化回调
    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue === newValue) return;

        switch (name) {
            case 'title':
                this._title.textContent = newValue || '';
                break;
            case 'price':
                this._price.textContent = newValue || '';
                break;
            case 'old-price':
                this._oldPrice.textContent = newValue || '';
                this._oldPrice.style.display = newValue ? 'inline' : 'none';
                break;
            case 'description':
                this._description.textContent = newValue || '';
                break;
            case 'image':
                this._image.src = newValue || '';
                break;
            case 'disabled':
                // disabled 是布尔属性, 存在即为 true
                break;
        }
    }

    connectedCallback() {
        // 初始化渲染
        this.render();
    }

    disconnectedCallback() {
        // 清理事件监听器
        this._card.removeEventListener('click', this._handleClick);
    }

    render() {
        this._title.textContent = this.getAttribute('title') || '';
        this._price.textContent = this.getAttribute('price') || '';

        const oldPrice = this.getAttribute('old-price');
        this._oldPrice.textContent = oldPrice || '';
        this._oldPrice.style.display = oldPrice ? 'inline' : 'none';

        this._description.textContent = this.getAttribute('description') || '';
        this._image.src = this.getAttribute('image') || '';
    }

    _handleClick() {
        if (this.hasAttribute('disabled')) return;

        // 触发自定义事件
        this.dispatchEvent(new CustomEvent('product-select', {
            bubbles: true,
            composed: true,
            detail: {
                title: this.getAttribute('title'),
                price: this.getAttribute('price')
            }
        }));
    }

    // 公开 API
    disable() {
        this.setAttribute('disabled', '');
    }

    enable() {
        this.removeAttribute('disabled');
    }
}

// 防止重复注册
if (!customElements.get('product-card')) {
    customElements.define('product-card', ProductCard);
}
```

使用示例:

```html
<product-card
    title="机械键盘"
    price="¥299"
    old-price="¥399"
    description="87 键青轴, RGB 背光"
    image="/images/keyboard.jpg">
</product-card>

<script>
document.querySelector('product-card').addEventListener('product-select', (e) => {
    console.log('用户选择了:', e.detail);
});
</script>
```

### 组件通信模式

你研究了几种组件间通信的方式:

**① 属性传递 (父 → 子)**

```html
<parent-component>
    <child-component data="value"></child-component>
</parent-component>
```

**② 自定义事件 (子 → 父)**

```javascript
// 子组件
this.dispatchEvent(new CustomEvent('data-change', {
    bubbles: true,
    composed: true,
    detail: { newValue: 'xxx' }
}));

// 父组件
this.shadowRoot.querySelector('child-component').addEventListener('data-change', (e) => {
    console.log(e.detail.newValue);
});
```

**③ 直接调用 (父 → 子)**

```javascript
// 子组件暴露公开方法
class ChildComponent extends HTMLElement {
    publicMethod() {
        console.log('Public method called');
    }
}

// 父组件调用
const child = this.shadowRoot.querySelector('child-component');
child.publicMethod();
```

**④ 全局状态管理**

```javascript
// 简单的 EventBus
class EventBus {
    constructor() {
        this.events = {};
    }

    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    }

    emit(event, data) {
        if (this.events[event]) {
            this.events[event].forEach(callback => callback(data));
        }
    }

    off(event, callback) {
        if (this.events[event]) {
            this.events[event] = this.events[event].filter(cb => cb !== callback);
        }
    }
}

const bus = new EventBus();

// 组件 A 发送
bus.emit('user-login', { userId: 123 });

// 组件 B 接收
bus.on('user-login', (data) => {
    console.log('User logged in:', data.userId);
});
```

### 兼容性与渐进增强

你查了一下浏览器兼容性:

- Chrome 67+
- Firefox 63+
- Safari 10.1+
- Edge 79+

"现代浏览器都支持了, " 你想, "但如果需要兼容旧浏览器, 可以用 polyfill。"

你写了一个检测代码:

```javascript
// 检测浏览器是否支持 Web Components
function supportsWebComponents() {
    return (
        'customElements' in window &&
        'attachShadow' in Element.prototype &&
        'getRootNode' in Element.prototype &&
        'content' in document.createElement('template')
    );
}

if (!supportsWebComponents()) {
    console.warn('浏览器不支持 Web Components, 加载 polyfill...');

    // 动态加载 polyfill
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/@webcomponents/webcomponentsjs@2/webcomponents-loader.js';
    document.head.appendChild(script);
}
```

### 与框架的对比

你列了一个对比表:

| 特性 | Web Components | React | Vue |
|------|----------------|-------|-----|
| 浏览器原生支持 | ✅ | ❌ | ❌ |
| 需要构建工具 | ❌ | ✅ | ✅ |
| 学习曲线 | 中 | 中 | 低 |
| 生态系统 | 小 | 大 | 大 |
| 样式封装 | Shadow DOM | CSS Modules | Scoped CSS |
| 性能 | 优 | 优 | 优 |
| TypeScript 支持 | 需要手动 | 优秀 | 优秀 |

"Web Components 的优势是原生、零依赖、真正的封装, " 你总结, "但生态系统和开发体验不如现代框架。"

你想到一个应用场景: "可以用 Web Components 开发组件库, 然后在 React/Vue 项目中使用!"

---

## 实战应用与总结

傍晚, 你决定用 Web Components 实现一个完整的小功能: 评分组件。

```javascript
// star-rating.js - 评分组件
class StarRating extends HTMLElement {
    constructor() {
        super();

        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                :host {
                    display: inline-block;
                }
                .stars {
                    display: flex;
                    gap: 4px;
                }
                .star {
                    font-size: 24px;
                    cursor: pointer;
                    user-select: none;
                    transition: all 0.2s;
                }
                .star:hover {
                    transform: scale(1.2);
                }
                .star.filled {
                    color: #ffd700;
                }
                .star.empty {
                    color: #ddd;
                }
                :host([readonly]) .star {
                    cursor: default;
                    pointer-events: none;
                }
            </style>
            <div class="stars"></div>
        `;

        this._stars = shadow.querySelector('.stars');
        this._rating = 0;
        this._max = 5;

        this.render();
    }

    static get observedAttributes() {
        return ['value', 'max', 'readonly'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue === newValue) return;

        if (name === 'value') {
            this._rating = parseFloat(newValue) || 0;
            this.render();
        } else if (name === 'max') {
            this._max = parseInt(newValue) || 5;
            this.render();
        }
    }

    connectedCallback() {
        this.render();
    }

    render() {
        this._stars.innerHTML = '';

        for (let i = 1; i <= this._max; i++) {
            const star = document.createElement('span');
            star.className = 'star';
            star.textContent = '★';

            if (i <= this._rating) {
                star.classList.add('filled');
            } else {
                star.classList.add('empty');
            }

            if (!this.hasAttribute('readonly')) {
                star.addEventListener('click', () => this._handleClick(i));
                star.addEventListener('mouseenter', () => this._handleHover(i));
            }

            this._stars.appendChild(star);
        }

        if (!this.hasAttribute('readonly')) {
            this._stars.addEventListener('mouseleave', () => this._handleHover(this._rating));
        }
    }

    _handleClick(rating) {
        this._rating = rating;
        this.setAttribute('value', rating);

        this.dispatchEvent(new CustomEvent('rating-change', {
            bubbles: true,
            composed: true,
            detail: { rating }
        }));

        this.render();
    }

    _handleHover(rating) {
        const stars = this._stars.querySelectorAll('.star');
        stars.forEach((star, index) => {
            if (index < rating) {
                star.classList.add('filled');
                star.classList.remove('empty');
            } else {
                star.classList.remove('filled');
                star.classList.add('empty');
            }
        });
    }

    // 公开 API
    get value() {
        return this._rating;
    }

    set value(val) {
        this.setAttribute('value', val);
    }

    reset() {
        this.value = 0;
    }
}

if (!customElements.get('star-rating')) {
    customElements.define('star-rating', StarRating);
}
```

使用示例:

```html
<!-- 可编辑的评分 -->
<star-rating value="0" max="5"></star-rating>

<!-- 只读的评分显示 -->
<star-rating value="4.5" max="5" readonly></star-rating>

<script>
const rating = document.querySelector('star-rating');

rating.addEventListener('rating-change', (e) => {
    console.log('用户评分:', e.detail.rating);

    // 发送到服务器
    fetch('/api/rating', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating: e.detail.rating })
    });
});
</script>
```

你测试了一下, 功能完美运行。

"这个组件可以在任何项目中使用, " 你满意地想, "不依赖任何框架, 真正的可复用。"

你在 Notion 中创建了一个新页面, 标题是 "Web Components 学习总结"。周末的两天, 从紧急故障到深入研究, 你对这个原生组件系统有了全面的理解。

---

## 知识档案: Web Components 原生组件系统的八个核心机制

**规则 1: Web Components 是浏览器原生支持的组件系统, 由三大核心技术组成**

Web Components 不是单一技术, 而是三个 Web 标准的组合, 让开发者能创建可复用的自定义元素。

```javascript
// 三大核心技术

// ① Custom Elements: 定义自定义 HTML 元素
class MyElement extends HTMLElement {
    constructor() {
        super();
        // 初始化组件
    }
}
customElements.define('my-element', MyElement);

// ② Shadow DOM: 提供样式和 DOM 封装
class IsolatedElement extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });
        shadow.innerHTML = `
            <style>p { color: red; }</style>
            <p>Isolated content</p>
        `;
    }
}

// ③ HTML Templates: 定义可重用的 HTML 片段
<template id="my-template">
    <style>/* 组件样式 */</style>
    <div><!-- 组件结构 --></div>
</template>
```

三大技术的作用:
- **Custom Elements**: 注册和定义自定义元素, 提供生命周期钩子
- **Shadow DOM**: 封装组件内部结构和样式, 防止样式污染和泄漏
- **HTML Templates**: 定义可克隆的 HTML 模板, 提高性能和复用性

浏览器原生支持的优势:
- **零依赖**: 不需要任何框架或库
- **标准化**: W3C 标准, 跨浏览器一致
- **真正封装**: Shadow DOM 提供强封装, 不是约定而是隔离
- **可互操作**: 可以在任何框架中使用

---

**规则 2: Custom Elements 通过 extends HTMLElement 定义, 必须用 customElements.define 注册**

自定义元素必须继承 HTMLElement 或其子类, 并通过 customElements.define() 注册后才能使用。

```javascript
// 定义自定义元素
class UserCard extends HTMLElement {
    constructor() {
        super();  // 必须首先调用 super()

        // 初始化代码
        this.innerHTML = `
            <div class="user-card">
                <h3>${this.getAttribute('name')}</h3>
                <p>${this.getAttribute('email')}</p>
            </div>
        `;
    }
}

// 注册自定义元素
customElements.define('user-card', UserCard);

// 使用
<user-card name="Alice" email="alice@example.com"></user-card>
```

自定义元素命名规则:
- **必须包含连字符**: `my-element` (✅), `myelement` (❌)
- **全部小写**: `user-card` (✅), `UserCard` (❌)
- **不能是单个单词**: `card` (❌), `my-card` (✅)
- **避免与未来 HTML 标签冲突**: 连字符确保不会与未来的原生标签重名

重复注册检测:
```javascript
// 检查是否已注册
if (!customElements.get('user-card')) {
    customElements.define('user-card', UserCard);
}

// 或捕获异常
try {
    customElements.define('user-card', UserCard);
} catch (error) {
    console.warn('user-card 已经注册过了');
}
```

两种自定义元素类型:
```javascript
// ① 自主自定义元素 (Autonomous custom elements)
class MyButton extends HTMLElement { }
customElements.define('my-button', MyButton);
// 使用: <my-button></my-button>

// ② 自定义内置元素 (Customized built-in elements)
class FancyButton extends HTMLButtonElement { }
customElements.define('fancy-button', FancyButton, { extends: 'button' });
// 使用: <button is="fancy-button"></button>
```

---

**规则 3: Shadow DOM 提供真正的封装, mode 决定外部是否可访问 Shadow Root**

Shadow DOM 创建一个隔离的 DOM 树, 内部的样式和 DOM 结构与外部完全隔离。

```javascript
// 创建 Shadow DOM
class IsolatedComponent extends HTMLElement {
    constructor() {
        super();

        // mode: 'open' - 外部可通过 element.shadowRoot 访问
        const shadow = this.attachShadow({ mode: 'open' });

        // mode: 'closed' - 外部无法访问, this.shadowRoot 为 null
        // const shadow = this.attachShadow({ mode: 'closed' });

        shadow.innerHTML = `
            <style>
                /* 这些样式只作用于 Shadow DOM 内部 */
                p { color: red; }
            </style>
            <p>Isolated text</p>
        `;
    }
}
```

Shadow DOM 的封装特性:
```javascript
// 外部样式不影响 Shadow DOM
<style>
    p { color: blue; }  /* 不会影响 Shadow DOM 内的 p */
</style>

<isolated-component></isolated-component>  <!-- 内部 p 仍是红色 -->

// Shadow DOM 样式不泄漏到外部
const component = document.querySelector('isolated-component');
console.log(component.shadowRoot.querySelector('p'));  // 可以访问 (mode: 'open')

// 外部 JavaScript 无法直接访问 Shadow DOM 内的元素
document.querySelector('isolated-component p');  // null
```

Shadow DOM 样式穿透:
```javascript
shadow.innerHTML = `
    <style>
        :host {
            /* 选择 Shadow Host (组件本身) */
            display: block;
            border: 1px solid #ddd;
        }

        :host([disabled]) {
            /* 根据属性设置样式 */
            opacity: 0.5;
        }

        :host-context(.dark-theme) {
            /* 根据祖先元素设置样式 */
            background: #333;
        }

        ::slotted(p) {
            /* 选择插槽内容 */
            margin: 0;
        }
    </style>
`;
```

Shadow DOM 与 Light DOM:
- **Light DOM**: 用户提供的子元素 (外部 DOM)
- **Shadow DOM**: 组件内部的 DOM (Shadow Root)
- **Flattened Tree**: 渲染时的最终 DOM 树 (Light DOM 插入 Shadow DOM 的 slot)

mode 选择建议:
- **open**: 大多数场景, 允许外部访问和调试
- **closed**: 需要严格封装时, 但会增加调试难度

---

**规则 4: 自定义元素的四个生命周期回调对应创建、挂载、卸载和属性变化**

生命周期回调让开发者在元素的不同阶段执行代码, 类似 React 的生命周期。

```javascript
class LifecycleElement extends HTMLElement {
    constructor() {
        super();
        // 1. 元素被创建时调用
        // 适合: 初始化 Shadow DOM、设置初始状态
        // 限制: 不能访问属性、不能添加子元素
        console.log('constructor');

        this.attachShadow({ mode: 'open' });
    }

    connectedCallback() {
        // 2. 元素被插入 DOM 时调用
        // 适合: 获取数据、添加事件监听器、启动定时器
        console.log('connectedCallback');

        this.render();
        this.addEventListener('click', this.handleClick);
    }

    disconnectedCallback() {
        // 3. 元素从 DOM 移除时调用
        // 适合: 清理工作 (移除事件监听器、取消定时器、取消请求)
        console.log('disconnectedCallback');

        this.removeEventListener('click', this.handleClick);
        if (this.timer) clearInterval(this.timer);
    }

    attributeChangedCallback(name, oldValue, newValue) {
        // 4. 监听的属性变化时调用
        // 适合: 响应属性变化、重新渲染
        console.log(`${name}: ${oldValue} → ${newValue}`);

        if (oldValue !== newValue) {
            this.render();
        }
    }

    // 声明要监听的属性
    static get observedAttributes() {
        return ['title', 'count', 'disabled'];
    }
}
```

生命周期调用顺序:
```javascript
const element = document.createElement('lifecycle-element');
// 1. constructor 被调用

element.setAttribute('title', 'Hello');
// (不触发 attributeChangedCallback, 因为未挂载)

document.body.appendChild(element);
// 2. connectedCallback 被调用

element.setAttribute('count', '10');
// 3. attributeChangedCallback('count', null, '10') 被调用

element.remove();
// 4. disconnectedCallback 被调用
```

最佳实践:
```javascript
class BestPracticeElement extends HTMLElement {
    constructor() {
        super();

        // ✅ 创建 Shadow DOM
        this.attachShadow({ mode: 'open' });

        // ✅ 初始化内部状态
        this._data = null;

        // ❌ 不要访问属性
        // const title = this.getAttribute('title');  // 可能为 null

        // ❌ 不要添加事件监听器
        // this.addEventListener('click', ...);  // 应该在 connectedCallback
    }

    connectedCallback() {
        // ✅ 现在可以安全访问属性了
        this.render();

        // ✅ 添加事件监听器
        this.addEventListener('click', this.handleClick);

        // ✅ 获取数据
        this.fetchData();
    }

    disconnectedCallback() {
        // ✅ 清理所有副作用
        this.removeEventListener('click', this.handleClick);

        if (this.abortController) {
            this.abortController.abort();
        }
    }
}
```

---

**规则 5: observedAttributes 声明要监听的属性, 只有声明的属性变化才触发 attributeChangedCallback**

attributeChangedCallback 不会自动监听所有属性, 必须在 observedAttributes 中显式声明。

```javascript
class ReactiveElement extends HTMLElement {
    // 声明要监听的属性
    static get observedAttributes() {
        return ['title', 'count', 'disabled'];
        // 只有这三个属性变化时才会触发 attributeChangedCallback
    }

    attributeChangedCallback(name, oldValue, newValue) {
        // 只会在 title、count、disabled 变化时调用
        console.log(`${name} changed: ${oldValue} → ${newValue}`);

        switch (name) {
            case 'title':
                this.updateTitle(newValue);
                break;
            case 'count':
                this.updateCount(parseInt(newValue));
                break;
            case 'disabled':
                this.updateDisabledState(newValue !== null);
                break;
        }
    }
}

const element = document.createElement('reactive-element');
document.body.appendChild(element);

element.setAttribute('title', 'Hello');
// ✅ attributeChangedCallback 被调用: title changed: null → Hello

element.setAttribute('data-id', '123');
// ❌ attributeChangedCallback 不会被调用 (data-id 未在 observedAttributes 中)
```

属性与属性值 (Attributes vs Properties):
```javascript
class AttributePropertySync extends HTMLElement {
    static get observedAttributes() {
        return ['value'];
    }

    // 属性变化 → 更新 property
    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'value') {
            this._value = newValue;
        }
    }

    // Property getter/setter
    get value() {
        return this._value;
    }

    set value(val) {
        this._value = val;
        // Property 变化 → 更新 attribute
        this.setAttribute('value', val);
    }
}

const element = new AttributePropertySync();

// 方式 1: 通过 attribute 设置
element.setAttribute('value', '100');
// → attributeChangedCallback 调用 → this._value = '100'

// 方式 2: 通过 property 设置
element.value = '200';
// → setter 调用 → this.setAttribute('value', '200') → attributeChangedCallback
```

布尔属性处理:
```javascript
class BooleanAttributeElement extends HTMLElement {
    static get observedAttributes() {
        return ['disabled', 'checked'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        // 布尔属性: 存在即为 true, 不存在为 false
        const isPresent = newValue !== null;

        if (name === 'disabled') {
            this._disabled = isPresent;
            this.updateDisabledState();
        }
    }

    get disabled() {
        return this.hasAttribute('disabled');
    }

    set disabled(val) {
        if (val) {
            this.setAttribute('disabled', '');  // 添加属性
        } else {
            this.removeAttribute('disabled');  // 移除属性
        }
    }
}

const element = new BooleanAttributeElement();
element.disabled = true;   // <element disabled>
element.disabled = false;  // <element>
```

---

**规则 6: Slot 插槽机制允许用户向组件内部投射内容, 支持具名插槽和默认插槽**

Slot 让组件使用者可以向组件内部传递自定义内容, 实现组件的灵活组合。

```javascript
class SlotContainer extends HTMLElement {
    constructor() {
        super();

        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .container {
                    border: 1px solid #ddd;
                    padding: 16px;
                }
                .header { font-weight: bold; }
                .content { margin: 12px 0; }
                .footer { font-size: 12px; color: #666; }
            </style>
            <div class="container">
                <div class="header">
                    <slot name="header">默认标题</slot>
                </div>
                <div class="content">
                    <slot>默认内容</slot>
                </div>
                <div class="footer">
                    <slot name="footer">默认页脚</slot>
                </div>
            </div>
        `;
    }
}

customElements.define('slot-container', SlotContainer);
```

使用 slot:
```html
<!-- 使用所有插槽 -->
<slot-container>
    <span slot="header">自定义标题</span>
    <p>这是主要内容 (默认插槽)</p>
    <small slot="footer">2024-01-01</small>
</slot-container>

<!-- 只使用部分插槽 -->
<slot-container>
    <p>只提供主要内容, 其他使用默认值</p>
</slot-container>

<!-- 不提供任何内容 -->
<slot-container></slot-container>
<!-- 全部显示默认值 -->
```

Slot 的渲染机制:
```javascript
// Light DOM (用户提供)
<my-component>
    <span slot="title">Hello</span>
    <p>Content</p>
</my-component>

// Shadow DOM (组件内部)
shadowRoot.innerHTML = `
    <div>
        <slot name="title"></slot>
        <slot></slot>
    </div>
`;

// Flattened Tree (渲染结果)
<my-component>
    #shadow-root
        <div>
            <span slot="title">Hello</span>  <!-- 插入 name="title" 的 slot -->
            <p>Content</p>                   <!-- 插入默认 slot -->
        </div>
</my-component>
```

Slot 的 JavaScript 访问:
```javascript
class SlotAwareElement extends HTMLElement {
    constructor() {
        super();

        const shadow = this.attachShadow({ mode: 'open' });
        shadow.innerHTML = `<slot></slot>`;

        const slot = shadow.querySelector('slot');

        // 监听 slot 内容变化
        slot.addEventListener('slotchange', (e) => {
            const assignedNodes = slot.assignedNodes();
            console.log('Slot 内容:', assignedNodes);

            // 获取元素节点 (排除文本节点)
            const assignedElements = slot.assignedElements();
            console.log('Slot 元素:', assignedElements);
        });
    }
}
```

Slot 样式:
```javascript
shadow.innerHTML = `
    <style>
        /* 选择 slot 中的元素 */
        ::slotted(*) {
            margin: 8px 0;
        }

        /* 选择特定元素 */
        ::slotted(p) {
            color: blue;
        }

        /* ::slotted 只能选择直接子元素, 不能选择后代 */
        ::slotted(p span) {
            /* ❌ 无效 */
        }
    </style>
    <slot></slot>
`;
```

---

**规则 7: 自定义事件通过 dispatchEvent 触发, composed: true 允许事件穿透 Shadow DOM 边界**

Web Components 通过自定义事件与外部通信, 但 Shadow DOM 会阻止事件冒泡, 需要特殊处理。

```javascript
class EventEmitter extends HTMLElement {
    constructor() {
        super();

        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <button>Click me</button>
        `;

        shadow.querySelector('button').addEventListener('click', () => {
            // 触发自定义事件
            this.dispatchEvent(new CustomEvent('item-selected', {
                bubbles: true,      // 允许事件冒泡
                composed: true,     // 允许穿透 Shadow DOM 边界
                detail: {
                    timestamp: Date.now(),
                    data: 'some data'
                }
            }));
        });
    }
}

customElements.define('event-emitter', EventEmitter);
```

事件选项详解:
```javascript
// bubbles: 是否冒泡
// - false: 事件不会向上冒泡到父元素
// - true: 事件会冒泡, 可被祖先元素捕获

// composed: 是否穿透 Shadow DOM
// - false: 事件在 Shadow DOM 边界处停止
// - true: 事件可以穿透 Shadow Root, 冒泡到外部

new CustomEvent('my-event', {
    bubbles: true,
    composed: true,
    detail: { /* 自定义数据 */ }
});
```

事件传播示例:
```html
<div id="outer">
    <event-emitter></event-emitter>
</div>

<script>
// 监听自定义事件
document.getElementById('outer').addEventListener('item-selected', (e) => {
    console.log('外部捕获到事件');
    console.log('Detail:', e.detail);
    console.log('Target:', e.target);          // <event-emitter>
    console.log('Composed path:', e.composedPath());
});

// 如果 composed: false
// → 外部无法捕获事件 (事件被 Shadow DOM 阻止)

// 如果 composed: true
// → 外部可以捕获事件
</script>
```

事件重定向 (Event Retargeting):
```javascript
// Shadow DOM 内部触发的事件, 在外部看到的 target 会被重定向

// 内部 HTML
shadowRoot.innerHTML = `<button>Click</button>`;

// 内部监听器
shadowRoot.querySelector('button').addEventListener('click', (e) => {
    console.log('内部 target:', e.target);  // <button>
});

// 外部监听器
element.addEventListener('click', (e) => {
    console.log('外部 target:', e.target);  // <event-emitter> (重定向了)
    console.log('Composed path:', e.composedPath());
    // → [<button>, shadowRoot, <event-emitter>, <body>, <html>, document, Window]
});
```

组件间通信模式:
```javascript
// 父组件 → 子组件: 通过属性
<child-component data="value"></child-component>

// 子组件 → 父组件: 通过自定义事件
class ChildComponent extends HTMLElement {
    notifyParent() {
        this.dispatchEvent(new CustomEvent('child-update', {
            bubbles: true,
            composed: true,
            detail: { message: 'Hello from child' }
        }));
    }
}

// 兄弟组件: 通过共同父组件或事件总线
class EventBus extends EventTarget { }
const bus = new EventBus();

// 组件 A
bus.dispatchEvent(new CustomEvent('data-change', { detail: data }));

// 组件 B
bus.addEventListener('data-change', (e) => { });
```

---

**规则 8: Web Components 与框架可以互操作, 但需要注意属性传递和事件监听的差异**

Web Components 可以在 React、Vue 等框架中使用, 但需要处理框架特性与 Web Components 的差异。

```javascript
// 在 React 中使用 Web Components

// ❌ 问题 1: React 不会将对象/数组作为属性传递
function ReactComponent() {
    const data = { name: 'Alice', age: 25 };

    return <user-card data={data}></user-card>;
    // React 会将 data 转为字符串: data="[object Object]"
}

// ✅ 解决: 使用 ref 手动设置 property
function ReactComponentFixed() {
    const ref = useRef(null);
    const data = { name: 'Alice', age: 25 };

    useEffect(() => {
        if (ref.current) {
            ref.current.data = data;  // 直接设置 property
        }
    }, [data]);

    return <user-card ref={ref}></user-card>;
}

// ❌ 问题 2: React 不会添加自定义事件监听器
function ReactComponent2() {
    return (
        <custom-button
            onClick={(e) => console.log(e)}
            onCustomEvent={(e) => console.log(e)}>  {/* 无效! */}
        </custom-button>
    );
}

// ✅ 解决: 使用 ref 手动添加监听器
function ReactComponent2Fixed() {
    const ref = useRef(null);

    useEffect(() => {
        const element = ref.current;
        const handler = (e) => console.log('Custom event:', e.detail);

        element.addEventListener('custom-event', handler);

        return () => {
            element.removeEventListener('custom-event', handler);
        };
    }, []);

    return <custom-button ref={ref}></custom-button>;
}
```

在 Vue 中使用:
```vue
<template>
    <!-- Vue 3 支持自定义事件和属性绑定 -->
    <user-card
        :data="userData"
        @custom-event="handleCustomEvent">
    </user-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const userCardRef = ref(null);
const userData = ref({ name: 'Alice', age: 25 });

// Vue 3 自动处理大多数情况
// 但对于复杂对象, 可能仍需手动设置
onMounted(() => {
    if (userCardRef.value) {
        userCardRef.value.complexData = { /* ... */ };
    }
});

function handleCustomEvent(event) {
    console.log('Custom event:', event.detail);
}
</script>
```

框架适配器模式:
```javascript
// React 适配器: 封装 Web Component
import { useEffect, useRef } from 'react';

function WebComponentWrapper({ data, onCustomEvent, ...props }) {
    const ref = useRef(null);

    useEffect(() => {
        const element = ref.current;

        // 设置复杂属性
        if (data) {
            element.data = data;
        }

        // 添加事件监听器
        if (onCustomEvent) {
            element.addEventListener('custom-event', onCustomEvent);
            return () => {
                element.removeEventListener('custom-event', onCustomEvent);
            };
        }
    }, [data, onCustomEvent]);

    return <custom-element ref={ref} {...props} />;
}

// 使用适配器
function App() {
    return (
        <WebComponentWrapper
            data={{ name: 'Alice' }}
            onCustomEvent={(e) => console.log(e.detail)}
        />
    );
}
```

TypeScript 支持:
```typescript
// 声明自定义元素类型
declare global {
    namespace JSX {
        interface IntrinsicElements {
            'user-card': {
                title?: string;
                data?: UserData;
                onUserSelect?: (event: CustomEvent<UserData>) => void;
            };
        }
    }
}

// 或使用 React 的 DetailedHTMLProps
interface UserCardElement extends HTMLElement {
    data: UserData;
    addEventListener(
        type: 'user-select',
        listener: (event: CustomEvent<UserData>) => void
    ): void;
}

declare global {
    interface HTMLElementTagNameMap {
        'user-card': UserCardElement;
    }
}
```

兼容性处理:
```javascript
// 检测浏览器支持
function supportsWebComponents() {
    return (
        'customElements' in window &&
        'attachShadow' in Element.prototype &&
        'getRootNode' in Element.prototype &&
        'content' in document.createElement('template')
    );
}

// 动态加载 polyfill
async function ensureWebComponentsSupport() {
    if (!supportsWebComponents()) {
        await import('@webcomponents/webcomponentsjs');
    }
}

// 使用
ensureWebComponentsSupport().then(() => {
    // 初始化 Web Components
});
```

最佳实践:
```javascript
// 1. 提供 property 和 attribute 双向绑定
class BestPracticeElement extends HTMLElement {
    static get observedAttributes() {
        return ['value'];
    }

    get value() {
        return this._value;
    }

    set value(val) {
        this._value = val;
        this.setAttribute('value', val);
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'value') {
            this._value = newValue;
        }
    }
}

// 2. 所有事件都设置 composed: true
this.dispatchEvent(new CustomEvent('change', {
    bubbles: true,
    composed: true,
    detail: { value: this.value }
}));

// 3. 提供清晰的公开 API
class PublicAPIElement extends HTMLElement {
    // 公开方法
    focus() { /* ... */ }
    reset() { /* ... */ }
    validate() { /* ... */ }

    // 公开属性
    get value() { /* ... */ }
    set value(val) { /* ... */ }
}
```

---

**事故档案编号**: NETWORK-2024-1962
**影响范围**: Web Components, Custom Elements, Shadow DOM, 组件封装, 原生组件系统
**根本原因**: 组件重复注册导致 CustomElementRegistry 错误, 对浏览器原生组件系统缺乏理解
**学习成本**: 中高 (需理解 Custom Elements API、Shadow DOM 封装机制、生命周期、插槽系统)

这是 JavaScript 世界第 162 次被记录的网络与数据事故。Web Components 是浏览器原生支持的组件系统, 由 Custom Elements、Shadow DOM 和 HTML Templates 三大核心技术组成, 提供真正的组件封装和复用能力。Custom Elements 通过继承 HTMLElement 定义, 必须包含连字符且用 customElements.define() 注册, 注册时需防止重复注册导致异常。Shadow DOM 提供样式和 DOM 的真正封装, mode 参数决定外部是否可访问 Shadow Root, 内部样式与外部完全隔离。生命周期回调包括 constructor (创建)、connectedCallback (挂载)、disconnectedCallback (卸载)、attributeChangedCallback (属性变化), 必须在 observedAttributes 中声明要监听的属性。Slot 插槽机制允许用户向组件投射内容, 支持具名插槽和默认插槽, 实现灵活的组件组合。自定义事件通过 dispatchEvent 触发, composed: true 允许事件穿透 Shadow DOM 边界, 实现组件间通信。Web Components 可与 React/Vue 等框架互操作, 但需要注意属性传递和事件监听的差异, 通常需要适配器处理复杂属性和自定义事件。Web Components 提供零依赖、标准化、真正封装的原生组件开发能力, 是构建可复用组件的重要选择。

---
