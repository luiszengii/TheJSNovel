《第 122 次记录：坐标的迷宫 —— 页面、视口与元素的三重世界》

## 周末实验

周六下午,你坐在咖啡厅的落地窗边,阳光洒在笔记本屏幕上。

你正在给个人博客添加一个"回到顶部"按钮 —— 当用户滚动超过一屏时显示按钮,点击后平滑滚动到页面顶部。功能很简单,但你想深入理解浏览器的坐标系统。

你写下第一版代码:

```javascript
const backToTopButton = document.querySelector('.back-to-top');

// 监听滚动
window.addEventListener('scroll', () => {
  const scrollY = window.pageYOffset;

  if (scrollY > 500) {
    backToTopButton.style.display = 'block';
  } else {
    backToTopButton.style.display = 'none';
  }
});

// 点击回到顶部
backToTopButton.addEventListener('click', () => {
  window.scrollTo(0, 0);
});
```

功能正常工作。但你想知道:`pageYOffset`、`scrollY`、`scrollTop` 这些属性有什么区别?你打开 MDN,发现了更多滚动相关的属性:`window.scrollX`、`document.documentElement.scrollTop`、`document.body.scrollTop`...

"这么多滚动属性?" 你决定系统地测试它们。

## 坐标探索

你创建了一个长页面,然后滚动到不同位置测试:

```javascript
// 测试各种滚动属性
function logScrollPosition() {
  console.log('--- 当前滚动位置 ---');

  // Window 对象的滚动
  console.log('window.scrollY:', window.scrollY);
  console.log('window.pageYOffset:', window.pageYOffset);
  console.log('window.scrollX:', window.scrollX);
  console.log('window.pageXOffset:', window.pageXOffset);

  // Document.documentElement 的滚动
  console.log('documentElement.scrollTop:', document.documentElement.scrollTop);
  console.log('documentElement.scrollLeft:', document.documentElement.scrollLeft);

  // Document.body 的滚动
  console.log('body.scrollTop:', document.body.scrollTop);
  console.log('body.scrollLeft:', document.body.scrollLeft);
}

window.addEventListener('scroll', logScrollPosition);
```

滚动页面后,控制台输出:

```
--- 当前滚动位置 ---
window.scrollY: 500
window.pageYOffset: 500
window.scrollX: 0
window.pageXOffset: 0
documentElement.scrollTop: 500
documentElement.scrollLeft: 0
body.scrollTop: 0
body.scrollLeft: 0
```

"有意思," 你喝了口咖啡,"`window.scrollY` 和 `pageYOffset` 完全相同,`documentElement.scrollTop` 也是 500,但 `body.scrollTop` 是 0。"

你查阅文档,发现:
- `window.scrollY` 和 `window.pageYOffset` 是同一个值(后者是旧版兼容属性)
- 现代浏览器中,滚动容器是 `document.documentElement` (`<html>` 元素)
- `document.body.scrollTop` 在现代浏览器中通常是 0

"那如果我要获取元素在页面中的位置呢?" 你继续实验。

你在页面中间放了一个元素:

```html
<div id="target" style="margin-top: 1000px; background: yellow;">
  目标元素
</div>
```

```javascript
const target = document.getElementById('target');

console.log('--- 元素的各种坐标 ---');

// 1. 相对于文档的坐标
const rect = target.getBoundingClientRect();
console.log('getBoundingClientRect:', rect);
// { top: 500, left: 8, width: ..., height: ... }
// top 是相对于视口的距离

// 2. 计算相对于页面的坐标
const pageY = rect.top + window.scrollY;
console.log('相对于页面的 Y:', pageY); // 1500

// 3. offsetTop/offsetLeft
console.log('offsetTop:', target.offsetTop);  // 1000
console.log('offsetLeft:', target.offsetLeft); // 8
```

你画了一个坐标系统的图:

```
┌────────────────────────────────────┐
│  浏览器窗口 (Browser Window)        │
│  ┌──────────────────────────────┐  │
│  │  视口 (Viewport)              │←─ window.innerHeight
│  │  ┌────────────────────────┐  │  │
│  │  │  页面 (Document)        │  │  │
│  │  │  ┌──────────────────┐  │  │  │
│  │  │  │  元素 (Element)   │  │  │  │
│  │  │  └──────────────────┘  │  │  │
│  │  │        ↑               │  │  │
│  │  │        │ offsetTop     │  │  │
│  │  │  ──────┘               │  │  │
│  │  │                        │  │  │
│  │  └────────────────────────┘  │  │
│  │     ↑                        │  │
│  │     │ window.scrollY         │  │
│  │  ───┘                        │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘

坐标系统:
1. 视口坐标: getBoundingClientRect() (相对于浏览器窗口)
2. 页面坐标: offsetTop/offsetLeft (相对于最近的定位父元素)
3. 文档坐标: pageY = rect.top + scrollY (相对于整个文档)
```

