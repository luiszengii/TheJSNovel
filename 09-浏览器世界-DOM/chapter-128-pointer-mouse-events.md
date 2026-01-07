《第 128 次记录：精确捕捉用户意图 —— 鼠标、触摸与指针的统一世界》

## 移动端适配灾难

周三上午 10 点 17 分，你收到了一个紧急 bug 报告："图片编辑器在手机上无法使用！"

这个图片编辑器是上个月开发的，功能是让用户在画布上拖拽调整图片的位置和大小。你当时只在桌面浏览器上测试过，一切正常。但现在产品经理反馈："iPad 和手机上完全拖不动，双指缩放也不行。"

你打开 Chrome DevTools 的设备模拟器，切换到 iPad 模式，尝试拖拽画布上的图片——果然没有任何反应。你检查了代码：

```javascript
const canvas = document.querySelector('.canvas');
const image = canvas.querySelector('.image');

let isDragging = false;
let startX = 0;
let startY = 0;

// 鼠标按下
image.addEventListener('mousedown', (event) => {
  isDragging = true;
  startX = event.clientX - image.offsetLeft;
  startY = event.clientY - image.offsetTop;
  console.log('开始拖拽');
});

// 鼠标移动
document.addEventListener('mousemove', (event) => {
  if (!isDragging) return;

  image.style.left = (event.clientX - startX) + 'px';
  image.style.top = (event.clientY - startY) + 'px';
});

// 鼠标释放
document.addEventListener('mouseup', () => {
  isDragging = false;
  console.log('结束拖拽');
});
```

"问题找到了，" 你恍然大悟，"我只监听了 `mousedown`、`mousemove`、`mouseup` 这些鼠标事件，但触摸屏没有鼠标，需要监听 `touchstart`、`touchmove`、`touchend` 事件。"

前端组的小林走过来："别分别处理鼠标和触摸事件，用 Pointer Events API 吧，它统一了鼠标、触摸、触控笔的交互。"

"Pointer Events？" 你问。

"对，" 小林说，"`pointerdown` 代替 `mousedown` 和 `touchstart`，`pointermove` 代替 `mousemove` 和 `touchmove`，`pointerup` 代替 `mouseup` 和 `touchend`。一套代码同时支持所有输入设备。"

## 重构为 Pointer Events

小林给你展示了 Pointer Events 的用法：

```javascript
const canvas = document.querySelector('.canvas');
const image = canvas.querySelector('.image');

let isDragging = false;
let startX = 0;
let startY = 0;

// 指针按下（鼠标、触摸、触控笔都会触发）
image.addEventListener('pointerdown', (event) => {
  isDragging = true;
  startX = event.clientX - image.offsetLeft;
  startY = event.clientY - image.offsetTop;

  // 捕获指针，确保后续事件发送到此元素
  image.setPointerCapture(event.pointerId);

  console.log('开始拖拽，输入类型:', event.pointerType);
  // event.pointerType 可能是 'mouse', 'touch', 'pen'
});

// 指针移动
image.addEventListener('pointermove', (event) => {
  if (!isDragging) return;

  image.style.left = (event.clientX - startX) + 'px';
  image.style.top = (event.clientY - startY) + 'px';
});

// 指针释放
image.addEventListener('pointerup', (event) => {
  isDragging = false;

  // 释放指针捕获
  image.releasePointerCapture(event.pointerId);

  console.log('结束拖拽');
});

// 指针取消（比如触摸被中断）
image.addEventListener('pointercancel', () => {
  isDragging = false;
  console.log('拖拽被取消');
});
```

你在设备模拟器上测试：
- iPad 模拟器 → 手指拖拽正常 ✅
- iPhone 模拟器 → 手指拖拽正常 ✅
- 桌面鼠标 → 鼠标拖拽正常 ✅

"太神奇了！" 你惊叹道，"一套代码同时支持鼠标和触摸。"

小林点头："Pointer Events 是现代标准，浏览器支持度很好。你还可以通过 `event.pointerType` 判断输入设备类型，根据需要做差异化处理。"

