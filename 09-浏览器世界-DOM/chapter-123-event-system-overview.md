《第 123 次记录：事件的生命周期 —— 从点击到响应的完整旅程》

## 分享会现场

周三下午 3 点,会议室里坐满了前端团队的成员。

今天的技术分享会轮到你主讲,主题是"浏览器事件系统深度解析"。你打开投影仪,屏幕上显示着一个简单的 HTML 结构:

```html
<div id="outer">
  <button id="inner">点击我</button>
</div>
```

"我们每天都在写事件监听器," 你开场道,"但有多少人真正理解,当用户点击这个按钮时,浏览器内部发生了什么?"

前端组的小李举手:"不就是触发 click 事件,然后执行回调函数吗?"

"表面上是这样," 你微笑着说,"但实际过程要复杂得多。"

你在控制台写下第一段代码:

```javascript
const outer = document.getElementById('outer');
const inner = document.getElementById('inner');

outer.addEventListener('click', () => {
  console.log('outer 被点击');
});

inner.addEventListener('click', () => {
  console.log('inner 被点击');
});
```

"现在,如果我点击按钮,控制台会输出什么?" 你问道。

小张说:"两个都输出吧?因为按钮在 div 里面。"

你点击了按钮,控制台输出:

```
inner 被点击
outer 被点击
```

"没错," 你点头,"但为什么是这个顺序?为什么点击按钮,父元素也收到了事件?"

会议室陷入沉默。技术主管说:"这就是事件冒泡。但我想知道完整的流程。"

## 事件流解析

你切换到一个复杂的示例:

```javascript
const outer = document.getElementById('outer');
const inner = document.getElementById('inner');

// 给每个元素添加三种事件监听器
outer.addEventListener('click', () => {
  console.log('outer - 冒泡阶段');
}, false); // false 表示冒泡阶段

outer.addEventListener('click', () => {
  console.log('outer - 捕获阶段');
}, true); // true 表示捕获阶段

inner.addEventListener('click', () => {
  console.log('inner - 冒泡阶段');
}, false);

inner.addEventListener('click', () => {
  console.log('inner - 捕获阶段');
}, true);
```

你点击按钮,控制台输出:

```
outer - 捕获阶段
inner - 捕获阶段
inner - 冒泡阶段
outer - 冒泡阶段
```

"这就是完整的事件流," 你在白板上画了一个图:

```
window
  ↓ 捕获阶段 (Capture Phase)
document
  ↓
html
  ↓
body
  ↓
#outer
  ↓
#inner ← 目标阶段 (Target Phase)
  ↑
#outer
  ↑ 冒泡阶段 (Bubble Phase)
body
  ↑
html
  ↑
document
  ↑
window
```

"事件从 window 开始,向下传播到目标元素,这是捕获阶段。到达目标后,再从目标向上冒泡回 window,这是冒泡阶段。"

小陈问:"那为什么我们平时只写 `addEventListener('click', handler)`,从来没有传第三个参数?"

"因为第三个参数默认是 false," 你解释道,"意思是在冒泡阶段监听。大多数场景下,冒泡阶段就够用了。"

你展示了一个实际的问题:

```javascript
// HTML:
// <div class="modal">
//   <div class="modal-content">
//     <button class="close">关闭</button>
//   </div>
// </div>

const modal = document.querySelector('.modal');
const content = document.querySelector('.modal-content');
const closeBtn = document.querySelector('.close');

// 点击遮罩层关闭弹窗
modal.addEventListener('click', () => {
  console.log('关闭弹窗');
  modal.style.display = 'none';
});

// 点击关闭按钮
closeBtn.addEventListener('click', () => {
  console.log('点击了关闭按钮');
  modal.style.display = 'none';
});
```

"这段代码有什么问题?" 你问道。

小李皱眉:"点击关闭按钮时,会触发两次关闭?"

"不止两次," 你点击了弹窗内容区域,控制台输出:

```
关闭弹窗
```

"点击内容区域也关闭了弹窗," 你说,"因为事件冒泡到了 modal 元素。这不是我们想要的行为。"

## 事件对象探索

"事件对象包含了大量信息," 你继续讲解,打开了一个新的示例:

```javascript
button.addEventListener('click', (event) => {
  console.log('事件对象:', event);

  // 事件类型
  console.log('type:', event.type); // "click"

  // 事件目标
  console.log('target:', event.target); // 实际被点击的元素
  console.log('currentTarget:', event.currentTarget); // 绑定监听器的元素

  // 事件阶段
  console.log('eventPhase:', event.eventPhase);
  // 1: CAPTURING_PHASE (捕获)
  // 2: AT_TARGET (目标)
  // 3: BUBBLING_PHASE (冒泡)

  // 是否可以冒泡
  console.log('bubbles:', event.bubbles); // true

  // 是否可以取消
  console.log('cancelable:', event.cancelable); // true

  // 时间戳
  console.log('timeStamp:', event.timeStamp);
});
```

