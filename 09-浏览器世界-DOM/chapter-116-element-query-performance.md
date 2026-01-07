《第 116 次记录：查询的代价 —— 从卡顿到瞬间响应》

## 性能告警

周四上午 10 点 17 分，你的邮箱收到一封用户投诉邮件：

> **主题：数据表格卡顿严重**
>
> 你好，我们在使用数据管理后台时，发现表格的勾选框反应很慢，有时候点击后要等 1-2 秒才有响应。数据量大的时候，整个页面都会卡住。这严重影响了我们的工作效率。
>
> 浏览器：Chrome 110
> 数据量：约 1000 行

你皱起眉头。1000 行数据不算多，为什么会卡顿？

你打开开发环境，创建了一个包含 1000 行的测试表格：

```html
<table class="data-table">
  <thead>
    <tr>
      <th><input type="checkbox" class="select-all"></th>
      <th>ID</th>
      <th>姓名</th>
      <th>部门</th>
      <th>操作</th>
    </tr>
  </thead>
  <tbody>
    <!-- 1000 行数据 -->
    <tr class="row">
      <td><input type="checkbox" class="row-checkbox"></td>
      <td>1001</td>
      <td>张三</td>
      <td>研发部</td>
      <td><button class="btn-edit">编辑</button></td>
    </tr>
    <!-- ...999 行... -->
  </tbody>
</table>
```

你点击第一行的复选框，页面确实卡顿了一下。你打开 Chrome DevTools，切换到 Performance 面板，录制了一次点击操作。

火焰图显示：主线程被一个名为 `handleCheckboxClick` 的函数阻塞了整整 347ms。

你查看代码，找到了这个函数：

```javascript
// 当前的实现
document.querySelectorAll('.row-checkbox').forEach(checkbox => {
  checkbox.addEventListener('click', function() {
    // 每次点击时，都查询所有行来更新"全选"状态
    const allRows = document.querySelectorAll('.row');
    const checkedRows = document.querySelectorAll('.row-checkbox:checked');

    const selectAllCheckbox = document.querySelector('.select-all');
    selectAllCheckbox.checked = (checkedRows.length === allRows.length);
  });
});
```

"问题找到了，" 你喃喃道，"每次点击都要查询两次 `.row`，一次查询所有行，一次查询选中的行。1000 行数据，每次查询都要遍历整个 DOM 树。"

你打开控制台，写了个性能测试：

```javascript
console.time('querySelectorAll');
const rows = document.querySelectorAll('.row');
console.timeEnd('querySelectorAll');
// querySelectorAll: 12.8ms
```

12.8ms 乘以 1000 次点击？不对，每次点击只执行一次查询...等等，你重新检查代码，发现了真正的问题：

```javascript
// 问题代码：在循环绑定事件时，每次都查询
document.querySelectorAll('.row-checkbox').forEach(checkbox => {
  checkbox.addEventListener('click', function() {
    // 这里每次点击都会执行查询
    const allRows = document.querySelectorAll('.row');      // 12ms
    const checkedRows = document.querySelectorAll('.row-checkbox:checked'); // 10ms
    // ...
  });
});
```

"这不就是个查询吗，怎么会这么慢？" 你决定深入研究查询方法的性能差异。

## 性能对比

你写了一个基准测试，对比不同查询方法的性能：

```javascript
// 基准测试
function benchmark(name, fn, iterations = 1000) {
  console.time(name);
  for (let i = 0; i < iterations; i++) {
    fn();
  }
  console.timeEnd(name);
}

// 测试 1: getElementById
benchmark('getElementById × 1000', () => {
  document.getElementById('user-1001');
});
// getElementById × 1000: 2.1ms

// 测试 2: getElementsByClassName
benchmark('getElementsByClassName × 1000', () => {
  document.getElementsByClassName('row');
});
// getElementsByClassName × 1000: 15.3ms

// 测试 3: querySelectorAll
benchmark('querySelectorAll × 1000', () => {
  document.querySelectorAll('.row');
});
// querySelectorAll × 1000: 198.7ms

// 测试 4: querySelector
benchmark('querySelector × 1000', () => {
  document.querySelector('.row');
});
// querySelector × 1000: 92.4ms
```

测试结果让你震惊：

