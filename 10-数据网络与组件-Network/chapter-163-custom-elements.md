《第 163 次记录: 周二上午的技术选型 —— Custom Elements 自定义元素完整指南》

---

## 技术选型的起点

周二上午 10 点，会议室的白板上写着一行大字："前端组件库重构方案讨论"。

你坐在会议桌前，面前摆着笔记本和一杯已经凉了的咖啡。这次会议已经进行了半小时，技术经理老李刚刚抛出了一个让所有人都沉默的问题：

"我们是继续用 React 重构这 200 多个组件，还是考虑用 Web Components？"

团队分成了两派。前端组长小张坚持用 React："我们已经有完整的技术栈了，为什么要冒险？" 但架构师老王提出了不同意见："这些基础组件要给三个不同框架的项目用，React 组件做不到跨框架复用。"

老李看向你："你上周研究了 Web Components，有什么发现？"

你打开笔记本，调出上周末写的技术调研报告。你深吸一口气，开始讲述你的发现...

---

## 自定义元素的核心机制

"首先，我们需要理解 Custom Elements 到底是什么，" 你说着，打开 Chrome DevTools 的控制台。

"Custom Elements 是 Web Components 三大核心技术之一，它允许我们定义自己的 HTML 元素。关键是，这些元素是**浏览器原生支持**的，不依赖任何框架。"

你敲下第一个示例：

```javascript
// 最简单的自定义元素
class SimpleButton extends HTMLElement {
    constructor() {
        super();

        // 设置内部 HTML
        this.innerHTML = `
            <button style="
                padding: 12px 24px;
                background: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            ">
                Click Me
            </button>
        `;
    }
}

// 注册元素
customElements.define('simple-button', SimpleButton);
```

"然后我们就可以像使用普通 HTML 标签一样使用它："

```html
<simple-button></simple-button>
```

你刷新页面，一个蓝色按钮立刻出现在屏幕上。

小张皱眉："这和 React 组件有什么区别？"

"区别在于，" 你解释道，"这是**浏览器原生的**。不需要 React、Vue 或任何框架。任何项目都可以直接用 `<simple-button>` 标签。"

老王点头："继续说说技术细节。"

---

## 定义规则与命名约定

"第一个重要的规则，" 你说着，在白板上写下几行字，"自定义元素的命名必须遵守严格规则。"

你展示代码：

```javascript
// ✅ 正确的命名
customElements.define('user-card', UserCard);
customElements.define('my-button', MyButton);
customElements.define('app-header', AppHeader);
customElements.define('todo-list-item', TodoListItem);

// ❌ 错误的命名
customElements.define('usercard', UserCard);      // 没有连字符
customElements.define('UserCard', UserCard);      // 大写字母
customElements.define('user_card', UserCard);     // 下划线不行
customElements.define('button', MyButton);        // 单个单词
```

"为什么必须有连字符？" 小张问。

"防止与未来的原生 HTML 标签冲突，" 你回答，"HTML 规范保证所有原生标签都不会包含连字符。比如如果你定义了 `<button>`，就会和原生 `<button>` 标签冲突；但 `<my-button>` 永远不会冲突。"

你继续解释定义流程：

```javascript
// 完整的定义流程
class UserCard extends HTMLElement {
    constructor() {
        // 1. 必须首先调用 super()
        super();

        // 2. 初始化内部状态
        this._data = null;
        this._rendered = false;

        // 3. 可以添加内部 HTML（但此时不应该访问属性）
        this.innerHTML = `<div class="user-card">Loading...</div>`;
    }

    // 4. 元素被插入 DOM 时调用
    connectedCallback() {
        console.log('UserCard connected to DOM');
        this.render();
    }

    // 5. 元素从 DOM 移除时调用
    disconnectedCallback() {
        console.log('UserCard removed from DOM');
        this.cleanup();
    }

    render() {
        this._rendered = true;
        this.innerHTML = `
            <div class="user-card">
                <h3>User Card</h3>
                <p>Rendered at ${new Date().toLocaleTimeString()}</p>
            </div>
        `;
    }

    cleanup() {
        // 清理工作：移除事件监听器、取消定时器等
    }
}

// 注册元素
customElements.define('user-card', UserCard);
```

"注意，" 你强调，"`customElements.define()` 是全局注册。一旦注册，整个文档中的所有 `<user-card>` 标签都会被升级为这个类的实例。"

---

## 生命周期的完整流程

"生命周期是 Custom Elements 最重要的概念，" 你切换到下一页 PPT。

"一共有四个生命周期回调：`constructor`、`connectedCallback`、`disconnectedCallback`、`attributeChangedCallback`。理解它们的调用时机和限制非常关键。"

你展示了一个完整的生命周期示例：

```javascript
class LifecycleDemo extends HTMLElement {
    constructor() {
        super();
        console.log('1. constructor 被调用');

        // ✅ 可以做的事
        this._state = { count: 0 };
        this.attachShadow({ mode: 'open' });

        // ❌ 不应该做的事
        // this.getAttribute('title');  // 属性可能还不存在
        // this.addEventListener('click', ...);  // 应该在 connectedCallback 中添加
    }

    connectedCallback() {
        console.log('2. connectedCallback 被调用');
        console.log('   元素已插入 DOM，现在可以安全地：');
        console.log('   - 访问属性');
        console.log('   - 添加事件监听器');
        console.log('   - 启动定时器');
        console.log('   - 发起网络请求');

        // ✅ 现在可以安全访问属性
        const title = this.getAttribute('title');
        console.log('   title 属性:', title);

        // ✅ 添加事件监听器
        this.addEventListener('click', this._handleClick);

        // ✅ 渲染内容
        this.render();
    }

    disconnectedCallback() {
        console.log('3. disconnectedCallback 被调用');
        console.log('   元素已从 DOM 移除，应该清理：');
        console.log('   - 移除事件监听器');
        console.log('   - 清除定时器');
        console.log('   - 取消网络请求');

        // ✅ 清理事件监听器
        this.removeEventListener('click', this._handleClick);

        // ✅ 清理定时器
        if (this._timer) {
            clearInterval(this._timer);
            this._timer = null;
        }
    }

    // 声明要监听哪些属性
    static get observedAttributes() {
        return ['title', 'count'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        console.log(`4. attributeChangedCallback 被调用`);
        console.log(`   属性 "${name}" 从 "${oldValue}" 变为 "${newValue}"`);

        // 响应属性变化
        if (name === 'title') {
            this.updateTitle(newValue);
        } else if (name === 'count') {
            this._state.count = parseInt(newValue) || 0;
            this.updateCount();
        }
    }

    render() {
        const shadow = this.shadowRoot;
        shadow.innerHTML = `
            <style>
                .demo {
                    padding: 16px;
                    border: 2px solid #007bff;
                    border-radius: 4px;
                }
            </style>
            <div class="demo">
                <h3>${this.getAttribute('title') || 'No title'}</h3>
                <p>Count: ${this._state.count}</p>
            </div>
        `;
    }

    updateTitle(title) {
        const h3 = this.shadowRoot.querySelector('h3');
        if (h3) h3.textContent = title;
    }

    updateCount() {
        const p = this.shadowRoot.querySelector('p');
        if (p) p.textContent = `Count: ${this._state.count}`;
    }

    _handleClick = () => {
        this._state.count++;
        this.setAttribute('count', this._state.count);
    }
}

customElements.define('lifecycle-demo', LifecycleDemo);
```

