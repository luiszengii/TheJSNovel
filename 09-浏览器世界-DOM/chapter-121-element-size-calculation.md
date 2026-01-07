《第 121 次记录：尺寸幻觉 —— 一个元素的四种宽度》

## 诡异的 Bug

周四上午 10 点 15 分,你收到了一个诡异的 Bug 报告。

"图片预览功能失效了," 测试工程师小王在 Slack 上说,"但只在某些图片上会出现。"你打开测试环境,上传了一张宽度 800px 的图片。预览窗口显示正常。你又上传了一张 1920px 的大图 —— 预览窗口溢出了,图片被裁切掉一半。

"这不可能," 你喃喃自语。代码逻辑很简单:获取图片宽度,如果超过容器宽度就缩放。

```javascript
function previewImage(img) {
  const container = document.querySelector('.preview-container');
  const containerWidth = container.offsetWidth;
  const imageWidth = img.width;

  if (imageWidth > containerWidth) {
    img.style.width = containerWidth + 'px';
  }
}
```

你在控制台打印了调试信息:

```javascript
console.log('容器宽度:', container.offsetWidth);     // 600
console.log('图片 width 属性:', img.width);          // 1920
console.log('图片实际渲染宽度:', img.offsetWidth);   // 800
```

"等等," 你愣住了,"图片的 `width` 是 1920,但 `offsetWidth` 却是 800?"

你检查了 HTML 和 CSS:

```html
<div class="preview-container">
  <img src="large-image.jpg" class="preview-image">
</div>
```

```css
.preview-container {
  width: 600px;
  padding: 20px;
  border: 2px solid #ccc;
}

.preview-image {
  max-width: 100%;
  height: auto;
}
```

"max-width 限制了渲染宽度," 你若有所思,"但 `img.width` 读取的是图片的原始尺寸。"

你尝试用 `img.offsetWidth` 替代 `img.width`,但问题依然存在 —— 有些图片仍然溢出容器。你重新打印调试信息,这次包含了容器的所有尺寸:

```javascript
console.log('offsetWidth:', container.offsetWidth);    // 644
console.log('clientWidth:', container.clientWidth);    // 640
console.log('scrollWidth:', container.scrollWidth);    // 800
console.log('getBoundingClientRect:', container.getBoundingClientRect().width); // 644
```

"四个不同的宽度值?" 你困惑地盯着屏幕,"到底应该用哪一个?"

## 线索追踪

你决定系统地测试每个尺寸属性的含义。创建了一个测试页面:

```html
<div class="box" style="
  width: 200px;
  padding: 20px;
  border: 5px solid blue;
  margin: 10px;
  overflow: auto;
">
  <div class="content" style="width: 250px; height: 300px;">
    内容区域
  </div>
</div>
```

你在控制台逐个测试:

```javascript
const box = document.querySelector('.box');

// 测试 1: offsetWidth
console.log('offsetWidth:', box.offsetWidth);
// 250 = width(200) + padding(20×2) + border(5×2)

// 测试 2: clientWidth
console.log('clientWidth:', box.clientWidth);
// 240 = width(200) + padding(20×2) - 滚动条宽度(如果有)

// 测试 3: scrollWidth
console.log('scrollWidth:', box.scrollWidth);
// 240 (没有溢出时等于 clientWidth)

// 测试 4: getBoundingClientRect
console.log('getBoundingClientRect:', box.getBoundingClientRect());
// { width: 250, height: ..., x: ..., y: ... }
```

你画了一个图来理解这些值:

```
┌─────────────────────────────────────────┐
│          margin (不包含在任何尺寸中)       │
│  ┌───────────────────────────────────┐  │
│  │ border (包含在 offsetWidth 中)      │  │
│  │ ┌───────────────────────────────┐ │  │
│  │ │ padding (包含在 clientWidth 中)│ │  │
│  │ │ ┌───────────────────────────┐ │ │  │
│  │ │ │   content (width: 200px)  │ │ │  │
│  │ │ │                           │ │ │  │
│  │ │ └───────────────────────────┘ │ │  │
│  │ └───────────────────────────────┘ │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘

offsetWidth  = content + padding + border = 250
clientWidth  = content + padding = 240
scrollWidth  = 实际内容宽度(如果溢出则更大)
getBoundingClientRect().width = offsetWidth(包含 transform)
```