"注意 `target` 和 `currentTarget` 的区别," 你强调:

```javascript
const outer = document.getElementById('outer');
const inner = document.getElementById('inner');

outer.addEventListener('click', (event) => {
  console.log('target:', event.target); // inner (实际点击的元素)
  console.log('currentTarget:', event.currentTarget); // outer (绑定监听器的元素)
});

// 当点击 inner 时:
// target 是 inner (用户实际点击的元素)
// currentTarget 是 outer (这个监听器注册在哪个元素上)
```

小张问:"那怎么解决刚才弹窗的问题?"

"有两种方法," 你展示代码:

```javascript
// 方法 1: 阻止冒泡
const content = document.querySelector('.modal-content');

content.addEventListener('click', (event) => {
  event.stopPropagation(); // 阻止事件继续冒泡
  console.log('点击了内容区域,但不会触发 modal 的监听器');
});

// 方法 2: 判断 target
modal.addEventListener('click', (event) => {
  // 只有直接点击 modal(不是子元素)才关闭
  if (event.target === modal) {
    console.log('关闭弹窗');
    modal.style.display = 'none';
  }
});
```

## 事件控制方法

技术主管问:"除了 `stopPropagation`,还有哪些控制事件的方法?"

你整理了一个完整的列表:

```javascript
button.addEventListener('click', (event) => {
  // 1. 阻止冒泡(停止向上传播)
  event.stopPropagation();
  // 效果: 当前元素的监听器执行,但不会触发父元素的监听器

  // 2. 立即停止传播(包括同一元素的其他监听器)
  event.stopImmediatePropagation();
  // 效果: 后续所有监听器都不执行

  // 3. 阻止默认行为
  event.preventDefault();
  // 效果: 阻止浏览器的默认行为(如链接跳转、表单提交)

  // 4. 检查是否可以阻止默认行为
  console.log(event.cancelable); // true/false
});
```

你演示了它们的区别:

```javascript
const button = document.querySelector('button');

// 注册三个监听器
button.addEventListener('click', (event) => {
  console.log('监听器 1');
  event.stopPropagation(); // 只阻止冒泡
});

button.addEventListener('click', (event) => {
  console.log('监听器 2'); // 仍然会执行
});

button.addEventListener('click', (event) => {
  console.log('监听器 3'); // 仍然会执行
});

// 点击按钮输出:
// 监听器 1
// 监听器 2
// 监听器 3
// (父元素的监听器不执行)
```

```javascript
// 改用 stopImmediatePropagation
button.addEventListener('click', (event) => {
  console.log('监听器 1');
  event.stopImmediatePropagation(); // 立即停止
});

button.addEventListener('click', (event) => {
  console.log('监听器 2'); // 不会执行
});

// 点击按钮输出:
// 监听器 1
// (后续监听器都不执行)
```

"那 `preventDefault` 呢?" 小李问。

```javascript
// 阻止链接跳转
const link = document.querySelector('a');

link.addEventListener('click', (event) => {
  event.preventDefault();
  console.log('链接被点击,但不会跳转');
});

// 阻止表单提交
const form = document.querySelector('form');

form.addEventListener('submit', (event) => {
  event.preventDefault();
  console.log('表单不会提交,可以自定义处理');

  // 自定义提交逻辑
  const formData = new FormData(form);
  fetch('/api/submit', {
    method: 'POST',
    body: formData
  });
});

// 阻止右键菜单
document.addEventListener('contextmenu', (event) => {
  event.preventDefault();
  console.log('右键菜单被禁用');
});
```

## 事件监听器管理

"还有一个常见的问题," 你说,"如何正确移除事件监听器?"

```javascript
// ❌ 错误:无法移除
button.addEventListener('click', () => {
  console.log('clicked');
});

button.removeEventListener('click', () => {
  console.log('clicked');
});
// 无效! 因为两个箭头函数是不同的引用

// ✅ 正确:保存函数引用
function handleClick() {
  console.log('clicked');
}

button.addEventListener('click', handleClick);
button.removeEventListener('click', handleClick);
// 有效! 因为是同一个函数引用
```

"那如果想用箭头函数怎么办?" 小陈问。

```javascript
// 方案 1: 保存函数引用
const handleClick = () => {
  console.log('clicked');
};

button.addEventListener('click', handleClick);
button.removeEventListener('click', handleClick);

// 方案 2: 使用 once 选项(自动移除)
button.addEventListener('click', () => {
  console.log('只执行一次');
}, { once: true });

// 方案 3: 使用 AbortController(现代方式)
const controller = new AbortController();

button.addEventListener('click', () => {
  console.log('clicked');
}, { signal: controller.signal });

// 需要移除时
controller.abort(); // 移除所有使用此 signal 的监听器
```