"我们来测试一下生命周期的调用顺序，" 你打开控制台：

```javascript
// 测试 1: 创建元素
const demo = document.createElement('lifecycle-demo');
// 输出: 1. constructor 被调用

// 测试 2: 设置属性（此时元素还未挂载）
demo.setAttribute('title', 'Hello');
// 不会触发 attributeChangedCallback，因为元素还没挂载

// 测试 3: 插入 DOM
document.body.appendChild(demo);
// 输出: 2. connectedCallback 被调用
//       title 属性: Hello

// 测试 4: 修改属性（元素已挂载）
demo.setAttribute('count', '10');
// 输出: 4. attributeChangedCallback 被调用
//       属性 "count" 从 "null" 变为 "10"

// 测试 5: 移除元素
demo.remove();
// 输出: 3. disconnectedCallback 被调用
```

小张若有所思："所以 `constructor` 不能做太多事？"

"对，" 你确认，"`constructor` 的限制很严格：不能访问属性、不能访问子元素、不能添加事件监听器。所有这些操作都应该放在 `connectedCallback` 中。"

老王补充："这和 React 的 `componentDidMount` 类似。"

"完全正确，" 你点头，"生命周期的设计理念是一样的。"

---

## 属性与 Property 的同步

"下一个关键问题，" 你继续，"是 **Attribute** 和 **Property** 的区别。"

"HTML 元素有两种设置值的方式：Attribute（HTML 属性）和 Property（JavaScript 属性）。Custom Elements 需要正确处理两者的同步。"

你展示了一个完整的示例：

```javascript
class SyncDemo extends HTMLElement {
    static get observedAttributes() {
        return ['value'];
    }

    constructor() {
        super();
        this._value = '';  // 内部状态
    }

    // Property getter: 读取 JavaScript 属性
    get value() {
        return this._value;
    }

    // Property setter: 设置 JavaScript 属性
    set value(val) {
        this._value = val;
        // Property 变化 → 同步到 Attribute
        this.setAttribute('value', val);
    }

    // Attribute 变化回调
    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'value' && newValue !== this._value) {
            // Attribute 变化 → 同步到内部状态
            this._value = newValue;
            this.updateUI();
        }
    }

    connectedCallback() {
        this.innerHTML = `<input type="text" />`;
        const input = this.querySelector('input');

        // 初始化 input 的值
        input.value = this._value;

        // input 变化 → 同步到 Property
        input.addEventListener('input', (e) => {
            this.value = e.target.value;
        });
    }

    updateUI() {
        const input = this.querySelector('input');
        if (input && input.value !== this._value) {
            input.value = this._value;
        }
    }
}

customElements.define('sync-demo', SyncDemo);
```

"现在测试三种同步路径：" 你演示道：

```javascript
const demo = document.body.appendChild(
    document.createElement('sync-demo')
);

// 路径 1: 通过 Attribute 设置
demo.setAttribute('value', 'Hello');
console.log(demo.value);  // "Hello" ✅ Attribute → Property

// 路径 2: 通过 Property 设置
demo.value = 'World';
console.log(demo.getAttribute('value'));  // "World" ✅ Property → Attribute

// 路径 3: 用户在 input 中输入
// input 事件 → Property setter → Attribute → attributeChangedCallback
```

"这种双向同步的模式，" 你总结道，"是 Custom Elements 的最佳实践。它确保无论用户通过 HTML、JavaScript 还是 UI 交互修改值，三者始终保持同步。"

小张问："那布尔属性怎么处理？比如 `disabled`？"

"好问题，" 你切换到下一个示例：

```javascript
class BooleanAttrDemo extends HTMLElement {
    static get observedAttributes() {
        return ['disabled'];
    }

    // Property getter: 返回布尔值
    get disabled() {
        return this.hasAttribute('disabled');
    }

    // Property setter: 布尔值 → Attribute 存在性
    set disabled(val) {
        if (val) {
            this.setAttribute('disabled', '');  // 添加属性（值为空字符串）
        } else {
            this.removeAttribute('disabled');   // 移除属性
        }
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'disabled') {
            // 属性存在 → true, 不存在 → false
            const isDisabled = newValue !== null;
            this.updateDisabledState(isDisabled);
        }
    }

    connectedCallback() {
        this.innerHTML = `
            <button>Click me</button>
        `;
        this.updateDisabledState(this.disabled);
    }

    updateDisabledState(disabled) {
        const button = this.querySelector('button');
        if (button) {
            button.disabled = disabled;
            button.style.opacity = disabled ? '0.5' : '1';
        }
    }
}

customElements.define('boolean-attr-demo', BooleanAttrDemo);
```

"布尔属性的关键，" 你解释，"是**属性的存在性**表示真值，而不是属性的值。就像原生的 `<button disabled>` 一样。"