| 方法 | 1000 次查询时间 | 相对速度 |
|------|---------------|---------|
| `getElementById` | 2.1ms | **100x** 最快 |
| `getElementsByClassName` | 15.3ms | **13x** |
| `querySelector` | 92.4ms | **2x** |
| `querySelectorAll` | 198.7ms | 1x 基准 |

"`getElementById` 比 `querySelectorAll` 快了将近 100 倍？" 你惊讶地说。

后端组的老刘路过，看了看你的屏幕："querySelectorAll 每次都重新遍历整个 DOM 树，时间复杂度是 O(n)。getElementById 是 O(1)，因为浏览器维护了 ID 的哈希表。"

"哈希表？" 你恍然大悟，"所以 getElementById 是直接查找，不需要遍历？"

"没错，" 老刘点头，"DOM 树可能有几千个节点，遍历一遍当然慢。"

你重新审视了查询方法的内部机制：

```javascript
// getElementById - O(1) 时间复杂度
// 浏览器内部维护了一个 ID → Element 的哈希表
document.getElementById('user-1001');
// 相当于：idMap.get('user-1001')

// getElementsByClassName - O(n) 时间复杂度，但有优化
// 返回实时的 HTMLCollection，会被缓存
document.getElementsByClassName('row');
// 首次查询：遍历 DOM 树，构建集合
// 再次查询：如果 DOM 没变化，返回缓存的集合

// querySelectorAll - O(n) 时间复杂度，无缓存
// 每次都重新遍历 DOM 树，返回静态的 NodeList
document.querySelectorAll('.row');
// 每次查询：完整遍历 DOM 树，构建新的 NodeList
```

"关键是 `querySelectorAll` 不会缓存结果，" 你在笔记里写道，"每次调用都是全新的遍历。"

## 优化方案

你开始重构表格组件，应用性能优化策略：

**优化 1: 缓存查询结果**

```javascript
// ❌ 之前：每次点击都查询
document.querySelectorAll('.row-checkbox').forEach(checkbox => {
  checkbox.addEventListener('click', function() {
    const allRows = document.querySelectorAll('.row'); // 重复查询！
    const checkedRows = document.querySelectorAll('.row-checkbox:checked');
    // ...
  });
});

// ✅ 优化：缓存查询结果
const allRows = document.querySelectorAll('.row'); // 只查询一次
const allCheckboxes = document.querySelectorAll('.row-checkbox');

allCheckboxes.forEach(checkbox => {
  checkbox.addEventListener('click', function() {
    // 直接使用缓存的结果
    const checkedCount = Array.from(allCheckboxes).filter(cb => cb.checked).length;

    const selectAllCheckbox = document.querySelector('.select-all');
    selectAllCheckbox.checked = (checkedCount === allRows.length);
  });
});
```

**优化 2: 使用事件委托**

```javascript
// ✅ 更好的优化：事件委托，避免重复查询
const tableBody = document.querySelector('tbody');
const selectAllCheckbox = document.querySelector('.select-all');

// 只在父元素上绑定一个监听器
tableBody.addEventListener('click', (e) => {
  if (e.target.classList.contains('row-checkbox')) {
    // 使用 getElementsByClassName，速度更快
    const allCheckboxes = tableBody.getElementsByClassName('row-checkbox');
    const checkedCount = Array.from(allCheckboxes).filter(cb => cb.checked).length;

    selectAllCheckbox.checked = (checkedCount === allCheckboxes.length);
  }
});
```

**优化 3: 使用 ID 查询（最快）**

```javascript
// ✅ 如果元素有 ID，优先使用 getElementById
// 修改 HTML 结构，给每行添加 ID
<tr class="row" id="row-1001">
  <td><input type="checkbox" class="row-checkbox" data-row-id="1001"></td>
  <!-- ... -->
</tr>

// 点击时可以快速定位到对应的行
checkbox.addEventListener('click', function() {
  const rowId = this.dataset.rowId;
  const row = document.getElementById('row-' + rowId); // O(1) 查找！
  // ...
});
```

你重构了整个表格组件：