你测试了 `pointerType` 属性：

```javascript
image.addEventListener('pointerdown', (event) => {
  console.log('输入类型:', event.pointerType);

  if (event.pointerType === 'mouse') {
    console.log('鼠标点击，精确定位');
  } else if (event.pointerType === 'touch') {
    console.log('触摸操作，可能有多个触点');
  } else if (event.pointerType === 'pen') {
    console.log('触控笔，支持压感');
    console.log('压力:', event.pressure); // 0.0 到 1.0
  }
});
```

## 多点触控处理

你突然想起产品需求里有"双指缩放"功能。小林说："多点触控需要追踪多个 `pointerId`，每个触点都有唯一的 ID。"

小林展示了多点触控的实现：

```javascript
const activePointers = new Map(); // 追踪活跃的触点

image.addEventListener('pointerdown', (event) => {
  // 记录触点
  activePointers.set(event.pointerId, {
    x: event.clientX,
    y: event.clientY
  });

  console.log('当前触点数:', activePointers.size);

  if (activePointers.size === 2) {
    // 双指触控开始
    console.log('开始双指缩放/旋转');
    initTwoFingerGesture();
  }

  image.setPointerCapture(event.pointerId);
});

image.addEventListener('pointermove', (event) => {
  if (!activePointers.has(event.pointerId)) return;

  // 更新触点位置
  activePointers.set(event.pointerId, {
    x: event.clientX,
    y: event.clientY
  });

  if (activePointers.size === 1) {
    // 单指拖拽
    handleDrag(event);
  } else if (activePointers.size === 2) {
    // 双指缩放/旋转
    handleTwoFingerGesture();
  }
});

image.addEventListener('pointerup', (event) => {
  activePointers.delete(event.pointerId);
  image.releasePointerCapture(event.pointerId);

  console.log('剩余触点数:', activePointers.size);
});

image.addEventListener('pointercancel', (event) => {
  activePointers.delete(event.pointerId);
});

function handleTwoFingerGesture() {
  const pointers = Array.from(activePointers.values());
  const [p1, p2] = pointers;

  // 计算两点间距离（用于缩放）
  const distance = Math.hypot(p2.x - p1.x, p2.y - p1.y);
  console.log('两指距离:', distance);

  // 计算两点间角度（用于旋转）
  const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x);
  console.log('两指角度:', angle * 180 / Math.PI);

  // 应用缩放和旋转
  applyTransform(distance, angle);
}
```

你测试了双指缩放：在 iPad 模拟器上，两根手指向外滑动，图片放大；两根手指向内滑动，图片缩小。"完美！" 你兴奋地说。

## 鼠标事件的细节

小林提醒："虽然 Pointer Events 更现代，但你仍需要了解传统的鼠标事件，很多遗留代码还在使用。"

他展示了鼠标事件的完整列表：

```javascript
const element = document.querySelector('.element');

// 基础鼠标事件
element.addEventListener('mousedown', (event) => {
  console.log('鼠标按下');
  console.log('按钮:', event.button); // 0: 左键, 1: 中键, 2: 右键
  console.log('坐标:', event.clientX, event.clientY);
});

element.addEventListener('mouseup', (event) => {
  console.log('鼠标释放');
});

element.addEventListener('click', (event) => {
  console.log('点击（mousedown + mouseup）');
  console.log('点击次数:', event.detail); // 1: 单击, 2: 双击, 3: 三击
});

element.addEventListener('dblclick', (event) => {
  console.log('双击');
});

element.addEventListener('contextmenu', (event) => {
  console.log('右键菜单');
  event.preventDefault(); // 阻止默认右键菜单
});

// 鼠标移动事件
element.addEventListener('mousemove', (event) => {
  console.log('鼠标移动:', event.clientX, event.clientY);
  console.log('相对元素的偏移:', event.offsetX, event.offsetY);
});

element.addEventListener('mouseenter', (event) => {
  console.log('鼠标进入（不冒泡）');
});

element.addEventListener('mouseleave', (event) => {
  console.log('鼠标离开（不冒泡）');
});

element.addEventListener('mouseover', (event) => {
  console.log('鼠标进入（冒泡）');
  console.log('来自元素:', event.relatedTarget);
});

element.addEventListener('mouseout', (event) => {
  console.log('鼠标离开（冒泡）');
  console.log('去往元素:', event.relatedTarget);
});

// 滚轮事件
element.addEventListener('wheel', (event) => {
  console.log('滚轮滚动');
  console.log('deltaX:', event.deltaX); // 水平滚动
  console.log('deltaY:', event.deltaY); // 垂直滚动
  console.log('deltaZ:', event.deltaZ); // Z 轴滚动（很少用）
  console.log('deltaMode:', event.deltaMode); // 0: 像素, 1: 行, 2: 页
});
```