```html
<!-- 这两种写法都表示 disabled = true -->
<boolean-attr-demo disabled></boolean-attr-demo>
<boolean-attr-demo disabled=""></boolean-attr-demo>

<!-- 只有移除属性才表示 disabled = false -->
<boolean-attr-demo></boolean-attr-demo>
```

---

## 自主元素与定制内置元素

"Custom Elements 有两种形式，" 你说着，在白板上画了两个分支。

"第一种是**自主自定义元素**（Autonomous custom elements），我们刚才看到的都是这种。它们继承 `HTMLElement`，完全独立。"

"第二种是**定制内置元素**（Customized built-in elements），它们扩展现有的 HTML 元素。"

你展示了对比：

```javascript
// 方式 1: 自主自定义元素
class FancyButton extends HTMLElement {
    constructor() {
        super();
        this.innerHTML = `
            <button>Fancy Button</button>
        `;
    }
}

customElements.define('fancy-button', FancyButton);

// 使用方式
<fancy-button></fancy-button>


// 方式 2: 定制内置元素
class ExtendedButton extends HTMLButtonElement {
    constructor() {
        super();
        this.addEventListener('click', () => {
            console.log('Extended button clicked!');
        });
    }
}

customElements.define('extended-button', ExtendedButton, {
    extends: 'button'  // ← 关键：指定扩展哪个元素
});

// 使用方式
<button is="extended-button">Extended Button</button>
```

"注意区别，" 你强调：

```javascript
// 自主元素：新标签名
<fancy-button></fancy-button>

// 定制内置元素：原标签名 + is 属性
<button is="extended-button"></button>
```

小张问："为什么要有第二种方式？"

"因为有些场景下，你想**保留原生元素的功能**，只是增强它，" 你解释，"比如你想扩展 `<button>`，但仍然保留它的表单提交、键盘访问等原生行为。"

你展示了一个实际例子：

```javascript
// 扩展 <a> 元素，添加点击统计
class TrackedLink extends HTMLAnchorElement {
    constructor() {
        super();

        this.addEventListener('click', (e) => {
            // 统计点击
            console.log('Link clicked:', this.href);

            // 发送统计数据
            fetch('/api/track', {
                method: 'POST',
                body: JSON.stringify({
                    url: this.href,
                    timestamp: Date.now()
                })
            });

            // 原生的链接跳转行为仍然会执行
        });
    }
}

customElements.define('tracked-link', TrackedLink, {
    extends: 'a'
});
```

```html
<!-- 使用：所有原生 <a> 的功能都保留 -->
<a is="tracked-link" href="/page">
    This link tracks clicks
</a>
```

"但有个问题，" 你补充道，"Safari 长期不支持定制内置元素。所以如果你需要跨浏览器兼容，建议只用自主自定义元素。"

老王记下笔记："明白了，兼容性是个考虑因素。"

---

## 高级模式与最佳实践

"最后，我想分享几个高级模式，" 你说着，切换到最后几页 PPT。

### 模式 1: 延迟渲染

"不要在 `constructor` 中渲染，应该延迟到 `connectedCallback`："

```javascript
class LazyRender extends HTMLElement {
    constructor() {
        super();
        // ❌ 不要在这里渲染
        // this.innerHTML = '...';

        // ✅ 只初始化状态
        this._rendered = false;
    }

    connectedCallback() {
        // ✅ 元素挂载后才渲染
        if (!this._rendered) {
            this.render();
            this._rendered = true;
        }
    }

    render() {
        this.innerHTML = `
            <div>Content rendered at ${Date.now()}</div>
        `;
    }
}
```

### 模式 2: 防止重复渲染

"如果元素被频繁移动，`connectedCallback` 会被多次调用。需要防止重复渲染："

```javascript
class OptimizedRender extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this._initialized = false;
    }

    connectedCallback() {
        // ✅ 只在第一次挂载时渲染
        if (!this._initialized) {
            this.render();
            this._initialized = true;
        }

        // 每次挂载都需要的操作（如事件监听）
        this.addEventListener('click', this._handleClick);
    }

    disconnectedCallback() {
        // 每次移除都需要清理
        this.removeEventListener('click', this._handleClick);
    }

    render() {
        // 耗时的渲染操作只执行一次
        this.shadowRoot.innerHTML = `...`;
    }

    _handleClick = () => {
        console.log('Clicked');
    }
}
```

### 模式 3: 异步属性更新

"属性变化可能很频繁，应该批量处理："

```javascript
class BatchUpdate extends HTMLElement {
    static get observedAttributes() {
        return ['x', 'y', 'width', 'height'];
    }

    constructor() {
        super();
        this._updateScheduled = false;
        this._pendingUpdate = {};
    }

    attributeChangedCallback(name, oldValue, newValue) {
        // 收集变化
        this._pendingUpdate[name] = newValue;

        // 调度批量更新
        if (!this._updateScheduled) {
            this._updateScheduled = true;

            // 使用 Promise.resolve() 在微任务中批量更新
            Promise.resolve().then(() => {
                this.performUpdate(this._pendingUpdate);
                this._pendingUpdate = {};
                this._updateScheduled = false;
            });
        }
    }

    performUpdate(changes) {
        console.log('批量更新:', changes);
        // 一次性处理所有属性变化
        // 例如：更新 Canvas、重新布局等
    }
}
```

### 模式 4: 优雅降级

"处理未升级的元素："

```javascript
class GracefulElement extends HTMLElement {
    connectedCallback() {
        // 检查是否已升级
        if (!customElements.get('graceful-element')) {
            console.warn('Element not upgraded yet');
            return;
        }

        this.render();
    }

    render() {
        this.innerHTML = `<div>Upgraded content</div>`;
    }
}

// 延迟注册
setTimeout(() => {
    customElements.define('graceful-element', GracefulElement);
}, 1000);
```

```html
<!-- HTML 中先使用 -->
<graceful-element>
    <!-- 提供降级内容 -->
    <div>Loading...</div>
</graceful-element>

<!-- 1秒后元素会被升级，降级内容被替换 -->
```

### 模式 5: 数据驱动更新

"实现类似 React 的单向数据流："