"原来如此," 你恍然大悟,"不同的尺寸属性包含不同的部分。"

但问题还没结束。你测试了一个有滚动条的元素:

```javascript
const scrollBox = document.querySelector('.scroll-box');
scrollBox.style.overflow = 'scroll';
scrollBox.innerHTML = '<div style="width: 400px;">很宽的内容</div>';

console.log('clientWidth:', scrollBox.clientWidth);   // 223 (240 - 17)
console.log('scrollWidth:', scrollBox.scrollWidth);   // 400
console.log('offsetWidth:', scrollBox.offsetWidth);   // 250
```

"滚动条占据了 17px," 你记下这个发现,"clientWidth 会减去滚动条宽度,但 offsetWidth 不会。"

## 真相揭晓

你回到图片预览的 Bug,现在明白了问题所在:

```javascript
// ❌ 错误的代码
function previewImage(img) {
  const container = document.querySelector('.preview-container');
  const containerWidth = container.offsetWidth; // 包含 padding 和 border!

  // 容器的 offsetWidth 是 644 (600 + 20×2 + 2×2)
  // 但内容区域只有 600px
  // 如果图片宽度设为 644px,会溢出!
}
```

你重新审视容器的尺寸:

```javascript
const container = document.querySelector('.preview-container');

console.log('容器的各种宽度:');
console.log('offsetWidth:', container.offsetWidth);   // 644 (含 padding、border)
console.log('clientWidth:', container.clientWidth);   // 640 (含 padding,不含 border)
console.log('style.width:', container.style.width);   // "600px" (只有 content)

// 计算内容区域实际可用宽度
const computedStyle = window.getComputedStyle(container);
const contentWidth = parseFloat(computedStyle.width); // 600
```

"要获取内容区域的宽度,应该读取 `getComputedStyle` 的 `width`," 你写下修复方案:

```javascript
// ✅ 正确的代码
function previewImage(img) {
  const container = document.querySelector('.preview-container');

  // 方式 1: 读取 CSS 的 width 值
  const style = window.getComputedStyle(container);
  const contentWidth = parseFloat(style.width);

  // 方式 2: clientWidth 减去 padding
  const paddingLeft = parseFloat(style.paddingLeft);
  const paddingRight = parseFloat(style.paddingRight);
  const contentWidth2 = container.clientWidth - paddingLeft - paddingRight;

  // 获取图片的实际渲染宽度
  const imageWidth = img.getBoundingClientRect().width;

  if (imageWidth > contentWidth) {
    img.style.width = contentWidth + 'px';
  }
}
```

但你随即发现了另一个陷阱 —— `box-sizing` 属性:

```css
/* 默认:content-box */
.box {
  width: 200px;
  padding: 20px;
  border: 5px solid blue;
  box-sizing: content-box; /* 默认 */
}
/* offsetWidth = 200 + 20×2 + 5×2 = 250 */

/* 改为:border-box */
.box {
  width: 200px;
  padding: 20px;
  border: 5px solid blue;
  box-sizing: border-box;
}
/* offsetWidth = 200 (width 已包含 padding 和 border) */
```

"box-sizing 会改变 width 的含义," 你记下这个关键点,"必须检查这个属性才能正确计算。"

你写了一个通用的尺寸计算工具:

```javascript
// 获取元素的精确尺寸
function getElementMetrics(element) {
  const style = window.getComputedStyle(element);
  const rect = element.getBoundingClientRect();

  return {
    // 包含 border 的完整尺寸
    offsetWidth: element.offsetWidth,
    offsetHeight: element.offsetHeight,

    // 包含 padding,不含 border 和滚动条
    clientWidth: element.clientWidth,
    clientHeight: element.clientHeight,

    // 实际内容宽度(包括溢出部分)
    scrollWidth: element.scrollWidth,
    scrollHeight: element.scrollHeight,

    // 视觉渲染尺寸(包含 transform)
    boundingWidth: rect.width,
    boundingHeight: rect.height,

    // CSS 定义的 width/height
    cssWidth: parseFloat(style.width),
    cssHeight: parseFloat(style.height),

    // box-sizing 模式
    boxSizing: style.boxSizing,

    // padding
    paddingTop: parseFloat(style.paddingTop),
    paddingRight: parseFloat(style.paddingRight),
    paddingBottom: parseFloat(style.paddingBottom),
    paddingLeft: parseFloat(style.paddingLeft),

    // border
    borderTopWidth: parseFloat(style.borderTopWidth),
    borderRightWidth: parseFloat(style.borderRightWidth),
    borderBottomWidth: parseFloat(style.borderBottomWidth),
    borderLeftWidth: parseFloat(style.borderLeftWidth),

    // 内容区域实际宽度
    get contentWidth() {
      if (this.boxSizing === 'border-box') {
        return this.cssWidth - this.paddingLeft - this.paddingRight
               - this.borderLeftWidth - this.borderRightWidth;
      }
      return this.cssWidth;
    },

    get contentHeight() {
      if (this.boxSizing === 'border-box') {
        return this.cssHeight - this.paddingTop - this.paddingBottom
               - this.borderTopWidth - this.borderBottomWidth;
      }
      return this.cssHeight;
    }
  };
}

// 使用
const container = document.querySelector('.preview-container');
const metrics = getElementMetrics(container);
console.log('内容区域宽度:', metrics.contentWidth);
```