小林特别强调了 `mouseenter` vs `mouseover` 的区别：

```javascript
const parent = document.querySelector('.parent');
const child = parent.querySelector('.child');

// mouseenter / mouseleave: 不冒泡
parent.addEventListener('mouseenter', () => {
  console.log('进入 parent（不冒泡）');
  // 鼠标从外部进入 parent 时触发一次
  // 鼠标在 parent 内部移动（包括进入 child）不会再次触发
});

parent.addEventListener('mouseleave', () => {
  console.log('离开 parent（不冒泡）');
  // 鼠标离开 parent 边界时触发一次
});

// mouseover / mouseout: 冒泡
parent.addEventListener('mouseover', (event) => {
  console.log('进入 parent 或其子元素（冒泡）');
  console.log('实际进入的元素:', event.target);
  console.log('来自元素:', event.relatedTarget);
  // 鼠标进入 parent 时触发
  // 鼠标从 parent 进入 child 时也会触发（因为冒泡）
});

parent.addEventListener('mouseout', (event) => {
  console.log('离开 parent 或其子元素（冒泡）');
  // 鼠标离开 parent 或从 parent 进入 child 时都会触发
});
```

"实际开发中，" 小林说，"`mouseenter` 和 `mouseleave` 更直观，适合实现 hover 效果。`mouseover` 和 `mouseout` 因为冒泡，适合事件委托。"

## 坐标系统详解

小林展示了鼠标事件的多种坐标属性：

```javascript
element.addEventListener('click', (event) => {
  // 1. clientX / clientY: 相对于浏览器视口的坐标
  console.log('视口坐标:', event.clientX, event.clientY);
  // 不随页面滚动变化，始终相对于可见区域左上角

  // 2. pageX / pageY: 相对于整个文档的坐标
  console.log('文档坐标:', event.pageX, event.pageY);
  // 包含滚动偏移，相对于文档左上角
  // pageX = clientX + window.scrollX
  // pageY = clientY + window.scrollY

  // 3. offsetX / offsetY: 相对于目标元素的坐标
  console.log('元素内坐标:', event.offsetX, event.offsetY);
  // 相对于事件目标元素（event.target）的左上角

  // 4. screenX / screenY: 相对于屏幕的坐标
  console.log('屏幕坐标:', event.screenX, event.screenY);
  // 相对于整个显示器屏幕的左上角（很少用）

  // 5. 移动距离（只在 mousemove 中有用）
  console.log('相对上次的移动:', event.movementX, event.movementY);
});
```

小林画了一个示意图：

```
屏幕 (screenX, screenY)
└── 浏览器窗口
    ├── 地址栏/工具栏
    └── 视口 (clientX, clientY)
        └── 文档 (pageX, pageY)
            └── 元素 (offsetX, offsetY)
```

"选择哪个坐标属性，" 小林解释道，"取决于你的需求：拖拽元素用 `clientX/clientY`，绘制画布用 `offsetX/offsetY`，记录用户行为用 `pageX/pageY`。"

## 修饰键和按钮状态

小林继续展示事件对象的其他属性：