```javascript
class DataDriven extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this._data = { count: 0, message: '' };
    }

    // 唯一的数据入口
    setState(newData) {
        this._data = { ...this._data, ...newData };
        this.render();
    }

    connectedCallback() {
        this.render();

        // 事件触发状态更新
        this.shadowRoot.addEventListener('click', () => {
            this.setState({
                count: this._data.count + 1,
                message: `Clicked ${this._data.count + 1} times`
            });
        });
    }

    render() {
        // 数据 → UI 的单向流动
        this.shadowRoot.innerHTML = `
            <style>
                .container {
                    padding: 16px;
                    cursor: pointer;
                }
            </style>
            <div class="container">
                <p>Count: ${this._data.count}</p>
                <p>${this._data.message}</p>
            </div>
        `;
    }
}

customElements.define('data-driven', DataDriven);
```

---

## 决策时刻

会议已经进行了近两个小时。你合上笔记本，等待大家的反应。

老李首先发言："从技术角度看，Custom Elements 确实很强大。但我们需要考虑实际问题：学习成本、生态系统、调试工具..."

小张补充："React 的开发体验更好，有完整的工具链、丰富的生态。Custom Elements 相比之下太原始了。"

"但跨框架复用是真实需求，" 老王反驳，"我们的 Design System 要给 React、Vue 和 Angular 三个项目用。如果用 React 组件，其他两个项目怎么办？"

你想了想，说："我的建议是混合方案。"

所有人看向你。

"基础 UI 组件用 Custom Elements，" 你解释，"比如 Button、Input、Card 这些。它们逻辑简单，但需要跨框架复用。业务组件继续用 React，因为它们逻辑复杂，不需要复用。"

老李点头："这是个务实的方案。小张，你觉得呢？"

小张思考了一会儿："可以试试。但我们需要先做个 Proof of Concept，验证性能、兼容性和开发体验。"

"同意，" 老王说，"我们先用 Custom Elements 重构 5 个最基础的组件，看看效果。"

会议结束时，老李拍了拍你的肩膀："这周就麻烦你了，PoC 方案由你来做。"

你回到座位，打开 VS Code，开始设计第一个 Custom Element 组件的架构...

---

## 知识档案: Custom Elements 自定义元素的八个核心规则

**规则 1: 元素命名必须包含连字符，且全部小写**

Custom Elements 的命名规则严格限制，防止与现有或未来的 HTML 标签冲突。

```javascript
// 命名规则
// ✅ 正确：包含连字符，全部小写
customElements.define('user-card', UserCard);
customElements.define('my-button', MyButton);
customElements.define('todo-list-item', TodoListItem);

// ❌ 错误：违反命名规则
customElements.define('usercard', UserCard);     // 缺少连字符
customElements.define('UserCard', UserCard);     // 包含大写
customElements.define('user_card', UserCard);    // 下划线不允许
customElements.define('button', MyButton);       // 单个单词，可能冲突

// 规则原因
// HTML 规范保证：所有原生标签名不会包含连字符
// 因此 <my-element> 永远不会与原生标签冲突
// 但 <element> 可能在未来成为原生标签
```

命名最佳实践:
- **使用命名空间前缀**: `app-button`, `ui-card` 避免与其他库冲突
- **语义化命名**: `user-profile`, `product-card` 而非 `comp-1`, `widget-a`
- **避免过长**: `my-btn` 比 `my-super-fancy-button-component` 更好
- **一致性**: 团队统一命名风格和前缀

---

**规则 2: 类必须继承 HTMLElement，constructor 必须调用 super()**

Custom Elements 必须继承自 `HTMLElement` 或其子类，并在 constructor 中首先调用 `super()`。

```javascript
// 基本继承
class MyElement extends HTMLElement {
    constructor() {
        super();  // ✅ 必须首先调用

        // ✅ 可以做的事
        this._state = {};                          // 初始化内部状态
        this.attachShadow({ mode: 'open' });      // 创建 Shadow DOM
        this._handleClick = this._handleClick.bind(this);  // 绑定方法

        // ❌ 不应该做的事
        // this.getAttribute('title');             // 属性可能还不存在
        // this.addEventListener('click', ...);    // 应该在 connectedCallback
        // this.appendChild(...);                  // 不应该修改子元素
        // this.classList.add(...);               // 不应该修改自身
    }
}

// 继承内置元素（定制内置元素）
class FancyButton extends HTMLButtonElement {
    constructor() {
        super();  // 继承 button 的所有功能
        this.setAttribute('role', 'button');
    }
}

customElements.define('fancy-button', FancyButton, {
    extends: 'button'  // 必须指定扩展的元素
});

// 使用方式对比
// 自主元素: <my-element></my-element>
// 定制内置元素: <button is="fancy-button"></button>
```

constructor 限制的原因:
- **时机问题**: constructor 调用时，元素还未插入 DOM，无法访问文档上下文
- **属性未就绪**: HTML 解析器可能还未设置属性
- **性能考虑**: 延迟初始化到 connectedCallback 可以提高性能
- **规范要求**: 违反规范可能导致未定义行为或错误

---

**规则 3: 生命周期回调按严格顺序执行，各有专门用途**

四个生命周期回调在元素生命周期的不同阶段被调用，必须理解它们的时机和限制。