"原来有三套坐标系," 你恍然大悟,"视口坐标会随滚动变化,页面坐标是固定的。"

## 实战应用

你决定用这些知识实现几个常见功能。

**功能 1: 判断元素是否在视口内**

```javascript
function isElementInViewport(element) {
  const rect = element.getBoundingClientRect();

  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= window.innerHeight &&
    rect.right <= window.innerWidth
  );
}

// 优化版:允许部分可见
function isElementPartiallyInViewport(element) {
  const rect = element.getBoundingClientRect();

  return (
    rect.bottom > 0 &&
    rect.top < window.innerHeight &&
    rect.right > 0 &&
    rect.left < window.innerWidth
  );
}

// 使用
window.addEventListener('scroll', () => {
  const target = document.getElementById('target');

  if (isElementInViewport(target)) {
    console.log('元素完全可见');
  } else if (isElementPartiallyInViewport(target)) {
    console.log('元素部分可见');
  } else {
    console.log('元素不可见');
  }
});
```

**功能 2: 平滑滚动到元素**

```javascript
// ❌ 旧方法:立即跳转
function scrollToElement(element) {
  const rect = element.getBoundingClientRect();
  const scrollTop = window.scrollY + rect.top;
  window.scrollTo(0, scrollTop);
}

// ✅ 新方法:平滑滚动
function smoothScrollToElement(element) {
  element.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
    inline: 'nearest'
  });
}

// ✅ 手动控制平滑滚动
function customScrollToElement(element, duration = 500) {
  const targetPosition = element.getBoundingClientRect().top + window.scrollY;
  const startPosition = window.scrollY;
  const distance = targetPosition - startPosition;
  const startTime = performance.now();

  function animation(currentTime) {
    const timeElapsed = currentTime - startTime;
    const progress = Math.min(timeElapsed / duration, 1);

    // 缓动函数:easeInOutQuad
    const ease = progress < 0.5
      ? 2 * progress * progress
      : 1 - Math.pow(-2 * progress + 2, 2) / 2;

    window.scrollTo(0, startPosition + distance * ease);

    if (timeElapsed < duration) {
      requestAnimationFrame(animation);
    }
  }

  requestAnimationFrame(animation);
}

// 使用
backToTopButton.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
});
```

**功能 3: 吸顶导航栏**

```javascript
const navbar = document.querySelector('.navbar');
const navbarHeight = navbar.offsetHeight;

// 记录导航栏原始位置
const navbarOffsetTop = navbar.offsetTop;

window.addEventListener('scroll', () => {
  if (window.scrollY >= navbarOffsetTop) {
    // 滚动超过导航栏位置,固定到顶部
    navbar.classList.add('fixed');
    // 给 body 添加 padding,防止内容跳动
    document.body.style.paddingTop = navbarHeight + 'px';
  } else {
    navbar.classList.remove('fixed');
    document.body.style.paddingTop = '0';
  }
});

// CSS:
// .navbar.fixed {
//   position: fixed;
//   top: 0;
//   left: 0;
//   right: 0;
//   z-index: 100;
// }
```

**功能 4: 无限滚动**

```javascript
function setupInfiniteScroll(callback) {
  window.addEventListener('scroll', () => {
    // 计算距离底部的距离
    const scrollHeight = document.documentElement.scrollHeight;
    const scrollTop = window.scrollY;
    const clientHeight = window.innerHeight;

    const distanceToBottom = scrollHeight - scrollTop - clientHeight;

    // 距离底部小于 200px 时加载更多
    if (distanceToBottom < 200) {
      callback();
    }
  });
}

// 使用
setupInfiniteScroll(() => {
  console.log('加载更多内容...');
  loadMoreItems();
});
```

你测试了所有功能,都工作正常。但你注意到一个性能问题 —— 滚动事件触发频率太高了。

