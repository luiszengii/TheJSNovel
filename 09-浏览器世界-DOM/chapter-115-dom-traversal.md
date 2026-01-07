《第 115 次记录：隐形的节点 —— DOM 树的真实面貌》

## 谜团现场

周三下午，你在做一个文档目录树的"展开/折叠"功能。

设计稿很简单：点击章节标题，展开显示下面的所有小节；再次点击，折叠隐藏。你看了看 HTML 结构，觉得不会太难：

```html
<div class="chapter">
  <h3 class="title">第一章：浏览器基础</h3>
  <ul class="sections">
    <li>1.1 渲染引擎</li>
    <li>1.2 JavaScript 引擎</li>
    <li>1.3 网络模块</li>
  </ul>
</div>
```

你写了个简单的遍历函数，获取所有子节点：

```javascript
const chapter = document.querySelector('.chapter');
const children = chapter.childNodes;

console.log('子节点数量：', children.length);
console.log('子节点列表：', children);
```

你期望看到 2 个子节点：`h3` 和 `ul`。但控制台输出让你愣住了：

```
子节点数量： 5
子节点列表： NodeList(5) [text, h3.title, text, ul.sections, text]
```

"5 个？" 你皱起眉头，"这三个 `text` 是什么东西？"

你打开 Elements 面板，仔细查看 DOM 树。浏览器显示的结构确实是这样的：

```
div.chapter
  #text "\n  "
  h3.title "第一章：浏览器基础"
  #text "\n  "
  ul.sections
    #text "\n    "
    li "1.1 渲染引擎"
    #text "\n    "
    li "1.2 JavaScript 引擎"
    #text "\n    "
    li "1.3 网络模块"
    #text "\n  "
  #text "\n"
```

你点击其中一个 `#text` 节点，DevTools 高亮显示的是...空白符？

"为什么连空格和换行都算节点？" 你自言自语，"这些 `#text` 节点从哪来的？"

你查看 HTML 源码，发现每个标签之间确实有换行符和缩进：

```html
<div class="chapter">
  <h3 class="title">第一章：浏览器基础</h3>   ← 这里有换行和缩进
  <ul class="sections">                        ← 这里也有
    <li>1.1 渲染引擎</li>                      ← 这里也有
    <li>1.2 JavaScript 引擎</li>
    <li>1.3 网络模块</li>
  </ul>
</div>
```

"难道这些空白符都被解析成了文本节点？" 你打开 MDN，开始查阅 DOM 遍历的文档。

## 线索追踪

你决定系统地测试 DOM 的遍历属性。首先是 `childNodes` 和 `children` 的区别：

```javascript
const chapter = document.querySelector('.chapter');

console.log('childNodes:', chapter.childNodes);
// NodeList(5) [text, h3, text, ul, text]

console.log('children:', chapter.children);
// HTMLCollection(2) [h3.title, ul.sections]
```

"有意思，" 你点了点头，"`children` 只返回元素节点，过滤掉了文本节点。"

你继续测试 `nextSibling` 和 `nextElementSibling`：

```javascript
const title = document.querySelector('.title');

console.log('nextSibling:', title.nextSibling);
// #text "\n  "   ← 文本节点！

console.log('nextElementSibling:', title.nextElementSibling);
// <ul class="sections">...</ul>   ← 元素节点
```

"原来如此，" 你在笔记本上记下，"浏览器提供了两套 API：一套包含所有节点类型，一套只包含元素节点。"

你写了一个递归函数，遍历整棵 DOM 树，看看到底有多少文本节点：

```javascript
function traverseTree(node, depth = 0) {
  const indent = '  '.repeat(depth);

  if (node.nodeType === Node.ELEMENT_NODE) {
    console.log(`${indent}元素: <${node.tagName.toLowerCase()}>`);
  } else if (node.nodeType === Node.TEXT_NODE) {
    const text = node.textContent.trim();
    if (text) {
      console.log(`${indent}文本: "${text}"`);
    } else {
      console.log(`${indent}文本: [空白]`);
    }
  } else if (node.nodeType === Node.COMMENT_NODE) {
    console.log(`${indent}注释: <!-- ${node.textContent} -->`);
  }

  // 递归遍历子节点
  node.childNodes.forEach(child => {
    traverseTree(child, depth + 1);
  });
}

traverseTree(document.querySelector('.chapter'));
```