你展示了 `addEventListener` 的完整选项:

```javascript
element.addEventListener('click', handler, {
  capture: false,    // 是否在捕获阶段触发(默认 false)
  once: false,       // 是否只执行一次(默认 false)
  passive: false,    // 是否永远不调用 preventDefault(默认 false)
  signal: undefined  // AbortSignal 用于移除监听器
});

// passive 的作用:性能优化
// 告诉浏览器"我不会调用 preventDefault",浏览器可以立即执行默认行为
document.addEventListener('touchstart', handler, { passive: true });
// 适用于滚动事件,提升滚动性能
```

分享会接近尾声,你总结了事件系统的核心概念:

```javascript
// 事件流的三个阶段
// 1. 捕获阶段: window → document → ... → 父元素 → 目标元素
// 2. 目标阶段: 目标元素
// 3. 冒泡阶段: 目标元素 → 父元素 → ... → document → window

// 事件对象的关键属性
// event.target: 实际触发事件的元素
// event.currentTarget: 绑定监听器的元素
// event.eventPhase: 当前阶段(1:捕获 2:目标 3:冒泡)

// 事件控制方法
// event.stopPropagation(): 阻止冒泡/捕获
// event.stopImmediatePropagation(): 立即停止传播
// event.preventDefault(): 阻止默认行为

// 监听器选项
// capture: 捕获阶段触发
// once: 只触发一次
// passive: 性能优化(不调用 preventDefault)
// signal: AbortController 移除监听器
```

下午 5 点,技术分享会结束。小李走过来说:"我终于明白为什么我的弹窗总是点哪里都关闭了。"

你笑着点头:"理解事件流,才能写出正确的事件处理代码。"

## 事件系统法则

**规则 1: 事件流的三个阶段按顺序执行**

事件从 window 开始,经过捕获阶段向下传播到目标元素,然后经过冒泡阶段向上传播回 window。`addEventListener` 的第三个参数控制监听器在哪个阶段触发:true 为捕获阶段,false(默认)为冒泡阶段。

```javascript
const outer = document.getElementById('outer');
const inner = document.getElementById('inner');

// 冒泡阶段监听(默认)
outer.addEventListener('click', () => {
  console.log('outer - 冒泡');
}, false); // 或省略第三个参数

// 捕获阶段监听
outer.addEventListener('click', () => {
  console.log('outer - 捕获');
}, true);

// 点击 inner 时的完整流程:
// 1. 捕获: window → document → body → outer(捕获监听器触发) → inner
// 2. 目标: inner 的监听器触发
// 3. 冒泡: inner → outer(冒泡监听器触发) → body → document → window

// 输出顺序:
// outer - 捕获
// inner 的监听器
// outer - 冒泡
```

**规则 2: target 是事件源,currentTarget 是监听器所在元素**

`event.target` 始终指向实际触发事件的元素(事件源),`event.currentTarget` 指向绑定监听器的元素(等同于 this)。在事件冒泡过程中,target 不变,currentTarget 会变化。

```javascript
const outer = document.getElementById('outer');
const inner = document.getElementById('inner');

outer.addEventListener('click', function(event) {
  console.log('target:', event.target);           // inner (实际点击的元素)
  console.log('currentTarget:', event.currentTarget); // outer (这个监听器在 outer 上)
  console.log('this:', this);                     // outer (等同于 currentTarget)
});

// 实际应用:判断点击的是哪个子元素
outer.addEventListener('click', (event) => {
  if (event.target.matches('button')) {
    console.log('点击了按钮');
  } else if (event.target.matches('a')) {
    console.log('点击了链接');
  }
});

// 注意:箭头函数没有自己的 this
outer.addEventListener('click', (event) => {
  console.log(this); // window (不是 outer)
  console.log(event.currentTarget); // outer (正确的引用)
});
```

**规则 3: stopPropagation 阻止传播但不影响同级监听器**

`event.stopPropagation()` 阻止事件继续向上冒泡或向下捕获,但不会阻止同一元素上的其他监听器执行。要阻止后续所有监听器,需要用 `stopImmediatePropagation()`。

```javascript
const button = document.querySelector('button');

button.addEventListener('click', (event) => {
  console.log('监听器 1');
  event.stopPropagation(); // 阻止冒泡到父元素
});

button.addEventListener('click', () => {
  console.log('监听器 2'); // 仍然执行
});

button.addEventListener('click', () => {
  console.log('监听器 3'); // 仍然执行
});

// 点击按钮输出:
// 监听器 1
// 监听器 2
// 监听器 3
// 父元素的监听器不执行

// 使用 stopImmediatePropagation
button.addEventListener('click', (event) => {
  console.log('监听器 1');
  event.stopImmediatePropagation(); // 立即停止
});

// 点击按钮输出:
// 监听器 1
// (后续监听器都不执行)
```