```javascript
// 测试滚动事件频率
let scrollCount = 0;

window.addEventListener('scroll', () => {
  scrollCount++;
});

setInterval(() => {
  console.log('过去 1 秒触发了', scrollCount, '次 scroll 事件');
  scrollCount = 0;
}, 1000);

// 输出:过去 1 秒触发了 60 次 scroll 事件
```

"每秒 60 次!" 你意识到需要优化。你实现了一个节流函数:

```javascript
// 节流函数
function throttle(func, wait) {
  let timeout;
  let previous = 0;

  return function(...args) {
    const now = Date.now();
    const remaining = wait - (now - previous);

    if (remaining <= 0) {
      if (timeout) {
        clearTimeout(timeout);
        timeout = null;
      }
      previous = now;
      func.apply(this, args);
    } else if (!timeout) {
      timeout = setTimeout(() => {
        previous = Date.now();
        timeout = null;
        func.apply(this, args);
      }, remaining);
    }
  };
}

// 使用节流
window.addEventListener('scroll', throttle(() => {
  // 滚动处理逻辑
  updateBackToTopButton();
}, 100)); // 最多每 100ms 执行一次
```

傍晚时分,你关上笔记本。博客的滚动功能完美运行,而且性能优化到位。你对浏览器的坐标系统有了更深的理解。

## 坐标系统法则

**规则 1: scrollY 与 pageYOffset 是同一个值**

`window.scrollY` 和 `window.pageYOffset` 返回页面垂直方向的滚动距离,单位是像素。两者是同一个值,`pageYOffset` 是为了兼容旧浏览器的别名。现代代码应优先使用 `scrollY`。

```javascript
// 获取当前滚动位置
const scrollTop = window.scrollY;  // ✅ 推荐
const scrollTop2 = window.pageYOffset; // ✅ 兼容旧浏览器
const scrollLeft = window.scrollX; // 水平滚动

// documentElement.scrollTop 也可以用,但不如 window.scrollY 直观
const scrollTop3 = document.documentElement.scrollTop;

// 注意:这三个值相同
console.log(window.scrollY === window.pageYOffset); // true
console.log(window.scrollY === document.documentElement.scrollTop); // true

// body.scrollTop 在现代浏览器中通常是 0
console.log(document.body.scrollTop); // 0 (不推荐使用)
```

**规则 2: getBoundingClientRect 返回相对于视口的坐标**

`element.getBoundingClientRect()` 返回元素相对于浏览器视口(viewport)的位置和尺寸。视口坐标会随滚动变化,即使元素位置固定,其 `top` 值也会随滚动改变。要获取相对于文档的坐标,需要加上滚动距离。

```javascript
const element = document.querySelector('.target');
const rect = element.getBoundingClientRect();

// rect 包含的属性:
// {
//   top: 100,    // 距视口顶部
//   left: 50,    // 距视口左侧
//   right: 250,  // 距视口左侧(left + width)
//   bottom: 300, // 距视口顶部(top + height)
//   width: 200,
//   height: 200,
//   x: 50,       // 等同于 left
//   y: 100       // 等同于 top
// }

// 计算相对于文档的坐标
const pageX = rect.left + window.scrollX;
const pageY = rect.top + window.scrollY;

// 判断元素是否在视口内
const inViewport = rect.top >= 0 && rect.bottom <= window.innerHeight;
```

**规则 3: offsetTop 是相对于 offsetParent 的距离**

`element.offsetTop` 返回元素相对于其 `offsetParent` 的距离,不是相对于文档。`offsetParent` 是最近的定位祖先元素(position 不是 static)。要获取相对于文档的距离,需要累加所有祖先的 `offsetTop`。

```javascript
// HTML 结构:
// <div class="container" style="position: relative; margin-top: 100px;">
//   <div class="box" style="margin-top: 50px;"></div>
// </div>

const box = document.querySelector('.box');

console.log(box.offsetTop);    // 50 (相对于 .container)
console.log(box.offsetParent); // <div class="container">

// 获取相对于文档的距离
function getOffsetTop(element) {
  let offsetTop = 0;
  while (element) {
    offsetTop += element.offsetTop;
    element = element.offsetParent;
  }
  return offsetTop;
}

console.log(getOffsetTop(box)); // 150 (100 + 50)

// 注意:如果没有定位祖先,offsetParent 是 body
const root = document.querySelector('#root');
console.log(root.offsetParent); // <body> 或 null
```

**规则 4: scrollIntoView 实现自动滚动到元素**