你用这个工具重新实现了图片预览功能,所有测试用例都通过了。下午 3 点,你关闭了那个 Bug ticket。

## 尺寸计算法则

**规则 1: 四种宽度属性的精确含义**

浏览器提供了四种读取元素宽度的方式,每种包含的部分不同。`offsetWidth` 包含 content + padding + border;`clientWidth` 包含 content + padding(减去滚动条);`scrollWidth` 是实际内容宽度(包括溢出);`getBoundingClientRect().width` 等于 offsetWidth 但包含 CSS transform 的影响。

```javascript
const element = document.querySelector('.box');

// 1. offsetWidth: content + padding + border
console.log(element.offsetWidth);
// 适用: 获取元素占据的总空间(不含 margin)

// 2. clientWidth: content + padding - scrollbar
console.log(element.clientWidth);
// 适用: 获取可视区域宽度(不含 border)

// 3. scrollWidth: 实际内容宽度(包括溢出部分)
console.log(element.scrollWidth);
// 适用: 检测内容是否溢出

// 4. getBoundingClientRect().width: 视觉渲染宽度
console.log(element.getBoundingClientRect().width);
// 适用: 获取屏幕上的实际尺寸(包含 transform)

// 关系:
// offsetWidth >= clientWidth (差值 = border + scrollbar)
// scrollWidth >= clientWidth (差值 = 溢出的内容)
```

**规则 2: box-sizing 改变 width 的计算基准**

CSS 的 `box-sizing` 属性决定了 `width` 是否包含 padding 和 border。默认值 `content-box` 只包含内容区域;`border-box` 包含内容、padding 和 border。这会影响 JavaScript 读取的 `style.width` 值。

```javascript
// content-box (默认)
.box {
  width: 200px;
  padding: 20px;
  border: 5px solid blue;
  box-sizing: content-box;
}
// offsetWidth = 200 + 40 + 10 = 250
// style.width = "200px" (只包含 content)

// border-box
.box {
  width: 200px;
  padding: 20px;
  border: 5px solid blue;
  box-sizing: border-box;
}
// offsetWidth = 200 (width 已包含 padding 和 border)
// 内容区域实际宽度 = 200 - 40 - 10 = 150

// 获取内容区域宽度的正确方式:
const style = window.getComputedStyle(element);
const width = parseFloat(style.width);
const boxSizing = style.boxSizing;

if (boxSizing === 'border-box') {
  const padding = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
  const border = parseFloat(style.borderLeftWidth) + parseFloat(style.borderRightWidth);
  contentWidth = width - padding - border;
} else {
  contentWidth = width;
}
```

**规则 3: getComputedStyle 返回计算后的最终值**

`element.style.width` 只能读取内联样式,而 `getComputedStyle` 返回所有样式规则计算后的最终值,包括继承和默认值。返回的值都是绝对单位(如 px),即使 CSS 中定义的是相对单位(如 em、%)。

```javascript
// HTML:
// <div class="box"></div>

// CSS:
// .box { width: 50%; padding: 1em; }

const box = document.querySelector('.box');

// element.style 只能读取内联样式
console.log(box.style.width);   // "" (空字符串,因为不是内联样式)

// getComputedStyle 返回计算后的值
const style = window.getComputedStyle(box);
console.log(style.width);       // "400px" (50% 已转为绝对值)
console.log(style.padding);     // "16px" (1em 已转为像素)

// 注意: getComputedStyle 返回的是只读对象
style.width = '500px'; // 无效!应该用 box.style.width = '500px'
```