```javascript
class LifecycleElement extends HTMLElement {
    // 1. constructor: 元素被创建（new 或 createElement）
    constructor() {
        super();
        console.log('1. constructor');

        // ✅ 适合做的事
        this._state = { initialized: false };     // 初始化状态
        this.attachShadow({ mode: 'open' });      // 创建 Shadow DOM

        // ❌ 限制
        // - 不能访问 attributes
        // - 不能添加/修改子元素
        // - 不能添加事件监听器
        // - 不能访问父节点或兄弟节点
    }

    // 2. connectedCallback: 元素被插入 DOM
    connectedCallback() {
        console.log('2. connectedCallback');

        // ✅ 适合做的事
        this.render();                             // 渲染内容
        this.addEventListener('click', this._handleClick);  // 添加事件
        this._timer = setInterval(..., 1000);     // 启动定时器
        this.fetchData();                          // 发起网络请求

        // 访问属性
        const title = this.getAttribute('title');

        // 访问父节点
        const parent = this.parentNode;

        // 特殊情况: 可能被多次调用
        // 元素在 DOM 中移动时会触发 disconnected → connected
    }

    // 3. disconnectedCallback: 元素从 DOM 移除
    disconnectedCallback() {
        console.log('3. disconnectedCallback');

        // ✅ 清理工作
        this.removeEventListener('click', this._handleClick);  // 移除事件
        clearInterval(this._timer);                // 清除定时器
        this._abortController?.abort();           // 取消请求

        // 注意: 元素可能被重新插入
        // 不要销毁可能需要的状态
    }

    // 4. attributeChangedCallback: 监听的属性变化
    static get observedAttributes() {
        return ['title', 'count'];  // 声明要监听的属性
    }

    attributeChangedCallback(name, oldValue, newValue) {
        console.log(`4. attributeChangedCallback: ${name}`);
        console.log(`   ${oldValue} → ${newValue}`);

        // ✅ 响应属性变化
        if (name === 'title') {
            this.updateTitle(newValue);
        }

        // 注意: 在 connectedCallback 之前也可能被调用
        // 需要检查元素是否已初始化
        if (!this.isConnected) return;
    }
}

// 调用顺序测试
const element = document.createElement('lifecycle-element');
// 输出: 1. constructor

element.setAttribute('title', 'Hello');
// (不触发 attributeChangedCallback，因为未监听或未挂载)

document.body.appendChild(element);
// 输出: 2. connectedCallback

element.setAttribute('title', 'World');
// 输出: 4. attributeChangedCallback: title
//       Hello → World

element.remove();
// 输出: 3. disconnectedCallback
```

生命周期最佳实践:
- **constructor**: 仅初始化状态，不访问外部
- **connectedCallback**: 渲染、事件、定时器、网络请求
- **disconnectedCallback**: 清理所有副作用，防止内存泄漏
- **attributeChangedCallback**: 响应式更新，检查 isConnected 状态

---

**规则 4: observedAttributes 声明要监听的属性，只有声明的属性变化才触发回调**

`attributeChangedCallback` 不会自动监听所有属性，必须在 `observedAttributes` 中显式声明。

```javascript
class AttributeDemo extends HTMLElement {
    // ✅ 必须声明要监听的属性
    static get observedAttributes() {
        return ['title', 'count', 'disabled'];
        // 只有这三个属性变化才会触发 attributeChangedCallback
    }

    attributeChangedCallback(name, oldValue, newValue) {
        console.log(`${name}: ${oldValue} → ${newValue}`);

        switch (name) {
            case 'title':
                this.updateTitle(newValue);
                break;
            case 'count':
                this.updateCount(parseInt(newValue) || 0);
                break;
            case 'disabled':
                this.updateDisabledState(newValue !== null);
                break;
        }
    }

    updateTitle(title) {
        const h3 = this.shadowRoot?.querySelector('h3');
        if (h3) h3.textContent = title;
    }

    updateCount(count) {
        const span = this.shadowRoot?.querySelector('.count');
        if (span) span.textContent = count;
    }

    updateDisabledState(disabled) {
        this.classList.toggle('disabled', disabled);
    }
}

// 测试属性监听
const demo = document.createElement('attribute-demo');
document.body.appendChild(demo);

demo.setAttribute('title', 'Hello');
// ✅ 触发 attributeChangedCallback

demo.setAttribute('count', '10');
// ✅ 触发 attributeChangedCallback

demo.setAttribute('data-id', '123');
// ❌ 不触发 attributeChangedCallback（未声明）

demo.setAttribute('class', 'active');
// ❌ 不触发 attributeChangedCallback（未声明）
```

属性类型处理模式:

```javascript
// 字符串属性
get title() {
    return this.getAttribute('title') || '';
}

set title(val) {
    this.setAttribute('title', val);
}

// 数字属性
get count() {
    return parseInt(this.getAttribute('count')) || 0;
}

set count(val) {
    this.setAttribute('count', val.toString());
}

// 布尔属性（重要：存在性表示真值）
get disabled() {
    return this.hasAttribute('disabled');
}

set disabled(val) {
    if (val) {
        this.setAttribute('disabled', '');  // 添加属性
    } else {
        this.removeAttribute('disabled');   // 移除属性
    }
}

// 对象/数组属性（JSON）
get data() {
    const json = this.getAttribute('data');
    try {
        return json ? JSON.parse(json) : null;
    } catch (e) {
        return null;
    }
}

set data(val) {
    this.setAttribute('data', JSON.stringify(val));
}
```

性能优化:
- **批量属性更新**: 使用微任务批处理多个属性变化
- **避免无效更新**: 检查 `oldValue !== newValue`
- **延迟渲染**: 属性变化时标记脏状态，在 connectedCallback 统一渲染

---

**规则 5: Attribute 与 Property 必须双向同步，保持一致性**

HTML Attribute（HTML 属性）和 JavaScript Property（对象属性）是两个独立的系统，需要手动同步。

```javascript
class SyncElement extends HTMLElement {
    static get observedAttributes() {
        return ['value'];
    }

    constructor() {
        super();
        this._value = '';  // 内部状态
    }

    // Property getter: JavaScript 读取
    get value() {
        return this._value;
    }

    // Property setter: JavaScript 设置
    set value(val) {
        this._value = val;
        // Property → Attribute 同步
        this.setAttribute('value', val);
        // 触发 attributeChangedCallback
    }

    // Attribute → Property 同步
    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'value' && newValue !== this._value) {
            this._value = newValue;
            this.updateUI();
        }
    }

    updateUI() {
        // 内部状态 → UI 更新
        const span = this.shadowRoot?.querySelector('span');
        if (span) span.textContent = this._value;
    }
}

// 三种设置方式
const el = document.createElement('sync-element');
document.body.appendChild(el);

// 方式 1: Attribute (HTML)
el.setAttribute('value', 'Hello');
// 流程: setAttribute → attributeChangedCallback → _value → updateUI
console.log(el.value);  // "Hello" ✅

// 方式 2: Property (JavaScript)
el.value = 'World';
// 流程: setter → _value → setAttribute → attributeChangedCallback → updateUI
console.log(el.getAttribute('value'));  // "World" ✅

// 方式 3: HTML
<sync-element value="Initial"></sync-element>
// 流程: HTML 解析 → setAttribute → attributeChangedCallback → _value
```