`element.scrollIntoView()` 是浏览器原生的滚动到元素方法,支持平滑滚动和对齐控制。现代浏览器都支持,比手动计算滚动位置更可靠。

```javascript
const element = document.querySelector('.target');

// 基本用法:滚动到元素顶部
element.scrollIntoView();

// 配置选项
element.scrollIntoView({
  behavior: 'smooth',  // 平滑滚动('smooth')或立即跳转('auto')
  block: 'start',      // 垂直对齐:'start'(顶部),'center'(居中),'end'(底部),'nearest'(最近)
  inline: 'nearest'    // 水平对齐:同 block
});

// 实用案例:
// 1. 滚动到顶部
window.scrollTo({ top: 0, behavior: 'smooth' });

// 2. 滚动到底部
window.scrollTo({
  top: document.documentElement.scrollHeight,
  behavior: 'smooth'
});

// 3. 滚动到元素,且元素居中
element.scrollIntoView({ behavior: 'smooth', block: 'center' });

// 4. 只在需要时滚动(元素不可见才滚动)
element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
```

**规则 5: 视口尺寸用 innerHeight,文档高度用 scrollHeight**

`window.innerHeight` 是浏览器视口的高度(不含工具栏)。`document.documentElement.scrollHeight` 是整个文档的高度(包括滚动区域)。两者的差值决定了最大滚动距离。

```javascript
// 视口尺寸(浏览器窗口的可视区域)
const viewportWidth = window.innerWidth;
const viewportHeight = window.innerHeight;

// 文档总尺寸(包括滚动区域)
const documentWidth = document.documentElement.scrollWidth;
const documentHeight = document.documentElement.scrollHeight;

// 最大滚动距离
const maxScrollX = documentWidth - viewportWidth;
const maxScrollY = documentHeight - viewportHeight;

// 判断页面是否可滚动
const canScrollVertically = documentHeight > viewportHeight;
const canScrollHorizontally = documentWidth > viewportWidth;

// 计算滚动进度(0-1)
const scrollProgress = window.scrollY / maxScrollY;
console.log('滚动进度:', (scrollProgress * 100).toFixed(1) + '%');

// 判断是否滚动到底部
const isAtBottom = window.scrollY >= maxScrollY - 1; // 允许 1px 误差
```

**规则 6: 滚动事件需要节流优化性能**

`scroll` 事件在滚动过程中会高频触发(每秒可达 60 次),直接在事件处理器中执行复杂操作会导致性能问题。应使用节流(throttle)或防抖(debounce)优化。

```javascript
// 问题:滚动事件触发频率太高
window.addEventListener('scroll', () => {
  console.log('滚动中...'); // 每秒触发 60 次!
  performExpensiveOperation(); // 性能问题
});

// 解决方案 1: 节流(throttle)- 控制执行频率
function throttle(func, wait) {
  let timeout;
  let previous = 0;

  return function(...args) {
    const now = Date.now();
    if (now - previous >= wait) {
      previous = now;
      func.apply(this, args);
    }
  };
}

window.addEventListener('scroll', throttle(() => {
  console.log('滚动中...');
  performExpensiveOperation();
}, 100)); // 最多每 100ms 执行一次

// 解决方案 2: 防抖(debounce)- 停止滚动后执行
function debounce(func, wait) {
  let timeout;

  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      func.apply(this, args);
    }, wait);
  };
}

window.addEventListener('scroll', debounce(() => {
  console.log('滚动停止');
  performExpensiveOperation();
}, 150)); // 停止滚动 150ms 后执行

// 选择:
// - 节流:需要实时反馈(如进度条、懒加载)
// - 防抖:只需最终状态(如保存滚动位置)
```

---

**记录者注**:

浏览器的坐标系统不是一个平面,而是三层叠加的世界:视口坐标、文档坐标、元素坐标。`getBoundingClientRect` 给你视口视角(看到的),`offsetTop` 给你元素视角(相对于父元素),`scrollY + rect.top` 给你文档视角(整个页面)。

滚动本质上是视口在文档上的移动。`window.scrollY` 告诉你视口移动了多远,`scrollHeight - innerHeight` 告诉你还能移动多远。这两个值定义了滚动的边界。

理解这三套坐标系,才能准确地控制滚动、定位元素、实现动画。记住:**视口坐标会变,文档坐标不变;getBoundingClientRect 给相对值,offsetTop 给绝对值;滚动事件很频繁,必须节流优化**。