```javascript
// 重构后的表格组件
class DataTable {
  constructor(tableElement) {
    this.table = tableElement;
    this.tbody = tableElement.querySelector('tbody');
    this.selectAllCheckbox = tableElement.querySelector('.select-all');

    // 缓存查询结果
    this.updateCheckboxCache();

    // 使用事件委托
    this.tbody.addEventListener('click', this.handleClick.bind(this));
    this.selectAllCheckbox.addEventListener('change', this.handleSelectAll.bind(this));
  }

  updateCheckboxCache() {
    // 使用 getElementsByClassName，比 querySelectorAll 快
    this.checkboxes = this.tbody.getElementsByClassName('row-checkbox');
  }

  handleClick(e) {
    if (e.target.classList.contains('row-checkbox')) {
      this.updateSelectAllState();
    }
  }

  updateSelectAllState() {
    // 直接遍历缓存的 HTMLCollection
    let checkedCount = 0;
    for (let i = 0; i < this.checkboxes.length; i++) {
      if (this.checkboxes[i].checked) checkedCount++;
    }

    this.selectAllCheckbox.checked = (checkedCount === this.checkboxes.length);
  }

  handleSelectAll(e) {
    const isChecked = e.target.checked;

    // 批量更新，避免触发多次重排
    for (let i = 0; i < this.checkboxes.length; i++) {
      this.checkboxes[i].checked = isChecked;
    }
  }
}

// 初始化
const table = new DataTable(document.querySelector('.data-table'));
```

你重新录制 Performance，点击复选框：

- **优化前**：347ms
- **优化后**：3.2ms

性能提升了 **108 倍**！

下午 4 点 12 分，你回复用户邮件：

> 问题已修复，性能提升超过 100 倍，勾选框现在瞬间响应。请测试确认。

5 分钟后，用户回复：

> 太棒了！现在非常流畅，感谢！

你靠在椅背上，长舒一口气。

## 查询性能法则

**规则 1: getElementById 是最快的查询方法（O(1)）**

`getElementById` 的速度优势来自浏览器的内部优化：

```javascript
// 浏览器内部维护了一个 ID 哈希表
// idMap: Map<string, HTMLElement>

// 解析 HTML 时，自动构建哈希表
<div id="user-1001">...</div>
// → idMap.set('user-1001', divElement)

// 查询时，直接从哈希表获取
document.getElementById('user-1001');
// → idMap.get('user-1001')  // O(1) 时间复杂度
```

最佳实践：

```javascript
// ✅ 如果元素有 ID，优先使用 getElementById
const element = document.getElementById('main-content');

// ❌ 不要用 querySelector 查询 ID（慢 50-100 倍）
const element = document.querySelector('#main-content');
```

注意事项：

1. **ID 必须唯一**：浏览器不会检查 ID 重复，只会返回第一个匹配的元素
2. **ID 区分大小写**：`getElementById('User')` 和 `getElementById('user')` 不同
3. **只在 document 上调用**：`element.getElementById()` 不存在

**规则 2: querySelectorAll 每次都重新遍历 DOM（O(n)）**

`querySelectorAll` 的执行过程：

```javascript
document.querySelectorAll('.row');

// 内部执行流程：
// 1. 解析 CSS 选择器 ".row"
// 2. 从根节点开始，深度优先遍历整个 DOM 树
// 3. 对每个节点检查是否匹配选择器
// 4. 将匹配的节点收集到 NodeList 中
// 5. 返回静态的 NodeList（不会自动更新）
```

时间复杂度分析：

```javascript
// 假设 DOM 树有 n 个节点
document.querySelectorAll('.row');  // O(n) - 遍历所有节点

document.querySelectorAll('.row .cell');  // O(n) - 仍然是 O(n)，但常数更大

document.querySelectorAll('div > span + p');  // O(n) - 选择器越复杂，常数越大
```

性能陷阱：

```javascript
// ❌ 在循环中使用 querySelectorAll
for (let i = 0; i < 1000; i++) {
  const rows = document.querySelectorAll('.row'); // 每次都遍历整个 DOM！
  // ...
}
// 时间复杂度：O(1000 × n)

// ✅ 缓存查询结果
const rows = document.querySelectorAll('.row'); // 只遍历一次
for (let i = 0; i < 1000; i++) {
  // 使用缓存的结果
  // ...
}
// 时间复杂度：O(n + 1000)
```

**规则 3: 缓存查询结果是性能优化的关键**

缓存策略：

