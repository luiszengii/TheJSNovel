《第 119 次记录:即时生效的代价 —— DOM 修改引发的性能危机》

## 性能灾难

周五下午 4 点 23 分,你盯着监控面板上刚刚飙升的响应时间曲线,额头开始冒汗。

后台管理系统的"批量编辑"功能刚上线半小时,客服热线已经接到了 7 个投诉。用户反馈说:批量修改 100 条记录时,页面会直接卡死 3-5 秒,浏览器甚至弹出"页面无响应"警告。

你快速打开测试环境,创建了一个包含 100 条记录的测试数据。点击"批量修改价格"按钮,整个浏览器窗口瞬间凝固。鼠标光标变成了旋转的圈圈,任务栏里的进度条卡在 50% 不动了。

5 秒后,页面终于恢复响应。但这 5 秒的等待时间,对用户来说就像过了一个世纪。

你打开 Chrome DevTools Performance 面板,录制了一次批量修改操作。火焰图显示了一个让人震惊的事实:主线程被 `updatePrice` 函数阻塞了整整 4,873ms,期间浏览器完全无法响应任何用户操作。

你切换到代码,找到了这个函数:

```javascript
// 批量修改价格的实现
function updatePrice(newPrice) {
  const rows = document.querySelectorAll('.data-row');

  rows.forEach(row => {
    // 每次修改都会触发重排
    const priceCell = row.querySelector('.price');
    priceCell.textContent = `¥${newPrice}`;

    // 立即读取布局信息,强制同步重排
    const width = priceCell.offsetWidth;

    // 添加动画效果
    priceCell.style.color = 'red';
    priceCell.style.fontWeight = 'bold';
  });
}
```

"每次都修改 DOM,然后立即读取布局..." 你皱起眉头,"这是在强制浏览器同步重排。100 次循环就是 100 次重排!"

技术总监路过你的座位,看了一眼屏幕:"又是重排问题?"

"是的," 你点头,"批量操作引发的性能崩溃。"

"赶紧修复,客户那边压力很大," 他拍了拍你的肩膀,"记得这次要写个深度分析报告,避免其他模块犯同样的错误。"

## 深入追踪

你决定系统地研究 DOM 修改的性能问题。首先,你写了一个测试工具来量化重排的代价:

```javascript
// 性能测试工具
function measurePerformance(name, fn) {
  const start = performance.now();
  fn();
  const end = performance.now();
  console.log(`${name}: ${(end - start).toFixed(2)}ms`);
}

// 测试 1: 频繁修改 + 频繁读取(强制重排)
measurePerformance('频繁重排', () => {
  const rows = document.querySelectorAll('.data-row');
  rows.forEach(row => {
    row.style.color = 'red';
    const height = row.offsetHeight; // 强制重排!
  });
});
// 频繁重排: 487.23ms

// 测试 2: 批量修改,延迟读取
measurePerformance('批量修改', () => {
  const rows = document.querySelectorAll('.data-row');

  // 阶段 1: 只修改
  rows.forEach(row => {
    row.style.color = 'red';
  });

  // 阶段 2: 只读取
  const heights = [];
  rows.forEach(row => {
    heights.push(row.offsetHeight);
  });
});
// 批量修改: 23.47ms

// 测试 3: 使用 DocumentFragment
measurePerformance('使用 Fragment', () => {
  const fragment = document.createDocumentFragment();

  for (let i = 0; i < 100; i++) {
    const row = document.createElement('div');
    row.className = 'data-row';
    row.style.color = 'red';
    row.textContent = `Row ${i}`;
    fragment.appendChild(row);
  }

  document.querySelector('.container').appendChild(fragment);
});
// 使用 Fragment: 5.12ms
```

测试结果让你倒吸一口凉气:

| 方法 | 执行时间 | 性能对比 |
|------|---------|---------|
| **频繁重排** | 487.23ms | 1x (基准) |
| **批量修改** | 23.47ms | **20x 快** |
| **Fragment** | 5.12ms | **95x 快** |

"频繁重排比批量修改慢了 20 倍..." 你在笔记里写下,"而使用 DocumentFragment 能快 95 倍。"

你打开 MDN,查阅浏览器渲染机制的文档。你发现了重排(Reflow)和重绘(Repaint)的秘密:

```javascript
// 浏览器的渲染流程
// 1. JavaScript 修改 DOM/CSSOM
// 2. 样式计算 (Recalculate Style)
// 3. 布局 (Layout/Reflow) - 计算元素位置和尺寸
// 4. 绘制 (Paint/Repaint) - 绘制像素
// 5. 合成 (Composite) - 将图层合并到屏幕

// 会触发重排的操作:
// - 修改元素的几何属性: width, height, margin, padding, border
// - 修改元素的位置: top, left, right, bottom
// - 修改元素的显示: display: none → block
// - 读取布局信息: offsetWidth, offsetHeight, clientWidth, getBoundingClientRect()

// 只触发重绘的操作:
// - 修改颜色: color, background-color
// - 修改可见性: visibility, opacity
```

你写了一个测试来验证强制重排的原理:

```javascript
const element = document.querySelector('.test');

// 场景 1: 连续修改(批量模式)
element.style.width = '100px';
element.style.height = '100px';
element.style.margin = '10px';
// 浏览器会把这些修改放入队列,稍后统一处理

// 场景 2: 修改后立即读取(强制重排)
element.style.width = '100px';
const width = element.offsetWidth; // 强制浏览器立即计算布局!
element.style.height = '100px';
const height = element.offsetHeight; // 又触发一次重排!

// 原理:
// 当你读取布局信息时,浏览器必须保证数据是最新的
// 所以它会:
// 1. 立即处理所有待处理的样式修改
// 2. 重新计算布局
// 3. 返回准确的布局信息
```

"这就是性能杀手," 你恍然大悟,"修改和读取交织在一起,导致每次读取都触发一次完整的重排。"

你继续实验,测试了不同 DOM 操作的性能:

```javascript
// 实验: 插入 1000 个节点的性能对比

// 方法 1: 逐个 appendChild (最慢)
console.time('逐个插入');
for (let i = 0; i < 1000; i++) {
  const div = document.createElement('div');
  div.textContent = `Item ${i}`;
  document.body.appendChild(div); // 每次都触发重排!
}
console.timeEnd('逐个插入');
// 逐个插入: 234.56ms

// 方法 2: innerHTML (较慢)
console.time('innerHTML');
let html = '';
for (let i = 0; i < 1000; i++) {
  html += `<div>Item ${i}</div>`;
}
document.body.innerHTML = html;
console.timeEnd('innerHTML');
// innerHTML: 45.23ms

// 方法 3: DocumentFragment (最快)
console.time('DocumentFragment');
const fragment = document.createDocumentFragment();
for (let i = 0; i < 1000; i++) {
  const div = document.createElement('div');
  div.textContent = `Item ${i}`;
  fragment.appendChild(div); // 在内存中操作,不触发重排
}
document.body.appendChild(fragment); // 只触发一次重排!
console.timeEnd('DocumentFragment');
// DocumentFragment: 12.34ms
```

你整理了一份性能对比表:

| 插入 1000 个节点 | 重排次数 | 执行时间 | 性能排名 |
|---------------|---------|---------|---------|
| 逐个 appendChild | ~1000 次 | 234.56ms | ⚠️ 慢 |
| innerHTML | 1 次 | 45.23ms | ✓ 中等 |
| DocumentFragment | 1 次 | 12.34ms | ✅ 快 |

"原来 DocumentFragment 是性能优化的关键," 你在笔记里记下,"它在内存中操作,只在最后插入文档时触发一次重排。"

## 性能优化实战

你开始重构批量修改功能。首先是修复强制重排的问题:

```javascript
// ❌ 之前的实现(频繁重排)
function updatePriceBad(newPrice) {
  const rows = document.querySelectorAll('.data-row');

  rows.forEach(row => {
    const priceCell = row.querySelector('.price');
    priceCell.textContent = `¥${newPrice}`;
    priceCell.style.color = 'red';

    // 强制重排!
    const width = priceCell.offsetWidth;

    priceCell.style.fontWeight = 'bold';
  });
}

// ✅ 优化 1: 分离读写操作
function updatePriceGood(newPrice) {
  const rows = document.querySelectorAll('.data-row');

  // 阶段 1: 批量写入(修改 DOM)
  rows.forEach(row => {
    const priceCell = row.querySelector('.price');
    priceCell.textContent = `¥${newPrice}`;
    priceCell.style.color = 'red';
    priceCell.style.fontWeight = 'bold';
  });

  // 阶段 2: 批量读取(如果需要)
  const widths = [];
  rows.forEach(row => {
    const priceCell = row.querySelector('.price');
    widths.push(priceCell.offsetWidth);
  });

  // 只触发一次重排!
}

// ✅ 优化 2: 使用 CSS 类替代内联样式
function updatePriceBest(newPrice) {
  const rows = document.querySelectorAll('.data-row');

  rows.forEach(row => {
    const priceCell = row.querySelector('.price');
    priceCell.textContent = `¥${newPrice}`;
    priceCell.classList.add('highlight'); // CSS 类处理样式
  });
}

// CSS 定义:
// .highlight {
//   color: red;
//   font-weight: bold;
//   transition: all 0.3s; /* 还能加动画效果 */
// }
```