同步模式对比:

```javascript
// ❌ 错误：单向同步（缺少 Property → Attribute）
class BadSync extends HTMLElement {
    get value() {
        return this.getAttribute('value');
    }

    set value(val) {
        this._value = val;  // 只更新内部状态
        // 缺少: this.setAttribute('value', val);
    }

    // 问题:
    // el.value = 'test';
    // console.log(el.getAttribute('value'));  // null ❌
}

// ✅ 正确：双向同步
class GoodSync extends HTMLElement {
    get value() {
        return this._value;
    }

    set value(val) {
        this._value = val;
        this.setAttribute('value', val);  // Property → Attribute
    }

    attributeChangedCallback(name, oldValue, newValue) {
        this._value = newValue;  // Attribute → Property
        this.updateUI();
    }
}

// ✅ 最佳实践：防止循环更新
class BestSync extends HTMLElement {
    set value(val) {
        if (this._value === val) return;  // 避免无效更新
        this._value = val;
        this.setAttribute('value', val);
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (this._value === newValue) return;  // 避免循环
        this._value = newValue;
        this.updateUI();
    }
}
```

复杂对象同步:

```javascript
class ObjectSync extends HTMLElement {
    static get observedAttributes() {
        return ['user'];
    }

    // Property: JavaScript 对象
    get user() {
        return this._user;
    }

    set user(obj) {
        this._user = obj;
        // 对象 → JSON → Attribute
        this.setAttribute('user', JSON.stringify(obj));
    }

    // Attribute: JSON 字符串 → 对象
    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'user') {
            try {
                this._user = JSON.parse(newValue);
                this.updateUI();
            } catch (e) {
                console.error('Invalid JSON:', newValue);
            }
        }
    }
}

// 使用
el.user = { name: 'Alice', age: 25 };
// → setAttribute('user', '{"name":"Alice","age":25}')

<object-sync user='{"name":"Bob","age":30}'></object-sync>
// → JSON.parse() → this._user
```

---

**规则 6: connectedCallback 可能被多次调用，需要幂等性设计**

当元素在 DOM 中移动时，`disconnectedCallback` 和 `connectedCallback` 会依次触发。

```javascript
class MovableElement extends HTMLElement {
    constructor() {
        super();
        this._initialized = false;
        this._renderCount = 0;
    }

    connectedCallback() {
        console.log('connectedCallback called');

        // ❌ 错误：每次调用都重新初始化
        // this.innerHTML = '<div>...</div>';
        // 问题：元素移动时会重复渲染，丢失状态

        // ✅ 正确：只初始化一次
        if (!this._initialized) {
            this.innerHTML = '<div>Content</div>';
            this._initialized = true;
        }

        // ✅ 每次挂载都需要的操作
        this.addEventListener('click', this._handleClick);
        this._startPolling();

        this._renderCount++;
        console.log(`Rendered ${this._renderCount} times`);
    }

    disconnectedCallback() {
        console.log('disconnectedCallback called');

        // ✅ 每次移除都需要清理
        this.removeEventListener('click', this._handleClick);
        this._stopPolling();

        // ❌ 不要清理可能需要的状态
        // this._initialized = false;  // 错误：下次挂载还需要这个状态
    }

    _handleClick = () => {
        console.log('Clicked');
    }

    _startPolling() {
        this._pollingTimer = setInterval(() => {
            console.log('Polling...');
        }, 1000);
    }

    _stopPolling() {
        if (this._pollingTimer) {
            clearInterval(this._pollingTimer);
            this._pollingTimer = null;
        }
    }
}

// 测试移动元素
const el = document.createElement('movable-element');
document.body.appendChild(el);
// 输出: connectedCallback called
//       Rendered 1 times

// 移动到另一个容器
const container = document.createElement('div');
document.body.appendChild(container);
container.appendChild(el);
// 输出: disconnectedCallback called
//       connectedCallback called
//       Rendered 2 times
```

幂等性设计模式:

```javascript
// 模式 1: 标志位控制
class IdempotentElement extends HTMLElement {
    connectedCallback() {
        if (!this._setup) {
            this.performExpensiveSetup();
            this._setup = true;
        }

        this.attachListeners();  // 每次挂载都执行
    }

    disconnectedCallback() {
        this.detachListeners();  // 每次移除都执行
        // 不重置 this._setup
    }
}

// 模式 2: 检查 DOM 状态
class DOMCheckElement extends HTMLElement {
    connectedCallback() {
        // 检查是否已渲染
        if (!this.shadowRoot.querySelector('.container')) {
            this.render();
        }

        this.attachListeners();
    }
}

// 模式 3: 引用计数
class RefCountElement extends HTMLElement {
    constructor() {
        super();
        this._connectionCount = 0;
    }

    connectedCallback() {
        this._connectionCount++;
        console.log(`Connected ${this._connectionCount} times`);

        if (this._connectionCount === 1) {
            // 只在第一次挂载时执行
            this.initialize();
        }
    }
}
```

实际应用场景:

```javascript
// 场景 1: 拖拽组件
class DraggableElement extends HTMLElement {
    connectedCallback() {
        // ✅ 每次挂载都重新绑定，因为父容器可能变化
        this.addEventListener('mousedown', this._startDrag);
    }

    disconnectedCallback() {
        // ✅ 每次移除都清理
        this.removeEventListener('mousedown', this._startDrag);
    }
}

// 场景 2: 动画组件
class AnimatedElement extends HTMLElement {
    connectedCallback() {
        if (!this._animated) {
            // ✅ 只播放一次进入动画
            this.playEnterAnimation();
            this._animated = true;
        }
    }
}

// 场景 3: 数据订阅组件
class SubscriberElement extends HTMLElement {
    connectedCallback() {
        // ✅ 每次挂载都重新订阅
        this._unsubscribe = store.subscribe(this.handleUpdate);
    }

    disconnectedCallback() {
        // ✅ 每次移除都取消订阅，防止内存泄漏
        this._unsubscribe?.();
    }
}
```