```javascript
// 场景 1: 页面加载后，DOM 不会变化
const staticElements = {
  header: document.querySelector('.header'),
  nav: document.querySelector('.nav'),
  footer: document.querySelector('.footer')
};

// 后续使用缓存的引用
staticElements.header.classList.add('sticky');

// 场景 2: DOM 会动态变化，需要智能缓存
class ElementCache {
  constructor() {
    this.cache = new Map();
    this.version = 0;

    // 监听 DOM 变化，使缓存失效
    const observer = new MutationObserver(() => {
      this.version++;
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }

  query(selector) {
    const cacheKey = `${selector}-${this.version}`;

    if (!this.cache.has(cacheKey)) {
      this.cache.set(cacheKey, document.querySelectorAll(selector));
    }

    return this.cache.get(cacheKey);
  }
}

const cache = new ElementCache();
const rows = cache.query('.row'); // 缓存结果
```

缓存失效策略：

```javascript
// 手动失效
let cachedRows = document.querySelectorAll('.row');

// DOM 变化后，重新查询
function addNewRow() {
  // ...添加新行...
  cachedRows = document.querySelectorAll('.row'); // 更新缓存
}
```

**规则 4: HTMLCollection 是实时的，NodeList 可能是静态的**

```javascript
// getElementsByClassName 返回 HTMLCollection（实时）
const rows1 = document.getElementsByClassName('row');
console.log(rows1.length); // 1000

// 添加新行
const newRow = document.createElement('div');
newRow.className = 'row';
document.body.appendChild(newRow);

console.log(rows1.length); // 1001 - 自动更新！

// querySelectorAll 返回 NodeList（静态）
const rows2 = document.querySelectorAll('.row');
console.log(rows2.length); // 1001

// 添加新行
const newRow2 = document.createElement('div');
newRow2.className = 'row';
document.body.appendChild(newRow2);

console.log(rows2.length); // 1001 - 不会更新
```

实时 vs 静态的性能影响：

```javascript
// HTMLCollection（实时）- 可能更慢（需要实时计算）
const live = document.getElementsByClassName('row');
console.log(live.length); // 每次访问都重新计算

// NodeList（静态）- 可能更快（结果已固定）
const static = document.querySelectorAll('.row');
console.log(static.length); // 直接返回固定值
```

**规则 5: 使用最具体的选择器，避免通配符**

选择器性能排序（从快到慢）：

```javascript
// 1. ID 选择器（最快）
document.querySelector('#user-1001')          // 快

// 2. 类选择器
document.querySelector('.row')                 // 较快

// 3. 标签选择器
document.querySelector('div')                  // 中等

// 4. 属性选择器
document.querySelector('[data-id="1001"]')    // 较慢

// 5. 伪类选择器
document.querySelector(':nth-child(2)')       // 较慢

// 6. 通配符选择器（最慢）
document.querySelector('*')                    // 最慢
```

优化技巧：

```javascript
// ❌ 过于通用的选择器
document.querySelectorAll('div div span');  // 慢

// ✅ 使用类名限定范围
document.querySelectorAll('.content .title span');  // 快

// ❌ 通配符
document.querySelectorAll('.container *');  // 非常慢

// ✅ 具体标签
document.querySelectorAll('.container div');  // 快
```

**规则 6: closest() 适合向上查找父元素**

`closest()` 从当前元素开始，向上遍历 DOM 树，查找第一个匹配的祖先元素：

```javascript
// 事件委托中的常见用法
table.addEventListener('click', (e) => {
  const row = e.target.closest('.row');

  if (row) {
    console.log('点击了行:', row);
  }
});

// 等价于手动遍历
function findClosest(element, selector) {
  let current = element;

  while (current && current !== document.body) {
    if (current.matches(selector)) {
      return current;
    }
    current = current.parentElement;
  }

  return null;
}
```

性能特点：

- ✅ 时间复杂度：O(深度)，通常很快（DOM 树深度有限）
- ✅ 比 `querySelectorAll` 快（不需要遍历整个 DOM）
- ✅ 适合事件委托场景

---

**记录者注**：

DOM 查询不是"免费"的。每次调用 `querySelectorAll`，浏览器都要遍历整个 DOM 树，检查每个节点是否匹配选择器。当 DOM 树有几千个节点时，这个过程会变得非常慢。

`getElementById` 之所以快，是因为浏览器维护了 ID 的哈希表，可以在 O(1) 时间内直接找到元素。这就是为什么老司机都推荐"能用 ID 就用 ID"。

性能优化的黄金法则：**测量、优化、验证**。不要凭直觉优化，用 Performance 面板测量实际性能，找到真正的瓶颈，然后针对性优化。100 倍的性能提升，往往来自于缓存一个查询结果这样的小改动。