输出结果让你震惊：

```
元素: <div>
  文本: [空白]
  元素: <h3>
    文本: "第一章：浏览器基础"
  文本: [空白]
  元素: <ul>
    文本: [空白]
    元素: <li>
      文本: "1.1 渲染引擎"
    文本: [空白]
    元素: <li>
      文本: "1.2 JavaScript 引擎"
    文本: [空白]
    元素: <li>
      文本: "1.3 网络模块"
    文本: [空白]
  文本: [空白]
```

"文本节点无处不在..." 你喃喃道。

你检查 HTML 源码，发现每个标签之间的换行符和缩进空格，都被浏览器严格地解析成了文本节点。即使这些文本节点的内容只是 `"\n  "`，浏览器也会忠实地创建它们。

"这就是 DOM 树的真实样子吗？" 你若有所思。

你尝试用 `nodeType === Node.ELEMENT_NODE` 过滤文本节点，重写遍历函数：

```javascript
function traverseElements(node, depth = 0) {
  const indent = '  '.repeat(depth);
  console.log(`${indent}<${node.tagName.toLowerCase()}>`);

  // 只遍历元素节点
  node.childNodes.forEach(child => {
    if (child.nodeType === Node.ELEMENT_NODE) {
      traverseElements(child, depth + 1);
    }
  });
}

traverseElements(document.querySelector('.chapter'));
```

代码可以工作，但看起来很繁琐。每次遍历都要检查 `nodeType`，增加了很多样板代码。

"等等，" 你突然想起，"浏览器应该提供了更好的方法。"

你重新打开 MDN，搜索 "DOM traversal"，找到了答案。

## 真相揭示

你发现，DOM 提供了**两套完整的遍历 API**：

**① Node 遍历（包含所有节点类型）**：

```javascript
// 父节点
node.parentNode

// 子节点
node.childNodes        // NodeList，包含所有类型节点
node.firstChild        // 第一个子节点（可能是文本节点）
node.lastChild         // 最后一个子节点（可能是文本节点）

// 兄弟节点
node.nextSibling       // 下一个兄弟节点（可能是文本节点）
node.previousSibling   // 上一个兄弟节点（可能是文本节点）
```

**② Element 遍历（只包含元素节点）**：

```javascript
// 父元素
node.parentElement

// 子元素
node.children               // HTMLCollection，只包含元素节点
node.firstElementChild      // 第一个子元素
node.lastElementChild       // 最后一个子元素

// 兄弟元素
node.nextElementSibling     // 下一个兄弟元素
node.previousElementSibling // 上一个兄弟元素
```

你重写了遍历函数，这次使用 Element 遍历 API：

```javascript
// 使用 Element 遍历 API
function traverseElementsClean(element, depth = 0) {
  const indent = '  '.repeat(depth);
  console.log(`${indent}<${element.tagName.toLowerCase()}>`);

  // 直接使用 children，自动过滤文本节点
  Array.from(element.children).forEach(child => {
    traverseElementsClean(child, depth + 1);
  });
}

traverseElementsClean(document.querySelector('.chapter'));
```

输出结果清晰多了：

```
<div>
  <h3>
  <ul>
    <li>
    <li>
    <li>
```

"这才是我想要的！" 你长舒一口气。

你继续研究，发现了更高级的遍历工具：**TreeWalker** 和 **NodeIterator**。

```javascript
// TreeWalker：提供灵活的 DOM 树遍历
const walker = document.createTreeWalker(
  document.querySelector('.chapter'),  // 根节点
  NodeFilter.SHOW_ELEMENT,              // 只显示元素节点
  {
    acceptNode(node) {
      // 可以自定义过滤逻辑
      if (node.tagName === 'LI') {
        return NodeFilter.FILTER_ACCEPT; // 接受
      }
      return NodeFilter.FILTER_SKIP; // 跳过（但继续遍历子节点）
    }
  }
);

// 遍历所有 li 元素
let currentNode = walker.nextNode();
while (currentNode) {
  console.log('找到 li:', currentNode.textContent);
  currentNode = walker.nextNode();
}
```

输出：

```
找到 li: 1.1 渲染引擎
找到 li: 1.2 JavaScript 引擎
找到 li: 1.3 网络模块
```