**规则 4: preventDefault 阻止默认行为不影响传播**

`event.preventDefault()` 阻止浏览器的默认行为(如链接跳转、表单提交),但不影响事件传播。可以同时使用 `preventDefault()` 和 `stopPropagation()`。

```javascript
// 阻止链接跳转但事件继续冒泡
link.addEventListener('click', (event) => {
  event.preventDefault(); // 不跳转
  console.log('链接被点击');
  // 事件继续冒泡到父元素
});

// 阻止表单提交
form.addEventListener('submit', (event) => {
  event.preventDefault();

  // 验证失败
  if (!isValid) {
    console.log('验证失败');
    return;
  }

  // 自定义提交
  fetch('/api/submit', { method: 'POST', body: new FormData(form) });
});

// 检查是否可以阻止
element.addEventListener('click', (event) => {
  if (event.cancelable) {
    event.preventDefault(); // 可以阻止
  } else {
    console.log('此事件的默认行为无法阻止');
  }
});

// 注意:某些事件无法阻止默认行为
// 例如 passive: true 的滚动事件
```

**规则 5: removeEventListener 需要相同的函数引用**

移除事件监听器必须传入与添加时完全相同的函数引用。匿名函数或重新定义的函数无法被移除。现代方式可以使用 AbortController。

```javascript
// ❌ 无法移除:不同的函数引用
button.addEventListener('click', () => console.log('clicked'));
button.removeEventListener('click', () => console.log('clicked'));
// 无效

// ✅ 正确:保存函数引用
const handler = () => console.log('clicked');
button.addEventListener('click', handler);
button.removeEventListener('click', handler);
// 有效

// ✅ 自动移除:once 选项
button.addEventListener('click', handler, { once: true });
// 执行一次后自动移除

// ✅ 现代方式:AbortController
const controller = new AbortController();

button.addEventListener('click', handler, { signal: controller.signal });
input.addEventListener('input', handler2, { signal: controller.signal });
// 批量移除所有使用此 signal 的监听器
controller.abort();

// 实际应用:组件卸载时清理
class Component {
  constructor() {
    this.controller = new AbortController();
    this.signal = this.controller.signal;
  }

  mount() {
    button.addEventListener('click', this.handleClick, { signal: this.signal });
    window.addEventListener('resize', this.handleResize, { signal: this.signal });
  }

  unmount() {
    this.controller.abort(); // 一次性移除所有监听器
  }
}
```

**规则 6: passive 选项提升滚动性能**

`passive: true` 告诉浏览器监听器不会调用 `preventDefault()`,浏览器可以立即执行默认行为(如滚动),不需要等待监听器执行完毕。适用于 touch 和 wheel 事件,能显著提升滚动性能。

```javascript
// ❌ 性能问题:浏览器必须等待监听器执行完
document.addEventListener('touchstart', (event) => {
  console.log('touch started');
  // 浏览器不知道你是否会调用 preventDefault()
  // 所以必须等待这个函数执行完才能滚动
}, false);

// ✅ 性能优化:明确告诉浏览器不会阻止默认行为
document.addEventListener('touchstart', (event) => {
  console.log('touch started');
  // 浏览器知道你不会调用 preventDefault()
  // 可以立即开始滚动,不需要等待
}, { passive: true });

// 注意:如果设置了 passive: true,调用 preventDefault() 会被忽略
document.addEventListener('touchstart', (event) => {
  event.preventDefault(); // ⚠️ 无效!会在控制台报警告
}, { passive: true });

// 实际应用:滚动监听
window.addEventListener('scroll', handleScroll, { passive: true });
// 提升滚动性能

// 注意:某些浏览器对 touchstart/touchmove 默认 passive: true
// Chrome 56+ 对 wheel/mousewheel/touchstart/touchmove 默认 passive: true
```

---

**记录者注**:

事件不是瞬间发生的,而是有一个完整的生命周期:从 window 捕获到目标,再从目标冒泡回 window。这个三阶段的设计让事件处理变得灵活:你可以在捕获阶段统一拦截,在目标阶段处理具体逻辑,在冒泡阶段做集中管理。

`target` 和 `currentTarget` 的区别是事件委托的基础,`stopPropagation` 和 `preventDefault` 控制事件的传播和默认行为,`once` 和 `passive` 优化监听器的性能和生命周期。

理解事件流,才能写出正确、高效的事件处理代码。记住:**默认是冒泡,捕获需要显式指定;target 是事件源,currentTarget 是监听器所在;阻止传播用 stopPropagation,阻止默认行为用 preventDefault**。
