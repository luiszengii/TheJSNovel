《第 167 次记录: 客户演示前 15 分钟的样式灾难 —— Shadow DOM 样式隔离的封闭边界》

---

## 演示准备

周四下午 2 点 45 分, 距离客户演示还有 15 分钟。

你坐在会议室里, 笔记本连着投影仪, 浏览器打开着演示页面。这是公司重要的潜在客户——一家跨国企业的技术团队, 他们在评估你们的 Web Components 组件库方案。演示文档已经准备了一周, 每个细节都检查过三遍。

"应该没问题。" 你想着, 点开最后一次预演。

屏幕上显示着精美的组件库 Demo: 统一的蓝色主题, 优雅的卡片布局, 流畅的交互效果。你的团队用 Shadow DOM 重构了整个组件库, 实现了真正的样式隔离——这是今天演示的核心卖点。

你深吸一口气, 准备切换到客户要求的 "深色主题" 演示模式。

然后你点击了页面右上角的 "切换深色模式" 按钮。

一秒钟后, 你的心跳停了。

屏幕上的组件库完全没有变化。所有卡片仍然是白色背景, 所有文字仍然是深色, 就像深色主题的样式根本不存在一样。但更诡异的是——页面的其他部分 (导航栏、侧边栏、页脚) 都正确地切换成了深色。

只有你们引以为傲的 Web Components 组件库, 像是被遗忘在了浅色世界里。

"这不可能..." 你喃喃自语, 疯狂地刷新页面。结果还是一样。你打开 DevTools, 检查 `<body>` 标签——深色主题的 class `dark-theme` 确实已经添加上了。你检查全局 CSS——深色主题的样式规则都在, 语法完全正确。

但组件就是不变色。

你看了一眼时间: 2:48 pm。12 分钟后, 客户的技术总监就会走进这个会议室。

---

## 紧急排查

你的手指在键盘上飞快地敲击着。

第一个怀疑: 是不是 CSS 文件没加载? 你打开 Network 面板——所有样式文件都正常加载, 200 状态码, 没有任何错误。

第二个怀疑: 是不是选择器写错了? 你打开 `themes.css`, 检查深色主题的定义:

```css
/* themes.css */
body.dark-theme {
    --primary-color: #1e88e5;
    --background-color: #1a1a1a;
    --text-color: #f0f0f0;
    --card-bg: #2c2c2c;
}

body.dark-theme .card {
    background: var(--card-bg);
    color: var(--text-color);
}
```

语法没问题。你在 DevTools 的 Elements 面板里检查计算样式——`body.dark-theme` 的 CSS 变量都正确设置了。

但当你展开 Shadow DOM 的 `#shadow-root` 节点, 查看内部的 `.card` 元素时, 你看到了让人绝望的结果:

```
Computed Styles:
  background: white  ← 这是 Shadow DOM 内部的默认样式
  color: #333        ← 完全没有继承外部的 CSS 变量
```

"Shadow DOM..." 你突然意识到问题所在。

你们在重构时, 为了实现 "完美的样式隔离", 把所有组件都封装在了 Shadow DOM 里。这确实解决了样式冲突问题——外部样式无法污染组件内部。但同时也意味着...

"外部样式也进不来!" 你脱口而出。

你快速打开组件的源代码:

```javascript
class ThemeCard extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    background: white;
                    color: #333;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
            </style>
            <div class="card">
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('theme-card', ThemeCard);
```

问题一目了然: Shadow DOM 内部的样式是写死的 `background: white`。而外部的 `body.dark-theme .card` 选择器根本无法穿透 Shadow DOM 的边界。

你看了一眼时间: 2:52 pm。8 分钟。

---

## 第一次尝试

"CSS 变量!" 你想起来, "CSS 变量可以继承!"

你之前读过这个知识点: CSS 自定义属性 (CSS Variables) 是少数几个可以穿透 Shadow DOM 边界的机制之一。因为变量值是通过继承传递的, 而不是选择器匹配。

你快速修改组件的样式:

```javascript
shadow.innerHTML = `
    <style>
        .card {
            /* 使用 CSS 变量, 提供默认值 */
            background: var(--card-bg, white);
            color: var(--text-color, #333);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
    </style>
    <div class="card">
        <slot></slot>
    </div>
`;
```

你保存文件, 刷新页面, 屏住呼吸。

然后你笑了——组件变色了! 当你点击 "切换深色模式" 按钮时, 所有卡片都正确地切换成了深色背景和浅色文字。

"搞定了!" 你松了一口气。

但就在这时, 你注意到一个新问题: 页面上有一个特殊的 "高亮卡片", 在设计稿中它应该有独特的边框颜色, 但现在它和普通卡片完全一样。

你检查 HTML:

```html
<theme-card class="highlight">
    <h3>重要通知</h3>
    <p>这是一个需要特别强调的卡片</p>
</theme-card>
```

你检查全局 CSS:

```css
.highlight {
    border: 2px solid #ff6b6b;
}
```

但边框没有出现。

"又是 Shadow DOM 隔离..." 你意识到, 外部的 `.highlight` 选择器无法选中 Shadow DOM 内部的 `.card` 元素。

你看了一眼时间: 2:55 pm。5 分钟。

---

## 第二次尝试

你想起了另一个 CSS 特性: `:host` 选择器。

`:host` 可以选择 Shadow Host 本身——也就是 `<theme-card>` 元素。你快速修改样式:

```javascript
shadow.innerHTML = `
    <style>
        :host {
            display: block;
        }

        /* 当 host 有 highlight class 时 */
        :host(.highlight) .card {
            border: 2px solid #ff6b6b;
        }

        .card {
            background: var(--card-bg, white);
            color: var(--text-color, #333);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
    </style>
    <div class="card">
        <slot></slot>
    </div>
`;
```

刷新页面——高亮卡片的边框出现了!

"还有 3 分钟..." 你快速浏览演示页面, 检查每个组件。大部分都正常了, 但你注意到页面底部的 "用户评价卡片" 有问题。

这些卡片在演示文档中有特别说明: "当用户评价卡片放在 `<article>` 标签内时, 应该有更大的内边距以适应文章排版。"

你检查 HTML 结构:

```html
<article class="blog-post">
    <theme-card>
        <p>"这个组件库太棒了!" - 用户 A</p>
    </theme-card>
</article>
```

你检查全局 CSS:

```css
article theme-card {
    padding: 40px;  /* 希望覆盖默认的 20px */
}
```

但卡片的内边距仍然是 20px。外部样式又一次被 Shadow DOM 隔离了。

"这该怎么办..." 你开始冒冷汗。如果用 CSS 变量, 需要为每个可能的样式变化都定义变量, 太繁琐了。

你突然想起还有一个选择器: `:host-context()`。

---

## 第三次突破

你快速修改样式, 添加 `:host-context()`:

```javascript
shadow.innerHTML = `
    <style>
        :host {
            display: block;
        }

        :host(.highlight) .card {
            border: 2px solid #ff6b6b;
        }

        /* 当祖先元素是 article 时 */
        :host-context(article) .card {
            padding: 40px;
        }

        .card {
            background: var(--card-bg, white);
            color: var(--text-color, #333);
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
    </style>
    <div class="card">
        <slot></slot>
    </div>
`;
```

刷新页面——文章内的卡片内边距变成了 40px!

"完美!" 你几乎要欢呼了。

这时候, 会议室的门被推开了, 前台小姐姐探头进来: "客户到了, 5 分钟后上来。"

你快速检查了一遍所有演示页面:
- ✅ 深色主题切换正常
- ✅ 高亮卡片边框正确
- ✅ 文章内卡片内边距正确
- ✅ 所有交互功能正常

你长舒了一口气, 擦了擦额头的汗。

但你心里清楚, 今天差点翻车的根本原因, 是对 Shadow DOM 样式隔离机制理解不够深入。你打开笔记本, 快速记下了刚才踩的坑和解决方案。

3 分钟后, 客户的技术团队走进会议室。你站起来, 自信地点击了演示按钮。

整个演示过程非常顺利。当你展示深色主题切换时, 技术总监点了点头: "很流畅。"

演示结束后, 技术总监问了一个问题: "你们的组件库用了 Shadow DOM, 但客户如何定制组件样式?"

你胸有成竹地回答: "我们提供了三层样式定制方案: CSS 变量用于主题定制, `:host()` 用于状态变化, `::part()` 用于暴露特定内部元素..."

技术总监满意地笑了: "看来你们对 Shadow DOM 理解得很透彻。"

你也笑了, 但心里想着: "15 分钟前我差点就砸了。"

---

## 复盘总结

晚上回到家, 你打开笔记本, 整理今天的收获。你画了一张 Shadow DOM 样式隔离的思维导图:

```
Shadow DOM 样式系统
├── 完全隔离
│   ├── 外部样式 ❌ → Shadow DOM 内部
│   └── 内部样式 ❌ → 外部文档
│
├── 穿透通道
│   ├── CSS 变量 ✅ (继承机制)
│   ├── :host ✅ (选择 Host 本身)
│   ├── :host-context() ✅ (感知祖先上下文)
│   └── ::part() ✅ (暴露内部元素)
│
└── Slot 内容
    ├── Light DOM 内容 ✅ (受外部样式影响)
    └── ::slotted() ✅ (Shadow DOM 样式化 slot 内容)
```

你又回想起今天的三个关键问题:

**问题 1: 主题切换失败**
- **根因**: Shadow DOM 内部样式写死, 外部样式规则无法穿透
- **解决**: 使用 CSS 变量, 利用继承机制穿透边界

**问题 2: 外部 class 无效**
- **根因**: 外部选择器 `.highlight` 无法选中 Shadow DOM 内部元素
- **解决**: 使用 `:host(.highlight)` 检测 Host 的 class

**问题 3: 上下文相关样式失效**
- **根因**: 外部上下文选择器 `article theme-card` 无法影响内部
- **解决**: 使用 `:host-context(article)` 感知祖先元素

你总结出一个核心洞察: **Shadow DOM 的样式隔离是双向的——这既是它最大的优势 (避免样式冲突), 也是它最大的挑战 (需要设计穿透机制)。**

你又补充了几个实战建议:

```javascript
// ✅ 最佳实践: 为所有可定制的样式提供 CSS 变量
shadow.innerHTML = `
    <style>
        .card {
            background: var(--card-bg, white);
            color: var(--card-color, #333);
            padding: var(--card-padding, 20px);
            border-radius: var(--card-radius, 8px);
            border: var(--card-border, none);
            box-shadow: var(--card-shadow, 0 2px 8px rgba(0,0,0,0.1));
        }

        /* 为常见状态提供 :host 变体 */
        :host([disabled]) .card {
            opacity: 0.5;
            pointer-events: none;
        }

        :host(.large) .card {
            padding: var(--card-padding-large, 40px);
        }

        /* 为常见上下文提供 :host-context 变体 */
        :host-context(.compact) .card {
            padding: var(--card-padding-compact, 12px);
        }
    </style>
`;
```

你还记录了几个容易踩的坑:

**坑 1: 以为 CSS 变量能解决所有问题**
- ❌ 错误想法: "只要用了 CSS 变量, 外部就能完全控制内部样式"
- ✅ 正确理解: CSS 变量只能传递值, 不能传递选择器逻辑
- 🎯 解决方案: CSS 变量 + :host/:host-context() 组合使用

**坑 2: 误用 :host-context() 的优先级**
- ❌ 错误代码:
  ```css
  :host-context(.dark) .card { background: #2c2c2c; }
  .card { background: white; }  /* 这个优先级更高! */
  ```
- ✅ 正确代码:
  ```css
  .card { background: var(--card-bg, white); }
  :host-context(.dark) { --card-bg: #2c2c2c; }
  ```

**坑 3: 忘记 ::slotted() 只能选直接子元素**
- ❌ 错误代码:
  ```css
  ::slotted(div p) { color: red; }  /* 无法选中 div 内的 p */
  ```
- ✅ 正确代码:
  ```css
  ::slotted(div) { }  /* 只能选中 slot 的直接子元素 */
  /* 深层样式需要在外部 CSS 中定义 */
  ```

你保存了笔记, 关上电脑。虽然今天的演示差点翻车, 但你庆幸自己在关键时刻找到了解决方案。

更重要的是, 你现在真正理解了 Shadow DOM 样式隔离的边界和穿透机制。

---

## 知识档案: Shadow DOM 样式隔离的七个核心机制

**规则 1: Shadow DOM 实现双向样式隔离, 外部样式进不来, 内部样式出不去**

Shadow DOM 创建了一个完全封闭的样式作用域, 与外部文档的样式系统完全隔离。

```javascript
class IsolatedComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                /* Shadow DOM 内部样式 */
                p {
                    color: red;
                    font-size: 24px;
                }
            </style>
            <p>Shadow DOM 内的段落</p>
        `;
    }
}

customElements.define('isolated-component', IsolatedComponent);
```

外部样式测试:

```html
<style>
    /* 外部样式 */
    p {
        color: blue;
        font-size: 16px;
    }
</style>

<p>外部段落 (蓝色 16px)</p>
<isolated-component></isolated-component>
```

结果:
- 外部 `<p>` 是蓝色 16px (外部样式生效)
- Shadow DOM 内的 `<p>` 是红色 24px (内部样式生效, 外部样式不影响)

**关键洞察**: 双向隔离的设计目的:
- **保护组件**: 外部样式不会意外污染组件内部
- **保护页面**: 组件内部样式不会泄漏到外部文档
- **代价**: 外部无法直接样式化组件内部元素

```javascript
// ❌ 这些外部选择器都无法穿透 Shadow DOM
isolated-component p { }           // 无效
isolated-component > p { }         // 无效
isolated-component * { }           // 无效
#id-inside-shadow { }              // 无效
.class-inside-shadow { }           // 无效
```

---

**规则 2: CSS 自定义属性 (变量) 可以穿透 Shadow DOM 边界, 实现主题定制**

CSS 变量通过继承机制传递值, 不受 Shadow DOM 边界限制。

```javascript
class ThemeableComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    /* ✅ 使用 CSS 变量, 提供默认值 */
                    background: var(--card-bg, white);
                    color: var(--card-color, #333);
                    padding: var(--card-padding, 20px);
                    border-radius: var(--card-radius, 8px);
                    border: var(--card-border, none);
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
/* 全局主题变量 */
:root {
    --card-bg: white;
    --card-color: #333;
    --card-padding: 20px;
    --card-radius: 8px;
    --card-border: none;
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
    --card-padding: 40px;
    --card-radius: 16px;
}
```

使用示例:

```html
<!-- 默认主题 -->
<themeable-component>
    <h3>默认卡片</h3>
</themeable-component>

<!-- 大尺寸变体 -->
<themeable-component class="large">
    <h3>大尺寸卡片</h3>
</themeable-component>

<!-- 切换深色主题 -->
<script>
document.body.classList.toggle('dark-theme');
// 所有组件自动响应主题变化
</script>
```

**最佳实践**:

```javascript
// ✅ 为所有可定制的样式属性提供 CSS 变量
// ✅ 总是提供合理的默认值
// ✅ 使用语义化的变量名

shadow.innerHTML = `
    <style>
        .button {
            /* 主题变量 */
            background: var(--button-bg, #007bff);
            color: var(--button-color, white);

            /* 尺寸变量 */
            padding: var(--button-padding, 12px 24px);
            font-size: var(--button-font-size, 16px);

            /* 边框变量 */
            border: var(--button-border, none);
            border-radius: var(--button-radius, 4px);

            /* 效果变量 */
            box-shadow: var(--button-shadow, none);
            transition: var(--button-transition, all 0.3s);
        }

        .button:hover {
            background: var(--button-hover-bg, #0056b3);
            box-shadow: var(--button-hover-shadow, 0 4px 8px rgba(0,0,0,0.2));
        }
    </style>
`;
```

---

**规则 3: :host 选择器选择 Shadow Host 本身, 可以响应外部 class 和属性**

`:host` 伪类选择器选择承载 Shadow DOM 的宿主元素 (Shadow Host)。

```javascript
class HostStylingComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                /* 选择 host 本身 */
                :host {
                    display: block;
                    border: 1px solid #ddd;
                    padding: 16px;
                }

                /* 根据 host 的属性选择 */
                :host([disabled]) {
                    opacity: 0.5;
                    pointer-events: none;
                }

                /* 根据 host 的 class 选择 */
                :host(.large) {
                    padding: 32px;
                    font-size: 1.2em;
                }

                :host(.highlight) {
                    border-color: #ff6b6b;
                    border-width: 2px;
                }

                /* 根据 host 的伪类选择 */
                :host(:hover) {
                    border-color: #007bff;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }

                :host(:focus) {
                    outline: 2px solid #007bff;
                    outline-offset: 2px;
                }

                /* 影响内部元素 */
                :host(.large) .content {
                    font-size: 18px;
                }

                .content {
                    margin: 0;
                }
            </style>
            <div class="content">
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('host-styling-component', HostStylingComponent);
```

使用示例:

```html
<!-- 默认样式 -->
<host-styling-component>
    <p>默认内容</p>
</host-styling-component>

<!-- disabled 状态 -->
<host-styling-component disabled>
    <p>禁用状态 (半透明, 无法交互)</p>
</host-styling-component>

<!-- large 变体 -->
<host-styling-component class="large">
    <p>大尺寸变体 (更大内边距和字体)</p>
</host-styling-component>

<!-- highlight 变体 -->
<host-styling-component class="highlight">
    <p>高亮边框</p>
</host-styling-component>

<!-- 动态修改 -->
<script>
const component = document.querySelector('host-styling-component');
component.classList.add('large');        // 触发 :host(.large)
component.setAttribute('disabled', '');  // 触发 :host([disabled])
</script>
```

**:host 优先级规则**:

外部样式 > :host 内部样式

```css
/* 外部样式 */
host-styling-component {
    border-color: purple;  /* 优先级最高 */
}
```

```javascript
/* 内部样式 */
shadow.innerHTML = `
    <style>
        :host {
            border-color: blue;  /* 优先级低于外部 */
        }
    </style>
`;
```

结果: 边框颜色是 purple (外部样式生效)

---

**规则 4: :host-context() 根据祖先元素的状态调整组件样式, 实现上下文感知**

`:host-context()` 允许组件根据其祖先元素的 class、属性或标签来调整自身样式。

```javascript
class ContextAwareComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .card {
                    background: white;
                    color: #333;
                    padding: 20px;
                    border-radius: 8px;
                }

                /* 当祖先元素有 .dark-theme 类时 */
                :host-context(.dark-theme) .card {
                    background: #2c2c2c;
                    color: #f0f0f0;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.5);
                }

                /* 当在 article 元素内时 */
                :host-context(article) .card {
                    padding: 40px;
                    max-width: 800px;
                    margin: 0 auto;
                }

                /* 当在 aside 元素内时 */
                :host-context(aside) .card {
                    padding: 12px;
                    font-size: 14px;
                }

                /* 当祖先元素有 .compact 类时 */
                :host-context(.compact) .card {
                    padding: 12px;
                    border-radius: 4px;
                }

                /* 多条件组合 */
                :host-context(.dark-theme.compact) .card {
                    background: #1a1a1a;
                    padding: 8px;
                }
            </style>
            <div class="card">
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('context-aware-component', ContextAwareComponent);
```

使用场景:

```html
<!-- 场景 1: 在深色主题容器内 -->
<div class="dark-theme">
    <context-aware-component>
        <p>深色主题样式 (深色背景)</p>
    </context-aware-component>
</div>

<!-- 场景 2: 在文章内 -->
<article>
    <context-aware-component>
        <p>文章内样式 (更大内边距, 居中)</p>
    </context-aware-component>
</article>

<!-- 场景 3: 在侧边栏内 -->
<aside>
    <context-aware-component>
        <p>侧边栏样式 (更小内边距和字体)</p>
    </context-aware-component>
</aside>

<!-- 场景 4: 紧凑模式 -->
<div class="compact">
    <context-aware-component>
        <p>紧凑模式样式</p>
    </context-aware-component>
</div>

<!-- 场景 5: 深色主题 + 紧凑模式 -->
<div class="dark-theme compact">
    <context-aware-component>
        <p>深色紧凑模式 (组合条件)</p>
    </context-aware-component>
</div>
```

**实际应用: 响应式布局**:

```javascript
shadow.innerHTML = `
    <style>
        .container {
            padding: 20px;
        }

        /* 在移动视口容器内 */
        :host-context(.mobile-view) .container {
            padding: 12px;
            font-size: 14px;
        }

        /* 在平板视口容器内 */
        :host-context(.tablet-view) .container {
            padding: 16px;
            font-size: 15px;
        }

        /* 在打印上下文内 */
        :host-context(.print-mode) .container {
            padding: 0;
            color: black;
            background: white;
        }
    </style>
`;
```

**:host-context() 的限制**:

```javascript
// ✅ 支持: 类选择器
:host-context(.dark-theme) { }

// ✅ 支持: 标签选择器
:host-context(article) { }

// ✅ 支持: 属性选择器
:host-context([data-theme="dark"]) { }

// ✅ 支持: 组合
:host-context(.dark-theme.compact) { }

// ❌ 不支持: 后代选择器
:host-context(div p) { }  // 无效

// ❌ 不支持: 伪类 (大多数)
:host-context(:hover) { }  // 无效
```

---

**规则 5: ::slotted() 可以样式化 slot 投射的内容, 但仅限直接子元素**

`::slotted()` 伪元素允许 Shadow DOM 内部样式选择通过 `<slot>` 投射的 Light DOM 内容。

```javascript
class SlottedStylingComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .container {
                    padding: 16px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                }

                /* ✅ 正确: 选择 slot 的直接子元素 */
                ::slotted(p) {
                    margin-bottom: 16px;
                    line-height: 1.6;
                }

                ::slotted(h2) {
                    color: #007bff;
                    margin-top: 0;
                    margin-bottom: 16px;
                }

                ::slotted(.highlight) {
                    background: yellow;
                    padding: 4px;
                }

                ::slotted([data-priority="high"]) {
                    color: red;
                    font-weight: bold;
                }

                /* 通配符: 选择所有 slot 直接子元素 */
                ::slotted(*) {
                    box-sizing: border-box;
                    margin: 8px 0;
                }

                /* ❌ 限制: 无法选择后代元素 */
                ::slotted(div p) {
                    /* 无效! ::slotted() 不能深入后代 */
                }
            </style>
            <div class="container">
                <slot></slot>
            </div>
        `;
    }
}

customElements.define('slotted-styling-component', SlottedStylingComponent);
```

使用示例:

```html
<slotted-styling-component>
    <!-- ✅ 这些是 slot 的直接子元素, ::slotted() 可以选中 -->
    <h2>标题 (蓝色)</h2>
    <p>段落 (16px 下边距)</p>
    <p class="highlight">高亮段落 (黄色背景)</p>
    <p data-priority="high">高优先级 (红色粗体)</p>

    <!-- ❌ 嵌套元素无法被 ::slotted(p) 选中 -->
    <div>
        <p>嵌套段落 (不受 ::slotted(p) 影响)</p>
    </div>
</slotted-styling-component>
```

**::slotted() 的限制总结**:

```css
/* ✅ 支持 */
::slotted(*)                  /* 通配符 */
::slotted(p)                  /* 类型选择器 */
::slotted(.class)             /* 类选择器 */
::slotted([attr])             /* 属性选择器 */
::slotted(p.class[attr])      /* 组合选择器 */

/* ❌ 不支持 */
::slotted(div p)              /* 后代选择器 */
::slotted(p > span)           /* 子选择器 */
::slotted(p + p)              /* 相邻兄弟选择器 */
::slotted(p)::before          /* 伪元素 */
::slotted(p:hover)            /* 大多数伪类 */
```

**为什么有这些限制**:
- Slot 内容在 Light DOM, Shadow DOM 只能 "看到" 顶层元素
- 深入后代会破坏 Light DOM 的样式封装
- 伪元素和伪类涉及更复杂的渲染流程

**解决方案**:

如果需要深度样式化 slot 内容:

```css
/* 方案 1: 使用外部 CSS */
slotted-styling-component div p {
    color: green;
}

/* 方案 2: 让用户自己添加样式类 */
<slotted-styling-component>
    <div class="custom-container">
        <p class="custom-paragraph">带样式的段落</p>
    </div>
</slotted-styling-component>

/* 方案 3: 通过 CSS 变量传递样式值 */
::slotted(div) {
    --nested-color: blue;
}
/* 用户在外部 CSS 中使用变量 */
slotted-styling-component div p {
    color: var(--nested-color);
}
```

---

**规则 6: ::part() 允许外部有限地样式化 Shadow DOM 内部暴露的元素**

CSS Shadow Parts 提供了一种受控的方式, 让组件明确暴露哪些内部元素可以被外部样式化。

```javascript
class PartExposureComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                .container {
                    padding: 16px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                }

                .title {
                    font-size: 18px;
                    color: #333;
                    margin-bottom: 12px;
                }

                .content {
                    color: #666;
                    line-height: 1.6;
                }

                .footer {
                    margin-top: 12px;
                    font-size: 12px;
                    color: #999;
                }
            </style>

            <!-- ✅ 暴露 part, 外部可样式化 -->
            <div class="container" part="container">
                <div class="title" part="title">
                    <slot name="title">默认标题</slot>
                </div>

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

customElements.define('part-exposure-component', PartExposureComponent);
```

外部样式化:

```css
/* ✅ 可以样式化暴露的 part */
part-exposure-component::part(container) {
    border-color: blue;
    border-width: 2px;
    border-radius: 16px;
    background: #f0f0f0;
}

part-exposure-component::part(title) {
    color: #007bff;
    font-size: 24px;
    font-weight: bold;
}

part-exposure-component::part(content) {
    line-height: 1.8;
    color: #333;
}

/* ❌ 无法样式化没有 part 的元素 */
part-exposure-component::part(footer) {
    /* 无效! footer 没有暴露为 part */
}
```

**多个 part 名称**:

```javascript
shadow.innerHTML = `
    <!-- 一个元素可以有多个 part 名称 -->
    <button class="submit-btn" part="button submit-button primary-action">
        提交
    </button>
`;
```

```css
/* 外部可以用任何一个 part 名称选择 */
part-exposure-component::part(button) { }
part-exposure-component::part(submit-button) { }
part-exposure-component::part(primary-action) { }
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

**part vs CSS 变量 vs 外部样式对比**:

| 机制 | 灵活性 | 封装性 | 适用场景 |
|------|--------|--------|----------|
| CSS 变量 | 低 (只能改值) | 高 | 主题定制, 配置参数 |
| ::part() | 中 (可改多个属性) | 中 | 关键元素定制 |
| 外部样式 | 高 (完全控制) | 低 | Light DOM 内容 |

---

**规则 7: 样式穿透策略应该分层设计, 从通用到特定渐进暴露**

综合使用多种穿透机制, 设计灵活且可维护的组件样式系统。

```javascript
class ComprehensiveComponent extends HTMLElement {
    constructor() {
        super();
        const shadow = this.attachShadow({ mode: 'open' });

        shadow.innerHTML = `
            <style>
                /* 层级 1: 使用 CSS 变量实现主题定制 (最灵活) */
                :host {
                    display: block;
                }

                .card {
                    /* 主题变量 */
                    background: var(--card-bg, white);
                    color: var(--card-color, #333);

                    /* 尺寸变量 */
                    padding: var(--card-padding, 20px);
                    border-radius: var(--card-radius, 8px);

                    /* 边框变量 */
                    border: var(--card-border, 1px solid #ddd);

                    /* 效果变量 */
                    box-shadow: var(--card-shadow, 0 2px 8px rgba(0,0,0,0.1));
                    transition: var(--card-transition, all 0.3s);
                }

                /* 层级 2: 使用 :host 响应外部状态 (状态变化) */
                :host([disabled]) .card {
                    opacity: 0.5;
                    pointer-events: none;
                }

                :host(.large) .card {
                    padding: var(--card-padding-large, 40px);
                    font-size: 1.2em;
                }

                :host(.highlight) .card {
                    border-color: var(--card-highlight-color, #ff6b6b);
                    border-width: 2px;
                }

                /* 层级 3: 使用 :host-context 响应上下文 (上下文感知) */
                :host-context(.dark-theme) .card {
                    --card-bg: #2c2c2c;
                    --card-color: #f0f0f0;
                    --card-shadow: 0 2px 8px rgba(0,0,0,0.5);
                }

                :host-context(article) .card {
                    max-width: 800px;
                    margin: 0 auto;
                }

                :host-context(.compact) .card {
                    --card-padding: 12px;
                    --card-radius: 4px;
                }

                /* 层级 4: 使用 ::slotted 样式化投射内容 (内容样式) */
                ::slotted(h2) {
                    margin-top: 0;
                    margin-bottom: 16px;
                    color: var(--card-heading-color, #007bff);
                }

                ::slotted(p) {
                    margin-bottom: 12px;
                    line-height: 1.6;
                }

                .header {
                    padding: 12px 16px;
                    background: var(--card-header-bg, #f5f5f5);
                    border-bottom: 1px solid var(--card-border-color, #ddd);
                }

                .body {
                    padding: 16px;
                }
            </style>

            <!-- 层级 5: 使用 part 暴露关键元素 (精细控制) -->
            <div class="card" part="card">
                <div class="header" part="header">
                    <slot name="header">默认标题</slot>
                </div>
                <div class="body" part="body">
                    <slot></slot>
                </div>
            </div>
        `;
    }
}

customElements.define('comprehensive-component', ComprehensiveComponent);
```

外部定制示例:

```css
/* 层级 1: 全局主题变量 */
:root {
    --card-bg: white;
    --card-color: #333;
    --card-padding: 20px;
    --card-radius: 8px;
}

body.dark-theme {
    --card-bg: #2c2c2c;
    --card-color: #f0f0f0;
}

/* 层级 2: 特定实例定制 */
comprehensive-component.special {
    --card-bg: #e3f2fd;
    --card-border: 2px solid #007bff;
}

/* 层级 3: 使用 part 精细控制 */
comprehensive-component::part(header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

comprehensive-component::part(body) {
    background: #fafafa;
}
```

使用示例:

```html
<!-- 默认样式 -->
<comprehensive-component>
    <h2 slot="header">标题</h2>
    <p>内容段落 1</p>
    <p>内容段落 2</p>
</comprehensive-component>

<!-- 大尺寸 + 高亮 -->
<comprehensive-component class="large highlight">
    <h2 slot="header">重要通知</h2>
    <p>这是一个需要强调的卡片</p>
</comprehensive-component>

<!-- 禁用状态 -->
<comprehensive-component disabled>
    <h2 slot="header">不可用</h2>
    <p>此功能暂时不可用</p>
</comprehensive-component>

<!-- 深色主题容器内 -->
<div class="dark-theme">
    <comprehensive-component>
        <h2 slot="header">深色主题</h2>
        <p>自动响应主题变化</p>
    </comprehensive-component>
</div>

<!-- 特殊样式实例 -->
<comprehensive-component class="special">
    <h2 slot="header">特殊卡片</h2>
    <p>带有自定义颜色和边框</p>
</comprehensive-component>
```

**设计原则总结**:

1. **CSS 变量**: 用于主题级别的定制 (颜色、尺寸、效果)
2. **:host()**: 用于响应组件自身的状态 (disabled、size、variant)
3. **:host-context()**: 用于响应外部上下文 (主题容器、布局容器)
4. **::slotted()**: 用于样式化用户提供的内容
5. **::part()**: 用于暴露关键内部元素供精细定制

**权衡考虑**:

- **灵活性 vs 封装性**: CSS 变量最灵活但封装性最弱, ::part() 更受控
- **易用性 vs 定制性**: CSS 变量易用, ::part() 需要明确暴露
- **维护成本**: 过多的 part 暴露增加维护负担, 应该只暴露真正需要定制的元素

---

**事故档案编号**: NETWORK-2024-1967
**影响范围**: Shadow DOM 样式系统, CSS 变量穿透, :host/:host-context() 选择器, ::slotted() 伪元素, ::part() 伪元素, Web Components 主题定制
**根本原因**: 对 Shadow DOM 双向样式隔离机制理解不足, 未提供足够的样式穿透机制导致主题切换和上下文样式失效
**学习成本**: 中高 (需理解 Shadow DOM 封装边界、CSS 变量继承、伪类选择器作用域、样式优先级规则)

这是 JavaScript 世界第 167 次被记录的网络与数据事故。Shadow DOM 实现双向样式隔离, 外部样式规则无法穿透内部, 内部样式也不会泄漏到外部, 必须在 Shadow DOM 内部重写所有样式。CSS 自定义属性 (变量) 通过继承机制可以穿透 Shadow DOM 边界, 是实现主题定制的主要方式, 应为所有可定制样式提供变量并提供合理默认值。:host 伪类选择器选择 Shadow Host 本身, 可以根据 host 的 class、属性或伪类调整内部样式, 外部样式优先级高于 :host 内部样式。:host-context() 根据祖先元素的状态调整组件样式实现上下文感知, 适用于响应主题容器、布局容器或打印模式。::slotted() 可以样式化 slot 投射的 Light DOM 内容但仅限直接子元素无法深入后代, 深层样式需要在外部 CSS 中定义或通过 CSS 变量传递。::part() 允许组件明确暴露哪些内部元素可被外部样式化提供受控的定制能力, 一个元素可以有多个 part 名称且可以通过 exportparts 转发子组件的 part。样式穿透策略应该分层设计: CSS 变量用于主题定制, :host 用于状态响应, :host-context 用于上下文感知, ::slotted 用于内容样式, ::part 用于关键元素暴露。理解 Shadow DOM 样式隔离边界和穿透机制是构建灵活且可维护的 Web Components 样式系统的关键。

---