```javascript
element.addEventListener('click', (event) => {
  // 修饰键状态
  console.log('Ctrl 键:', event.ctrlKey);
  console.log('Shift 键:', event.shiftKey);
  console.log('Alt 键:', event.altKey);
  console.log('Meta 键:', event.metaKey); // Mac 的 Command 键 / Windows 的 Win 键

  // 鼠标按钮（mousedown / mouseup 中）
  console.log('按钮:', event.button);
  // 0: 主按钮（通常是左键）
  // 1: 辅助按钮（通常是中键/滚轮）
  // 2: 次要按钮（通常是右键）
  // 3: 浏览器后退按钮
  // 4: 浏览器前进按钮

  // 按钮状态掩码（多个按钮同时按下时）
  console.log('按钮状态:', event.buttons);
  // 0: 无按钮按下
  // 1: 主按钮
  // 2: 次要按钮
  // 4: 辅助按钮
  // 可以用位运算检查: (event.buttons & 1) 检查主按钮是否按下

  // 实际应用：Ctrl + 点击
  if (event.ctrlKey && event.button === 0) {
    console.log('Ctrl + 左键点击，打开新标签');
    event.preventDefault();
    window.open(event.target.href, '_blank');
  }

  // Shift + 点击
  if (event.shiftKey) {
    console.log('Shift + 点击，批量选择');
    selectRange(lastSelectedItem, event.target);
  }
});
```

## 触摸事件的特殊性

小林提醒："虽然 Pointer Events 是未来趋势，但你仍需要了解 Touch Events，因为有些旧设备或特定需求仍会用到。"

```javascript
// Touch Events（触摸事件）
element.addEventListener('touchstart', (event) => {
  console.log('触摸开始');
  console.log('触点列表:', event.touches);           // 所有当前触点
  console.log('目标元素的触点:', event.targetTouches); // 当前元素上的触点
  console.log('改变的触点:', event.changedTouches);   // 这次事件涉及的触点

  // 遍历所有触点
  Array.from(event.touches).forEach((touch, index) => {
    console.log(`触点 ${index}:`);
    console.log('  identifier:', touch.identifier); // 触点唯一 ID
    console.log('  clientX:', touch.clientX);
    console.log('  clientY:', touch.clientY);
    console.log('  pageX:', touch.pageX);
    console.log('  pageY:', touch.pageY);
    console.log('  screenX:', touch.screenX);
    console.log('  screenY:', touch.screenY);
    console.log('  目标元素:', touch.target);
  });

  // 阻止默认行为（如页面滚动）
  event.preventDefault();
});

element.addEventListener('touchmove', (event) => {
  console.log('触摸移动');
  // touches: 所有当前触点
  // changedTouches: 移动的触点
});

element.addEventListener('touchend', (event) => {
  console.log('触摸结束');
  // touches: 剩余触点
  // changedTouches: 刚移除的触点
});

element.addEventListener('touchcancel', (event) => {
  console.log('触摸取消（被中断）');
  // 例如：来电、系统通知等打断触摸
});
```

"注意 Touch Events 和 Mouse Events 的区别，" 小林说：
- Touch Events 有 `touches`、`targetTouches`、`changedTouches` 三个触点列表
- Touch Events 支持多点触控，Mouse Events 只有单点
- Touch Events 没有 hover 概念，Mouse Events 有 `mouseenter`、`mouseleave`

下午 5 点，你完成了图片编辑器的移动端适配。使用 Pointer Events 重构后，代码量减少了 40%，同时支持鼠标、触摸、触控笔三种输入方式。你给产品经理发消息："移动端适配完成，iPad 和手机都可以正常使用了，还支持双指缩放和旋转。"

## 指针与鼠标事件法则

**规则 1: 优先使用 Pointer Events 统一处理输入**

Pointer Events API 统一了鼠标、触摸、触控笔的交互，一套代码支持所有输入设备。使用 `pointerdown`、`pointermove`、`pointerup` 代替分别处理 `mousedown`/`touchstart`、`mousemove`/`touchmove`、`mouseup`/`touchend`。