---

**规则 7: 使用 Shadow DOM 实现真正封装，但需要理解样式和事件的穿透规则**

Shadow DOM 提供真正的封装，但样式和事件传播有特殊规则。

```javascript
class ShadowElement extends HTMLElement {
    constructor() {
        super();

        // 创建 Shadow Root
        // mode: 'open' → element.shadowRoot 可访问
        // mode: 'closed' → element.shadowRoot === null（更严格）
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                /* 样式完全封闭在 Shadow DOM 内 */
                :host {
                    display: block;
                    border: 1px solid #ddd;
                }

                :host([disabled]) {
                    opacity: 0.5;
                }

                p {
                    color: red;  /* 不影响外部的 <p> */
                }
            </style>
            <div class="container">
                <p>Shadow content</p>
                <slot></slot>  <!-- Light DOM 投影点 -->
            </div>
        `;
    }
}

// 样式隔离测试
<style>
    p { color: blue; }  /* 外部样式 */
</style>

<p>Outside: blue</p>
<shadow-element>
    <!-- Shadow DOM 内部: red -->
    <!-- Light DOM (slot): blue -->
    <p>Slotted: blue</p>
</shadow-element>
```

事件穿透规则:

```javascript
class EventElement extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <button>Internal Button</button>
        `;

        // 内部监听
        shadow.querySelector('button').addEventListener('click', (e) => {
            console.log('内部 target:', e.target);  // <button>
            console.log('内部 composed:', e.composed);
        });
    }

    connectedCallback() {
        // 外部监听
        this.addEventListener('click', (e) => {
            console.log('外部 target:', e.target);  // <event-element> (重定向)
            console.log('外部 composed:', e.composed);
        });
    }
}

// 自定义事件穿透
class CustomEventElement extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `<button>Trigger</button>`;

        shadow.querySelector('button').addEventListener('click', () => {
            // ❌ 默认不穿透 Shadow DOM
            this.dispatchEvent(new CustomEvent('item-selected', {
                bubbles: true,
                composed: false,  // 无法穿透
                detail: { id: 123 }
            }));

            // ✅ 设置 composed: true 才能穿透
            this.dispatchEvent(new CustomEvent('item-confirmed', {
                bubbles: true,
                composed: true,  // 可以穿透 ✅
                detail: { id: 123 }
            }));
        });
    }
}

// 外部监听
document.addEventListener('item-selected', (e) => {
    console.log('Never fires');  // ❌ 事件被 Shadow DOM 阻止
});

document.addEventListener('item-confirmed', (e) => {
    console.log('Fires:', e.detail);  // ✅ 事件穿透成功
});
```

Shadow DOM 与 Light DOM 交互:

```javascript
class SlotElement extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .wrapper {
                    padding: 16px;
                    background: #f0f0f0;
                }

                /* 选择 slot 中的元素 */
                ::slotted(p) {
                    color: green;
                }

                ::slotted(.highlight) {
                    background: yellow;
                }
            </style>
            <div class="wrapper">
                <h3>Header</h3>
                <slot></slot>  <!-- 默认 slot -->
                <slot name="footer"></slot>  <!-- 具名 slot -->
            </div>
        `;
    }

    connectedCallback() {
        // 访问 Light DOM（slot 内容）
        const slot = this.shadowRoot.querySelector('slot');

        // 监听 slot 内容变化
        slot.addEventListener('slotchange', (e) => {
            const nodes = slot.assignedNodes();
            console.log('Slot content:', nodes);
        });
    }
}

// 使用
<slot-element>
    <p>Default slot content</p>
    <p class="highlight">Highlighted</p>
    <div slot="footer">Footer content</div>
</slot-element>
```

样式穿透策略:

```javascript
// 策略 1: CSS 自定义属性（推荐）
class ThemeableElement extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .button {
                    /* 使用 CSS 变量，允许外部定制 */
                    background: var(--button-bg, #007bff);
                    color: var(--button-color, white);
                    padding: var(--button-padding, 12px);
                }
            </style>
            <button class="button">
                <slot></slot>
            </button>
        `;
    }
}

// 外部定制样式
<style>
    themeable-element {
        --button-bg: #ff0000;
        --button-color: white;
    }
</style>

// 策略 2: part 伪元素（CSS Shadow Parts）
class PartElement extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .title { font-size: 18px; }
            </style>
            <div part="title" class="title">Title</div>
            <div part="content">Content</div>
        `;
    }
}

// 外部样式化 part
<style>
    part-element::part(title) {
        color: red;
        font-weight: bold;
    }

    part-element::part(content) {
        background: yellow;
    }
</style>
```

---

**规则 8: 注册是全局的且不可撤销，需要防止重复注册和命名冲突**

`customElements.define()` 是全局注册，一旦注册无法注销或修改，必须谨慎处理。

```javascript
// ❌ 错误：重复注册会抛出异常
customElements.define('my-element', MyElement);
customElements.define('my-element', MyElement);
// DOMException: Failed to execute 'define' on 'CustomElementRegistry':
// the name "my-element" has already been defined

// ✅ 正确：防止重复注册
if (!customElements.get('my-element')) {
    customElements.define('my-element', MyElement);
}

// 或使用 try-catch
try {
    customElements.define('my-element', MyElement);
} catch (error) {
    console.warn('Element already defined:', error);
}
```

检测和等待注册:

```javascript
// 检查元素是否已注册
const isDefined = customElements.get('my-element') !== undefined;

// 等待元素定义完成
customElements.whenDefined('my-element').then(() => {
    console.log('my-element is now defined');

    // 现在可以安全使用
    const element = document.createElement('my-element');
    document.body.appendChild(element);
});

// 实际应用：渐进增强
<my-element>
    <!-- 提供降级内容 -->
    <div class="fallback">Loading...</div>
</my-element>