你还发现了一个有趣的事实：即使是空白符，浏览器也会严格按照 HTML 规范解析。你做了个实验：

```html
<!-- 实验 1：有换行和缩进 -->
<div id="test1">
  <span>A</span>
  <span>B</span>
</div>

<!-- 实验 2：无换行和缩进 -->
<div id="test2"><span>A</span><span>B</span></div>
```

```javascript
console.log('test1 的 childNodes:', document.querySelector('#test1').childNodes.length);
// 5 个节点：text, span, text, span, text

console.log('test2 的 childNodes:', document.querySelector('#test2').childNodes.length);
// 2 个节点：span, span
```

"原来 HTML 的格式化会影响 DOM 树的结构，" 你在笔记里写道，"这不是 bug，而是浏览器对 HTML 规范的忠实执行。"

你重构了"展开/折叠"功能，代码变得简洁多了：

```javascript
// 重构后的展开/折叠功能
document.querySelectorAll('.chapter .title').forEach(title => {
  title.addEventListener('click', () => {
    // 使用 nextElementSibling 直接获取下一个元素节点
    const sections = title.nextElementSibling;

    if (sections && sections.classList.contains('sections')) {
      sections.classList.toggle('collapsed');
    }
  });
});
```

功能完美运行。你对 DOM 树的理解又深了一层。

## DOM 遍历机制

**规则 1: DOM 树包含所有节点类型**

DOM 树不仅仅包含元素节点，还包含：

| 节点类型 | nodeType 常量 | nodeType 值 | 示例 |
|---------|--------------|------------|------|
| **元素节点** | `Node.ELEMENT_NODE` | 1 | `<div>`, `<span>` |
| **文本节点** | `Node.TEXT_NODE` | 3 | `"Hello"`, `"\n  "` |
| **注释节点** | `Node.COMMENT_NODE` | 8 | `<!-- comment -->` |
| 文档节点 | `Node.DOCUMENT_NODE` | 9 | `document` |
| 文档类型节点 | `Node.DOCUMENT_TYPE_NODE` | 10 | `<!DOCTYPE html>` |
| 文档片段节点 | `Node.DOCUMENT_FRAGMENT_NODE` | 11 | `DocumentFragment` |

检查节点类型：

```javascript
const node = document.querySelector('.title').nextSibling;

if (node.nodeType === Node.TEXT_NODE) {
  console.log('这是文本节点，内容是：', node.textContent);
} else if (node.nodeType === Node.ELEMENT_NODE) {
  console.log('这是元素节点，标签是：', node.tagName);
}
```

**规则 2: childNodes 包含所有子节点，children 只包含元素**

```javascript
const container = document.querySelector('.container');

// childNodes - 包含所有节点类型（元素、文本、注释等）
console.log(container.childNodes);
// NodeList(7) [text, div, text, span, text, comment, text]

// children - 只包含元素节点
console.log(container.children);
// HTMLCollection(2) [div, span]
```

区别：

| 属性 | 返回类型 | 包含节点类型 | 是否动态 |
|------|---------|------------|---------|
| `childNodes` | `NodeList` | 所有类型（元素、文本、注释等） | ✅ 动态 |
| `children` | `HTMLCollection` | 只有元素节点 | ✅ 动态 |

**规则 3: 空格和换行会生成文本节点**

HTML 中的空白符（空格、换行、制表符）会被解析成文本节点：

```html
<div>
  <span>A</span>
  <span>B</span>
</div>
```

实际的 DOM 树结构：

```
div
├─ #text "\n  "          ← 换行 + 两个空格
├─ span
│  └─ #text "A"
├─ #text "\n  "          ← 换行 + 两个空格
├─ span
│  └─ #text "B"
└─ #text "\n"            ← 换行
```

如果不想要文本节点，可以移除空白符：

```html
<div><span>A</span><span>B</span></div>
```

此时的 DOM 树：

```
div
├─ span
│  └─ #text "A"
└─ span
   └─ #text "B"
```

**规则 4: 使用 Element 遍历属性避免文本节点干扰**

对比两套 API：