```javascript
// ❌ 旧方式：分别处理鼠标和触摸
element.addEventListener('mousedown', handleStart);
element.addEventListener('touchstart', handleStart);

element.addEventListener('mousemove', handleMove);
element.addEventListener('touchmove', handleMove);

element.addEventListener('mouseup', handleEnd);
element.addEventListener('touchend', handleEnd);

// ✅ 新方式：Pointer Events 统一处理
element.addEventListener('pointerdown', handleStart);
element.addEventListener('pointermove', handleMove);
element.addEventListener('pointerup', handleEnd);
element.addEventListener('pointercancel', handleCancel);

// 可以通过 pointerType 区分输入设备
function handleStart(event) {
  console.log('输入类型:', event.pointerType); // 'mouse', 'touch', 'pen'

  if (event.pointerType === 'pen') {
    console.log('压力:', event.pressure); // 触控笔压感
  }
}
```

**规则 2: 使用 setPointerCapture 确保事件连续性**

调用 `setPointerCapture(pointerId)` 可以捕获指针，确保后续的 `pointermove` 和 `pointerup` 事件发送到捕获元素，即使指针移出元素边界。这对拖拽操作至关重要。

```javascript
let isDragging = false;

element.addEventListener('pointerdown', (event) => {
  isDragging = true;

  // 捕获指针
  element.setPointerCapture(event.pointerId);
  // 现在所有后续事件都发送到 element，即使指针移出边界

  console.log('开始拖拽');
});

element.addEventListener('pointermove', (event) => {
  if (!isDragging) return;

  // 即使鼠标移出 element，仍会收到 pointermove 事件
  updatePosition(event.clientX, event.clientY);
});

element.addEventListener('pointerup', (event) => {
  isDragging = false;

  // 释放指针捕获
  element.releasePointerCapture(event.pointerId);

  console.log('结束拖拽');
});

// 没有 setPointerCapture 的问题
element.addEventListener('pointerdown', (event) => {
  isDragging = true;
  // ❌ 没有捕获指针
});

element.addEventListener('pointermove', (event) => {
  // ⚠️ 如果鼠标快速移出 element，这里不会收到事件
  // 导致拖拽中断
});
```

**规则 3: 追踪 pointerId 处理多点触控**

每个指针（手指、鼠标、触控笔）都有唯一的 `pointerId`。使用 `Map` 或对象追踪多个活跃指针，实现多点触控手势（如双指缩放、旋转）。

```javascript
const activePointers = new Map();

element.addEventListener('pointerdown', (event) => {
  // 记录新触点
  activePointers.set(event.pointerId, {
    x: event.clientX,
    y: event.clientY,
    type: event.pointerType
  });

  console.log('活跃触点数:', activePointers.size);

  if (activePointers.size === 1) {
    startDrag();
  } else if (activePointers.size === 2) {
    startPinchZoom();
  }

  element.setPointerCapture(event.pointerId);
});

element.addEventListener('pointermove', (event) => {
  if (!activePointers.has(event.pointerId)) return;

  // 更新触点位置
  activePointers.set(event.pointerId, {
    x: event.clientX,
    y: event.clientY,
    type: event.pointerType
  });

  if (activePointers.size === 2) {
    // 计算两点间距离和角度
    const pointers = Array.from(activePointers.values());
    const [p1, p2] = pointers;

    const distance = Math.hypot(p2.x - p1.x, p2.y - p1.y);
    const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x);

    applyPinchZoom(distance, angle);
  }
});

element.addEventListener('pointerup', (event) => {
  activePointers.delete(event.pointerId);
  element.releasePointerCapture(event.pointerId);

  if (activePointers.size === 0) {
    endGesture();
  }
});
```

**规则 4: mouseenter 和 mouseover 的选择**

`mouseenter`/`mouseleave` 不冒泡，适合实现简单的 hover 效果。`mouseover`/`mouseout` 冒泡，适合事件委托和需要知道 `relatedTarget` 的场景。