**规则 4: getBoundingClientRect 包含 CSS transform**

`offsetWidth` 和 `clientWidth` 不受 CSS transform 影响,返回的是原始尺寸。而 `getBoundingClientRect()` 返回的是元素在屏幕上的实际视觉尺寸,包含 transform、scale 等变换的影响。

```javascript
const element = document.querySelector('.box');
element.style.width = '100px';
element.style.transform = 'scale(2)';

console.log('offsetWidth:', element.offsetWidth);
// 100 (不受 transform 影响)

console.log('getBoundingClientRect:', element.getBoundingClientRect().width);
// 200 (包含 scale(2) 的影响)

// 应用场景:
// - 需要原始尺寸 → offsetWidth
// - 需要屏幕上的实际大小 → getBoundingClientRect
// - 判断元素是否在视口内 → 必须用 getBoundingClientRect
```

**规则 5: scrollWidth 用于检测内容溢出**

当元素内容超出容器时,`scrollWidth` 会大于 `clientWidth`。这是检测内容是否溢出的标准方法。注意,即使没有溢出,`scrollWidth` 也可能略大于 `clientWidth`(由于浏览器的子像素渲染)。

```javascript
const container = document.querySelector('.container');

// 检测是否有横向溢出
const hasHorizontalOverflow = container.scrollWidth > container.clientWidth;

// 检测是否有纵向溢出
const hasVerticalOverflow = container.scrollHeight > container.clientHeight;

// 获取溢出的内容宽度
const overflowWidth = container.scrollWidth - container.clientWidth;

// 实用函数:检测并自动添加滚动条样式
function checkOverflow(element) {
  if (element.scrollWidth > element.clientWidth) {
    element.classList.add('has-horizontal-scroll');
  }
  if (element.scrollHeight > element.clientHeight) {
    element.classList.add('has-vertical-scroll');
  }
}

// 滚动到底部检测(常用于无限滚动)
container.addEventListener('scroll', () => {
  const isAtBottom =
    container.scrollHeight - container.scrollTop === container.clientHeight;

  if (isAtBottom) {
    loadMoreContent();
  }
});
```

**规则 6: 图片的 naturalWidth 与 width 的区别**

`img.width` 返回图片的渲染宽度,受 CSS 样式影响;`img.naturalWidth` 返回图片的原始宽度,不受样式影响。同理适用于 height。注意,`naturalWidth` 只有在图片加载完成后才可用。

```javascript
const img = document.querySelector('img');

// HTML:
// <img src="large.jpg" style="width: 400px;">
// 图片原始尺寸: 1920×1080

console.log('width:', img.width);              // 400 (CSS 设置的渲染宽度)
console.log('naturalWidth:', img.naturalWidth); // 1920 (图片原始宽度)
console.log('offsetWidth:', img.offsetWidth);  // 400 (渲染宽度)

// 等待图片加载完成
img.addEventListener('load', () => {
  console.log('原始尺寸:', img.naturalWidth, '×', img.naturalHeight);

  // 判断图片是否被缩放
  const isScaled = img.naturalWidth !== img.offsetWidth;

  // 计算缩放比例
  const scale = img.offsetWidth / img.naturalWidth;
  console.log('缩放比例:', scale);
});

// 注意:如果图片未加载,naturalWidth 是 0
console.log(img.naturalWidth); // 可能是 0(未加载)或实际宽度(已加载)
```

---

**记录者注**:

一个元素的宽度不是一个数字,而是一个多维度的概念。`offsetWidth` 告诉你它占据了多少空间,`clientWidth` 告诉你有多少空间可以放内容,`scrollWidth` 告诉你内容实际有多宽,`getBoundingClientRect` 告诉你它在屏幕上看起来有多宽。

这些数字的差异,源于浏览器对盒模型的严格定义:content、padding、border、margin 各司其职,每个尺寸属性包含不同的部分。CSS 的 `box-sizing` 改变了这个定义,transform 又增加了视觉层面的变化,图片还有原始尺寸和渲染尺寸的区别。

理解这些差异,才能准确地进行尺寸计算和布局控制。记住:**不要假设任何默认行为,始终明确你需要的是哪种宽度,并使用正确的 API 读取它**。