你测试了三种实现的性能:

```javascript
// 100 行数据的性能对比
measurePerformance('优化前', () => updatePriceBad(99.99));
// 优化前: 487.23ms

measurePerformance('优化 1', () => updatePriceGood(99.99));
// 优化 1: 23.47ms (20x 快)

measurePerformance('优化 2', () => updatePriceBest(99.99));
// 优化 2: 8.92ms (54x 快)
```

"使用 CSS 类最快," 你点头,"因为浏览器可以更好地优化类的应用。"

接下来,你优化了批量插入节点的代码:

```javascript
// 批量添加数据行的优化

// ❌ 之前的实现
function addRowsBad(data) {
  const tbody = document.querySelector('tbody');

  data.forEach(item => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${item.id}</td>
      <td>${item.name}</td>
      <td class="price">¥${item.price}</td>
    `;
    tbody.appendChild(row); // 每次都触发重排!
  });
}

// ✅ 优化 1: 使用 DocumentFragment
function addRowsGood(data) {
  const tbody = document.querySelector('tbody');
  const fragment = document.createDocumentFragment();

  data.forEach(item => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${item.id}</td>
      <td>${item.name}</td>
      <td class="price">¥${item.price}</td>
    `;
    fragment.appendChild(row); // 在内存中操作
  });

  tbody.appendChild(fragment); // 只触发一次重排!
}

// ✅ 优化 2: 批量 innerHTML
function addRowsBest(data) {
  const tbody = document.querySelector('tbody');

  const html = data.map(item => `
    <tr>
      <td>${item.id}</td>
      <td>${item.name}</td>
      <td class="price">¥${item.price}</td>
    </tr>
  `).join('');

  tbody.innerHTML += html; // 只触发一次解析和重排
}
```

你写了一个完整的性能优化工具类:

```javascript
// DOM 修改性能优化工具
class DOMUpdater {
  constructor() {
    this.readQueue = []; // 读取操作队列
    this.writeQueue = []; // 写入操作队列
  }

  // 批量读取布局信息
  read(callback) {
    this.readQueue.push(callback);
  }

  // 批量修改 DOM
  write(callback) {
    this.writeQueue.push(callback);
  }

  // 执行批量操作
  flush() {
    // 先执行所有读取操作
    this.readQueue.forEach(fn => fn());
    this.readQueue = [];

    // 再执行所有写入操作
    this.writeQueue.forEach(fn => fn());
    this.writeQueue = [];
  }

  // 使用 requestAnimationFrame 优化
  flushAsync() {
    requestAnimationFrame(() => {
      this.flush();
    });
  }
}

// 使用示例
const updater = new DOMUpdater();

// 场景: 批量修改 100 个元素
const elements = document.querySelectorAll('.data-row');

elements.forEach(el => {
  // 注册写入操作
  updater.write(() => {
    el.style.color = 'red';
    el.style.fontWeight = 'bold';
  });

  // 注册读取操作
  updater.read(() => {
    const height = el.offsetHeight;
    console.log('Height:', height);
  });
});

// 批量执行(写入 → 读取 → 只触发一次重排)
updater.flush();
```

你重写了整个批量编辑模块:

```javascript
// 重构后的批量编辑模块
class BatchEditor {
  constructor(tableElement) {
    this.table = tableElement;
    this.tbody = tableElement.querySelector('tbody');
  }

  // 批量修改价格
  updatePrices(newPrice) {
    const rows = this.tbody.querySelectorAll('tr');

    // 使用 CSS 类批量修改样式
    rows.forEach(row => {
      const priceCell = row.querySelector('.price');
      priceCell.textContent = `¥${newPrice}`;
      priceCell.classList.add('highlight');
    });

    // 3 秒后移除高亮
    setTimeout(() => {
      rows.forEach(row => {
        row.querySelector('.price').classList.remove('highlight');
      });
    }, 3000);
  }

  // 批量添加数据
  addRows(data) {
    const fragment = document.createDocumentFragment();

    data.forEach(item => {
      const row = this.createRow(item);
      fragment.appendChild(row);
    });

    this.tbody.appendChild(fragment);
  }

  // 创建单行(辅助方法)
  createRow(item) {
    const row = document.createElement('tr');
    row.className = 'data-row';
    row.innerHTML = `
      <td>${item.id}</td>
      <td>${item.name}</td>
      <td class="price">¥${item.price}</td>
      <td>
        <button class="btn-edit">编辑</button>
      </td>
    `;
    return row;
  }

  // 批量删除
  removeRows(ids) {
    const idsSet = new Set(ids);
    const rowsToRemove = [];

    // 阶段 1: 收集要删除的行
    this.tbody.querySelectorAll('tr').forEach(row => {
      const id = row.querySelector('td').textContent;
      if (idsSet.has(id)) {
        rowsToRemove.push(row);
      }
    });

    // 阶段 2: 使用 DocumentFragment 批量移除
    rowsToRemove.forEach(row => row.remove());
  }
}

// 使用
const editor = new BatchEditor(document.querySelector('.data-table'));

// 批量修改 100 条记录的价格
editor.updatePrices(99.99);
```

你重新录制 Performance,对比优化前后的性能:

**优化前**:
- 主线程阻塞: 4,873ms
- 重排次数: 100 次
- 用户体验: ⚠️ 页面卡死

**优化后**:
- 主线程阻塞: 89ms
- 重排次数: 1 次
- 用户体验: ✅ 流畅响应

性能提升了 **54 倍**!

下午 5 点 47 分,你发布了修复版本。15 分钟后,客服反馈:用户反映批量编辑功能"快得像换了个系统"。

你靠在椅背上,长舒一口气。

## 文档修改的性能法则

**规则 1: DOM 修改会触发重排和重绘**

浏览器渲染流程:

```
JavaScript 修改 DOM/CSS
      ↓
样式计算 (Recalculate Style)
      ↓
布局 (Layout/Reflow) ← 昂贵的操作!
      ↓
绘制 (Paint/Repaint)
      ↓
合成 (Composite)
```

触发重排的操作(昂贵):

```javascript
// 修改几何属性
element.style.width = '100px';
element.style.height = '100px';
element.style.margin = '10px';
element.style.padding = '5px';

// 修改位置
element.style.top = '50px';
element.style.left = '100px';

// 修改显示
element.style.display = 'none'; // → 'block'

// 添加/删除元素
parent.appendChild(child);
parent.removeChild(child);

// 修改内容
element.textContent = 'New text';
element.innerHTML = '<div>...</div>';

// 修改类名(如果影响布局)
element.className = 'new-class';
```

只触发重绘的操作(较便宜):

```javascript
// 修改颜色
element.style.color = 'red';
element.style.background = 'blue';

// 修改可见性
element.style.visibility = 'hidden';
element.style.opacity = '0.5';

// 修改轮廓
element.style.outline = '1px solid red';
```

**规则 2: 读取布局信息会强制同步重排**

会触发强制重排的属性:

```javascript
// 尺寸属性
element.offsetWidth
element.offsetHeight
element.clientWidth
element.clientHeight
element.scrollWidth
element.scrollHeight

// 位置属性
element.offsetTop
element.offsetLeft
element.clientTop
element.clientLeft
element.scrollTop
element.scrollLeft

// 计算样式
window.getComputedStyle(element)
element.getBoundingClientRect()

// 滚动相关
element.scrollIntoView()
element.scrollTo()
```

强制重排的原理:

```javascript
// 浏览器的优化策略:批量处理修改
element.style.width = '100px';  // 放入队列
element.style.height = '100px'; // 放入队列
element.style.margin = '10px';  // 放入队列
// 稍后统一处理这些修改,只触发一次重排

// 但如果你读取布局信息:
element.style.width = '100px';
const width = element.offsetWidth; // 强制立即处理队列,触发重排!
element.style.height = '100px';
const height = element.offsetHeight; // 又触发一次重排!
```

**规则 3: 分离读写操作避免频繁重排**

反模式(频繁重排):

```javascript
// ❌ 读写交织,每次读取都触发重排
for (let i = 0; i < 100; i++) {
  const element = elements[i];
  element.style.width = '100px'; // 写入
  const width = element.offsetWidth; // 读取 → 触发重排!
  element.style.height = width + 'px'; // 写入
}
// 结果: 100 次重排!
```

优化模式(批量操作):

```javascript
// ✅ 分离读写操作
// 阶段 1: 批量写入
for (let i = 0; i < 100; i++) {
  elements[i].style.width = '100px';
}

// 阶段 2: 批量读取
const widths = [];
for (let i = 0; i < 100; i++) {
  widths[i] = elements[i].offsetWidth;
}

// 阶段 3: 批量写入
for (let i = 0; i < 100; i++) {
  elements[i].style.height = widths[i] + 'px';
}
// 结果: 只触发 2 次重排!
```

**规则 4: DocumentFragment 优化批量插入**

DocumentFragment 是轻量级的文档片段:

```javascript
// ❌ 逐个插入(触发 1000 次重排)
for (let i = 0; i < 1000; i++) {
  const div = document.createElement('div');
  div.textContent = `Item ${i}`;
  container.appendChild(div); // 每次都触发重排!
}

// ✅ 使用 DocumentFragment(只触发 1 次重排)
const fragment = document.createDocumentFragment();
for (let i = 0; i < 1000; i++) {
  const div = document.createElement('div');
  div.textContent = `Item ${i}`;
  fragment.appendChild(div); // 在内存中操作,不触发重排
}
container.appendChild(fragment); // 只在这里触发一次重排!
```

DocumentFragment 特点:

- ✅ 在内存中操作,不影响文档
- ✅ 插入时会自动"消失",子节点直接添加到目标元素
- ✅ 可以重复使用
- ✅ 性能优于 innerHTML

```javascript
const fragment = document.createDocumentFragment();

// 添加多个子节点
const div1 = document.createElement('div');
const div2 = document.createElement('div');
fragment.appendChild(div1);
fragment.appendChild(div2);

// 插入到文档
container.appendChild(fragment);

// 此时 fragment 已经"空"了,子节点都转移到 container 中
console.log(fragment.childNodes.length); // 0
```

**规则 5: 使用 CSS 类替代内联样式**

反模式(触发多次重排):

```javascript
// ❌ 修改多个内联样式
element.style.color = 'red';
element.style.background = 'blue';
element.style.fontSize = '16px';
element.style.fontWeight = 'bold';
element.style.padding = '10px';
// 可能触发多次重排
```

优化模式(触发一次重排):

```javascript
// ✅ 使用 CSS 类
element.classList.add('highlight');

// CSS 定义:
// .highlight {
//   color: red;
//   background: blue;
//   font-size: 16px;
//   font-weight: bold;
//   padding: 10px;
// }
// 只触发一次重排,且浏览器优化更好
```

批量修改样式:

```javascript
// ❌ 多次修改 style
element.style.cssText = 'color: red; background: blue;';

// ✅ 更好的方式:使用类
element.className = 'highlight';

// ✅ 或使用 classList
element.classList.add('highlight', 'active', 'focus');
```

**规则 6: 使用 requestAnimationFrame 优化动画**

DOM 动画优化:

```javascript
// ❌ 不优化的动画
function animate() {
  element.style.left = element.offsetLeft + 1 + 'px';
  setTimeout(animate, 16); // ~60fps
}
animate();

// ✅ 使用 requestAnimationFrame
function animateRAF() {
  element.style.left = element.offsetLeft + 1 + 'px';
  requestAnimationFrame(animateRAF);
}
requestAnimationFrame(animateRAF);

// ✅ 更好:批量操作
let position = 0;
function animateBatch() {
  position += 1;
  element.style.left = position + 'px';

  if (position < 100) {
    requestAnimationFrame(animateBatch);
  }
}
requestAnimationFrame(animateBatch);
```

requestAnimationFrame 优势:

- ✅ 与浏览器刷新率同步(通常 60fps)
- ✅ 页面不可见时自动暂停,节省资源
- ✅ 浏览器可以优化并行的动画
- ✅ 不会丢帧

---

**记录者注**:

DOM 修改的"即时生效"是一把双刃剑。浏览器必须立即响应你的修改指令,这意味着每次修改都可能触发昂贵的重排和重绘操作。当修改次数达到数百次时,这些微小的延迟会累积成显著的性能问题。

强制同步重排是最隐蔽的性能杀手。当你在修改 DOM 后立即读取布局信息时,浏览器被迫放弃批量优化,立即计算最新的布局。100 次修改和读取交织,就是 100 次完整的重排。

性能优化的核心原则:**批量操作,分离读写,使用 Fragment,优先 CSS 类**。记住这四点,你就能避免 99% 的 DOM 性能问题。记住:**测量优先,优化有据,验证有效**。