```javascript
const parent = document.querySelector('.parent');

// ✅ hover 效果：使用 mouseenter/mouseleave（不冒泡）
parent.addEventListener('mouseenter', () => {
  parent.classList.add('hover');
  // 鼠标进入 parent 时触发一次
  // 鼠标在 parent 内移动（包括子元素）不会再次触发
});

parent.addEventListener('mouseleave', () => {
  parent.classList.remove('hover');
  // 鼠标离开 parent 时触发一次
});

// ✅ 事件委托：使用 mouseover/mouseout（冒泡）
parent.addEventListener('mouseover', (event) => {
  // 判断鼠标进入的是哪个子元素
  if (event.target.matches('.item')) {
    highlightItem(event.target);
  }

  // relatedTarget: 鼠标来自哪个元素
  console.log('从', event.relatedTarget, '进入', event.target);
});

// ❌ 错误：用 mouseover 实现 hover（会因子元素触发多次）
parent.addEventListener('mouseover', () => {
  parent.classList.add('hover'); // ⚠️ 鼠标在子元素间移动时会多次触发
});
```

**规则 5: 选择正确的坐标属性**

鼠标和指针事件提供多种坐标属性，根据用途选择合适的：
- `clientX/clientY`: 相对视口，拖拽元素、定位弹窗
- `pageX/pageY`: 相对文档，记录用户行为、热力图
- `offsetX/offsetY`: 相对目标元素，画布绘制、图片编辑
- `screenX/screenY`: 相对屏幕，很少使用

```javascript
element.addEventListener('click', (event) => {
  // 1. 拖拽元素：使用 clientX/clientY（相对视口）
  element.style.left = event.clientX + 'px';
  element.style.top = event.clientY + 'px';

  // 2. 画布绘制：使用 offsetX/offsetY（相对元素）
  const canvas = event.target;
  const ctx = canvas.getContext('2d');
  ctx.fillRect(event.offsetX, event.offsetY, 5, 5);

  // 3. 记录用户行为：使用 pageX/pageY（相对文档）
  analytics.track('click', {
    x: event.pageX,
    y: event.pageY,
    element: event.target.tagName
  });

  // 关系：
  // pageX = clientX + window.scrollX
  // pageY = clientY + window.scrollY
});
```

**规则 6: 修饰键组合实现快捷操作**

通过检查 `ctrlKey`、`shiftKey`、`altKey`、`metaKey` 实现组合键操作，提升用户体验。

```javascript
element.addEventListener('click', (event) => {
  // Ctrl/Cmd + 点击：新标签打开
  if ((event.ctrlKey || event.metaKey) && event.button === 0) {
    event.preventDefault();
    window.open(event.target.href, '_blank');
    return;
  }

  // Shift + 点击：范围选择
  if (event.shiftKey) {
    selectRange(lastSelected, event.target);
    return;
  }

  // Alt + 点击：预览
  if (event.altKey) {
    showPreview(event.target);
    return;
  }

  // 普通点击
  handleNormalClick(event);
});

// 多按钮检测
document.addEventListener('mousedown', (event) => {
  // event.button: 单个按钮（0: 左, 1: 中, 2: 右）
  // event.buttons: 按钮状态掩码（位运算）

  if (event.buttons === 3) {
    // 同时按下左键（1）和右键（2）
    console.log('左右键同时按下');
  }

  if (event.buttons & 1) {
    console.log('左键按下（可能还有其他键）');
  }
});
```

---

**记录者注**:

用户与网页的交互始于指针的移动和按下。早期浏览器只有鼠标事件（Mouse Events），触摸屏普及后又有了触摸事件（Touch Events），触控笔的出现让情况变得更复杂。Pointer Events API 统一了这三种输入方式，让开发者用一套代码处理所有设备。

关键在于理解指针捕获（`setPointerCapture`）确保拖拽连续性，追踪 `pointerId` 实现多点触控，选择正确的坐标属性（`clientX`、`pageX`、`offsetX`）处理不同场景，利用修饰键（Ctrl、Shift、Alt）实现快捷操作。

记住：**优先使用 Pointer Events，它是现代标准；理解 `mouseenter` vs `mouseover` 的冒泡差异；正确选择坐标属性。指针事件是用户与界面交互的基石**。