<script>
customElements.whenDefined('my-element').then(() => {
    // 元素升级后，移除降级内容
    document.querySelectorAll('my-element .fallback').forEach(el => {
        el.remove();
    });
});
</script>
```

命名冲突处理:

```javascript
// 策略 1: 使用命名空间前缀
const APP_PREFIX = 'myapp';

function defineElement(name, constructor) {
    const fullName = `${APP_PREFIX}-${name}`;

    if (!customElements.get(fullName)) {
        customElements.define(fullName, constructor);
    }

    return fullName;
}

// 使用
defineElement('button', MyButton);  // 注册为 "myapp-button"
defineElement('card', MyCard);      // 注册为 "myapp-card"

// 策略 2: 版本化命名
class ButtonV1 extends HTMLElement { }
class ButtonV2 extends HTMLElement { }

customElements.define('app-button-v1', ButtonV1);
customElements.define('app-button-v2', ButtonV2);

// 策略 3: 动态命名（测试环境）
function defineTestElement(constructor) {
    const name = `test-element-${Date.now()}`;
    customElements.define(name, constructor);
    return name;
}

// 单元测试中使用
it('should render correctly', () => {
    const tagName = defineTestElement(MyElement);
    const element = document.createElement(tagName);
    // 测试...
});
```

注册时机控制:

```javascript
// 延迟注册：按需加载
const registry = {
    'heavy-chart': () => import('./components/heavy-chart.js'),
    'data-table': () => import('./components/data-table.js'),
};

async function lazyDefine(name) {
    if (customElements.get(name)) return;

    const module = await registry[name]();
    customElements.define(name, module.default);
}

// 使用
document.addEventListener('DOMContentLoaded', () => {
    // 检测页面中需要的组件
    const needed = new Set();

    document.querySelectorAll('heavy-chart, data-table').forEach(el => {
        needed.add(el.tagName.toLowerCase());
    });

    // 按需注册
    needed.forEach(name => lazyDefine(name));
});

// 条件注册：根据环境
if (window.matchMedia('(min-width: 768px)').matches) {
    customElements.define('desktop-nav', DesktopNav);
} else {
    customElements.define('mobile-nav', MobileNav);
}
```

全局注册的影响:

```javascript
// 问题 1: 无法卸载
// 一旦注册，该元素永久存在，无法移除或更新
customElements.define('my-element', MyElement);
// 无法撤销 ❌

// 问题 2: 热更新困难
// 开发环境需要特殊处理
if (module.hot) {
    module.hot.accept(() => {
        console.warn('Custom Elements cannot be hot-reloaded');
        window.location.reload();  // 只能刷新页面
    });
}

// 问题 3: 测试隔离
// 单元测试需要唯一命名或隔离环境
beforeEach(() => {
    // 无法清理已注册的元素
    // 需要使用唯一名称或 iframe 隔离
});

// 解决方案：使用 iframe 隔离测试
function createTestEnvironment() {
    const iframe = document.createElement('iframe');
    document.body.appendChild(iframe);

    const customElements = iframe.contentWindow.customElements;

    // 在隔离环境中注册
    customElements.define('test-element', TestElement);

    return { iframe, customElements };
}
```

最佳实践:

```javascript
// 1. 组件库导出注册函数，而非自动注册
export class MyButton extends HTMLElement { }

export function register(name = 'my-button') {
    if (!customElements.get(name)) {
        customElements.define(name, MyButton);
    }
}

// 用户决定何时注册
import { MyButton, register } from 'my-components';
register('app-button');  // 自定义名称

// 2. 提供全局注册选项
export class MyCard extends HTMLElement { }

if (typeof window !== 'undefined' && window.AUTO_REGISTER) {
    customElements.define('my-card', MyCard);
}

// 3. 注册管理器
class ElementRegistry {
    constructor(prefix) {
        this.prefix = prefix;
        this.registered = new Set();
    }

    define(name, constructor) {
        const fullName = `${this.prefix}-${name}`;

        if (this.registered.has(fullName)) {
            console.warn(`${fullName} already registered`);
            return fullName;
        }

        if (!customElements.get(fullName)) {
            customElements.define(fullName, constructor);
            this.registered.add(fullName);
        }

        return fullName;
    }

    getRegistered() {
        return Array.from(this.registered);
    }
}

// 使用
const registry = new ElementRegistry('app');
registry.define('button', MyButton);  // "app-button"
registry.define('card', MyCard);      // "app-card"
console.log(registry.getRegistered());
```

---

**事故档案编号**: NETWORK-2024-1963
**影响范围**: Custom Elements, 自定义元素定义, 生命周期管理, 属性系统, Shadow DOM 封装, 组件架构设计
**根本原因**: 缺乏对 Custom Elements 完整定义流程和生命周期机制的系统理解, 导致组件封装不当、属性同步混乱、事件处理错误
**学习成本**: 中高 (需理解 Web Components 规范、DOM 生命周期、Shadow DOM 封装机制、浏览器升级流程)

这是 JavaScript 世界第 163 次被记录的网络与数据事故。Custom Elements 元素命名必须包含连字符且全部小写, 防止与现有或未来的原生 HTML 标签冲突。类必须继承 HTMLElement 并在 constructor 中首先调用 super(), constructor 有严格限制不能访问属性或 DOM。生命周期回调按严格顺序执行: constructor (创建) → connectedCallback (挂载) → attributeChangedCallback (属性变化) → disconnectedCallback (卸载), 各有专门用途和限制。observedAttributes 静态 getter 声明要监听的属性, 只有声明的属性变化才触发 attributeChangedCallback。Attribute 与 Property 必须双向同步以保持一致性, 通过 getter/setter 和 attributeChangedCallback 实现。connectedCallback 可能被多次调用需要幂等性设计, 使用标志位控制昂贵的初始化操作。Shadow DOM 提供真正封装但事件需要 composed: true 才能穿透, 样式通过 CSS 变量或 ::part 实现外部定制。customElements.define() 是全局注册且不可撤销, 需要防止重复注册和命名冲突, 使用 customElements.get() 检测或 whenDefined() 等待。理解 Custom Elements 的完整定义流程和生命周期机制是构建健壮可复用 Web Components 的基础。

---