```javascript
const container = document.querySelector('.container');

// ===== Node 遍历（包含所有节点类型）=====
container.childNodes        // 包含文本节点
container.firstChild        // 可能是文本节点
container.lastChild         // 可能是文本节点
container.nextSibling       // 可能是文本节点
container.previousSibling   // 可能是文本节点

// ===== Element 遍历（只包含元素节点）=====
container.children             // 只有元素节点
container.firstElementChild    // 第一个元素节点
container.lastElementChild     // 最后一个元素节点
container.nextElementSibling   // 下一个元素节点
container.previousElementSibling // 上一个元素节点
```

实际案例：

```html
<ul class="list">
  <li>Item 1</li>
  <li>Item 2</li>
  <li>Item 3</li>
</ul>
```

```javascript
const list = document.querySelector('.list');
const firstItem = list.firstElementChild; // <li>Item 1</li>

console.log(firstItem.nextSibling);
// #text "\n  "   ← 文本节点！

console.log(firstItem.nextElementSibling);
// <li>Item 2</li>   ← 元素节点
```

**规则 5: 递归遍历时注意深度优先 vs 广度优先**

**深度优先遍历（DFS）**：

```javascript
function traverseDFS(element, callback, depth = 0) {
  callback(element, depth);

  Array.from(element.children).forEach(child => {
    traverseDFS(child, callback, depth + 1);
  });
}

traverseDFS(document.querySelector('.root'), (el, depth) => {
  console.log('  '.repeat(depth) + el.tagName);
});

// 输出顺序：
// DIV (root)
//   H1
//     SPAN
//   UL
//     LI
//     LI
```

**广度优先遍历（BFS）**：

```javascript
function traverseBFS(element, callback) {
  const queue = [element];
  let depth = 0;

  while (queue.length > 0) {
    const levelSize = queue.length;

    for (let i = 0; i < levelSize; i++) {
      const current = queue.shift();
      callback(current, depth);

      queue.push(...Array.from(current.children));
    }

    depth++;
  }
}

traverseBFS(document.querySelector('.root'), (el, depth) => {
  console.log('  '.repeat(depth) + el.tagName);
});

// 输出顺序：
// DIV (root)
//   H1
//   UL
//     SPAN
//     LI
//     LI
```

**规则 6: TreeWalker 适合复杂的遍历场景**

`TreeWalker` 提供了最灵活的遍历能力：

```javascript
// 创建 TreeWalker
const walker = document.createTreeWalker(
  rootNode,                  // 根节点
  NodeFilter.SHOW_ELEMENT,   // 显示哪些节点类型
  {
    acceptNode(node) {
      // 自定义过滤逻辑
      return NodeFilter.FILTER_ACCEPT; // 接受
      // return NodeFilter.FILTER_REJECT; // 拒绝（跳过子树）
      // return NodeFilter.FILTER_SKIP;   // 跳过（但遍历子树）
    }
  }
);

// 遍历方法
walker.firstChild()    // 移动到第一个子节点
walker.lastChild()     // 移动到最后一个子节点
walker.nextNode()      // 移动到下一个节点（深度优先）
walker.previousNode()  // 移动到上一个节点
walker.nextSibling()   // 移动到下一个兄弟节点
walker.previousSibling() // 移动到上一个兄弟节点
walker.parentNode()    // 移动到父节点
```

实际应用：查找所有包含特定文本的元素：

```javascript
const walker = document.createTreeWalker(
  document.body,
  NodeFilter.SHOW_ELEMENT,
  {
    acceptNode(node) {
      if (node.textContent.includes('bug')) {
        return NodeFilter.FILTER_ACCEPT;
      }
      return NodeFilter.FILTER_SKIP;
    }
  }
);

let node = walker.nextNode();
while (node) {
  console.log('找到包含 "bug" 的元素:', node.tagName, node.textContent);
  node = walker.nextNode();
}
```

---

**记录者注**：

DOM 树不是你在 HTML 代码中看到的简洁结构，而是包含了所有空白符、注释、文本的完整树。每个换行、每个缩进空格，都会被忠实地解析成文本节点。

这不是浏览器的 bug，而是对 HTML 规范的严格执行。HTML 是纯文本格式，浏览器必须保留所有字符，包括那些"看不见"的空白符。

理解 DOM 树的真实面貌，才能在遍历节点时避免被文本节点干扰。记住：**当你需要遍历元素时，用 `children`、`nextElementSibling`；当你需要处理所有内容时，用 `childNodes`、`nextSibling`。**
